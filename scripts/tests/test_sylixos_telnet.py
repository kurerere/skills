import contextlib
import importlib.util
import io
from pathlib import Path
import socket
import tempfile
import tracemalloc
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[2] / "skills/sylixos/scripts/telnet_runner.py"
SPEC = importlib.util.spec_from_file_location("sylixos_telnet", SCRIPT)
telnet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(telnet)
PROMPT = "[root@sylixos:/root]# "
TIMEOUTS = dict(connect=1, login=1, prompt=1, command=.01)


class TelnetTests(unittest.TestCase):
    def connection(self, chunks):
        sock = Mock()
        sock.__enter__ = Mock(return_value=sock)
        sock.__exit__ = Mock(return_value=False)
        sock.recv.side_effect = [b"login: ", b"password: ", PROMPT.encode(), *chunks]
        return sock

    def run_command(self, chunks, **options):
        sock = self.connection(chunks)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(telnet.socket, "create_connection", return_value=sock), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = telnet.run_telnet("127.0.0.1", ["help"], dict(TIMEOUTS, command=1), **options)
        return result, stdout.getvalue(), stderr.getvalue(), sock

    def test_default_login_is_root(self):
        with patch.dict(telnet.os.environ, {}, clear=True):
            _, _, _, sock = self.run_command([b"help\r\n" + PROMPT.encode()])
        sent = [call.args[0] for call in sock.sendall.call_args_list]
        self.assertEqual(sent[:2], [b"root\n", b"root\n"])

    def test_login_uses_given_user_and_password_env(self):
        with patch.dict(telnet.os.environ, {"SYLIXOS_PASSWORD": "s3cret"}):
            _, _, _, sock = self.run_command([b"help\r\n" + PROMPT.encode()], user="admin")
        sent = [call.args[0] for call in sock.sendall.call_args_list]
        self.assertEqual(sent[:2], [b"admin\n", b"s3cret\n"])

    def test_hash_and_arrow_in_output_do_not_finish_command(self):
        code, output, error, sock = self.run_command([
            b"help\r\nprogress #", b"\r\nprogress =>", b"\r\nfinished\r\n" + PROMPT.encode()
        ])
        self.assertEqual(code, 0)
        self.assertEqual(output, "progress #\nprogress =>\nfinished\n")
        self.assertEqual(error, "")
        self.assertEqual(sock.recv.call_count, 6)

    def test_prompt_path_can_change_after_cd(self):
        code, output, _, _ = self.run_command([b"help\r\n[root@sylixos:/apps]# "])
        self.assertEqual((code, output), (0, ""))

    def test_prompt_path_with_brackets_and_colon(self):
        code, output, _, _ = self.run_command([b"help\r\n[root@sylixos:/apps/a]b:c]# "])
        self.assertEqual((code, output), (0, ""))

    def test_real_error_containing_command_is_preserved(self):
        code, output, _, _ = self.run_command([b"tool: could not execute help\r\n" + PROMPT.encode()])
        self.assertEqual(code, 0)
        self.assertEqual(output, "tool: could not execute help\n")

    def test_disconnect_preserves_partial_output_and_is_not_timeout(self):
        code, output, error, _ = self.run_command([b"help\r\npartial output", b""])
        self.assertEqual(code, 1)
        self.assertEqual(output, "partial output")
        self.assertIn("closed", error)
        self.assertNotIn("timed out", error)

    def test_connection_reset_is_not_timeout(self):
        code, output, error, _ = self.run_command([b"help\r\npartial\n", ConnectionResetError("reset")])
        self.assertEqual((code, output), (1, "partial\n"))
        self.assertIn("reset", error)
        self.assertNotIn("timed out", error)

    def test_timeout_preserves_partial_output(self):
        sock = self.connection([])
        login = iter([b"login: ", b"password: ", PROMPT.encode(), b"help\r\npartial"])
        def receive(size):
            try:
                return next(login)
            except StopIteration:
                raise socket.timeout()
        sock.recv.side_effect = receive
        output, error = io.StringIO(), io.StringIO()
        with patch.object(telnet.socket, "create_connection", return_value=sock), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            self.assertEqual(telnet.run_telnet("127.0.0.1", ["help"], TIMEOUTS), 2)
        self.assertEqual(output.getvalue(), "partial")
        self.assertIn("timed out", error.getvalue())

    def test_stream_is_visible_before_command_finishes_and_output_file_matches(self):
        stdout = io.StringIO()
        sock = self.connection([])
        chunks = iter([b"login: ", b"password: ", PROMPT.encode(), b"help\r\nfirst\r\n"])
        def receive(size):
            try:
                return next(chunks)
            except StopIteration:
                self.assertEqual(stdout.getvalue(), "first\n")
                return b"second\r\n" + PROMPT.encode()
        sock.recv.side_effect = receive
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.txt"
            with patch.object(telnet.socket, "create_connection", return_value=sock), \
                    contextlib.redirect_stdout(stdout):
                result = telnet.run_telnet("127.0.0.1", ["help"], TIMEOUTS, stream=True, output_path=path)
            self.assertEqual(result, 0)
            self.assertEqual(path.read_text(), "first\nsecond\n")
        self.assertEqual(stdout.getvalue(), "first\nsecond\n")

    def test_split_utf8_crlf_and_prompt(self):
        data = "help\r\n中文\r\n".encode() + PROMPT.encode()
        code, output, _, _ = self.run_command([bytes([value]) for value in data])
        self.assertEqual((code, output), (0, "中文\n"))

    def test_output_without_newline_before_prompt_is_preserved(self):
        code, output, _, _ = self.run_command([b"help\r\nunterminated" + PROMPT.encode()])
        self.assertEqual((code, output), (0, "unterminated"))

    def test_stream_emits_partial_lines_before_command_finishes(self):
        stdout = io.StringIO()
        sock = self.connection([])
        chunks = iter([b"login: ", b"password: ", PROMPT.encode(), b"help\r\nprogress 50%"])
        def receive(size):
            try:
                return next(chunks)
            except StopIteration:
                self.assertEqual(stdout.getvalue(), "progress 50%")
                return b"\r\n" + PROMPT.encode()
        sock.recv.side_effect = receive
        with patch.object(telnet.socket, "create_connection", return_value=sock), contextlib.redirect_stdout(stdout):
            self.assertEqual(telnet.run_telnet("127.0.0.1", ["help"], TIMEOUTS, stream=True), 0)

    def test_large_line_does_not_lose_output(self):
        data = b"x" * 65536
        code, output, _, _ = self.run_command([b"help\r\n", *([data] * 32), b"\r\n" + PROMPT.encode()])
        self.assertEqual(code, 0)
        self.assertEqual(output, "x" * (32 * len(data)) + "\n")

    def test_login_prompt_split_before_trailing_space_does_not_leak_echo(self):
        sock = self.connection([])
        sock.recv.side_effect = [b"login: ", b"password: ", PROMPT.rstrip().encode(), b" ",
                                b"help\r\nresult\r\n" + PROMPT.encode()]
        output = io.StringIO()
        with patch.object(telnet.socket, "create_connection", return_value=sock), contextlib.redirect_stdout(output):
            self.assertEqual(telnet.run_telnet("127.0.0.1", ["help"], TIMEOUTS), 0)
        self.assertEqual(output.getvalue(), "result\n")

    def test_stream_flushes_fragments_even_when_clock_has_not_advanced(self):
        sink = Mock()
        with patch.object(telnet.time, "monotonic", return_value=1.0):
            writer = telnet.CommandOutput("help", [sink], live=True)
            writer.feed("help\r\nfirst")
            writer.feed("second")
        self.assertEqual(sink.flush.call_count, 2)

    def test_receiver_memory_does_not_grow_with_streamed_output(self):
        class Source:
            left = 8 * 1024 * 1024
            def settimeout(self, value):
                pass
            def recv(self, size):
                if self.left:
                    count = min(self.left, size)
                    self.left -= count
                    return b"x" * (count - 1) + b"\n"
                return PROMPT.encode()
        received = 0
        def consume(text):
            nonlocal received
            received += len(text)
        pattern, prefix = telnet.shell_prompt(PROMPT)
        tracemalloc.start()
        try:
            result = telnet.recv_until(Source(), pattern, 10, on_text=consume, prompt_prefix=prefix)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        self.assertEqual(result.status, "matched")
        self.assertEqual(received, 8 * 1024 * 1024)
        self.assertLess(peak, 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
