import contextlib
import ftplib
import importlib.util
import io
from pathlib import Path
import tempfile
import socket
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[2] / "skills/sylixos/scripts/ftp_client.py"
SPEC = importlib.util.spec_from_file_location("sylixos_ftp", SCRIPT)
ftp_client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ftp_client)


class FtpClientTests(unittest.TestCase):
    def parse(self, *args):
        with contextlib.redirect_stderr(io.StringIO()):
            return ftp_client.build_parser().parse_args(["127.0.0.1", *args])

    def test_recursive_delete_rejects_root_aliases(self):
        for path in ("/", "//", "///", "/apps/..", "//apps/.."):
            with self.subTest(path=path), self.assertRaises(SystemExit):
                self.parse("rmtree", path)

    def test_list_can_read_root(self):
        self.assertEqual(self.parse("list", "//apps/..").remote_path, "/")

    def test_non_root_paths_are_normalized(self):
        self.assertEqual(self.parse("delete", "//apps/a/../file").remote_path, "/apps/file")

    def test_missing_directory_is_an_error(self):
        ftp = Mock()
        ftp.sendcmd.side_effect = ftplib.error_perm("550 Not found")
        ftp.nlst.side_effect = ftplib.error_perm("550 Not found")
        with self.assertRaises(ftplib.error_perm):
            ftp_client.entries(ftp, "/missing")

    def test_listing_permission_error_is_not_an_empty_directory(self):
        ftp = Mock()
        ftp.sendcmd.return_value = "250 OK"
        ftp.nlst.side_effect = ftplib.error_perm("550 Permission denied")
        ftp.retrlines.side_effect = ftplib.error_perm("550 Permission denied")
        with self.assertRaises(ftplib.error_perm):
            ftp_client.entries(ftp, "/restricted")

    def test_empty_directory_with_550_nlst_requires_successful_empty_list(self):
        ftp = Mock()
        ftp.sendcmd.return_value = "250 OK"
        ftp.nlst.side_effect = ftplib.error_perm("550 No files")
        ftp.retrlines.return_value = "226 Done"
        self.assertEqual(ftp_client.entries(ftp, "/empty"), [])
        ftp.retrlines.assert_called_once()

    def test_failed_nlst_with_nonempty_list_still_reports_failure(self):
        ftp = Mock()
        ftp.sendcmd.return_value = "250 OK"
        ftp.nlst.side_effect = ftplib.error_perm("550 Cannot list")
        ftp.retrlines.side_effect = lambda line, callback: callback("file")
        with self.assertRaises(ftplib.error_perm):
            ftp_client.entries(ftp, "/apps")

    def test_upload_verify_reads_back_binary_content(self):
        self.check_upload(b"\x00payload\xff", b"\x00payload\xff", verify=True)

    def test_upload_verify_rejects_same_size_corruption(self):
        with self.assertRaisesRegex(RuntimeError, "verif"):
            self.check_upload(b"abcd", b"abce", verify=True)

    def test_upload_verify_handles_empty_files(self):
        self.check_upload(b"", b"", verify=True)

    def test_upload_without_verify_does_not_download(self):
        ftp = self.check_upload(b"data", b"unused", verify=False)
        ftp.retrbinary.assert_not_called()

    def test_readback_failure_reports_upload_failure_without_success_message(self):
        ftp = Mock()
        ftp.retrbinary.side_effect = ftplib.error_perm("550 Cannot read")
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / "payload"
            local.write_bytes(b"data")
            args = self.parse("upload", str(local), "/apps/payload", "--verify")
            output = io.StringIO()
            with patch.object(ftp_client.ftplib, "FTP", return_value=ftp), \
                    patch.object(ftp_client.time, "sleep"), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                self.assertEqual(ftp_client.run_ftp(args), 1)
        self.assertNotIn("Successfully uploaded", output.getvalue())
        self.assertIn("Cannot read", output.getvalue())
        self.assertEqual(ftp.storbinary.call_count, 1)

    def test_permanent_errors_do_not_retry(self):
        for error in (ftplib.error_perm("530 Login incorrect"), ftplib.error_perm("550 Permission denied"),
                      FileNotFoundError("missing local file"), PermissionError("local permission"),
                      RuntimeError("verification failed")):
            with self.subTest(error=error):
                ftp = Mock()
                ftp.login.side_effect = error
                with patch.object(ftp_client.ftplib, "FTP", return_value=ftp), \
                        patch.object(ftp_client.time, "sleep") as sleep, \
                        contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(ftp_client.run_ftp(self.parse("list", "/apps")), 1)
                ftp.connect.assert_called_once()
                sleep.assert_not_called()

    def test_transient_error_retries_with_new_connection(self):
        for error in (socket.timeout("timeout"), ConnectionResetError("reset"), EOFError(), ftplib.error_temp("421 Busy")):
            with self.subTest(error=error):
                first, second = Mock(), Mock()
                first.connect.side_effect = error
                second.sendcmd.return_value = "250 OK"
                second.nlst.return_value = []
                with patch.object(ftp_client.ftplib, "FTP", side_effect=[first, second]), \
                        patch.object(ftp_client.time, "sleep") as sleep, \
                        contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(ftp_client.run_ftp(self.parse("list", "/apps")), 0)
                sleep.assert_called_once()
                first.close.assert_called_once()

    def test_delete_does_not_retry_transient_failure(self):
        ftp = Mock()
        ftp.connect.side_effect = socket.timeout("timeout")
        with patch.object(ftp_client.ftplib, "FTP", return_value=ftp), \
                patch.object(ftp_client.time, "sleep") as sleep, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ftp_client.run_ftp(self.parse("delete", "/apps/file")), 1)
        ftp.connect.assert_called_once()
        sleep.assert_not_called()

    def test_progress_is_throttled_and_reports_total_bytes(self):
        error = io.StringIO()
        with patch.object(ftp_client.time, "monotonic", return_value=1.0), contextlib.redirect_stderr(error):
            progress = ftp_client.TransferProgress("upload", 1000)
            for _ in range(1000):
                progress.update(b"x")
            progress.finish()
        self.assertLessEqual(len(error.getvalue().splitlines()), 2)
        self.assertIn("1000/1000 bytes", error.getvalue())

    def test_progress_upload_preserves_verify_and_keeps_stdout_clean(self):
        ftp = Mock()
        ftp.storbinary.side_effect = lambda command, source, blocksize, callback: callback(source.read())
        ftp.retrbinary.side_effect = lambda command, callback, blocksize: callback(b"data")
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / "payload"
            local.write_bytes(b"data")
            args = self.parse("upload", str(local), "/apps/file", "--verify", "--progress")
            output, error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                ftp_client.dispatch(ftp, args, [])
        self.assertIn("Verified SHA-256", output.getvalue())
        self.assertIn("upload: 4/4 bytes", error.getvalue())
        self.assertIn("verify: 4/4 bytes", error.getvalue())

    def test_download_progress_and_content(self):
        ftp = Mock()
        ftp.sendcmd.side_effect = ["200 Binary", "213 4"]
        ftp.retrbinary.side_effect = lambda command, callback, blocksize: callback(b"data")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "download"
            args = self.parse("download", str(target), "/apps/file", "--progress")
            output, error = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                ftp_client.dispatch(ftp, args, [])
            self.assertEqual(target.read_bytes(), b"data")
            self.assertEqual(list(target.parent.iterdir()), [target])
        self.assertIn("download: 4/4 bytes", error.getvalue())

    def test_download_failure_removes_partial_and_preserves_existing_destination(self):
        ftp = Mock()
        def receive(command, callback, blocksize):
            callback(b"partial")
            raise ftplib.error_perm("550 Read failed")
        ftp.retrbinary.side_effect = receive
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "download"
            target.write_bytes(b"original")
            args = self.parse("download", str(target), "/apps/file")
            with patch.object(ftp_client.ftplib, "FTP", return_value=ftp), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ftp_client.run_ftp(args), 1)
            self.assertEqual(target.read_bytes(), b"original")
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_download_progress_reports_local_replace_failure(self):
        ftp = Mock()
        ftp.sendcmd.side_effect = ["200 Binary", "213 4"]
        ftp.retrbinary.side_effect = lambda command, callback, blocksize: callback(b"data")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "download"
            error = io.StringIO()
            with patch.object(ftp_client.os, "replace", side_effect=PermissionError("cannot replace")), \
                    contextlib.redirect_stderr(error):
                with self.assertRaises(PermissionError):
                    ftp_client.download(ftp, "/apps/file", str(target), [], progress=True)
        self.assertIn("failed", error.getvalue())

    def test_dry_run_listing_failure_returns_nonzero_without_retry(self):
        ftp = Mock()
        ftp.sendcmd.return_value = "250 OK"
        ftp.nlst.side_effect = ftplib.error_perm("550 Permission denied")
        ftp.retrlines.side_effect = ftplib.error_perm("550 Permission denied")
        args = self.parse("rmtree", "/apps/test", "--dry-run")
        output = io.StringIO()
        with patch.object(ftp_client.ftplib, "FTP", return_value=ftp), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.assertEqual(ftp_client.run_ftp(args), 1)
        ftp.connect.assert_called_once()
        self.assertNotIn("Dry run complete", output.getvalue())
        self.assertFalse(any(call.args[0].startswith(("DELE ", "RMD ")) for call in ftp.sendcmd.call_args_list))

    def check_upload(self, local_data, remote_data, verify):
        ftp = Mock()
        def store(command, source, blocksize=8192, callback=None):
            while chunk := source.read(3):
                if callback:
                    callback(chunk)
        ftp.storbinary.side_effect = store
        ftp.retrbinary.side_effect = lambda command, callback, blocksize=8192: callback(remote_data)
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / "payload"
            local.write_bytes(local_data)
            args = self.parse("upload", str(local), "/apps/payload", *(["--verify"] if verify else []))
            with contextlib.redirect_stdout(io.StringIO()):
                ftp_client.dispatch(ftp, args, [])
        if verify:
            ftp.retrbinary.assert_called_once()
        return ftp

    def test_dry_run_lists_nested_deletions_without_mutations(self):
        self.check_tree(dry_run=True, contents_only=False)

    def test_dry_run_contents_only_keeps_root(self):
        self.check_tree(dry_run=True, contents_only=True)

    def test_recursive_delete_accepts_257_and_keeps_root_when_requested(self):
        self.check_tree(dry_run=False, contents_only=True)

    def check_tree(self, dry_run, contents_only):
        ftp = Mock()
        ftp.sendcmd.return_value = "257 OK"
        directories = {"/apps/test", "/apps/test/sub"}
        listings = {"/apps/test": ["sub", "file"], "/apps/test/sub": ["nested"]}
        options = (["--dry-run"] if dry_run else []) + (["--contents-only"] if contents_only else [])
        args = self.parse("rmtree", "/apps/test", *options)
        output = io.StringIO()
        with patch.object(ftp_client, "is_dir", side_effect=lambda ftp, path: path in directories), \
                patch.object(ftp_client, "entries", side_effect=lambda ftp, path: listings[path]), \
                contextlib.redirect_stdout(output):
            ftp_client.dispatch(ftp, args, [])
        commands = [call.args[0] for call in ftp.sendcmd.call_args_list]
        deletions = [command for command in commands if command.startswith(("DELE ", "RMD "))]
        if dry_run:
            self.assertEqual(deletions, [])
            self.assertIn("/apps/test/sub/nested", output.getvalue())
            self.assertIn("/apps/test/file", output.getvalue())
            self.assertEqual("Would remove directory /apps/test\n" in output.getvalue(), not contents_only)
        else:
            self.assertEqual(deletions, ["DELE /apps/test/sub/nested", "RMD /apps/test/sub", "DELE /apps/test/file"])

    def test_contents_only_reports_listing_failure(self):
        ftp = Mock()
        args = self.parse("rmtree", "/apps/test", "--contents-only")
        with patch.object(ftp_client, "is_dir", return_value=True), \
                patch.object(ftp_client, "entries", side_effect=ftplib.error_perm("550 Permission denied")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(ftplib.error_perm):
                ftp_client.dispatch(ftp, args, [])
        self.assertNotIn("Emptied", output.getvalue())
        ftp.sendcmd.assert_not_called()


if __name__ == "__main__":
    unittest.main()
