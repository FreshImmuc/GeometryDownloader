import sys
import os
import time
import json
import queue
import threading
import webbrowser

from flask import Flask, render_template_string, request, jsonify, Response
from werkzeug.serving import make_server
import requests
import yt_dlp

app = Flask(__name__)
port = "5234"

log_queue = queue.Queue()
_progress_state = {'last_pct': None, 'last_time': 0}


def emit(msg, level='info'):
    log_queue.put({'msg': msg, 'level': level, 't': time.time()})


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
    emit(f"Fetching Newgrounds page for ID {song_id}")
    url = f'https://www.newgrounds.com/audio/listen/{song_id}'
    response = requests.get(url)
    if response.status_code != 200:
        emit(f"HTTP {response.status_code} from Newgrounds", 'error')
        return None
    content = response.text
    start_index = content.find('embedController([{"url":"')
    if start_index == -1:
        emit("Could not locate audio URL on page", 'error')
        return None
    start_index += len('embedController([{"url":"')
    end_index = content.find('"', start_index)
    if end_index == -1:
        emit("Malformed audio URL", 'error')
        return None
    download_url = content[start_index:end_index].replace("\\/", "/")
    emit(f"Resolved stream URL")
    download_path = os.path.join(gd_folder(), f'{song_id}.mp3')
    emit(f"Downloading to {download_path}")
    r = requests.get(download_url)
    with open(download_path, 'wb') as f:
        f.write(r.content)
    emit(f"Wrote {len(r.content) // 1024} KB", 'success')
    return download_path


def get_ffmpeg_dir():
    try:
        return sys._MEIPASS
    except AttributeError:
        return None


def yt_progress_hook(d):
    status = d.get('status')
    if status == 'downloading':
        now = time.time()
        pct = d.get('_percent_str', '').strip()
        if pct == _progress_state['last_pct'] and now - _progress_state['last_time'] < 0.2:
            return
        _progress_state['last_pct'] = pct
        _progress_state['last_time'] = now
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        emit(f"Downloading {pct}  {speed}  ETA {eta}", 'progress')
    elif status == 'finished':
        emit("Stream complete, starting conversion", 'info')


def yt_postprocessor_hook(d):
    status = d.get('status')
    pp = d.get('postprocessor', '')
    if status == 'started':
        emit(f"Postprocessor: {pp}")
    elif status == 'finished':
        emit(f"{pp} done", 'success')


def download_youtube_audio(youtube_url, song_id):
    emit(f"Resolving YouTube URL")
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
        'progress_hooks': [yt_progress_hook],
        'postprocessor_hooks': [yt_postprocessor_hook],
    }
    if ffmpeg_loc:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    final_path = os.path.join(gd_folder(), f'{song_id}.mp3')
    return final_path if os.path.isfile(final_path) else None


def run_in_thread(target):
    threading.Thread(target=target, daemon=True).start()


@app.route('/')
def index():
    return render_template_string(get_template())


@app.route('/api/download_newgrounds', methods=['POST'])
def api_newgrounds():
    data = request.get_json(silent=True) or {}
    song_id = data.get('song_id', '').strip()
    if not song_id:
        return jsonify({'ok': False, 'error': 'missing song_id'}), 400

    def task():
        emit(f"--- Newgrounds: {song_id} ---", 'header')
        try:
            path = download_song(song_id)
            if path:
                emit(f"Saved as {song_id}.mp3", 'success')
            else:
                emit("Download failed", 'error')
        except Exception as e:
            emit(f"Error: {e}", 'error')
        emit('__DONE__', 'control')

    run_in_thread(task)
    return jsonify({'ok': True})


@app.route('/api/download_youtube', methods=['POST'])
def api_youtube():
    data = request.get_json(silent=True) or {}
    youtube_url = data.get('youtube_url', '').strip()
    song_id = data.get('song_id', '').strip()
    if not youtube_url or not song_id:
        return jsonify({'ok': False, 'error': 'missing fields'}), 400

    def task():
        emit(f"--- YouTube: {song_id} ---", 'header')
        try:
            path = download_youtube_audio(youtube_url, song_id)
            if path:
                emit(f"Saved as {song_id}.mp3", 'success')
            else:
                emit("File not found after conversion", 'error')
        except Exception as e:
            emit(f"Error: {e}", 'error')
        emit('__DONE__', 'control')

    run_in_thread(task)
    return jsonify({'ok': True})


@app.route('/api/logs')
def logs():
    def stream():
        yield ": connected\n\n"
        while True:
            try:
                event = log_queue.get(timeout=15)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield ": ping\n\n"
    return Response(stream(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    })


@app.route('/shutdown', methods=['POST'])
def shutdown():
    emit("Shutting down", 'warn')
    threading.Timer(0.5, lambda: os._exit(0)).start()
    return jsonify({'ok': True})


if __name__ == '__main__':
    server = make_server('localhost', int(port), app, threaded=True)
    try:
        webbrowser.open('http://127.0.0.1:' + port)
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
