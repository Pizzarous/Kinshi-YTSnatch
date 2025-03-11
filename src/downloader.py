import os
import yt_dlp


def download_video(url, output_path):
    # Function to download a single video
    try:
        # First, check if the video is accessible without downloading
        print("Checking video availability...")
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            # Just check if the video exists, don't store the info
            ydl.extract_info(url, download=False)

        # Then try to download with specific format selection
        print("Attempting download...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegMetadata',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach with simpler format selection...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                'format': 'best',  # Simplest format selection
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegMetadata',
                }],
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except yt_dlp.utils.DownloadError as e2:
            # If that also fails, try listing formats and a manual approach
            print("Second attempt failed. Let's list available formats:")
            try:
                with yt_dlp.YoutubeDL({'listformats': True}) as ydl:
                    # No need to store the result, listformats will print to console
                    ydl.extract_info(url, download=False)

                print("\nPlease try again and specify one of these formats using:")
                print("--format FORMAT_CODE")

            except Exception as e3:
                print(f"Unable to list formats: {str(e3)}")

            # Re-raise the original error to maintain program flow
            raise e2


def download_audio(url, output_path):
    # Function to download audio from a single video
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
            }],
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                'format': 'best',  # Try a simpler format selector
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }, {
                    'key': 'FFmpegMetadata',
                }],
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except Exception as e2:
            print(f"Alternative approach failed: {str(e2)}")
            raise e  # Re-raise the original error


def download_playlist(url, output_path):
    # Function to download all videos in a playlist
    try:
        # First, check if the playlist is accessible without downloading
        print("Checking playlist availability...")
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            # Just check if the playlist exists, don't store the info
            ydl.extract_info(url, download=False)

        # Then try to download with specific format selection
        print("Attempting playlist download...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegMetadata',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error with playlist download: {str(e)}")
        print("Trying alternative approach with simpler format selection...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                'format': 'best',  # Simplest format selection
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegMetadata',
                }],
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except Exception as e2:
            print(f"Alternative approach for playlist failed: {str(e2)}")
            raise e  # Re-raise the original error


def download_playlist_audio(url, output_path):
    # Function to download audio from all videos in a playlist
    try:
        # First check playlist availability
        print("Checking playlist availability...")
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            ydl.extract_info(url, download=False)

        print("Attempting playlist audio download...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error with playlist audio download: {str(e)}")
        print("Trying alternative approach...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                'format': 'best',  # Try a simpler format selector
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }, {
                    'key': 'FFmpegMetadata',
                }],
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except Exception as e2:
            print(f"Alternative approach for playlist audio failed: {str(e2)}")
            raise e  # Re-raise the original error
