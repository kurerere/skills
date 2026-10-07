import argparse
import ftplib
import os
from pathlib import Path
import sys


DEFAULT_TIMEOUT = 10.0


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


def run_ftp(ip, mode, local_path, remote_path, timeout, port=21):
    import time
    last_error = None
    for attempt in range(3):
        partial_path = None
        ftp = ftplib.FTP()
        try:
            ftp.connect(ip, port, timeout=timeout)
            ftp.login("root", "root")

            if mode == "upload":
                if not os.path.isfile(local_path):
                    raise FileNotFoundError(f"local file does not exist: {local_path}")
                with open(local_path, "rb") as source:
                    ftp.storbinary(f"STOR {remote_path}", source)
                print(f"Successfully uploaded {local_path} to {remote_path}")
                return 0
            else:
                destination = Path(local_path)
                partial_path = destination.with_name(
                    f".{destination.name}.part-{os.getpid()}"
                )
                with open(partial_path, "wb") as target:
                    ftp.retrbinary(f"RETR {remote_path}", target.write)
                os.replace(partial_path, destination)
                print(f"Successfully downloaded {remote_path} to {local_path}")
                return 0
        except Exception as error:
            last_error = error
            if partial_path is not None:
                try:
                    os.remove(partial_path)
                except OSError:
                    pass
            time.sleep(1)
        finally:
            try:
                ftp.close()
            except OSError:
                pass
    print(f"FTP Error: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transfer one file through SylixOS FTP.")
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
    parser.add_argument("mode", choices=("upload", "download"))
    parser.add_argument("local_path")
    parser.add_argument("remote_path")
    args = parser.parse_args()
    sys.exit(run_ftp(args.ip, args.mode, args.local_path, args.remote_path, args.timeout, port=args.port))
