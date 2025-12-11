# GitHub Actions セットアップガイド

## 概要
GitHub Actionsを使って、10分ごとに自動的に発信処理（`python main.py execute`）を実行します。

## セットアップ手順

### 1. GitHubリポジトリにプッシュ

まず、このプロジェクトをGitHubにプッシュしてください。

```bash
git add .
git commit -m "Add GitHub Actions workflow for scheduled execution"
git push origin main
```

### 2. GitHub Secrets の設定

GitHubリポジトリの設定画面で、環境変数（Secrets）を登録します。

1. GitHubのリポジトリページを開く
2. **Settings** タブをクリック
3. 左メニューから **Secrets and variables** > **Actions** を選択
4. **New repository secret** をクリック
5. 以下の環境変数を1つずつ追加:

| Name | Value |
|------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5c...` |
| `TWILIO_ACCOUNT_SID` | `ACxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | `your-auth-token` |
| `TWILIO_PHONE_NUMBER` | `+81xxxxxxxxxx` |
| `TWILIO_TWIML_BIN_URL` | `https://handler.twilio.com/twiml/EHxxxx...` |
| `DRY_RUN` | `False` （本番運用時）または `True` （テスト時） |

### 3. ワークフローの有効化

GitHub Actionsは自動的に有効になります。
リポジトリの **Actions** タブで実行状況を確認できます。

### 4. 動作確認

#### 手動実行でテスト

1. リポジトリの **Actions** タブを開く
2. 左側から **Scheduled Call Execution** を選択
3. 右上の **Run workflow** ボタンをクリック
4. **Run workflow** を再度クリック

これで即座に実行され、ログを確認できます。

#### 自動実行の確認

- 10分ごとに自動実行されます
- **Actions** タブで実行履歴とログを確認できます

## スケジュール設定のカスタマイズ

`.github/workflows/schedule.yml` の `cron` 設定を変更することで、実行頻度を調整できます。

```yaml
schedule:
  - cron: '*/10 * * * *'  # 10分ごと
  # - cron: '*/5 * * * *'   # 5分ごと
  # - cron: '0 * * * *'     # 1時間ごと（毎時0分）
  # - cron: '0 9 * * *'     # 毎日9:00 UTC（日本時間18:00）
```

**注意**: cronはUTC（協定世界時）で指定されます。日本時間（JST）から9時間引いた時刻を指定してください。

## トラブルシューティング

### ワークフローが実行されない

- リポジトリが **Public** であることを確認（Privateの場合は無料枠に制限あり）
- **Actions** タブでワークフローが有効になっているか確認
- Secretsが正しく設定されているか確認

### 実行はされるがエラーになる

- **Actions** タブのログを確認
- Secretsの値が正しいか再確認
- `DRY_RUN` を `True` にしてテスト実行してみる

### 発信されない

- Supabaseのデータベースに発信対象のデータがあるか確認
- `scheduled_at` が現在時刻より過去になっているか確認
- `status` が `waiting` になっているか確認

## コスト

GitHub Actionsの無料枠:
- Public リポジトリ: **完全無料・無制限**
- Private リポジトリ: **月2,000分まで無料**

10分ごとの実行（1回あたり約10秒）の場合:
- 1日: 144回 × 10秒 = 24分
- 1ヶ月: 約720分

→ Private リポジトリでも無料枠内で十分運用可能です。

## 将来的なRender移行について

Renderに移行する際は:
1. Render Cron Jobsを作成
2. GitHub Actionsのワークフローを無効化（`.github/workflows/schedule.yml` を削除またはコメントアウト）

データベース（Supabase）はそのまま使えるので、移行は簡単です。
