@echo off
echo Installing dependencies...
pip install flask requests yt-dlp pyinstaller

if not exist "ffmpeg-bin\ffmpeg.exe" (
    echo.
    echo ffmpeg-bin\ffmpeg.exe and ffprobe.exe are missing.
    echo Download ffmpeg-release-essentials.zip from https://www.gyan.dev/ffmpeg/builds/
    echo Extract bin\ffmpeg.exe and bin\ffprobe.exe into ffmpeg-bin\
    echo.
    pause
    exit /b 1
)

echo.
echo Building GeometryDownloader.exe...
pyinstaller GeometryDownloader.spec --clean

echo.
if exist "dist\GeometryDownloader.exe" (
    echo Build successful! GeometryDownloader.exe is in the dist\ folder.
) else (
    echo Build failed.
)
pause
