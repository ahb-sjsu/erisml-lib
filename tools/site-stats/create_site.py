#!/usr/bin/env python3
"""Create the GoatCounter site and its admin user without putting the password on a command line.

GoatCounter v2.7.0's `db create site` takes the password either from `-user.password` (a
command-line argument, readable by every local user in /proc) or from an interactive
terminal (`-password -` on stdin arrived only after v2.7.0). This gives it a terminal: the
password is read from a root-readable file and typed into a pseudo-terminal at each of the
two prompts. Nothing read from the terminal is printed unless the password has been
replaced by "<redacted>" first.

usage (as root):
    create_site.py <goatcounter-binary> <db-path> <vhost> <email> <password-file> <run-as-user>
"""

import os
import pty
import pwd
import select
import signal
import sys
import time

PROMPTS = (b"(will not echo): ", b"Confirm: ")


def main() -> int:
    if len(sys.argv) != 7:
        print(__doc__, file=sys.stderr)
        return 2
    binary, db, vhost, email, passfile, user = sys.argv[1:7]
    with open(passfile, "rb") as f:
        secret = f.read().strip()
    if not 8 <= len(secret) <= 50:
        print("password file: need 8 to 50 bytes", file=sys.stderr)
        return 2
    account = pwd.getpwnam(user)
    argv = [
        binary,
        "db",
        "create",
        "site",
        "-db",
        "sqlite+" + db,
        "-vhost",
        vhost,
        "-user.email",
        email,
    ]

    pid, fd = pty.fork()
    if pid == 0:
        # child: drop to the service user, then run goatcounter on the terminal
        os.chdir(os.path.dirname(db))
        os.setgroups([])
        os.setgid(account.pw_gid)
        os.setuid(account.pw_uid)
        os.execv(binary, argv)

    out, sent, deadline = b"", 0, time.time() + 60
    while time.time() < deadline:
        ready, _, _ = select.select([fd], [], [], 1.0)
        if fd not in ready:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:  # EIO: the child closed the terminal
            break
        if not chunk:
            break
        out += chunk
        prompts = sum(out.count(p) for p in PROMPTS)
        # one password per prompt, two prompts at most; the pause lets ReadPassword
        # switch echo off before the password arrives
        while sent < min(prompts, 2):
            time.sleep(0.2)
            os.write(fd, secret + b"\n")
            sent += 1
    else:
        os.kill(pid, signal.SIGTERM)
        print("goatcounter did not finish within 60 s; stopped it", file=sys.stderr)

    _, status = os.waitpid(pid, 0)
    text = out.replace(secret, b"<redacted>").decode(errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if line and not any(p.decode().strip() in line for p in PROMPTS):
            print(line)
    code = os.waitstatus_to_exitcode(status)
    print(f"goatcounter db create site: exit {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
