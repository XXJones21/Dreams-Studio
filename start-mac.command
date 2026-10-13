#!/bin/sh
# Double-click to start Dreams Studio. Close this window to stop it.
cd "$(dirname "$0")" || exit 1
# Finder-launched shells can miss Homebrew's PATH.
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v node >/dev/null 2>&1 ||
  ! node -e "const [a,b]=process.versions.node.split('.').map(Number);process.exit(a>22||(a===22&&b>=6)?0:1)"; then
  echo "Dreams Studio needs Node.js 22.6 or newer. Opening the download page."
  echo "Install Node.js, then double-click start-mac.command again."
  open https://nodejs.org/
  exit 1
fi

exec node --experimental-strip-types --disable-warning=ExperimentalWarning scripts/launch.ts
