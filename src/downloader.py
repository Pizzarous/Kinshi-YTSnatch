import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yt_dlp
from tqdm import tqdm

from error_handler import SuppressLogger, extract_error_message


def _get_yt_dlp_base_opts():
    """
    Returns base yt-dlp options with YouTube-specific workarounds.
    Addresses 403 errors and SABR streaming issues.
    """
    return {
        # Use multiple player clients to get more format options
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs"],
            }
        },
        # Add HTTP headers to appear more like a browser
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
        },
        # Retry and network options
        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": True,
        # Avoid throttling
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "sleep_interval_requests": 1,
    }


def _merge_opts(*opts_dicts):
    """Merge multiple yt-dlp option dicts, with later dicts taking precedence."""
    result = {}
    for opts in opts_dicts:
        for key, value in opts.items():
            if key == "extractor_args" and key in result:
                # Deep merge extractor_args
                for extractor, args in value.items():
                    if extractor not in result[key]:
                        result[key][extractor] = {}
                    result[key][extractor].update(args)
            elif key == "http_headers" and key in result:
                # Merge headers
                result[key].update(value)
            else:
                result[key] = value
    return result


def _download_with_retry(ydl, url, max_retries=3, delay=2):
    """
    Download a URL through an existing YoutubeDL instance, retrying a few times
    if a transient Windows file-lock error shows up (WinError 32/5). This happens
    when antivirus or search indexing briefly locks a file right after ffmpeg
    writes/renames it - retrying after a short pause almost always succeeds.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            ydl.download([url])
            return
        except (OSError, PermissionError) as e:
            last_error = e
            msg = str(e)
            transient = (
                "used by another process" in msg
                or "Access is denied" in msg
                or "WinError 32" in msg
                or "WinError 5" in msg
            )
            if transient and attempt < max_retries:
                time.sleep(delay)
                continue
            raise
    if last_error:
        raise last_error


def download_video(url, output_path):
    # Function to download a single video
    base_opts = _get_yt_dlp_base_opts()

    try:
        # First, check if the video is accessible without downloading
        print("Checking video availability...")
        check_opts = _merge_opts(base_opts, {"quiet": True})
        with yt_dlp.YoutubeDL(check_opts) as ydl:
            # Just check if the video exists, don't store the info
            ydl.extract_info(url, download=False)

        # Then try to download with specific format selection
        print("Attempting download...")
        ydl_opts = _merge_opts(
            base_opts,
            {
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
            },
        )
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach with simpler format selection...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = _merge_opts(
                base_opts,
                {
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
                },
            )
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                ydl.download([url])

        except yt_dlp.utils.DownloadError as e2:
            # If that also fails, try listing formats and a manual approach
            print("Second attempt failed. Let's list available formats:")
            try:
                list_opts = _merge_opts(base_opts, {"listformats": True})
                with yt_dlp.YoutubeDL(list_opts) as ydl:
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
    base_opts = _get_yt_dlp_base_opts()

    try:
        ydl_opts = _merge_opts(
            base_opts,
            {
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
            },
        )
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {str(e)}")
        print("Trying alternative approach...")

        # Alternative approach with simpler format selection
        try:
            alt_opts = _merge_opts(
                base_opts,
                {
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
                },
            )
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
    title = video_info.get("title") or video_url
    short_title = title[:50] + "..." if len(title) > 50 else title

    # Create progress bar for this download
    pbar = None

    def progress_hook(d):
        nonlocal pbar, title, short_title
        # If we started with just a URL as a placeholder title, swap in the
        # real title as soon as yt-dlp resolves it during download.
        info = d.get("info_dict") or {}
        real_title = info.get("title")
        if real_title and title == video_url:
            title = real_title
            short_title = title[:50] + "..." if len(title) > 50 else title

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
        base_opts = _get_yt_dlp_base_opts()
        ydl_opts = _merge_opts(
            base_opts,
            {
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
            },
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            _download_with_retry(ydl, video_url)

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
        base_opts = _get_yt_dlp_base_opts()
        ydl_opts = _merge_opts(
            base_opts,
            {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "ignoreerrors": True,
            },
        )

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
    title = video_info.get("title") or video_url
    short_title = title[:50] + "..." if len(title) > 50 else title

    # Create progress bar for this download
    pbar = None

    def progress_hook(d):
        nonlocal pbar, title, short_title
        # If we started with just a URL as a placeholder title, swap in the
        # real title as soon as yt-dlp resolves it during download.
        info = d.get("info_dict") or {}
        real_title = info.get("title")
        if real_title and title == video_url:
            title = real_title
            short_title = title[:50] + "..." if len(title) > 50 else title

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
        base_opts = _get_yt_dlp_base_opts()
        ydl_opts = _merge_opts(
            base_opts,
            {
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
            },
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            _download_with_retry(ydl, video_url)

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


def download_from_list(output_path, media_type):
    """
    Create a text file, wait for the user to paste one YouTube link per line and save it,
    then download every link (video or audio) the same way a playlist would be downloaded.
    The text file is deleted once all downloads finish.

    Args:
        output_path: folder to save downloads into
        media_type: "v" for video, "a" for audio
    """
    list_file = os.path.join(output_path, "links.txt")

    # Create an empty file for the user to fill in
    with open(list_file, "w", encoding="utf-8") as f:
        pass

    print(f"\nA file has been created at:\n  {list_file}")
    print("Open it, paste one YouTube link per line, then save and close it.")
    input("Press Enter here once you're done...\n")

    # Read back the links the user saved
    with open(list_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("No links found in the file. Nothing to download.")
        os.remove(list_file)
        return

    print(f"\nFound {len(urls)} link(s). Starting download...\n")

    # Build the download queue directly from the urls - no separate pass to
    # look up titles first. Each worker resolves the real title itself once
    # its download starts, so nothing is wasted double-fetching info.
    videos = [{"url": u, "id": u, "title": u} for u in urls]

    total_videos = len(videos)

    downloaded = 0
    skipped = 0
    pbar_lock = threading.Lock()
    active_bars = {}  # Track which progress bar positions are in use

    worker_fn = (
        _download_single_video_from_playlist
        if media_type == "v"
        else _download_single_audio_from_playlist
    )

    # Use ThreadPoolExecutor for parallel downloads (3 workers), same as playlist mode
    with ThreadPoolExecutor(max_workers=3) as executor:
        with tqdm(
            total=total_videos, desc="Overall Progress", position=0, leave=True
        ) as overall_pbar:
            try:
                futures = {
                    executor.submit(
                        worker_fn,
                        video,
                        output_path,
                        idx + 1,
                        pbar_lock,
                        active_bars,
                    ): idx
                    for idx, video in enumerate(videos)
                }

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

    # Clean up the txt file now that everything has downloaded
    try:
        os.remove(list_file)
        print(f"Removed temporary file: {list_file}\n")
    except OSError:
        pass


def download_playlist_audio(url, output_path):
    """Download audio from all videos in a playlist with parallel processing (3 concurrent downloads)"""
    try:
        print("Extracting playlist information...")

        # Extract playlist info
        base_opts = _get_yt_dlp_base_opts()
        ydl_opts = _merge_opts(
            base_opts,
            {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "ignoreerrors": True,
            },
        )

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
