"""OAuthリフレッシュトークン(ユーザー自身のGoogleアカウント権限)でGoogle Driveにアップロードする。"""
from __future__ import annotations

import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# drive.file: このアプリが作成したファイルのみにアクセスする最小権限スコープ
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _build_credentials() -> Credentials:
    return Credentials(
        token=None,
        refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
        client_id=os.environ["GDRIVE_CLIENT_ID"],
        client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def upload_file(file_path: str, folder_id: str, mime_type: str = "audio/mp4") -> dict:
    creds = _build_credentials()
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        .execute()
    )
    return uploaded
