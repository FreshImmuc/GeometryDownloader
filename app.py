import sys
import threading
from flask import Flask, render_template, render_template_string, request, redirect, url_for
import requests
import os
import webbrowser
import multiprocessing
import signal
import asyncio
from werkzeug.serving import BaseWSGIServer
import atexit
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options 
# driver = webdriver.Chrome(os.path.join(sys._MEIPASS, 'chromedriver.exe'))

app = Flask(__name__)
port = "5234"


def download_song(song_id):
    url = f'https://www.newgrounds.com/audio/listen/{song_id}'
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        start_index = content.find('embedController([{"url":"')
        if start_index != -1:
            start_index += len('embedController([{"url":"')
            end_index = content.find('"', start_index)
            if end_index != -1:
                download_url = content[start_index:end_index]
                download_url = download_url.replace("\\/", "/")  # Adjust URL format
                local_path = os.path.join(os.getenv('LOCALAPPDATA'), 'GeometryDash')
                download_path = os.path.join(local_path, f'{song_id}.mp3')
                response = requests.get(download_url)
                with open(download_path, 'wb') as file:
                    file.write(response.content)
                return download_path
    return None


@app.route('/')
def index():
    status_message = request.args.get('status_message', '')  # Get status message from URL argument
    
    # Access bundled HTML file using _MEIPASS attribute
    html_path = os.path.join(sys._MEIPASS, 'index.html')

    with open(html_path, 'r') as file:
        content = file.read()
    
    # Render the template with status_message
    return render_template_string(content, status_message=status_message)

@app.route('/download', methods=['POST'])
def get_url():
    song_id = request.form['song_id']
    download_path = download_song(song_id)
    if download_path:
        return redirect(url_for('index', status_message=f"Successfully downloaded the Song!"))
    else:
        return redirect(url_for('index', status_message="Error: Failed to retrieve download URL"))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    threading.Timer(1, shutdown_server).start()  # Wait for 10 seconds before shutting down
    return redirect(url_for('index', status_message=f"Stopped the App! You can close this window."))

def shutdown_server():
    os._exit(0)

if __name__ == '__main__':
    server = BaseWSGIServer('localhost', int(port), app)
    try:
        # # Open the browser in a smaller window as a popup
        # options = webdriver.ChromeOptions()
        # options.add_argument('window-size=800,600')  # Set desired window size
        # options.add_argument('popup')  # Open in a popup window
        
        # # Set the window size and position
        # driver.set_window_rect(x=0, y=0, width=800, height=600)
        
        # driver.get('http://127.0.0.1:5000')
        webbrowser.open('http://127.0.0.1:' + port)
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()