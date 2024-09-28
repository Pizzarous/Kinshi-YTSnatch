# Kinshi-YTSnatch

**Kinshi-YTSnatch** is a simple command-line tool that allows you to download YouTube videos or playlists and convert them to MP3 format. With options for video-only or audio-only downloads, it provides a streamlined way to manage media using `yt-dlp` and `ffmpeg` for conversion. Perfect for quick, easy video and audio downloads!

## Features

- **Single URL Download**: Download individual YouTube videos.
- **Playlist Download**: Download entire YouTube playlists.
- **Audio Extraction**: Convert YouTube videos to MP3 format.
- **Video Download**: Download videos in MP4 format.
- **User-Friendly CLI**: Simple command-line interface.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Pizzarous/Kinshi-YTSnatch.git
   ```

2. **Navigate to the directory**:

   ```bash
   cd Kinshi-YTSnatch
   ```

3. **Install dependencies**:

   Make sure you have **Python** (3.6+) installed. Then, run:

   ```bash
   pip install yt-dlp
   ```

4. **Download and set up FFmpeg**:
   - Download the [full version of FFmpeg](https://ffmpeg.org/download.html).
   - Place `ffmpeg.exe` into the `requirements` folder you just created.
   - Add the `requirements` folder to your Windows PATH:
     1. Right-click on **This PC** or **My Computer** and select **Properties**.
     2. Click on **Advanced system settings**.
     3. Click on the **Environment Variables** button.
     4. In the **System variables** section, find the **Path** variable and select it. Click **Edit**.
     5. Click **New** and add the path to your `requirements` folder (e.g., `C:\path\Kinshi-YTSnatch\requirements`).
     6. Click **OK** to close all dialog boxes.

## Usage

To run **Kinshi-YTSnatch**, you can either execute the Python script directly or use the included `run.bat` file.

### Option 1: Using Python directly

1. Navigate to the `src` directory:

   ```bash
   cd src
   ```

2. Run **Kinshi-YTSnatch**:

   ```bash
   python __main__.py
   ```

To modify the **Option 2 Batch File** section of your `README.md` to reflect the changes you have made in the Python code, you'll want to clarify how to run the application through the batch file. Below is an updated version that emphasizes using the batch file to run your project:

### Option 2: Using the Batch File

To easily run **Kinshi-YTSnatch**, you can use the included batch file. This will handle the setup for you.

1. **Double-click the `run.bat` file** located in the root directory of the repository to launch the application.

You'll then be prompted with options to choose from:

```
1. Download a single URL
2. Download a playlist
3. Exit
```

2. **Choose an option**:

   - **Single URL**: Downloads only the video from the provided URL.
   - **Playlist**: Downloads all videos from the provided playlist URL.
   - **Exit**: Exits the application.

3. After selecting an option, you'll be asked whether you'd like to download video or audio only (`v/a`).

4. Enter a custom folder name for the download or leave it empty to ignore it.

5. Finally, enter the URL you want to download from. The application will process the request and display completion status.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit the changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## Issues

If you encounter any issues, feel free to open an issue in the [Issues tab](https://github.com/Pizzarous/Kinshi-YTSnatch/issues).

---

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for handling video/audio downloads.
- [ffmpeg](https://ffmpeg.org/) for audio conversion.

---

Enjoy using **Kinshi-YTSnatch**! 😊
