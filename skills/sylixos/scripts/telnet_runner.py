import argparse
import codecs
from contextlib import ExitStack
import math
import os
import re
import shutil
import socket
import sys
import tempfile
import time
from typing import NamedTuple


DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_LOGIN_TIMEOUT = 10.0
DEFAULT_PROMPT_TIMEOUT = 10.0
DEFAULT_COMMAND_TIMEOUT = 30.0
RECEIVE_SIZE = 65536
PROMPT_WINDOW = 4096
LOGIN_PROMPT = re.compile(r"(?m)^[^\r\n]{0,1024}(?:#|=>)[ \t]*\Z")


class ReceiveResult(NamedTuple):
    output: str
    status: str
    error: str = ""


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid timeout: {value}") from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and greater than zero")
    return timeout


def recv_until(sock, pattern, timeout, on_text=None, prompt_prefix=None):
    pattern = re.compile(pattern)
    deadline = time.monotonic() + timeout
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    chunks = []
    pending = ""
    status, error = "timeout", ""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            sock.settimeout(remaining)
            data = sock.recv(RECEIVE_SIZE)
        except socket.timeout:
            break
        except OSError as failure:
            status, error = "error", str(failure)
            break
        if not data:
            status = "closed"
            break
        text = decoder.decode(data)
        if on_text is None:
            chunks.append(text)
        pending += text
        match = pattern.search(pending)
        if match:
            if on_text is not None:
                on_text(pending[:match.start()])
            return ReceiveResult("".join(chunks), "matched")
        cut = max(pending.rfind("\n") + 1, len(pending) - PROMPT_WINDOW)
        if on_text is not None and prompt_prefix:
            cut = len(pending)
            start = pending.rfind(prompt_prefix[0])
            if start >= 0:
                candidate = pending[start:]
                if "\n" not in candidate and len(candidate) <= PROMPT_WINDOW and (
                    prompt_prefix.startswith(candidate) or candidate.startswith(prompt_prefix)
                ):
                    cut = start
        if cut > 0:
            if on_text is not None:
                on_text(pending[:cut])
            pending = pending[cut:]
    tail = decoder.decode(b"", final=True)
    if on_text is not None:
        on_text(pending + tail)
        return ReceiveResult("", status, error)
    chunks.append(tail)
    return ReceiveResult("".join(chunks), status, error)


def wait_for(sock, pattern, timeout, description):
    result = recv_until(sock, pattern, timeout)
    if result.status == "timeout":
        raise TimeoutError(f"timed out waiting for {description} after {timeout:g}s")
    if result.status == "closed":
        raise ConnectionError(f"connection closed while waiting for {description}")
    if result.status == "error":
        raise ConnectionError(f"receive failed while waiting for {description}: {result.error}")
    return result.output


def shell_prompt(login_output):
    prompt = login_output.split("\n")[-1].rstrip("\r \t")
    sylixos = re.fullmatch(r"(\[[^:\]\r\n]+:)[^\r\n]*(\]#)", prompt)
    if sylixos:
        return (re.compile(re.escape(sylixos[1]) + r"[^\r\n]{0,2048}" + re.escape(sylixos[2]) + r"[ \t]*\Z"), sylixos[1])
    return re.compile(re.escape(prompt) + r"[ \t]*\Z"), prompt


class CommandOutput:
    def __init__(self, command, sinks, live=False):
        self.command = command
        self.sinks = sinks
        self.live = live
        self.first = ""
        self.first_done = False
        self.prompt_fragment = False
        self.carriage = ""
        self.last_flush = 0.0

    def write(self, text):
        for sink in self.sinks:
            sink.write(text)
        now = time.monotonic()
        if self.live or now - self.last_flush >= .1:
            for sink in self.sinks:
                sink.flush()
            self.last_flush = now

    def feed(self, text):
        text = self.carriage + text
        self.carriage = "\r" if text.endswith("\r") else ""
        if self.carriage:
            text = text[:-1]
        text = text.replace("\r\n", "\n")
        if not self.first_done:
            self.first += text
            line, separator, rest = self.first.partition("\n")
            if separator:
                self.first_done = True
                echo = line == self.command or (self.prompt_fragment and line.lstrip(" \t") == self.command)
                text = rest if echo else self.first
                self.first = ""
            elif len(self.first) > len(self.command) + 1:
                self.first_done = True
                text, self.first = self.first, ""
            else:
                return
        if text:
            self.write(text)

    def finish(self):
        if self.first or self.carriage:
            self.write(self.first + self.carriage)
            self.first, self.carriage = "", ""
        for sink in self.sinks:
            sink.flush()


def run_telnet(ip, command, timeouts, port=23, stream=False, output_path=None, user="root", password=None):
    if not command:
        raise ValueError("a board command is required")
    command_text = " ".join(command)
    stage = "local output"
    try:
        with ExitStack() as stack:
            sinks = []
            log = None
            if output_path is not None:
                log = stack.enter_context(open(output_path, "w+", encoding="utf-8", newline=""))
            if stream:
                sinks.append(sys.stdout)
                if log is not None:
                    sinks.append(log)
            else:
                capture = log if log is not None else stack.enter_context(
                    tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="w+", encoding="utf-8", newline=""))
                sinks.append(capture)
            writer = CommandOutput(command_text, sinks, live=stream)
            stage = "TCP connect"
            sock = stack.enter_context(socket.create_connection((ip, port), timeout=timeouts["connect"]))
            stage = "login"
            wait_for(sock, r"login:", timeouts["login"], "login prompt")
            sock.sendall(user.encode("utf-8") + b"\n")
            wait_for(sock, r"[Pp]assword:", timeouts["login"], "password prompt")
            if password is None:
                password = os.environ.get("SYLIXOS_PASSWORD", "root")
            sock.sendall(password.encode("utf-8") + b"\n")
            stage = "shell prompt"
            login_output = wait_for(sock, LOGIN_PROMPT, timeouts["prompt"], "shell prompt after login")
            writer.prompt_fragment = not login_output.endswith((" ", "\t"))
            pattern, prefix = shell_prompt(login_output)
            stage = "command"
            sock.sendall(command_text.encode("utf-8") + b"\n")
            try:
                result = recv_until(sock, pattern, timeouts["command"], on_text=writer.feed, prompt_prefix=prefix)
            finally:
                writer.finish()
                if not stream:
                    capture.seek(0)
                    shutil.copyfileobj(capture, sys.stdout)
                    sys.stdout.flush()
            if result.status == "matched":
                return 0
            if result.status == "timeout":
                reason = f"command output timed out after {timeouts['command']:g}s"
            elif result.status == "closed":
                reason = "connection closed before shell prompt"
            else:
                reason = f"receive failed: {result.error}"
            print(f"telnet_runner: {reason}; remote command result is unknown", file=sys.stderr)
            return 2 if result.status == "timeout" else 1
    except TimeoutError as error:
        print(f"Telnet timeout ({stage}): {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Telnet error ({stage}): {error}", file=sys.stderr)
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
    parser.add_argument(
        "-u",
        "--user",
        default=os.environ.get("SYLIXOS_USER", "root"),
        help="login user (default: $SYLIXOS_USER or root); password comes from $SYLIXOS_PASSWORD, default root",
    )
    parser.add_argument("--stream", action="store_true", help="print command output as it arrives")
    parser.add_argument("--output", type=str, help="save command output to a local UTF-8 file (overwrite)")
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
        stream=args.stream,
        output_path=args.output,
        user=args.user,
    )
    sys.exit(exit_code)
