# ai-agent-radar-audio

[takeday/ai-agent-radar](https://github.com/takeday/ai-agent-radar) の日次レポート(`reports/YYYYMMDD.md`)を、
Gemini APIでポッドキャスト風の対話台本に変換し、Gemini TTSで音声化してGoogle Driveに保存する。
毎日08:15 JSTにGitHub Actionsで自動実行される(元レポートは07:30 JST生成)。

Google Driveへの保存は、サービスアカウントの鍵ではなく **OAuthリフレッシュトークン(あなた自身のGoogle
アカウント権限)** で行う。組織ポリシーでサービスアカウントのJSON鍵作成がブロックされている環境でも動く。

## 事前準備(初回のみ、手動)

### 1. Gemini APIキーの取得

1. https://aistudio.google.com/apikey を開く
2. 「Create API key」で新規キーを発行
3. 発行されたキーをメモしておく(あとで `GEMINI_API_KEY` として登録)

### 2. Google Cloud側の準備

1. https://console.cloud.google.com/ でプロジェクトを新規作成(または既存プロジェクトを選択)
2. 「APIとサービス」→「ライブラリ」で **Google Drive API** を有効化
3. 「APIとサービス」→「OAuth同意画面」を設定
   - User Type: External(個人アカウントの場合)
   - スコープ追加は不要(アプリ側で `drive.file` を要求する)
   - テストユーザーに自分のGoogleアカウントを追加
   - **設定後、「アプリを公開」して公開ステータスを「本番環境」にする**
     (「テスト中」のままだとリフレッシュトークンが7日で失効し、毎日の自動実行が止まるため)
     公開しても審査(verification)は必須ではない。未検証アプリの警告が一度出るが、
     自分のアプリなのでそのまま続行してよい。
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
   - アプリケーションの種類: **デスクトップアプリ**
   - 作成後、JSONをダウンロード

### 3. リフレッシュトークンの取得(ローカルで一度だけ)

1. ダウンロードしたJSONを、このリポジトリ直下に `client_secret.json` という名前で保存
   (`.gitignore` 済みなのでコミットされない)
2. 以下を実行:

```bash
pip install -r requirements.txt
python scripts/get_refresh_token.py
```

3. ブラウザが開くのでGoogleアカウントでログインし、アクセスを許可する
4. ターミナルに表示される `GDRIVE_CLIENT_ID` / `GDRIVE_CLIENT_SECRET` / `GDRIVE_REFRESH_TOKEN` を控える

### 4. 保存先Google DriveフォルダIDの確認

1. Google Driveで音声ファイルを保存したいフォルダを作成(または既存フォルダを使用)
   (自分のアカウント権限でアップロードするので、共有設定は不要)
2. フォルダのURL末尾のID(`https://drive.google.com/drive/folders/【この部分】`)を控える

### 5. GitHub Secretsへの登録

このリポジトリの Settings → Secrets and variables → Actions で以下を登録:

| Secret名 | 値 |
|---|---|
| `GEMINI_API_KEY` | 手順1で取得したAPIキー |
| `GDRIVE_CLIENT_ID` | 手順3で控えたクライアントID |
| `GDRIVE_CLIENT_SECRET` | 手順3で控えたクライアントシークレット |
| `GDRIVE_REFRESH_TOKEN` | 手順3で控えたリフレッシュトークン |
| `GDRIVE_FOLDER_ID` | 手順4で控えたフォルダID |

CLIで登録する場合:

```bash
gh secret set GEMINI_API_KEY --body "取得したAPIキー"
gh secret set GDRIVE_CLIENT_ID --body "クライアントID"
gh secret set GDRIVE_CLIENT_SECRET --body "クライアントシークレット"
gh secret set GDRIVE_REFRESH_TOKEN --body "リフレッシュトークン"
gh secret set GDRIVE_FOLDER_ID --body "フォルダID"
```

### 6. 動作確認

Secrets登録後、Actionsタブ →「Daily report audio to Drive」→「Run workflow」で手動実行し、
Google Driveに `YYYYMMDD.m4a` が保存されることを確認する。

## 仕組み

1. `scripts/fetch_report.py` — `takeday/ai-agent-radar` の `reports/` から最新の `.md` を取得
2. `scripts/gemini_audio.py` — Geminiでレポートを2人ホストの対話台本に変換し、Gemini TTS(マルチスピーカー)で読み上げ音声(PCM)を生成
3. `scripts/main.py` — PCM→WAV→(ffmpeg)→m4aに変換し、`scripts/drive_upload.py` でGoogle Driveへアップロード
4. `scripts/get_refresh_token.py` — 初回セットアップ時にローカルで一度だけ実行するOAuth認可スクリプト

## 注意事項

- NotebookLM本体は使用していません(個人向けには公開APIがないため)。Gemini APIによる代替の音声解説です。
- レポート内容はAI要約のため、誤りを含む可能性があります(元リポジトリの注意書きに準拠)。
- リフレッシュトークンは強力な認証情報です。GitHub Secrets以外の場所に保存・共有しないこと。
