"""サービスアカウントでGoogle Driveの指定フォルダにファイルをアップロードする。"""
from __future__ import annotations

import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# drive.file: このアプリ(サービスアカウント)が作成したファイルのみにアクセスする最小権限スコープ
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def upload_file(
    service_account_json_path: str,
    file_path: str,
    folder_id: str,
    mime_type: str = "audio/mp4",
) -> dict:
    creds = service_account.Credentials.from_service_account_file(
        service_account_json_path, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        .execute()
    )
    return uploaded
