import os

from downloader import (
    download_audio,
    download_from_list,
    download_playlist,
    download_playlist_audio,
    download_video,
)
from menu import display_completion_art, display_menu
from utils import check_ffmpeg_installed, get_download_folder, remove_playlist_param


def main():
    # Check if FFmpeg is installed
    check_ffmpeg_installed()

    while True:
        display_menu()

        # Get the download folder path
        downloads_folder = get_download_folder()

        # Create the downloads folder if it doesn't exist
        os.makedirs(downloads_folder, exist_ok=True)

        # Prompt to select an option
        print("Select an option:")
        print("1. Download a single URL")
        print("2. Download a playlist")
        print("3. Download from a list of links (paste several links into a file)")
        print("4. Exit")

        option = input("Select an option (1-4): ")

        # Exit the program if the user selects option 4
        if option == "4":
            print("\nExiting the program. Goodbye!\n")
            break

        # Clear the screen and prompt the user to try again if an invalid option is selected
        if option not in ["1", "2", "3"]:
            os.system("cls")
            print("\nInvalid option selected. Please try again.\n")
            continue

        # Prompt the user to select the media type (video or audio)
        media_type = (
            input("Would you like to download video or audio only? (v/a): ")
            .strip()
            .lower()
        )

        # Clear the screen and prompt the user to try again if an invalid media type is selected
        if media_type not in ["v", "a"]:
            os.system("cls")
            print(
                "\nInvalid selection. Please choose 'v' for video or 'a' for audio.\n"
            )
            continue
        else:
            # Set the output path to downloads folder by default
            output_path = downloads_folder

        # Prompt to enter a folder name for the download
        folder_name = input(
            "Enter a folder name for the download (leave empty to ignore): "
        ).strip()

        # If a folder name is provided, create the folder and update the output path
        if folder_name:
            output_path = os.path.join(output_path, folder_name)
            os.makedirs(output_path, exist_ok=True)
            print(f"Downloading to: {output_path}")
        else:
            print(f"Downloading to: {output_path}")

        # Option 3 gathers links through a text file instead of a single URL prompt
        if option != "3":
            url = input("Enter the URL: ")

        # Download based on the selected option and media type
        if option == "1":
            # Remove playlist parameter for single URL downloads
            url = remove_playlist_param(url)
            if media_type == "v":
                download_video(url, output_path)
            elif media_type == "a":
                download_audio(url, output_path)
        elif option == "2":
            if media_type == "v":
                download_playlist(url, output_path)
            elif media_type == "a":
                download_playlist_audio(url, output_path)
        elif option == "3":
            download_from_list(output_path, media_type)

        # Display completion art and prompt to return to the main menu
        display_completion_art()
        input("\nReturning to the main menu...\n")

        # Clear the screen
        os.system("cls")


if __name__ == "__main__":
    main()
