block_cipher = None

from PyInstaller.utils.hooks import collect_all

yt_dlp_datas,      yt_dlp_binaries,      yt_dlp_hiddenimports      = collect_all('yt_dlp')
imageio_datas,     imageio_binaries,     imageio_hiddenimports      = collect_all('imageio_ffmpeg')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=yt_dlp_binaries + imageio_binaries,
    datas=yt_dlp_datas + imageio_datas + [
        ('templates/index.html', '.'),
    ],
    hiddenimports=yt_dlp_hiddenimports + imageio_hiddenimports + [
        'flask',
        'jinja2',
        'werkzeug',
        'werkzeug.serving',
        'requests',
        'certifi',
        'charset_normalizer',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GeometryDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon.ico',
)
