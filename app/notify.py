"""Optional outbound notification for a completed monitoring run."""

import os
import sys
import ctypes
import subprocess

import requests


def changed_items(results: list[dict]) -> list[tuple[str, dict, str]]:
    """Return each new/updated item once, with its company and status."""
    items = []
    for result in results:
        for status in ("new", "updated"):
            for item in result[status]:
                items.append((result["company"], item, status.upper()))
    return items


def make_notification(results: list[dict]) -> dict | None:
    """Create a compact, webhook-compatible alert only when items changed."""
    items = changed_items(results)
    if not items:
        return None

    lines = [f"Website Change Monitor: {len(items)} new or changed publication(s)."]
    for company, item, status in items:
        website_date = item.get("date") or "date not shown"
        lines.append(
            f"{status} | {company} | {item['type']} | {item['title']} "
            f"({website_date})\n{item['url']}"
        )

    text = "\n\n".join(lines)
    # `text` is recognised by common Teams/Slack-style webhook relays; the
    # duplicate `content` makes the payload usable by Discord-style relays.
    return {"text": text, "content": text, "title": "Website Change Monitor"}


def notify_webhook(results: list[dict], webhook_url: str | None = None) -> str | None:
    """Post one alert, returning a user-readable outcome without leaking URLs."""
    payload = make_notification(results)
    if payload is None:
        return None

    destination = webhook_url or os.getenv("MONITOR_WEBHOOK_URL")
    if not destination:
        return "Updates found, but no notification was sent (MONITOR_WEBHOOK_URL is not configured)."

    try:
        response = requests.post(destination, json=payload, timeout=20)
        response.raise_for_status()
    except requests.RequestException as error:
        return f"Notification failed: {error}"

    return f"Notification sent for {len(changed_items(results))} publication(s)."


def notify_windows_popup(results: list[dict]) -> str | None:
    """Show a local Windows popup for changes; no account or service required."""
    payload = make_notification(results)
    if payload is None:
        return None

    if sys.platform != "win32":
        return "Popup notification is available only on Windows."

    # Keep a busy first baseline from producing an impractically large dialog.
    message = payload["text"][:3500]
    if len(payload["text"]) > len(message):
        message += "\n\nOpen the console report or dashboard for the remaining items."

    try:
        ctypes.windll.user32.MessageBoxW(0, message, payload["title"], 0x40)
    except OSError as error:
        return f"Popup notification failed: {error}"

    return f"Popup notification shown for {len(changed_items(results))} publication(s)."


def notify_windows_toast(results: list[dict]) -> str | None:
    """Show a non-blocking Windows notification-center toast."""
    payload = make_notification(results)
    if payload is None:
        return None
    if sys.platform != "win32":
        return "Toast notification is available only on Windows."

    body = payload["text"][:500]
    if len(payload["text"]) > len(body):
        body += "\nOpen the monitor report for more details."

    script = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$nodes = $xml.GetElementsByTagName('text')
[void]$nodes.Item(0).AppendChild($xml.CreateTextNode($env:MONITOR_TOAST_TITLE))
[void]$nodes.Item(1).AppendChild($xml.CreateTextNode($env:MONITOR_TOAST_BODY))
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Website Change Monitor').Show($toast)
"""
    environment = os.environ.copy()
    environment["MONITOR_TOAST_TITLE"] = payload["title"]
    environment["MONITOR_TOAST_BODY"] = body
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True, timeout=15, capture_output=True, text=True, env=environment,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return f"Toast notification failed: {error}"

    return f"Windows notification shown for {len(changed_items(results))} publication(s)."
