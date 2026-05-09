@echo off
echo Installing dependencies...
pip install flask requests yt-dlp imageio-ffmpeg pyinstaller

echo.
echo Building GeometryDownloader.exe...
pyinstaller GeometryDownloader.spec --clean

echo.
if exist "dist\GeometryDownloader.exe" (
    echo Build successful! GeometryDownloader.exe is in the dist\ folder.
) else (
    echo Build failed. Check the output above for errors.
)
pause
