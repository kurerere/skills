import argparse
import errno
import ftplib
import hashlib
import math
import os
from pathlib import Path
import posixpath
import socket
import sys
import time


DEFAULT_TIMEOUT = 10.0
RETRYING_MODES = {"upload", "download", "list", "size", "mkdir"}
TRANSFER_BLOCK_SIZE = 65536


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid timeout: {value}") from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and greater than zero")
    return timeout


def valid_port(value):
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid port: {value}") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def absolute_remote(value):
    if not value.startswith("/"):
        raise argparse.ArgumentTypeError(f"remote path must be absolute: {value}")
    return posixpath.normpath("/" + value.lstrip("/"))


def non_root_remote(value):
    normalized = absolute_remote(value)
    if normalized == "/":
        raise argparse.ArgumentTypeError("refusing to operate on /")
    return normalized


# SylixOS FTP answers DELE with 257 instead of 250, which ftplib's
# delete() rejects; every command here accepts any 2xx reply instead.
def command(ftp, line):
    response = ftp.sendcmd(line)
    if not response.startswith("2"):
        raise ftplib.error_reply(response)
    return response


def is_dir(ftp, path):
    try:
        command(ftp, f"CWD {path}")
        return True
    except ftplib.error_perm:
        return False
    finally:
        try:
            command(ftp, "CWD /")
        except ftplib.all_errors:
            pass


def entries(ftp, path):
    command(ftp, f"CWD {path}")
    command(ftp, "CWD /")
    try:
        names = ftp.nlst(path)
    except ftplib.error_perm as error:
        if str(error).startswith("550"):
            lines = []
            ftp.retrlines(f"LIST {path}", lines.append)
            if not lines:
                return []
        raise
    result = []
    for name in names:
        base = name.rstrip("/").rsplit("/", 1)[-1]
        if base not in ("", ".", ".."):
            result.append(base)
    return sorted(set(result))


class TransferProgress:
    def __init__(self, operation, total=None):
        self.operation = operation
        self.total = total
        self.transferred = 0
        self.started = time.monotonic()
        self.last_report = self.started

    def update(self, block):
        self.transferred += len(block)
        now = time.monotonic()
        if now - self.last_report >= .5:
            self.report(now)

    def report(self, now, status=""):
        elapsed = max(0.0, now - self.started)
        rate = self.transferred / elapsed / (1024 * 1024) if elapsed else 0.0
        count = str(self.transferred) if self.total is None else f"{self.transferred}/{self.total}"
        percent = f" ({100 * self.transferred / self.total:.1f}%)" if self.total else ""
        print(f"{self.operation}: {count} bytes{percent}, {elapsed:.2f}s, {rate:.2f} MiB/s{status}", file=sys.stderr, flush=True)
        self.last_report = now

    def finish(self, success=True):
        self.report(time.monotonic(), " done" if success else " failed")


def upload(ftp, local_path, remote_path, verify=False, progress=False):
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"local file does not exist: {local_path}")
    local_hash = hashlib.sha256() if verify else None
    with open(local_path, "rb") as source:
        total = os.fstat(source.fileno()).st_size
        meter = TransferProgress("upload", total) if progress else None
        def uploaded(block):
            if local_hash is not None:
                local_hash.update(block)
            if meter is not None:
                meter.update(block)
        try:
            ftp.storbinary(f"STOR {remote_path}", source, blocksize=TRANSFER_BLOCK_SIZE,
                           callback=uploaded if verify or progress else None)
        except Exception:
            if meter is not None:
                meter.finish(success=False)
            raise
        if meter is not None:
            meter.finish()
    if verify:
        remote_hash = hashlib.sha256()
        meter = TransferProgress("verify", total) if progress else None
        def verified(block):
            remote_hash.update(block)
            if meter is not None:
                meter.update(block)
        try:
            ftp.retrbinary(f"RETR {remote_path}", verified, blocksize=TRANSFER_BLOCK_SIZE)
            if local_hash.digest() != remote_hash.digest():
                raise RuntimeError(f"upload verification failed for {remote_path}: SHA-256 mismatch")
        except Exception:
            if meter is not None:
                meter.finish(success=False)
            raise
        if meter is not None:
            meter.finish()
        print(f"Verified SHA-256: {remote_hash.hexdigest()}")
    print(f"Successfully uploaded {local_path} to {remote_path}")


def download(ftp, remote_path, local_path, partials, progress=False):
    destination = Path(local_path)
    partial_path = destination.with_name(f".{destination.name}.part-{os.getpid()}")
    partials.append(partial_path)
    total = None
    if progress:
        try:
            command(ftp, "TYPE I")
            total = int(command(ftp, f"SIZE {remote_path}").split()[1])
        except ftplib.error_perm:
            pass
    meter = TransferProgress("download", total) if progress else None
    try:
        with open(partial_path, "wb") as target:
            def received(block):
                target.write(block)
                meter.update(block)
            ftp.retrbinary(f"RETR {remote_path}", received if progress else target.write,
                           blocksize=TRANSFER_BLOCK_SIZE)
        os.replace(partial_path, destination)
    except Exception:
        if meter is not None:
            meter.finish(success=False)
        raise
    if meter is not None:
        meter.finish()
    print(f"Successfully downloaded {remote_path} to {local_path}")


def list_dir(ftp, remote_path):
    for name in entries(ftp, remote_path):
        child = posixpath.join(remote_path, name)
        print(f"{name}/" if is_dir(ftp, child) else name)


def size(ftp, remote_path):
    command(ftp, "TYPE I")
    print(int(command(ftp, f"SIZE {remote_path}").split()[1]))


def mkdir(ftp, remote_path):
    current = "/"
    for part in remote_path.strip("/").split("/"):
        current = posixpath.join(current, part)
        if not is_dir(ftp, current):
            command(ftp, f"MKD {current}")
    print(f"Directory ready: {remote_path}")


def delete(ftp, remote_path):
    if is_dir(ftp, remote_path):
        raise IsADirectoryError(f"remote path is a directory: {remote_path}")
    command(ftp, f"DELE {remote_path}")
    print(f"Deleted {remote_path}")


def rmdir(ftp, remote_path):
    command(ftp, f"RMD {remote_path}")
    print(f"Removed directory {remote_path}")


def remove_tree(ftp, remote_path, dry_run=False, contents_only=False):
    for name in entries(ftp, remote_path):
        child = posixpath.join(remote_path, name)
        if is_dir(ftp, child):
            remove_tree(ftp, child, dry_run=dry_run)
        else:
            if dry_run:
                print(f"Would delete file {child}")
            else:
                command(ftp, f"DELE {child}")
    if not contents_only:
        if dry_run:
            print(f"Would remove directory {remote_path}")
        else:
            command(ftp, f"RMD {remote_path}")


def rmtree(ftp, remote_path, contents_only, dry_run=False):
    remote_path = non_root_remote(remote_path)
    if not is_dir(ftp, remote_path):
        raise NotADirectoryError(f"remote path is not a directory: {remote_path}")
    remove_tree(ftp, remote_path, dry_run=dry_run, contents_only=contents_only)
    if dry_run:
        print("Dry run complete; no files or directories were removed")
    elif contents_only:
        print(f"Emptied {remote_path}")
    else:
        print(f"Removed tree {remote_path}")


def dispatch(ftp, args, partials):
    if args.mode == "upload":
        upload(ftp, args.local_path, args.remote_path, verify=args.verify, progress=args.progress)
    elif args.mode == "download":
        download(ftp, args.remote_path, args.local_path, partials, progress=args.progress)
    elif args.mode == "list":
        list_dir(ftp, args.remote_path)
    elif args.mode == "size":
        size(ftp, args.remote_path)
    elif args.mode == "mkdir":
        mkdir(ftp, args.remote_path)
    elif args.mode == "delete":
        delete(ftp, args.remote_path)
    elif args.mode == "rmdir":
        rmdir(ftp, args.remote_path)
    else:
        rmtree(ftp, args.remote_path, args.contents_only, dry_run=args.dry_run)


def retryable(error):
    if isinstance(error, (ftplib.error_temp, TimeoutError, ConnectionError, EOFError)):
        return True
    if isinstance(error, socket.gaierror):
        return error.errno == socket.EAI_AGAIN
    return isinstance(error, OSError) and error.errno in {
        errno.ENETDOWN, errno.ENETUNREACH, errno.EHOSTUNREACH,
        errno.ECONNABORTED, errno.ECONNRESET, errno.ECONNREFUSED, errno.ETIMEDOUT, errno.EPIPE,
    }


def run_ftp(args):
    attempts = 3 if args.mode in RETRYING_MODES else 1
    last_error = None
    for attempt in range(attempts):
        partials = []
        ftp = ftplib.FTP()
        try:
            ftp.connect(args.ip, args.port, timeout=args.timeout)
            ftp.login("root", "root")
            dispatch(ftp, args, partials)
            return 0
        except Exception as error:
            last_error = error
            for partial_path in partials:
                try:
                    os.remove(partial_path)
                except OSError:
                    pass
        finally:
            try:
                ftp.close()
            except OSError:
                pass
        if not retryable(last_error) or attempt + 1 >= attempts:
            break
        print(f"FTP retry {attempt + 2}/{attempts}: {last_error}", file=sys.stderr)
        time.sleep(1)
    print(f"FTP Error: {last_error}", file=sys.stderr)
    return 1


def build_parser():
    parser = argparse.ArgumentParser(description="Transfer and manage files through SylixOS FTP.")
    parser.add_argument(
        "-p",
        "--port",
        type=valid_port,
        default=21,
        help="FTP port (default: 21)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=positive_timeout,
        default=DEFAULT_TIMEOUT,
        help=f"FTP connection and transfer timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument("ip", help="SylixOS board IPv4 address")
    modes = parser.add_subparsers(dest="mode", required=True)

    for name, help_text in (("upload", "upload one local file"), ("download", "download one remote file")):
        sub = modes.add_parser(name, help=help_text)
        sub.add_argument("local_path")
        sub.add_argument("remote_path", type=non_root_remote)
        sub.add_argument("--progress", action="store_true", help="report transfer bytes, elapsed time and speed on stderr")
        if name == "upload":
            sub.add_argument("--verify", action="store_true", help="read back the uploaded file and compare SHA-256")

    for name, help_text in (
        ("list", "list directory entries, directories end with /"),
        ("size", "print remote file size in bytes"),
        ("mkdir", "create a directory and missing parents"),
        ("delete", "delete one remote file"),
        ("rmdir", "remove one empty remote directory"),
    ):
        sub = modes.add_parser(name, help=help_text)
        sub.add_argument("remote_path", type=absolute_remote if name == "list" else non_root_remote)

    sub = modes.add_parser("rmtree", help="recursively remove a remote directory")
    sub.add_argument("remote_path", type=non_root_remote)
    sub.add_argument("--dry-run", action="store_true", help="list planned deletions without removing anything")
    sub.add_argument(
        "--contents-only",
        action="store_true",
        help="remove everything inside the directory but keep the directory itself",
    )
    return parser


if __name__ == "__main__":
    sys.exit(run_ftp(build_parser().parse_args()))
