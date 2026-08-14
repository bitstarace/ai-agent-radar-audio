"""初回セットアップ用: ローカルで一度だけ実行し、Drive用のOAuthリフレッシュトークンを取得する。

事前準備:
1. Google Cloud Consoleで OAuth クライアントID(種類: デスクトップアプリ)を作成
2. ダウンロードしたJSONを、このリポジトリ直下に client_secret.json という名前で保存
   (このファイルはコミットしないこと。.gitignoreに追加済み)
3. OAuth同意画面の「公開ステータス」を「本番環境」にしておく
   (テスト中のままだとリフレッシュトークンが7日で失効し、毎日の自動実行が止まる)

使い方:
    pip install -r requirements.txt
    python scripts/get_refresh_token.py

ブラウザが開くのでGoogleアカウントでログインし、アクセスを許可すると
refresh_token / client_id / client_secret が表示される。
これをGitHub Secretsに登録する。
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n以下をGitHub Secretsに登録してください:\n")
    print(f"GDRIVE_CLIENT_ID={creds.client_id}")
    print(f"GDRIVE_CLIENT_SECRET={creds.client_secret}")
    print(f"GDRIVE_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
