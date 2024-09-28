import os
from utils import check_ffmpeg_installed, get_download_folder, remove_playlist_param
from downloader import download_video, download_playlist, download_audio, download_playlist_audio
from menu import display_menu, display_completion_art


def main():
    # Check if FFmpeg is installed
    check_ffmpeg_installed()

    while True:
        display_menu()
        downloads_folder = get_download_folder()
        audio_folder = os.path.join(downloads_folder, 'audio')
        video_folder = os.path.join(downloads_folder, 'video')

        os.makedirs(audio_folder, exist_ok=True)
        os.makedirs(video_folder, exist_ok=True)

        print("Select an option:")
        print("1. Download a single URL")
        print("2. Download a playlist")
        print("3. Exit")

        option = input("Select an option (1-3): ")

        if option == '3':
            print("\nExiting the program. Goodbye!\n")
            break

        media_type = input("Would you like to download video or audio only? (v/a): ").strip().lower()

        if media_type not in ['v', 'a']:
            print("Invalid selection. Please choose 'v' for video or 'a' for audio.")
            continue

        folder_name = input("Enter a folder name for the download (leave empty to ignore): ").strip()

        if option in ['1', '2']:
            output_path = video_folder if media_type == 'v' else audio_folder
        else:
            print("Invalid option selected. Please try again.")
            continue

        if folder_name:
            output_path = os.path.join(output_path, folder_name)
            os.makedirs(output_path, exist_ok=True)
            print(f"Downloading to: {output_path}")
        else:
            print(f"Downloading to: {output_path}")

        url = input("Enter the URL: ")

        if option == '1':
            url = remove_playlist_param(url)
            if media_type == 'v':
                download_video(url, output_path)
            elif media_type == 'a':
                download_audio(url, output_path)
        elif option == '2':
            if media_type == 'v':
                download_playlist(url, output_path)
            elif media_type == 'a':
                download_playlist_audio(url, output_path)

        display_completion_art()
        input("\nReturning to the main menu...\n")
        os.system('cls')  # Clear the screen


if __name__ == "__main__":
    main()
