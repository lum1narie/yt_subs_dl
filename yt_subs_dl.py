import argparse
import sys
import re
from datetime import datetime
import yt_dlp
import requests

# Languages that do not use spaces as word delimiters
NO_SPACE_LANGUAGES = {"ja", "zh", "ko", "th", "lo", "km", "my"}


def parse_srt_timestamp(ts_str):
    """Converts a SRT timestamp string to a datetime object."""
    # SRT uses comma as millisecond separator
    return datetime.strptime(ts_str.replace(",", "."), "%H:%M:%S.%f")


def get_video_info(url):
    """Retrieves video information using yt-dlp."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to fetch video info. {e}", file=sys.stderr)
        sys.exit(1)


def select_language(info, prefer_default_lang, lang_priority_list):
    """Selects the optimal language based on the specifications."""
    available_manual_subs = info.get("subtitles", {})
    available_auto_caps = info.get("automatic_captions", {})

    # 1. Prioritize default language (manual subtitles)
    video_lang = info.get("language")
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
    manual_subs_keys = info.get("subtitles", {}).keys()
    if manual_subs_keys:
        print(
            f"Available manual subtitles: {', '.join(manual_subs_keys)}",
            file=sys.stderr,
        )
    auto_caps_keys = info.get("automatic_captions", {}).keys()
    if auto_caps_keys:
        print(
            f"Available automatic captions: {', '.join(auto_caps_keys)}",
            file=sys.stderr,
        )
    sys.exit(1)


def get_srt_content(url, lang):
    """Fetches subtitle content by getting the URL and downloading it."""
    ydl_opts = {
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
            info = ydl.extract_info(url, download=False)
            req_subs = info.get("requested_subtitles")

            if not req_subs or lang not in req_subs or "url" not in req_subs[lang]:
                print(
                    f"Error: Could not find SRT subtitle URL for language '{lang}'.",
                    file=sys.stderr,
                )
                sys.exit(1)

            subtitle_url = req_subs[lang]["url"]

    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to fetch subtitle info. {e}", file=sys.stderr)
        sys.exit(1)

    try:
        response = requests.get(subtitle_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        # yt-dlp sometimes returns content with a BOM
        return response.text.lstrip("\ufeff")
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download subtitle content. {e}", file=sys.stderr)
        sys.exit(1)


def format_srt_content(srt_content, threshold, lang):
    """Formats the SRT content according to the specifications."""
    lines = srt_content.splitlines()
    output_parts = []
    last_end_time = None

    # Regular expression to detect SRT timestamp lines
    timestamp_re = re.compile(
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})"
    )

    text_buffer = []
    space_not_required = lang.rstrip("_orig") in NO_SPACE_LANGUAGES

    i = 0
    while i < len(lines):
        # Skip empty lines and sequence number
        if not lines[i].strip() or lines[i].strip().isdigit():
            i += 1
            continue

        match = timestamp_re.match(lines[i])
        if match:
            start_time_str, end_time_str = match.groups()
            current_start_time = parse_srt_timestamp(start_time_str)
            current_end_time = parse_srt_timestamp(end_time_str)

            # Text is on the next line(s)
            i += 1
            current_text_lines = []
            while i < len(lines) and lines[i].strip():
                current_text_lines.append(lines[i].strip())
                i += 1

            if not current_text_lines:
                continue

            current_text = " ".join(current_text_lines)

            if last_end_time:
                time_diff = (current_start_time - last_end_time).total_seconds()
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
            "".join(text_buffer) if space_not_required else " ".join(text_buffer)
        )

    return "".join(output_parts)


def handle_raw_output(srt_content):
    """Prints the raw SRT content to stdout and exits."""
    print(srt_content)
    sys.exit(0)


def handle_formatted_output(srt_content, args, selected_lang):
    """Formats and prints the SRT content to stdout."""
    if args.verbose:
        print("\n--- Raw SRT Content ---\n", file=sys.stderr)
        print(srt_content, file=sys.stderr)
        print("\n--- End Raw SRT Content ---\n", file=sys.stderr)

    formatted_text = format_srt_content(srt_content, args.threshold, selected_lang)
    print(formatted_text)


def main():
    """Main processing function."""
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

    args = parser.parse_args()

    if args.threshold < 0:
        print("Error: --threshold must be non-negative.", file=sys.stderr)
        sys.exit(1)

    lang_priority = args.languages.split(",")

    video_info = get_video_info(args.url)

    selected_lang = select_language(video_info, args.prefer_default, lang_priority)

    if args.verbose:
        print(f"Selected language: {selected_lang}", file=sys.stderr)

    srt_content = get_srt_content(args.url, selected_lang)

    if not srt_content:
        print("Error: Failed to retrieve subtitle content.", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        handle_raw_output(srt_content)
    else:
        handle_formatted_output(srt_content, args, selected_lang)


if __name__ == "__main__":
    main()
