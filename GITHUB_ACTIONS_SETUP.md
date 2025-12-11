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

### 2. GitHub Secrets の設定（詳細手順）

GitHubリポジトリの設定画面で、環境変数（Secrets）を登録します。
**これらの値は暗号化されて保存され、ログにも表示されないため安全です。**

#### 手順

1. **GitHubのリポジトリページを開く**
   - ブラウザで `https://github.com/Newrona-pi/6-oshi-call` を開きます

2. **Settings タブをクリック**
   - ページ上部のタブメニューから **Settings** をクリック
   - （※ Settingsが表示されない場合は、リポジトリの管理者権限がない可能性があります）

3. **Secrets and variables を開く**
   - 左側のサイドバーを下にスクロール
   - **Security** セクションの中にある **Secrets and variables** をクリック
   - さらに **Actions** をクリック

4. **New repository secret をクリック**
   - 右上にある緑色の **New repository secret** ボタンをクリック

5. **1つ目のSecretを追加: SUPABASE_URL**
   - **Name** 欄に: `SUPABASE_URL` と入力（大文字小文字を正確に）
   - **Secret** 欄に: Supabaseのプロジェクト URL を貼り付け
     - 例: `https://dluoikwksuixzavqltar.supabase.co`
     - （Supabase管理画面の Settings → API → Project URL からコピー）
   - **Add secret** ボタンをクリック

6. **2つ目のSecretを追加: SUPABASE_KEY**
   - 再度 **New repository secret** をクリック
   - **Name**: `SUPABASE_KEY`
   - **Secret**: Supabaseの anon/public key を貼り付け
     - 例: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`（とても長い文字列）
     - （Supabase管理画面の Settings → API → Project API keys → anon public からコピー）
   - **Add secret** をクリック

7. **3つ目のSecretを追加: TWILIO_ACCOUNT_SID**
   - **Name**: `TWILIO_ACCOUNT_SID`
   - **Secret**: Twilioの Account SID を貼り付け
     - 例: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
     - （Twilio Console のダッシュボード右上に表示されています）
   - **Add secret** をクリック

8. **4つ目のSecretを追加: TWILIO_AUTH_TOKEN**
   - **Name**: `TWILIO_AUTH_TOKEN`
   - **Secret**: Twilioの Auth Token を貼り付け
     - （Twilio Console のダッシュボードで「Show」をクリックして表示）
   - **Add secret** をクリック

9. **5つ目のSecretを追加: TWILIO_PHONE_NUMBER**
   - **Name**: `TWILIO_PHONE_NUMBER`
   - **Secret**: Twilioで購入した電話番号（発信元番号）
     - 例: `+81xxxxxxxxxx`
     - （必ず `+81` から始まるE.164形式で入力）
   - **Add secret** をクリック

10. **6つ目のSecretを追加: TWILIO_TWIML_BIN_URL**
    - **Name**: `TWILIO_TWIML_BIN_URL`
    - **Secret**: TwiML BinのURL
      - 例: `https://handler.twilio.com/twiml/EHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
      - （Twilio Console → TwiML Bins で作成したURLをコピー）
    - **Add secret** をクリック

11. **7つ目のSecretを追加: DRY_RUN**
    - **Name**: `DRY_RUN`
    - **Secret**: `False` （本番運用時）または `True` （テスト時）
      - **重要**: 最初は `True` にしてテストすることを推奨
    - **Add secret** をクリック

#### 確認

すべて追加すると、以下の7つのSecretsが表示されているはずです：

- ✅ SUPABASE_URL
- ✅ SUPABASE_KEY
- ✅ TWILIO_ACCOUNT_SID
- ✅ TWILIO_AUTH_TOKEN
- ✅ TWILIO_PHONE_NUMBER
- ✅ TWILIO_TWIML_BIN_URL
- ✅ DRY_RUN

**注意**: 一度登録したSecretの値は、セキュリティ上の理由で再表示できません。
間違えた場合は、同じ名前で再度登録すれば上書きされます。

#### 各値の取得場所まとめ

| Secret名 | 取得場所 |
|---------|---------|
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase → Settings → API → Project API keys → anon public |
| `TWILIO_ACCOUNT_SID` | Twilio Console → ダッシュボード右上 |
| `TWILIO_AUTH_TOKEN` | Twilio Console → ダッシュボード右上（Showをクリック） |
| `TWILIO_PHONE_NUMBER` | Twilio Console → Phone Numbers → Active numbers |
| `TWILIO_TWIML_BIN_URL` | Twilio Console → TwiML Bins → 作成したBinのURL |
| `DRY_RUN` | 手動で設定（`True` または `False`） |

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
