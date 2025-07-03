from datetime import datetime
from unittest.mock import patch
from yt_subs_dl import (
    parse_srt_timestamp,
    format_srt_content,
    select_language,
    get_video_info,
    get_srt_content,
)


def test_parse_srt_timestamp():
    """Tests the parsing of SRT timestamp strings."""
    assert parse_srt_timestamp("00:00:01,123") == datetime.strptime(
        "00:00:01.123", "%H:%M:%S.%f"
    )


def test_format_srt_content_cjk():
    """Tests formatting of SRT content for CJK languages."""
    srt_content = """
1
00:00:00,000 --> 00:00:02,000
こんにちは

2
00:00:03,000 --> 00:00:05,000
世界

3
00:00:10,000 --> 00:00:12,000
元気ですか
"""
    expected = "こんにちは世界\n元気ですか"
    assert format_srt_content(srt_content, 5.0, "ja") == expected


def test_format_srt_content_other_lang():
    """Tests formatting of SRT content for non-CJK languages."""
    srt_content = """
1
00:00:00,000 --> 00:00:02,000
Hello

2
00:00:03,000 --> 00:00:05,000
world

3
00:00:10,000 --> 00:00:12,000
How are you
"""
    expected = "Hello world\nHow are you"
    assert format_srt_content(srt_content, 5.0, "en") == expected


def test_format_srt_content_no_newline():
    """Tests that no newline is added if the time threshold is not met."""
    srt_content = """
1
00:00:00,000 --> 00:00:02,000
First part

2
00:00:03,000 --> 00:00:05,000
Second part
"""
    expected = "First part Second part"
    assert format_srt_content(srt_content, 2.0, "en") == expected


def test_select_language_priority():
    """Tests the language selection logic."""
    mock_info = {
        "subtitles": {"ja": [{}], "de": [{}]},
        "automatic_captions": {"en": [{}], "de": [{}], "ja": [{}]},
        "language": "de",
    }
    # Prefers default language
    assert select_language(mock_info, True, ["en", "ja"]) == "de"
    # Prefers ja over de
    assert select_language(mock_info, False, ["ja", "de"]) == "ja"
    # Prefers subtitles not automated
    assert select_language(mock_info, False, ["en", "ja"]) == "ja"
    # Falls back to existing languages
    assert select_language(mock_info, False, ["es", "en"]) == "en"


@patch("yt_dlp.YoutubeDL")
def test_get_video_info(mock_yt_dlp):
    """Tests the retrieval of video info."""
    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {"id": "test_id"}
    info = get_video_info("some_url")
    assert info["id"] == "test_id"


@patch("requests.get")
@patch("yt_dlp.YoutubeDL")
def test_get_srt_content(mock_yt_dlp, mock_requests_get):
    """Tests the subtitle content retrieval."""
    # Mock yt-dlp
    mock_ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        "requested_subtitles": {"en": {"url": "http://example.com/subtitle.srt"}}
    }

    # Mock requests.get
    mock_response = mock_requests_get.return_value
    mock_response.text = "SRT content"
    mock_response.raise_for_status.return_value = None

    # Call the function
    content = get_srt_content("some_url", "en")

    # Assertions
    mock_ydl_instance.extract_info.assert_called_with("some_url", download=False)
    mock_requests_get.assert_called_with("http://example.com/subtitle.srt")
    assert content == "SRT content"
