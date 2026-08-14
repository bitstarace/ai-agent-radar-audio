"""日次レポート → ポッドキャスト風音声解説(m4a) → Google Drive保存 の一連の処理。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from google import genai

from drive_upload import upload_file
from fetch_report import get_latest_report
from gemini_audio import generate_dialogue_script, pcm_to_wav_bytes, synthesize_audio


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


def main() -> None:
    api_key = os.environ["GEMINI_API_KEY"]
    service_account_json_path = os.environ["GDRIVE_SERVICE_ACCOUNT_JSON_PATH"]
    folder_id = os.environ["GDRIVE_FOLDER_ID"]

    report_name, report_body = get_latest_report()
    print(f"[1/4] レポート取得: {report_name} ({len(report_body)} chars)")

    client = genai.Client(api_key=api_key)

    script_text = generate_dialogue_script(client, report_body)
    print(f"[2/4] 台本生成完了 ({len(script_text)} chars)")

    pcm_bytes = synthesize_audio(client, script_text)
    print(f"[3/4] 音声合成完了 ({len(pcm_bytes)} bytes PCM)")

    date_stamp = os.path.splitext(report_name)[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, f"{date_stamp}.wav")
        m4a_path = os.path.join(tmpdir, f"{date_stamp}.m4a")

        with open(wav_path, "wb") as f:
            f.write(pcm_to_wav_bytes(pcm_bytes))

        wav_to_m4a(wav_path, m4a_path)

        uploaded = upload_file(service_account_json_path, m4a_path, folder_id)
        print(f"[4/4] Google Driveへアップロード完了: {uploaded.get('name')} (id={uploaded.get('id')})")
        print(uploaded.get("webViewLink", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"エラー: {exc}", file=sys.stderr)
        raise
