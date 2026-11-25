#!/bin/sh
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Install Python 3.10 or newer with Tk support, then try again."
  read -r ignored
  exit 1
fi
python3 app.py
result=$?
if [ "$result" -ne 0 ]; then
  echo "Check Tk with: python3 -m tkinter"
  read -r ignored
fi
exit "$result"
