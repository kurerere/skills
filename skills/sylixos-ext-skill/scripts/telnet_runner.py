import argparse
import re
import socket
import sys
import time


DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_LOGIN_TIMEOUT = 10.0
DEFAULT_PROMPT_TIMEOUT = 10.0
DEFAULT_COMMAND_TIMEOUT = 30.0


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid timeout: {value}") from error
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return timeout


def recv_until(sock, pattern, timeout):
    deadline = time.monotonic() + timeout
    buffer = b""

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return buffer.decode("utf-8", errors="ignore"), False

        try:
            sock.settimeout(min(0.5, remaining))
            data = sock.recv(4096)
            if not data:
                return buffer.decode("utf-8", errors="ignore"), False
            buffer += data
            text = buffer.decode("utf-8", errors="ignore")
            tail = text[-512:] if len(text) > 512 else text
            if re.search(pattern, tail):
                return text, True
        except socket.timeout:
            continue
        except OSError:
            return buffer.decode("utf-8", errors="ignore"), False


def clean_output(output, command):
    lines = output.replace("\r\n", "\n").split("\n")
    if lines and command in lines[0]:
        lines = lines[1:]
    if lines and re.search(r"(#|=>)\s*$", lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def wait_for(sock, pattern, timeout, description):
    _, matched = recv_until(sock, pattern, timeout)
    if not matched:
        raise TimeoutError(f"timed out waiting for {description} after {timeout:g}s")


def run_telnet(ip, command, timeouts, port=23):
    if not command:
        raise ValueError("a board command is required")

    command_text = " ".join(command)
    try:
        with socket.create_connection((ip, port), timeout=timeouts["connect"]) as sock:
            wait_for(sock, r"login:", timeouts["login"], "login prompt")
            sock.sendall(b"root\n")

            wait_for(sock, r"[Pp]assword:", timeouts["login"], "password prompt")
            sock.sendall(b"root\n")

            wait_for(sock, r"(#|=>)\s*$", timeouts["prompt"], "shell prompt after login")
            sock.sendall(command_text.encode("utf-8") + b"\n")

            output, completed = recv_until(
                sock, r"(#|=>)\s*$", timeouts["command"]
            )

        cleaned = clean_output(output, command_text)
        if cleaned:
            print(cleaned)
        if not completed:
            print(
                f"telnet_runner: command output timed out after "
                f"{timeouts['command']:g}s; remote command result is unknown",
                file=sys.stderr,
            )
            return 2
        return 0
    except TimeoutError as error:
        print(f"Telnet timeout: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Error connecting or executing: {error}", file=sys.stderr)
        return 1


def make_parser():
    parser = argparse.ArgumentParser(
        description="Run one command through a SylixOS Telnet shell."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=23,
        help="Telnet port (default: 23)",
    )
    parser.add_argument(
        "--connect-timeout",
        type=positive_timeout,
        default=DEFAULT_CONNECT_TIMEOUT,
        help=f"TCP connection timeout in seconds (default: {DEFAULT_CONNECT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--login-timeout",
        type=positive_timeout,
        default=DEFAULT_LOGIN_TIMEOUT,
        help=f"Each login prompt timeout in seconds (default: {DEFAULT_LOGIN_TIMEOUT:g})",
    )
    parser.add_argument(
        "--prompt-timeout",
        type=positive_timeout,
        default=DEFAULT_PROMPT_TIMEOUT,
        help=f"Shell prompt timeout in seconds (default: {DEFAULT_PROMPT_TIMEOUT:g})",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        "--command-timeout",
        dest="command_timeout",
        type=positive_timeout,
        default=DEFAULT_COMMAND_TIMEOUT,
        help=(
            "command output timeout in seconds; this does not stop the remote command "
            f"(default: {DEFAULT_COMMAND_TIMEOUT:g})"
        ),
    )
    parser.add_argument("ip", help="SylixOS board IPv4 address")
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="one command sent to the board"
    )
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()
    exit_code = run_telnet(
        args.ip,
        args.command,
        {
            "connect": args.connect_timeout,
            "login": args.login_timeout,
            "prompt": args.prompt_timeout,
            "command": args.command_timeout,
        },
        port=args.port,
    )
    sys.exit(exit_code)
