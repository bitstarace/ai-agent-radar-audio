"""takeday/ai-agent-radar の reports/ から最新の日次レポートを取得する。"""
from __future__ import annotations

import requests

SOURCE_REPO = "takeday/ai-agent-radar"
REPORTS_PATH = "reports"


def get_latest_report() -> tuple[str, str]:
    """(ファイル名, 本文Markdown) を返す。"""
    api_url = f"https://api.github.com/repos/{SOURCE_REPO}/contents/{REPORTS_PATH}"
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()
    entries = resp.json()

    md_files = [e for e in entries if e["type"] == "file" and e["name"].endswith(".md")]
    if not md_files:
        raise RuntimeError(f"{SOURCE_REPO}/{REPORTS_PATH} にMarkdownレポートが見つかりません")

    latest = max(md_files, key=lambda e: e["name"])
    content_resp = requests.get(latest["download_url"], timeout=30)
    content_resp.raise_for_status()
    return latest["name"], content_resp.text


if __name__ == "__main__":
    name, body = get_latest_report()
    print(f"latest report: {name} ({len(body)} chars)")
