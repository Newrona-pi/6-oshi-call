-- ================================================
-- Supabase テーブル作成SQL
-- ================================================
-- テーブル名: call_reservations
-- 用途: CSV から取り込んだ電話予約データを管理

CREATE TABLE IF NOT EXISTS call_reservations (
    id TEXT PRIMARY KEY,                    -- order_id をそのまま使用
    phone_number TEXT NOT NULL,             -- E.164形式の電話番号 (例: +819012345678)
    oshi_name TEXT NOT NULL,                -- 推しライバーの名前
    preferred_date DATE NOT NULL,           -- 希望日
    time_slot TEXT NOT NULL,                -- 時間帯 ("朝", "昼", "晩")
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- ランダム生成された発信予定時刻
    status TEXT NOT NULL DEFAULT 'waiting', -- ステータス: waiting, called, error
    error_message TEXT,                     -- エラー時のメッセージ
    called_at TIMESTAMP WITH TIME ZONE,     -- 実際に発信した時刻
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成（検索の高速化）
CREATE INDEX IF NOT EXISTS idx_status_scheduled ON call_reservations(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_oshi_name ON call_reservations(oshi_name);

-- 更新時刻の自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_call_reservations_updated_at BEFORE UPDATE
    ON call_reservations FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
