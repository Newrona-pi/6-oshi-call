# -*- coding: utf-8 -*-
"""
推しライバー自動電話システム
CSVからデータを取り込み、指定時刻にランダムでTwilioを用いて自動発信を行う

使い方:
    # CSVインポート
    python main.py import sample.csv
    
    # 発信実行
    python main.py execute
"""

import os
import sys
import csv
import random
from datetime import datetime, time, timedelta
from dateutil import parser, tz
import pandas as pd
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ================================================
# 設定値（ここを編集してください）
# ================================================

# Supabase設定
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Twilio設定
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")  # 発信元番号

# DRY_RUN: True の場合、実際には電話をかけずにログ出力のみ
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

# 時間帯の定義（開始時刻と終了時刻）
TIME_SLOTS = {
    "朝": (time(9, 0), time(11, 59)),    # 09:00 - 11:59
    "昼": (time(12, 0), time(17, 59)),   # 12:00 - 17:59
    "晩": (time(18, 0), time(20, 59)),   # 18:00 - 20:59
}

# 推しライバーごとの音声URL（★ここに音声ファイルのURLを設定してください）
OSHI_AUDIO_MAPPING = {
    "Aちゃん": "https://example.com/audio/a-chan.mp3",
    "Bくん": "https://example.com/audio/b-kun.mp3",
    # 必要に応じてここに追加
}

# タイムゾーン設定
JST = tz.gettz("Asia/Tokyo")

# ================================================
# クライアント初期化
# ================================================

def init_supabase() -> Client:
    """Supabaseクライアントを初期化"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URLとSUPABASE_KEYを環境変数に設定してください")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_twilio() -> TwilioClient:
    """Twilioクライアントを初期化"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError("TWILIO_ACCOUNT_SIDとTWILIO_AUTH_TOKENを環境変数に設定してください")
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ================================================
# ユーティリティ関数
# ================================================

def normalize_phone_number(phone: str) -> str:
    """
    電話番号を E.164 形式に変換
    例: 090-1234-5678 -> +819012345678
    """
    # ハイフンやスペースを削除
    phone = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    
    # 先頭が0の場合、+81に変換
    if phone.startswith("0"):
        phone = "+81" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+81" + phone
    
    return phone

def generate_random_datetime(preferred_date: str, time_slot: str) -> datetime:
    """
    希望日と時間帯からランダムな発信予定時刻を生成
    
    Args:
        preferred_date: 希望日 (例: "2025-12-25")
        time_slot: 時間帯 ("朝", "昼", "晩")
    
    Returns:
        ランダムな datetime オブジェクト（JST）
    """
    # 希望日をdatetimeに変換
    date_obj = parser.parse(preferred_date).date()
    
    # 時間帯の範囲を取得
    if time_slot not in TIME_SLOTS:
        raise ValueError(f"不正な時間帯: {time_slot}。'朝', '昼', '晩' のいずれかを指定してください。")
    
    start_time, end_time = TIME_SLOTS[time_slot]
    
    # 秒単位でランダムな時刻を生成
    start_seconds = start_time.hour * 3600 + start_time.minute * 60
    end_seconds = end_time.hour * 3600 + end_time.minute * 60
    
    random_seconds = random.randint(start_seconds, end_seconds)
    random_hour = random_seconds // 3600
    random_minute = (random_seconds % 3600) // 60
    random_second = random_seconds % 60
    
    # datetimeを作成
    scheduled_dt = datetime.combine(
        date_obj,
        time(random_hour, random_minute, random_second),
        tzinfo=JST
    )
    
    return scheduled_dt

# ================================================
# CSVインポート機能
# ================================================

def import_csv(csv_path: str):
    """
    CSVファイルを読み込み、Supabaseにインポート
    
    Args:
        csv_path: CSVファイルのパス
    """
    print(f"CSVファイルを読み込んでいます: {csv_path}")
    
    # CSVを読み込み
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ CSVの読み込みに失敗しました: {e}")
        return
    
    # 必要なカラムの確認
    required_columns = ["order_id", "phone_number", "oshi_name", "preferred_date", "time_slot"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ CSVに必要なカラムがありません: {missing_columns}")
        return
    
    # Supabaseクライアント初期化
    supabase = init_supabase()
    
    # 既存データの取得（冪等性のため）
    existing_data = supabase.table("call_reservations").select("id, status").execute()
    existing_ids = {item["id"]: item["status"] for item in existing_data.data}
    
    # データを1件ずつ処理
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        order_id = str(row["order_id"])
        
        # 既に完了しているデータはスキップ
        if order_id in existing_ids and existing_ids[order_id] == "called":
            print(f"⏭️  [{index + 1}] order_id={order_id} は既に発信済みのためスキップ")
            skip_count += 1
            continue
        
        try:
            # 電話番号の正規化
            phone_number = normalize_phone_number(str(row["phone_number"]))
            
            # ランダムな発信時刻の生成
            scheduled_at = generate_random_datetime(
                str(row["preferred_date"]),
                str(row["time_slot"])
            )
            
            # データベースに保存
            data = {
                "id": order_id,
                "phone_number": phone_number,
                "oshi_name": str(row["oshi_name"]),
                "preferred_date": str(row["preferred_date"]),
                "time_slot": str(row["time_slot"]),
                "scheduled_at": scheduled_at.isoformat(),
                "status": "waiting"
            }
            
            # Upsert（既存データがあれば更新、なければ挿入）
            supabase.table("call_reservations").upsert(data).execute()
            
            print(f"✅ [{index + 1}] order_id={order_id} を登録しました（発信予定: {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}）")
            success_count += 1
            
        except Exception as e:
            print(f"❌ [{index + 1}] order_id={order_id} の処理に失敗しました: {e}")
            error_count += 1
    
    print("\n" + "=" * 50)
    print(f"インポート完了: 成功={success_count}, スキップ={skip_count}, エラー={error_count}")
    print("=" * 50)

# ================================================
# 発信実行機能
# ================================================

def execute_calls():
    """
    データベースをチェックし、発信時刻が来ているデータに電話をかける
    """
    print("発信対象をチェックしています...")
    
    # Supabaseクライアント初期化
    supabase = init_supabase()
    
    # Twilioクライアント初期化
    twilio_client = init_twilio() if not DRY_RUN else None
    
    # 現在時刻（JST）
    now = datetime.now(JST)
    
    # 発信対象の抽出: status='waiting' かつ scheduled_at <= 現在時刻
    result = supabase.table("call_reservations")\
        .select("*")\
        .eq("status", "waiting")\
        .lte("scheduled_at", now.isoformat())\
        .execute()
    
    targets = result.data
    
    if not targets:
        print("📭 発信対象のデータはありません。")
        return
    
    print(f"📞 {len(targets)}件の発信対象が見つかりました。")
    
    # 1件ずつ発信
    for target in targets:
        order_id = target["id"]
        phone_number = target["phone_number"]
        oshi_name = target["oshi_name"]
        
        print(f"\n--- 発信処理開始: order_id={order_id} ---")
        print(f"  電話番号: {phone_number}")
        print(f"  推しライバー: {oshi_name}")
        
        try:
            # 音声URLを取得
            audio_url = OSHI_AUDIO_MAPPING.get(oshi_name)
            if not audio_url:
                raise ValueError(f"推しライバー '{oshi_name}' の音声URLが設定されていません")
            
            if DRY_RUN:
                print(f"  🧪 [DRY RUN] 電話をかける処理をスキップしました")
                print(f"  音声URL: {audio_url}")
            else:
                # TwiMLを生成
                twiml_url = f"{SUPABASE_URL}/functions/v1/twiml?audio_url={audio_url}"
                
                # Twilioで発信
                call = twilio_client.calls.create(
                    to=phone_number,
                    from_=TWILIO_PHONE_NUMBER,
                    url=twiml_url
                )
                
                print(f"  ✅ 発信成功: Call SID={call.sid}")
            
            # ステータスを更新
            supabase.table("call_reservations").update({
                "status": "called",
                "called_at": now.isoformat()
            }).eq("id", order_id).execute()
            
        except Exception as e:
            print(f"  ❌ 発信失敗: {e}")
            
            # エラー情報を記録
            supabase.table("call_reservations").update({
                "status": "error",
                "error_message": str(e)
            }).eq("id", order_id).execute()
    
    print("\n" + "=" * 50)
    print("発信処理完了")
    print("=" * 50)

# ================================================
# メイン処理
# ================================================

def main():
    """メイン処理"""
    # 引数チェック
    if len(sys.argv) < 2:
        print("使い方:")
        print("  CSVインポート: python main.py import <csv_path>")
        print("  発信実行: python main.py execute")
        return
    
    command = sys.argv[1]
    
    if command == "import":
        if len(sys.argv) < 3:
            print("❌ CSVファイルのパスを指定してください")
            return
        csv_path = sys.argv[2]
        import_csv(csv_path)
    
    elif command == "execute":
        if DRY_RUN:
            print("🧪 DRY RUNモードで実行します（実際には電話をかけません）")
        execute_calls()
    
    else:
        print(f"❌ 不明なコマンド: {command}")
        print("使用可能なコマンド: import, execute")

if __name__ == "__main__":
    main()
