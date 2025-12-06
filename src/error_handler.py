"""
Error handling utilities for Kinshi-YTSnatch
Handles yt-dlp error suppression and formatting
"""


class SuppressLogger:
    """Custom logger to suppress yt-dlp's verbose error messages"""

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass  # Suppress error messages from yt-dlp


def extract_error_message(exception):
    """
    Extract a clean, readable one-line error message from yt-dlp exceptions

    Args:
        exception: The exception object from yt-dlp

    Returns:
        str: A clean, formatted error message (max 70 chars)
    """
    error_msg = str(exception)

    # Extract the main error from yt-dlp's verbose output
    if "ERROR:" in error_msg:
        # Get the line with ERROR:
        error_lines = [line for line in error_msg.split("\n") if "ERROR:" in line]
        if error_lines:
            error_msg = error_lines[0].replace("ERROR:", "").strip()

            # Remove the video ID prefix if present (e.g., "[youtube] vFCMsitdmQI:")
            if "]" in error_msg and error_msg.startswith("["):
                error_msg = error_msg.split("]", 1)[1].strip()

            # Remove the colon after video ID if still present
            if ":" in error_msg and error_msg.index(":") < 15:
                error_msg = error_msg.split(":", 1)[1].strip()

            # Limit length to 70 chars
            if len(error_msg) > 70:
                error_msg = error_msg[:70] + "..."
    else:
        # Get first line of error
        error_msg = error_msg.split("\n")[0][:70]

    return error_msg
