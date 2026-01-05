import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import yt_dlp
from tqdm import tqdm

from error_handler import SuppressLogger, extract_error_message


def download_video(url, output_path):
    # Function to download a single video
    try:
        # First, check if the video is accessible without downloading
        print("Checking video availability...")
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            # Just check if the video exists, don't store the info
            ydl.extract_info(url, download=False)

        # Then try to download with specific format selection
        print("Attempting download...")
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # Download best video + best audio
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "writesubtitles": True,  # Download manual subtitles only
            "subtitleslangs": [
                "en",
                "all",
            ],  # Download English and all available subtitles
            "postprocessors": [
                {
                    "key": "FFmpegEmbedSubtitle",  # Embed subtitles into the video
                    "already_have_subtitle": False,
                },
                {
                    "key": "FFmpegMetadata",
                },
            ],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach with simpler format selection...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                "format": "best",  # Simplest format selection
                "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
                "writesubtitles": True,
                "subtitleslangs": ["en", "all"],
                "postprocessors": [
                    {
                        "key": "FFmpegEmbedSubtitle",
                        "already_have_subtitle": False,
                    },
                    {
                        "key": "FFmpegMetadata",
                    },
                ],
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except yt_dlp.utils.DownloadError as e2:
            # If that also fails, try listing formats and a manual approach
            print("Second attempt failed. Let's list available formats:")
            try:
                with yt_dlp.YoutubeDL({"listformats": True}) as ydl:
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
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegMetadata",
                },
            ],
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = {
                "format": "best",  # Try a simpler format selector
                "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {
                        "key": "FFmpegMetadata",
                    },
                ],
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except Exception as e2:
            print(f"Alternative approach failed: {str(e2)}")
            raise e  # Re-raise the original error


def _download_single_video_from_playlist(
    video_info, output_path, position, pbar_lock, active_bars
):
    """Helper function to download a single video with progress tracking"""
    video_url = (
        video_info.get("url") or f"https://www.youtube.com/watch?v={video_info['id']}"
    )
    title = video_info.get("title", "Unknown")
    short_title = title[:50] + "..." if len(title) > 50 else title

    # Create progress bar for this download
    pbar = None

    def progress_hook(d):
        nonlocal pbar
        if d["status"] == "downloading":
            if pbar is None:
                with pbar_lock:
                    # Find available position (1, 2, or 3)
                    bar_position = None
                    for pos in [1, 2, 3]:
                        if pos not in active_bars:
                            bar_position = pos
                            active_bars[pos] = True
                            break

                    if bar_position:
                        total = (
                            d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        )
                        pbar = tqdm(
                            total=total,
                            desc=f"[{position}] {short_title}",
                            position=bar_position,
                            leave=False,
                            unit="B",
                            unit_scale=True,
                        )

            if pbar and "downloaded_bytes" in d:
                pbar.update(d["downloaded_bytes"] - pbar.n)

        elif d["status"] == "finished" and pbar:
            pbar.close()
            with pbar_lock:
                # Free up the position
                for pos, active in list(active_bars.items()):
                    if active and pos in [1, 2, 3]:
                        del active_bars[pos]
                        break

    try:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # Download best video + best audio
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "writesubtitles": True,
            "subtitleslangs": ["en", "all"],
            "postprocessors": [
                {"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False},
                {"key": "FFmpegMetadata"},
            ],
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "logger": SuppressLogger(),  # Suppress error output
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Clean up progress bar if still exists
        if pbar:
            pbar.close()
            with pbar_lock:
                for pos in [1, 2, 3]:
                    if pos in active_bars:
                        del active_bars[pos]
                        break

        return {"status": "success", "title": title, "position": position}

    except Exception as e:
        # Clean up progress bar on error
        if pbar:
            pbar.close()
            with pbar_lock:
                for pos in [1, 2, 3]:
                    if pos in active_bars:
                        del active_bars[pos]
                        break

        # Extract clean error message using error handler
        error_msg = extract_error_message(e)
        return {
            "status": "error",
            "title": title,
            "position": position,
            "error": error_msg,
        }


def download_playlist(url, output_path):
    """Download all videos in a playlist with parallel processing (3 concurrent downloads)"""
    try:
        print("Extracting playlist information...")

        # Extract playlist info
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)

        if not playlist_info or "entries" not in playlist_info:
            print("Error: Could not extract playlist information")
            return

        # Filter out unavailable videos
        videos = [v for v in playlist_info["entries"] if v is not None]
        total_videos = len(videos)
        playlist_title = playlist_info.get("title", "Unknown Playlist")

        print(f"\nPlaylist: {playlist_title}")
        print(f"Total videos: {total_videos}\n")

        # Track statistics and active progress bars
        downloaded = 0
        skipped = 0
        pbar_lock = threading.Lock()
        active_bars = {}  # Track which progress bar positions are in use

        # Use ThreadPoolExecutor for parallel downloads (3 workers)
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Create progress bar for overall progress
            with tqdm(
                total=total_videos, desc="Overall Progress", position=0, leave=True
            ) as overall_pbar:
                try:
                    # Submit all download tasks
                    futures = {
                        executor.submit(
                            _download_single_video_from_playlist,
                            video,
                            output_path,
                            idx + 1,
                            pbar_lock,
                            active_bars,
                        ): idx
                        for idx, video in enumerate(videos)
                    }

                    # Process completed downloads
                    for future in as_completed(futures):
                        result = future.result()
                        if result["status"] == "success":
                            downloaded += 1
                            tqdm.write(
                                f"✓ [{result['position']}/{total_videos}] {result['title']}"
                            )
                        else:
                            skipped += 1
                            tqdm.write(
                                f"✗ [{result['position']}/{total_videos}] {result['title'][:50]} - {result['error']}"
                            )

                        overall_pbar.update(1)
                        # Update description to show success count
                        overall_pbar.set_description(f"Progress ({downloaded} ✓)")

                except KeyboardInterrupt:
                    print("\n\n🛑 Download interrupted by user (Ctrl+C)")
                    print("Cancelling remaining downloads...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    sys.exit(0)

        print(f"\n{'=' * 60}")
        print(f"Download Complete!")
        print(f"Downloaded: {downloaded} | Skipped: {skipped} | Total: {total_videos}")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"Error with playlist download: {str(e)}")
        raise


def _download_single_audio_from_playlist(
    video_info, output_path, position, pbar_lock, active_bars
):
    """Helper function to download a single audio with progress tracking"""
    video_url = (
        video_info.get("url") or f"https://www.youtube.com/watch?v={video_info['id']}"
    )
    title = video_info.get("title", "Unknown")
    short_title = title[:50] + "..." if len(title) > 50 else title

    # Create progress bar for this download
    pbar = None

    def progress_hook(d):
        nonlocal pbar
        if d["status"] == "downloading":
            if pbar is None:
                with pbar_lock:
                    # Find available position (1, 2, or 3)
                    bar_position = None
                    for pos in [1, 2, 3]:
                        if pos not in active_bars:
                            bar_position = pos
                            active_bars[pos] = True
                            break

                    if bar_position:
                        total = (
                            d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        )
                        pbar = tqdm(
                            total=total,
                            desc=f"[{position}] {short_title}",
                            position=bar_position,
                            leave=False,
                            unit="B",
                            unit_scale=True,
                        )

            if pbar and "downloaded_bytes" in d:
                pbar.update(d["downloaded_bytes"] - pbar.n)

        elif d["status"] == "finished" and pbar:
            pbar.close()
            with pbar_lock:
                # Free up the position
                for pos, active in list(active_bars.items()):
                    if active and pos in [1, 2, 3]:
                        del active_bars[pos]
                        break

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegMetadata",
                },
            ],
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "logger": SuppressLogger(),  # Suppress error output
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Clean up progress bar if still exists
        if pbar:
            pbar.close()
            with pbar_lock:
                for pos in [1, 2, 3]:
                    if pos in active_bars:
                        del active_bars[pos]
                        break

        return {"status": "success", "title": title, "position": position}

    except Exception as e:
        # Clean up progress bar on error
        if pbar:
            pbar.close()
            with pbar_lock:
                for pos in [1, 2, 3]:
                    if pos in active_bars:
                        del active_bars[pos]
                        break

        # Extract clean error message using error handler
        error_msg = extract_error_message(e)
        return {
            "status": "error",
            "title": title,
            "position": position,
            "error": error_msg,
        }


def download_playlist_audio(url, output_path):
    """Download audio from all videos in a playlist with parallel processing (3 concurrent downloads)"""
    try:
        print("Extracting playlist information...")

        # Extract playlist info
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)

        if not playlist_info or "entries" not in playlist_info:
            print("Error: Could not extract playlist information")
            return

        # Filter out unavailable videos
        videos = [v for v in playlist_info["entries"] if v is not None]
        total_videos = len(videos)
        playlist_title = playlist_info.get("title", "Unknown Playlist")

        print(f"\nPlaylist: {playlist_title}")
        print(f"Total videos: {total_videos}\n")

        # Track statistics and active progress bars
        downloaded = 0
        skipped = 0
        pbar_lock = threading.Lock()
        active_bars = {}  # Track which progress bar positions are in use

        # Use ThreadPoolExecutor for parallel downloads (3 workers)
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Create progress bar for overall progress
            with tqdm(
                total=total_videos, desc="Overall Progress", position=0, leave=True
            ) as overall_pbar:
                try:
                    # Submit all download tasks
                    futures = {
                        executor.submit(
                            _download_single_audio_from_playlist,
                            video,
                            output_path,
                            idx + 1,
                            pbar_lock,
                            active_bars,
                        ): idx
                        for idx, video in enumerate(videos)
                    }

                    # Process completed downloads
                    for future in as_completed(futures):
                        result = future.result()
                        if result["status"] == "success":
                            downloaded += 1
                            tqdm.write(
                                f"✓ [{result['position']}/{total_videos}] {result['title']}"
                            )
                        else:
                            skipped += 1
                            tqdm.write(
                                f"✗ [{result['position']}/{total_videos}] {result['title'][:50]} - {result['error']}"
                            )

                        overall_pbar.update(1)
                        # Update description to show success count
                        overall_pbar.set_description(f"Progress ({downloaded} ✓)")

                except KeyboardInterrupt:
                    print("\n\n🛑 Download interrupted by user (Ctrl+C)")
                    print("Cancelling remaining downloads...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    sys.exit(0)

        print(f"\n{'=' * 60}")
        print(f"Download Complete!")
        print(f"Downloaded: {downloaded} | Skipped: {skipped} | Total: {total_videos}")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"Error with playlist audio download: {str(e)}")
        raise
