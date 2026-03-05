import requests
from config import DISCORD_WEBHOOK_URL


def send_discord_notification(title: str, success: bool, detail: str = ""):
    """Send a Discord embed notification via webhook.

    Silently no-ops when DISCORD_WEBHOOK_URL is not configured.
    Never raises — logs a warning on HTTP errors.
    """
    if not DISCORD_WEBHOOK_URL:
        return

    color = 0x57F287 if success else 0xED4245  # green / red
    emoji = "✅" if success else "❌"

    embed = {
        "title": f"{emoji} {title}",
        "color": color,
    }
    if detail:
        embed["description"] = detail

    payload = {"embeds": [embed]}

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ Discord 通知发送失败: {e}")
