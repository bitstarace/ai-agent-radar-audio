# ai-agent-radar-audio

[takeday/ai-agent-radar](https://github.com/takeday/ai-agent-radar) の日次レポート(`reports/YYYYMMDD.md`)を、
Gemini APIでポッドキャスト風の対話台本に変換し、Gemini TTSで音声化してGoogle Driveに保存する。
毎日08:15 JSTにGitHub Actionsで自動実行される(元レポートは07:30 JST生成)。

## 事前準備(初回のみ、手動)

以下はGoogle/GCPアカウントの操作を伴うため、ご自身で行ってください。

### 1. Gemini APIキーの取得

1. https://aistudio.google.com/apikey を開く
2. 「Create API key」で新規キーを発行
3. 発行されたキーをメモしておく(あとで `GEMINI_API_KEY` として登録)

### 2. Google Driveアップロード用サービスアカウントの作成

1. https://console.cloud.google.com/ でプロジェクトを新規作成(または既存プロジェクトを選択)
2. 「APIとサービス」→「ライブラリ」で **Google Drive API** を有効化
3. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」で新規作成
   (名前は任意、例: `ai-agent-radar-audio-uploader`)
4. 作成したサービスアカウントの詳細画面 →「鍵」タブ →「鍵を追加」→「新しい鍵を作成」→ JSON形式でダウンロード
5. ダウンロードしたJSONファイルの中の `client_email` の値(例: `xxx@yyy.iam.gserviceaccount.com`)を控える

### 3. 保存先Google Driveフォルダをサービスアカウントに共有

1. Google Driveで音声ファイルを保存したいフォルダを作成(または既存フォルダを使用)
2. そのフォルダを右クリック →「共有」→ 上記の `client_email` を **編集者** として追加
3. フォルダのURL末尾のID(`https://drive.google.com/drive/folders/【この部分】`)を控える

### 4. GitHub Secretsへの登録

このリポジトリの Settings → Secrets and variables → Actions で以下を登録:

| Secret名 | 値 |
|---|---|
| `GEMINI_API_KEY` | 手順1で取得したAPIキー |
| `GDRIVE_SERVICE_ACCOUNT_JSON` | 手順2でダウンロードしたJSONファイルの中身をそのまま貼り付け |
| `GDRIVE_FOLDER_ID` | 手順3で控えたフォルダID |

CLIで登録する場合:

```bash
gh secret set GEMINI_API_KEY --body "取得したAPIキー"
gh secret set GDRIVE_SERVICE_ACCOUNT_JSON < /path/to/service-account.json
gh secret set GDRIVE_FOLDER_ID --body "フォルダID"
```

### 5. 動作確認

Secrets登録後、Actionsタブ →「Daily report audio to Drive」→「Run workflow」で手動実行し、
Google Driveに `YYYYMMDD.m4a` が保存されることを確認する。

## 仕組み

1. `scripts/fetch_report.py` — `takeday/ai-agent-radar` の `reports/` から最新の `.md` を取得
2. `scripts/gemini_audio.py` — Geminiでレポートを2人ホストの対話台本に変換し、Gemini TTS(マルチスピーカー)で読み上げ音声(PCM)を生成
3. `scripts/main.py` — PCM→WAV→(ffmpeg)→m4aに変換し、`scripts/drive_upload.py` でGoogle Driveへアップロード

## 注意事項

- NotebookLM本体は使用していません(個人向けには公開APIがないため)。Gemini APIによる代替の音声解説です。
- レポート内容はAI要約のため、誤りを含む可能性があります(元リポジトリの注意書きに準拠)。
