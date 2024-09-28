import os
from utils import check_ffmpeg_installed, get_download_folder, remove_playlist_param
from downloader import download_video, download_playlist, download_audio, download_playlist_audio
from menu import display_menu, display_completion_art


def main():
    # Check if FFmpeg is installed
    check_ffmpeg_installed()

    while True:
        display_menu()

        # Get the download folder paths for audio and video
        downloads_folder = get_download_folder()
        audio_folder = os.path.join(downloads_folder, 'audio')
        video_folder = os.path.join(downloads_folder, 'video')

        # Create the audio and video folders if they don't exist
        os.makedirs(audio_folder, exist_ok=True)
        os.makedirs(video_folder, exist_ok=True)

        # Prompt to select an option
        print("Select an option:")
        print("1. Download a single URL")
        print("2. Download a playlist")
        print("3. Exit")

        option = input("Select an option (1-3): ")

        # Exit the program if the user selects option 3
        if option == '3':
            print("\nExiting the program. Goodbye!\n")
            break

        # Clear the screen and prompt the user to try again if an invalid option is selected
        if option not in ['1', '2']:
            os.system('cls')
            print("\nInvalid option selected. Please try again.\n")
            continue

        # Prompt the user to select the media type (video or audio)
        media_type = input("Would you like to download video or audio only? (v/a): ").strip().lower()

        # Clear the screen and prompt the user to try again if an invalid media type is selected
        if media_type not in ['v', 'a']:
            os.system('cls')
            print("\nInvalid selection. Please choose 'v' for video or 'a' for audio.\n")
            continue
        else:
            # Set the output path based on the media type
            output_path = video_folder if media_type == 'v' else audio_folder

        # Prompt to enter a folder name for the download
        folder_name = input("Enter a folder name for the download (leave empty to ignore): ").strip()

        # If a folder name is provided, create the folder and update the output path
        if folder_name:
            output_path = os.path.join(output_path, folder_name)
            os.makedirs(output_path, exist_ok=True)
            print(f"Downloading to: {output_path}")
        else:
            print(f"Downloading to: {output_path}")

        url = input("Enter the URL: ")

        # Download based on the selected option and media type
        if option == '1':
            # Remove playlist parameter for single URL downloads
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

        # Display completion art and prompt to return to the main menu
        display_completion_art()
        input("\nReturning to the main menu...\n")

        # Clear the screen
        os.system('cls')


if __name__ == "__main__":
    main()
