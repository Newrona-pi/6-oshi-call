# 推しライバー自動電話システム (6-oshi-call)

ECサイトから出力されたCSVデータを元に、指定された日時にランダムな時刻で自動音声電話をかけるシステムです。

## システム概要

1. **CSVインポート**: 注文データ（電話番号、推しライバー、希望日、時間帯）を取り込み
2. **ランダム時刻生成**: 指定された時間帯（朝・昼・晩）内でランダムな発信時刻を計算
3. **Supabaseに保存**: 予約データをデータベースに保存
4. **自動発信**: 定期実行により、予定時刻が来たらTwilioで自動発信

## 技術スタック

- **言語**: Python 3.x
- **データベース**: Supabase (PostgreSQL)
- **音声通話**: Twilio
- **ライブラリ**: pandas, supabase-py, twilio, python-dotenv

## セットアップ手順

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Supabaseのセットアップ

1. [Supabase](https://supabase.com/) でプロジェクトを作成
2. SQL Editorで `schema.sql` を実行してテーブルを作成

```sql
-- schema.sql の内容をコピー&ペーストして実行
```

3. Project Settings から以下を取得:
   - Project URL (`SUPABASE_URL`)
   - API Keys の anon/public key (`SUPABASE_KEY`)

### 3. Twilioのセットアップ

1. [Twilio Console](https://console.twilio.com/) にログイン
2. Account SID と Auth Token を取得
3. 電話番号を購入（発信元番号として使用）

### 4. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、実際の値を設定:

```bash
cp .env.example .env
```

```.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+81xxxxxxxxxx

DRY_RUN=True  # 本番運用時は False に変更
```

### 5. 音声URLの設定

`main.py` の `OSHI_AUDIO_MAPPING` に音声ファイルのURLを設定:

```python
OSHI_AUDIO_MAPPING = {
    "Aちゃん": "https://your-domain.com/audio/a-chan.mp3",
    "Bくん": "https://your-domain.com/audio/b-kun.mp3",
}
```

## 使い方

### CSVのフォーマット

以下のカラムを持つCSVファイルを用意してください:

| カラム名 | 説明 | 例 |
|---------|------|-----|
| order_id | 注文ID（ユニーク） | ORD001 |
| phone_number | 電話番号 | 090-1234-5678 |
| oshi_name | 推しライバー名 | Aちゃん |
| preferred_date | 希望日 | 2025-12-25 |
| time_slot | 時間帯 | 朝 |

**時間帯の定義:**
- `朝`: 09:00 - 11:59
- `昼`: 12:00 - 17:59
- `晩`: 18:00 - 20:59

### コマンド

#### CSVをインポート

```bash
python main.py import sample.csv
```

実行すると:
- CSVデータを読み込み
- 各行に対してランダムな発信時刻を生成
- Supabaseに保存（既存データは上書きしない冪等処理）

#### 発信を実行

```bash
python main.py execute
```

実行すると:
- データベースから発信対象（status='waiting' かつ scheduled_at が過去）を取得
- Twilioで自動発信
- ステータスを `called` に更新

**定期実行の推奨:**
cron や Render の Cron Jobs を使用して、5分〜15分間隔で自動実行することを推奨します。

```cron
*/10 * * * * cd /path/to/project && python main.py execute
```

## DRY RUNモード

初回テスト時は `DRY_RUN=True` に設定することで、実際には電話をかけずにログだけを確認できます。

```bash
# .env で設定
DRY_RUN=True

# 実行
python main.py execute
```

ログに `[DRY RUN]` と表示され、Twilioへの発信は行われません。

## データベース管理

### Supabaseダッシュボードで確認

Table Editor から `call_reservations` テーブルを開くと、以下の情報が確認できます:

- 予約一覧
- 各予約のステータス（waiting, called, error）
- 発信予定時刻と実際の発信時刻

### ステータスの意味

- `waiting`: 発信待ち
- `called`: 発信完了
- `error`: 発信エラー（error_message にエラー内容が記録されます）

## トラブルシューティング

### Q: CSVインポート時に「既に発信済みのためスキップ」と表示される

A: 既に `called` ステータスのデータは、再インポートしても上書きされません（冪等性）。強制的に再発信したい場合は、Supabaseで該当レコードの `status` を `waiting` に手動で変更してください。

### Q: 発信がエラーになる

A: 以下を確認してください:
- Twilio の Account SID / Auth Token が正しいか
- 発信元電話番号が正しいか
- 相手の電話番号がE.164形式（+81...）に正規化されているか
- 音声URLにアクセスできるか

### Q: 音声が再生されない

A: `OSHI_AUDIO_MAPPING` に設定したURLが正しいか、外部からアクセス可能かを確認してください。

## ライセンス

MIT License

## サポート

問題が発生した場合は、Issueを作成してください。
