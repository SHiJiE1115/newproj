#!/usr/bin/env bash
set -euo pipefail

nonce="${1:?run nonce required}"
python3 --version > /out/python_version.txt 2>&1
strace --version > /out/strace_version.txt 2>&1
dpkg-query -W -f='${Package}=${Version}\n' \
  python3 python3-numpy python3-pandas python3-scipy \
  python3-sklearn python3-sympy strace libc6 \
  > /out/package_versions.txt 2>&1

set +e
strace --kill-on-exit -ff -ttt -yy -s 256 \
  --trace=openat,read,execve,connect \
  -o /out/trace \
  /usr/bin/python3 -I -B /probe/author_25.py "$nonce" \
  > /out/author_stdout.txt 2> /out/author_stderr.txt
code=$?
printf '%s\n' "$code" > /out/trace_exit_code.txt
exit "$code"
