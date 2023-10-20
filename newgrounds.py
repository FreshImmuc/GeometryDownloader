import tkinter as tk
from tkinterhtml import TkinterHtml

def get_url():
    song_id = entry.get()
    download_path = download_song(song_id)
    if download_path:
        message = f"The song {song_id} has been downloaded to {download_path}"
    else:
        message = f"Failed to retrieve download URL for song {song_id}"

    # Update the HTML content
    html_view.set_content(f"<h1>{message}</h1>")

def download_song(song_id):
    # Implement the download logic here
    pass

# Create the main window
root = tk.Tk()
root.title("Newgrounds Song Downloader")
root.geometry("600x400")

# Create an HTML view widget
html_view = TkinterHtml(root)
html_view.pack(expand=True, fill='both')

# Set HTML content (initial message)
html_view.set_content("<h1>Enter a song ID to download</h1>")

# Create label and entry widget for entering song ID
entry = tk.Entry(root)
entry.pack(pady=(10, 5))

# Create a button to trigger the URL retrieval
button = tk.Button(root, text="Download Song", command=get_url)
button.pack(pady=(5, 10))

# Start the GUI event loop
root.mainloop()
