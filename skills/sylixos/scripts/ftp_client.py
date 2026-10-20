import argparse
import ftplib
import hashlib
import os
from pathlib import Path
import posixpath
import sys
import time


DEFAULT_TIMEOUT = 10.0
RETRYING_MODES = {"upload", "download", "list", "size", "mkdir"}


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid timeout: {value}") from error
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
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


def upload(ftp, local_path, remote_path, verify=False):
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"local file does not exist: {local_path}")
    local_hash = hashlib.sha256() if verify else None
    with open(local_path, "rb") as source:
        ftp.storbinary(f"STOR {remote_path}", source, callback=local_hash.update if verify else None)
    if verify:
        remote_hash = hashlib.sha256()
        ftp.retrbinary(f"RETR {remote_path}", remote_hash.update)
        if local_hash.digest() != remote_hash.digest():
            raise RuntimeError(f"upload verification failed for {remote_path}: SHA-256 mismatch")
        print(f"Verified SHA-256: {remote_hash.hexdigest()}")
    print(f"Successfully uploaded {local_path} to {remote_path}")


def download(ftp, remote_path, local_path, partials):
    destination = Path(local_path)
    partial_path = destination.with_name(f".{destination.name}.part-{os.getpid()}")
    partials.append(partial_path)
    with open(partial_path, "wb") as target:
        ftp.retrbinary(f"RETR {remote_path}", target.write)
    os.replace(partial_path, destination)
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
        upload(ftp, args.local_path, args.remote_path, verify=args.verify)
    elif args.mode == "download":
        download(ftp, args.remote_path, args.local_path, partials)
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
            if attempt + 1 < attempts:
                time.sleep(1)
        finally:
            try:
                ftp.close()
            except OSError:
                pass
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
