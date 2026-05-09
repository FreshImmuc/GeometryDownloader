import sys
import os
import threading
import webbrowser

from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.serving import BaseWSGIServer
import requests
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)
port = "5234"


def get_template():
    try:
        html_path = os.path.join(sys._MEIPASS, 'index.html')
    except AttributeError:
        html_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    with open(html_path, 'r') as f:
        return f.read()


def gd_folder():
    return os.path.join(os.getenv('LOCALAPPDATA'), 'GeometryDash')


def download_song(song_id):
    url = f'https://www.newgrounds.com/audio/listen/{song_id}'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    content = response.text
    start_index = content.find('embedController([{"url":"')
    if start_index == -1:
        return None
    start_index += len('embedController([{"url":"')
    end_index = content.find('"', start_index)
    if end_index == -1:
        return None
    download_url = content[start_index:end_index].replace("\\/", "/")
    download_path = os.path.join(gd_folder(), f'{song_id}.mp3')
    r = requests.get(download_url)
    with open(download_path, 'wb') as f:
        f.write(r.content)
    return download_path


def get_ffmpeg_dir():
    try:
        return os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None


def download_youtube_audio(youtube_url, song_id):
    output_template = os.path.join(gd_folder(), f'{song_id}.%(ext)s')
    ffmpeg_loc = get_ffmpeg_dir()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    if ffmpeg_loc:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    final_path = os.path.join(gd_folder(), f'{song_id}.mp3')
    return final_path if os.path.isfile(final_path) else None


@app.route('/')
def index():
    status_message = request.args.get('status_message', '')
    return render_template_string(get_template(), status_message=status_message)


@app.route('/download', methods=['POST'])
def get_url():
    song_id = request.form['song_id']
    download_path = download_song(song_id)
    if download_path:
        return redirect(url_for('index', status_message="Successfully downloaded the Newgrounds song!"))
    return redirect(url_for('index', status_message="Error: Failed to retrieve Newgrounds song. Check the ID and try again."))


@app.route('/download_youtube', methods=['POST'])
def download_youtube():
    youtube_url = request.form['youtube_url']
    song_id = request.form['song_id']
    try:
        path = download_youtube_audio(youtube_url, song_id)
        if path:
            return redirect(url_for('index', status_message=f"Successfully downloaded YouTube audio as song ID {song_id}!"))
        return redirect(url_for('index', status_message="Error: File not found after conversion. Is ffmpeg installed?"))
    except Exception as e:
        return redirect(url_for('index', status_message=f"Error: {e}"))


@app.route('/shutdown', methods=['POST'])
def shutdown():
    threading.Timer(1, lambda: os._exit(0)).start()
    return redirect(url_for('index', status_message="Stopped the App! You can close this window."))


if __name__ == '__main__':
    server = BaseWSGIServer('localhost', int(port), app)
    try:
        webbrowser.open('http://127.0.0.1:' + port)
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
