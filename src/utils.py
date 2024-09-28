import os
import subprocess
import sys


def check_ffmpeg_installed():
    """Check if FFmpeg is installed and available in the system PATH."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("FFmpeg is not installed or not found in the system PATH.")
    except FileNotFoundError:
        print("FFmpeg is required for this application to work. Please install FFmpeg and ensure it's available in your system PATH.")
        print("Refer to the README for installation instructions.")
        sys.exit(1)

# def delete_file(file_path):
#     """Delete the file permanently without sending it to the Recycle Bin."""
#     try:
#         os.remove(file_path)
#         print(f"Deleted {file_path} permanently.")
#     except Exception as e:
#         print(f"Error deleting file: {file_path}. Error: {e}")


def get_download_folder():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    downloads_folder = os.path.join(project_root, '_downloads')
    os.makedirs(downloads_folder, exist_ok=True)
    print(f"Download folder resolved to: {downloads_folder}\n")
    return downloads_folder


def remove_playlist_param(url):
    """Remove the playlist part from the URL if it exists."""
    if '&list=' in url:
        url = url.split('&list=')[0]
    return url
