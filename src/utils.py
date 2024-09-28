import os
import subprocess
import sys


def check_ffmpeg_installed():
    # Check if FFmpeg is installed and available in the system PATH.
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("FFmpeg is not installed or not found in the system PATH.")
    except FileNotFoundError:
        print("FFmpeg is required for this application to work. Please install FFmpeg and ensure it's available in your system PATH.")
        print("Refer to the README for installation instructions.")
        sys.exit(1)


def get_download_folder():
    # Get the path to the download folder, creating it if it doesn't exist.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    downloads_folder = os.path.join(project_root, '_downloads')
    os.makedirs(downloads_folder, exist_ok=True)
    print(f"Download folder resolved to: {downloads_folder}\n")
    return downloads_folder


def remove_playlist_param(url):
    # Remove the playlist part from the URL if it exists.
    if '&list=' in url:
        url = url.split('&list=')[0]
    return url
