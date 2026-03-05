import sys
from unittest.mock import patch, MagicMock

import pytest

# requests is mocked in conftest.py; grab the mock for assertions
mock_requests = sys.modules['requests']


@pytest.fixture(autouse=True)
def reset_mocks():
    mock_requests.reset_mock()
    yield


def test_notification_sent_on_success():
    """When webhook URL is set, a POST is made with a green embed."""
    with patch('notifier.DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test'):
        from notifier import send_discord_notification
        send_discord_notification("My Song", success=True, detail="已归档至 2026-03/04")

    args, kwargs = mock_requests.post.call_args
    assert args[0] == 'https://discord.com/api/webhooks/test'
    embed = kwargs['json']['embeds'][0]
    assert embed['color'] == 0x57F287
    assert "✅" in embed['title']
    assert "My Song" in embed['title']
    assert embed['description'] == "已归档至 2026-03/04"


def test_notification_sent_on_failure():
    """When webhook URL is set and success=False, embed is red."""
    with patch('notifier.DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test'):
        from notifier import send_discord_notification
        send_discord_notification("bad_url", success=False, detail="Network error")

    embed = mock_requests.post.call_args[1]['json']['embeds'][0]
    assert embed['color'] == 0xED4245
    assert "❌" in embed['title']


def test_no_notification_when_url_not_set():
    """When webhook URL is None, requests.post is never called."""
    with patch('notifier.DISCORD_WEBHOOK_URL', None):
        from notifier import send_discord_notification
        send_discord_notification("Song", success=True)

    mock_requests.post.assert_not_called()


def test_http_error_does_not_raise(capsys):
    """If the POST fails, we print a warning but never raise."""
    mock_requests.post.side_effect = Exception("Connection refused")

    with patch('notifier.DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test'):
        from notifier import send_discord_notification
        send_discord_notification("Song", success=True)

    captured = capsys.readouterr()
    assert "⚠️" in captured.out
    assert "Connection refused" in captured.out

    # cleanup
    mock_requests.post.side_effect = None
