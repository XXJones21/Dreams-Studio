@echo off
rem Double-click to start Dreams Studio. Close this window to stop it.
cd /d "%~dp0"
where node >nul 2>nul || goto nonode
node -e "const [a,b]=process.versions.node.split('.').map(Number);process.exit(a>22||(a===22&&b>=6)?0:1)" || goto nonode
node --experimental-strip-types --disable-warning=ExperimentalWarning scripts/launch.ts
pause
exit /b

:nonode
echo Dreams Studio needs Node.js 22.6 or newer. Opening the download page.
echo Install Node.js, then double-click start-windows.cmd again.
start "" https://nodejs.org/
pause
