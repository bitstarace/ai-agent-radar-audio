"""takeday/ai-agent-radar の reports/ から最新の日次レポートを取得する。"""
from __future__ import annotations

import os

import requests

SOURCE_REPO = "takeday/ai-agent-radar"
REPORTS_PATH = "reports"


MAX_REPOS = int(os.environ.get("MAX_REPOS", "10"))
_REPO_SECTION = "## 新規・トレンド GitHub リポジトリ"


def limit_repos(markdown: str, max_repos: int = MAX_REPOS) -> str:
    """「新規・トレンド GitHub リポジトリ」セクションだけ、リポジトリ(####)を先頭 max_repos 件に絞る。

    他のセクションは変更しない。max_repos <= 0 なら全件。
    上限に達した後は、そのセクションの終わり(次の「## 」見出し)まで読み飛ばす。
    """
    if max_repos <= 0:
        return markdown
    out: list[str] = []
    in_section = False
    skipping = False
    count = 0
    for line in markdown.splitlines(keepends=True):
        if line.startswith("## "):
            in_section = line.startswith(_REPO_SECTION)
            skipping = False
        elif in_section and line.startswith("#### "):
            count += 1
            if count > max_repos:
                skipping = True
        if not skipping:
            out.append(line)
    return "".join(out).rstrip() + "\n"


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
