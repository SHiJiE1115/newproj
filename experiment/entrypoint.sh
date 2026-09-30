#!/usr/bin/env bash
set -euo pipefail

nonce="${1:?run nonce required}"
umask 022
mkdir -m 0700 /out/observer
stat -c '%u:%g:%a' /out/observer > /out/observer_pre_mode.txt
python3 --version > /out/python_version.txt 2>&1
strace --version > /out/strace_version.txt 2>&1
dpkg-query -W -f='${Package}=${Version}\n' \
  python3 python3-numpy python3-pandas python3-scipy \
  python3-sklearn python3-sympy strace libc6 \
  > /out/package_versions.txt 2>&1

set +e
strace --user=65534:65534 --kill-on-exit -ff -ttt -yy -s 256 \
  --trace=openat,read,execve,connect \
  -o /out/observer/trace \
  /usr/bin/python3 -I -B /probe/author_25.py "$nonce" \
  > /out/author_stdout.txt 2> /out/author_stderr.txt
code=$?
chmod 0755 /out/observer
chmod 0644 /out/observer/trace.* 2>/dev/null || true
printf '%s\n' "$code" > /out/trace_exit_code.txt
exit "$code"
