"""日次レポート → ポッドキャスト風音声解説(m4a) → Google Drive保存 の一連の処理。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from google import genai
from google.genai import types

from drive_upload import upload_file
from fetch_report import MAX_REPOS, get_latest_report, limit_repos
from gemini_audio import ensure_wav_bytes, generate_dialogue_script, synthesize_audio


def wav_to_m4a(wav_path: str, m4a_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            wav_path,
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            m4a_path,
        ],
        check=True,
        capture_output=True,
    )


def _diag_m4a(path: str) -> None:
    """変換後m4aの長さ・コーデック・音量をログに出す(診断用。失敗しても処理は続ける)。"""
    cmds = {
        "ffprobe": [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_name,sample_rate,channels,duration:format=duration,size",
            "-of", "default=nw=1", path,
        ],
        "volumedetect": ["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
    }
    for name, cmd in cmds.items():
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            out = (r.stdout + r.stderr).strip().splitlines()
            if name == "volumedetect":
                out = [l for l in out if "mean_volume" in l or "max_volume" in l]
            print(f"[diag] {name}: " + " | ".join(l.strip() for l in out))
        except Exception as exc:  # noqa: BLE001
            print(f"[diag] {name} 失敗: {exc}")


def main() -> None:
    api_key = os.environ["GEMINI_API_KEY"]
    folder_id = os.environ["GDRIVE_FOLDER_ID"]

    report_name, report_body = get_latest_report()
    full_len = len(report_body)
    report_body = limit_repos(report_body, MAX_REPOS)
    print(
        f"[1/4] レポート取得: {report_name} "
        f"({full_len} chars → GitHubリポジトリ先頭{MAX_REPOS}件に絞り込み {len(report_body)} chars)"
    )

    # speechConfig(TTS)はv1beta専用。SDK 3.x の既定は v1 のため明示する
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))

    script_text = generate_dialogue_script(client, report_body)
    print(f"[2/4] 台本生成完了 ({len(script_text)} chars)")

    audio_bytes = synthesize_audio(client, script_text)
    wav_bytes, wav_info = ensure_wav_bytes(audio_bytes)
    print(f"[3/4] 音声合成完了 ({len(audio_bytes)} bytes)")
    print(f"[diag] {wav_info}")

    date_stamp = os.path.splitext(report_name)[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, f"{date_stamp}.wav")
        m4a_path = os.path.join(tmpdir, f"{date_stamp}.m4a")

        with open(wav_path, "wb") as f:
            f.write(wav_bytes)

        wav_to_m4a(wav_path, m4a_path)
        _diag_m4a(m4a_path)

        uploaded = upload_file(m4a_path, folder_id)
        print(f"[4/4] Google Driveへアップロード完了: {uploaded.get('name')} (id={uploaded.get('id')})")
        print(uploaded.get("webViewLink", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"エラー: {exc}", file=sys.stderr)
        raise
