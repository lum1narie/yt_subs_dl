import argparse
import sys
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import yt_dlp
import requests

# Languages that do not use spaces as word delimiters
NO_SPACE_LANGUAGES: set[str] = {"ja", "zh", "ko", "th", "lo", "km", "my"}


def parse_srt_timestamp(ts_str: str) -> datetime:
    """Converts a SRT timestamp string to a datetime object.

    Args:
        ts_str (str): The SRT timestamp string (e.g., "00:00:01,234").

    Returns:
        datetime: A datetime object representing the parsed timestamp.

    Raises:
        ValueError: If the timestamp string format is invalid.
    """
    # SRT uses comma as millisecond separator
    return datetime.strptime(ts_str.replace(",", "."), "%H:%M:%S.%f")


def get_video_info(url: str) -> Dict[str, Any]:
    """Retrieves video information using yt-dlp.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        dict: A dictionary containing video information.

    Raises:
        SystemExit: If fetching video info fails.
    """
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: Dict[str, Any] = ydl.extract_info(url, download=False)
            return info
    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to fetch video info. {e}", file=sys.stderr)
        sys.exit(1)


def select_language(
    info: Dict[str, Any], prefer_default_lang: bool, lang_priority_list: List[str]
) -> str:
    """Selects the optimal language based on the specifications.

    Args:
        info (dict): The video information dictionary obtained from yt-dlp.
        prefer_default_lang (bool):
            Whether to prioritize the video's default language.
        lang_priority_list (list):
            A list of preferred language codes in order of priority.

    Returns:
        str: The selected language code.

    Raises:
        SystemExit: If no suitable language is found.
    """
    available_manual_subs: Dict[str, Any] = info.get("subtitles", {})
    available_auto_caps: Dict[str, Any] = info.get("automatic_captions", {})

    # 1. Prioritize default language (manual subtitles)
    video_lang: Optional[str] = info.get("language")
    if prefer_default_lang and video_lang and video_lang in available_manual_subs:
        return video_lang

    # 2. Check priority language list (manual subtitles)
    for lang in lang_priority_list:
        if lang in available_manual_subs:
            return lang

    # 3. Prioritize default language (auto-generated captions)
    if prefer_default_lang and video_lang and video_lang in available_auto_caps:
        return video_lang

    # 4. Check priority language list (auto-generated captions)
    for lang in lang_priority_list:
        if lang in available_auto_caps:
            return lang

    # If no suitable language is found
    print(
        "Error: Could not find a suitable subtitle language based on your preferences.",
        file=sys.stderr,
    )
    manual_subs_keys: List[str] = list(info.get("subtitles", {}).keys())
    if manual_subs_keys:
        print(
            f"Available manual subtitles: {', '.join(manual_subs_keys)}",
            file=sys.stderr,
        )
    auto_caps_keys: List[str] = list(info.get("automatic_captions", {}).keys())
    if auto_caps_keys:
        print(
            f"Available automatic captions: {', '.join(auto_caps_keys)}",
            file=sys.stderr,
        )
    sys.exit(1)


def get_srt_content(url: str, lang: str) -> str:
    """Fetches subtitle content by getting the URL and downloading it.

    Args:
        url (str): The URL of the YouTube video.
        lang (str): The language code of the desired subtitle.

    Returns:
        str: The raw SRT content as a string.

    Raises:
        SystemExit: If fetching subtitle info or downloading content fails.
    """
    ydl_opts: Dict[str, Any] = {
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang],
        "subtitlesformat": "srt",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: Dict[str, Any] = ydl.extract_info(url, download=False)
            req_subs: Optional[Dict[str, Any]] = info.get("requested_subtitles")

            if not req_subs or (lang not in req_subs) or ("url" not in req_subs[lang]):
                print(
                    f"Error: Could not find SRT subtitle URL for language '{lang}'.",
                    file=sys.stderr,
                )
                sys.exit(1)

            subtitle_url: str = req_subs[lang]["url"]

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to fetch subtitle info. {e}", file=sys.stderr)
        sys.exit(1)

    try:
        response: requests.Response = requests.get(subtitle_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        # yt-dlp sometimes returns content with a BOM
        return response.text.lstrip("\ufeff")
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download subtitle content. {e}", file=sys.stderr)
        sys.exit(1)


def format_srt_content(srt_content: str, threshold: float, lang: str) -> str:
    """Formats the SRT content according to the specifications.

    This function processes the raw SRT content, merging subtitle segments and
    inserting newlines based on a specified time threshold between segments.
    It also handles language-specific spacing rules (e.g., for CJK languages).

    Args:
        srt_content (str): The raw SRT content as a string.
        threshold (float):
            The time threshold in seconds. If the gap between two
            subtitle segments is greater than or equal to this
            threshold, a newline will be inserted.
        lang (str): The language code of the subtitle. Used to determine if
                    spaces are required between words
                    (e.g., for CJK languages).

    Returns:
        str: The formatted subtitle text.
    """
    lines: List[str] = srt_content.splitlines()
    output_parts: List[str] = []
    last_end_time: Optional[datetime] = None

    # Regular expression to detect SRT timestamp lines
    timestamp_re = re.compile(
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})"
    )

    text_buffer: List[str] = []
    space_not_required: bool = lang.rstrip("_orig") in NO_SPACE_LANGUAGES

    i: int = 0
    while i < len(lines):
        # Skip empty lines and sequence number
        if not lines[i].strip() or lines[i].strip().isdigit():
            i += 1
            continue

        match: Optional[re.Match[str]] = timestamp_re.match(lines[i])
        if match:
            start_time_str, end_time_str = match.groups()
            current_start_time: datetime = parse_srt_timestamp(start_time_str)
            current_end_time: datetime = parse_srt_timestamp(end_time_str)

            # Text is on the next line(s)
            i += 1
            current_text_lines: List[str] = []
            while i < len(lines) and lines[i].strip():
                current_text_lines.append(lines[i].strip())
                i += 1

            if not current_text_lines:
                continue

            current_text: str = " ".join(current_text_lines)

            if last_end_time:
                time_diff: float = (current_start_time - last_end_time).total_seconds()
                if time_diff >= threshold:
                    output_parts.append(
                        "".join(text_buffer)
                        if space_not_required
                        else " ".join(text_buffer)
                    )
                    output_parts.append("\n")
                    text_buffer = []

            text_buffer.append(current_text)
            last_end_time = current_end_time
        else:
            i += 1

    if text_buffer:
        output_parts.append(
            ("".join(text_buffer) if space_not_required else " ".join(text_buffer))
        )

    return "".join(output_parts)


def handle_raw_output(srt_content: str) -> None:
    """Prints the raw SRT content to stdout and exits.

    Args:
        srt_content (str): The raw SRT content to be printed.
    """
    print(srt_content)
    sys.exit(0)


def handle_formatted_output(
    srt_content: str, args: argparse.Namespace, selected_lang: str
) -> None:
    """Formats and prints the SRT content to stdout.

    Args:
        srt_content (str): The raw SRT content.
        args (argparse.Namespace): The parsed command-line arguments.
        selected_lang (str): The language code of the selected subtitle.
    """
    if args.verbose:
        print("\n--- Raw SRT Content ---\n", file=sys.stderr)
        print(srt_content, file=sys.stderr)
        print("\n--- End Raw SRT Content ---\n", file=sys.stderr)

    formatted_text: str = format_srt_content(srt_content, args.threshold, selected_lang)
    print(formatted_text)


def main() -> None:
    """Main processing function.

    Parses command-line arguments, retrieves video information, selects the
    appropriate subtitle language, fetches the subtitle content, and then
    either prints the raw content or formats it before printing, based on
    user arguments.

    Raises:
        SystemExit: If an invalid threshold is provided or if subtitle
                    content cannot be retrieved.
    """
    parser = argparse.ArgumentParser(
        description="Download and format YouTube subtitles."
    )
    parser.add_argument("url", help="URL of the YouTube video.")
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=5.0,
        help="Threshold in seconds to insert a newline. Must be >= 0. (default: 5.0)",
    )
    parser.add_argument(
        "-D",
        "--no-prefer-default-language",
        action="store_false",
        dest="prefer_default",
        help="Disable preferring the video's default language.",
    )
    parser.add_argument(
        "-l",
        "--languages",
        default="ja,en",
        help="Comma-separated list of preferred languages. (default: ja,en)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output, showing selected language and raw VTT content.",
    )
    parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Output the raw SRT content without formatting.",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.threshold < 0:
        print("Error: --threshold must be non-negative.", file=sys.stderr)
        sys.exit(1)

    lang_priority: List[str] = args.languages.split(",")

    video_info: Dict[str, Any] = get_video_info(args.url)

    selected_lang: str = select_language(video_info, args.prefer_default, lang_priority)

    if args.verbose:
        print(f"Selected language: {selected_lang}", file=sys.stderr)

    srt_content: str = get_srt_content(args.url, selected_lang)

    if not srt_content:
        print("Error: Failed to retrieve subtitle content.", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        handle_raw_output(srt_content)
    else:
        handle_formatted_output(srt_content, args, selected_lang)


if __name__ == "__main__":
    main()
