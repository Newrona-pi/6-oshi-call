# 定期実行の確認手順

## 1. GitHub Actions の実行履歴を確認

1. `https://github.com/Newrona-pi/6-oshi-call/actions` を開く
2. 左側の「Scheduled Call Execution」をクリック
3. 実行履歴を確認
   - 緑色のチェックマーク ✅ = 成功
   - 赤色のバツマーク ❌ = 失敗
   - 黄色の丸 🟡 = 実行中

## 2. 最新のワークフロー実行を確認

- 「All workflows」の一覧で、最新の実行時刻を確認
- スケジュール実行の場合、実行理由に「schedule」と表示される
- 手動実行の場合は「workflow_dispatch」と表示される

## 3. スケジュールが有効か確認

`.github/workflows/schedule.yml` の内容が正しくプッシュされているか確認：

```bash
# GitHubリポジトリで確認
https://github.com/Newrona-pi/6-oshi-call/blob/main/.github/workflows/schedule.yml
```

## トラブルシューティング

### 定期実行が動かない場合

#### A. 間隔を5分に戻す（推奨）

`schedule.yml` の cron を以下に変更：

```yaml
- cron: '*/5 * * * *'  # 5分ごと
```

1分間隔は負荷が高いため、GitHub側で制限される可能性があります。

#### B. ワークフローを再有効化

1. リポジトリの Actions タブを開く
2. 左側の「Scheduled Call Execution」をクリック
3. 右上に「This workflow has been disabled」と表示されている場合
   - 「Enable workflow」ボタンをクリック

#### C. ダミーコミットで活性化

```bash
# 空コミットを作成してプッシュ
git commit --allow-empty -m "Trigger workflow"
git push
```

これでリポジトリが「アクティブ」と認識され、スケジュール実行が開始されることがあります。

## 確実に動作確認する方法

### 手動実行で即座にテスト

1. Actions タブ → Scheduled Call Execution
2. 「Run workflow」をクリック
3. ログを確認して、正しく動作しているか確認

### ログの見方

実行ログで以下を確認：
- ✅ `発信対象をチェックしています...`
- ✅ `📞 X件の発信対象が見つかりました`
- ✅ `発信成功: Call SID=...`

または

- `📭 発信対象のデータはありません`（正常、発信すべきデータがない状態）

## 現在の設定の問題点

`*/1 * * * *`（1分ごと）は：
- GitHub Actions の無料枠を早く消費する
- 制限される可能性がある
- 電話発信のユースケースには過剰

**推奨: `*/5 * * * *`（5分ごと）に戻す**

## 次のアクション

1. cronを5分間隔に戻す
2. 変更をプッシュ
3. 10〜15分待つ
4. Actions タブで自動実行されているか確認
