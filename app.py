# -*- coding: utf-8 -*-
"""
Twilio Programmable Voice - シリアルコード認証型音声配信サービス
37cardのような電話音声配信システムのバックエンド実装

必要なライブラリ:
    pip install flask twilio

使い方:
    1. serial_codes.json を編集してシリアルコードと音声URLを設定
    2. python app.py でサーバーを起動
    3. Twilio管理画面で、着信時のWebhook URLを設定
       (例: https://your-domain.com/voice)
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import json
import os

app = Flask(__name__)

from flask import Flask, request, send_from_directory, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)

# =============================================================================
# ★ここを編集してください: データベース設定
# =============================================================================
# Renderなどの環境変数 'DATABASE_URL' があればそれを使い、なければローカルのSQLiteを使う
# ※RenderのPostgreSQL URLは 'postgres://' で始まることがありますが、
#   SQLAlchemyでpg8000を使うため 'postgresql+pg8000://' に置換します。
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local_dev.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+pg8000://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+pg8000://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# モデル定義 (データベースのテーブル構造)
# =============================================================================
class SerialCode(db.Model):
    __tablename__ = 'serial_codes'
    
    code = db.Column(db.String(20), primary_key=True)
    audio_url = db.Column(db.String(500), nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<SerialCode {self.code}>'

# JSONファイル（初期データ/シードデータ用）
DATA_FILE = 'serial_codes.json'

def init_db():
    """データベースの初期化とシードデータの投入"""
    with app.app_context():
        db.create_all()
        
        # データが1件もない場合のみ、JSONからデータをロードする
        if SerialCode.query.count() == 0:
            print("データベースが空です。serial_codes.json から初期データを投入します...")
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for code, info in data.items():
                    # 既に存在しないか念のため確認（create_all直後なら不要だが安全のため）
                    if not SerialCode.query.get(code):
                        new_code = SerialCode(
                            code=code,
                            audio_url=info['audio_url'],
                            used=info['used']
                        )
                        db.session.add(new_code)
                
                db.session.commit()
                print("初期データの投入が完了しました。")
            else:
                print(f"警告: {DATA_FILE} が見つかりません。")

# アプリ起動時にDB初期化を行う（本番ではコマンドで行うのが一般的だが簡易化のため）
init_db()

from flask import Flask, request, send_from_directory, url_for
# ... (imports)

# ... (db setup)

# ... (init_db function)

# ★追加: 音声ファイルを配信するエンドポイント
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """
    音声ファイルを配信するエンドポイント
    例: /audio/hayase.wav にアクセスすると、ローカルの hayase.wav を返す
    """
    return send_from_directory('.', filename)

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    """
    着信時に呼ばれるエンドポイント
    """
    response = VoiceResponse()
    
    # Gather: ユーザーからの入力（DTMFトーン）を受け付ける
    gather = Gather(
        num_digits=4,           # 入力桁数（★必要に応じて変更してください）
        action='/check_code',   # 入力後に呼ばれるエンドポイント
        method='POST',
        timeout=10              # 入力待ち時間（秒）
    )
    
    # 日本語で案内メッセージを読み上げる
    gather.say(
        'こんにちは。シリアルコードを入力してください。',
        language='ja-JP'
    )
    
    response.append(gather)
    
    # 入力がなかった場合のメッセージ
    response.say(
        '入力が確認できませんでした。もう一度おかけ直しください。',
        language='ja-JP'
    )
    
    return str(response)

@app.route('/check_code', methods=['POST'])
def check_code():
    """
    シリアルコード入力後に呼ばれるエンドポイント
    """
    response = VoiceResponse()
    
    # ユーザーが入力した番号を取得
    digits = request.form.get('Digits', '')
    
    print(f"入力されたコード: {digits}")
    
    # データベースから検索
    serial_code = SerialCode.query.get(digits)
    
    # シリアルコードの検証
    if not serial_code:
        # コードが存在しない場合
        response.say(
            '入力されたシリアルコードが見つかりません。もう一度確認してください。',
            language='ja-JP'
        )
        response.hangup()
        
    elif serial_code.used:
        # コードが既に使用済みの場合
        response.say(
            'このシリアルコードは既に使用されています。',
            language='ja-JP'
        )
        response.hangup()
        
    else:
        # コードが正しく、かつ未使用の場合
        response.say(
            '認証に成功しました。音声を再生します。',
            language='ja-JP'
        )
        
        # 音声ファイルのURLを生成
        # http(s)://で始まる場合はそのまま、そうでなければ自分のサーバーのURLとして生成
        audio_target = serial_code.audio_url
        if not audio_target.startswith(('http://', 'https://')):
            # 現在のサーバーのURL + /audio/ + ファイル名
            # _external=True で絶対URL (https://...) を生成する
            audio_url = url_for('serve_audio', filename=audio_target, _external=True)
            # Renderなどプロキシ環境下で http になることがあるためヘッダーを見て https にする補正
            if request.headers.get('X-Forwarded-Proto') == 'https':
                audio_url = audio_url.replace('http://', 'https://', 1)
        else:
            audio_url = audio_target

        print(f"再生URL: {audio_url}")
        response.play(audio_url)
        
        # 終了メッセージ
        response.say(
            'ご利用ありがとうございました。',
            language='ja-JP'
        )
        
        # ★重要: コードを使用済みにする (DB更新)
        serial_code.used = True
        db.session.commit()
        
        print(f"コード {digits} を使用済みにしました (DB更新)")
    
    return str(response)




@app.route('/admin/reset_code/<code>')
def reset_code(code):
    """
    管理者用: 指定したシリアルコードを未使用に戻す
    例: https://your-app.onrender.com/admin/reset_code/1234
    """
    serial_code = SerialCode.query.get(code)
    
    if not serial_code:
        return f'エラー: コード "{code}" は存在しません。', 404
    
    if not serial_code.used:
        return f'コード "{code}" は既に未使用です。'
    
    serial_code.used = False
    db.session.commit()
    
    return f'コード "{code}" を未使用に戻しました。'


@app.route('/admin/reset_all')
def reset_all():
    """
    管理者用: すべてのシリアルコードを未使用に戻す
    例: https://your-app.onrender.com/admin/reset_all
    """
    updated_count = SerialCode.query.filter_by(used=True).update({'used': False})
    db.session.commit()
    
    return f'{updated_count}個のコードを未使用に戻しました。'


@app.route('/')
def index():
    """
    ルートエンドポイント（動作確認用）
    
    ブラウザでアクセスしたときに、サーバーが動いているか確認できます。
    """
    return '''
    <html>
        <head>
            <meta charset="utf-8">
            <title>Twilio Voice Service</title>
        </head>
        <body>
            <h1>Twilio シリアルコード認証型音声配信サービス</h1>
            <p>サーバーは正常に動作しています。</p>
            <p>Twilio管理画面で、着信時のWebhook URLを設定してください。</p>
            <ul>
                <li>Voice URL: <code>/voice</code></li>
            </ul>
        </body>
    </html>
    '''


if __name__ == '__main__':
    # =============================================================================
    # ★ここを編集してください: サーバー設定
    # =============================================================================
    # 本番環境では、debug=False にして、適切なホスト・ポートを設定してください
    # ngrokなどを使用する場合は、このまま localhost:5000 で問題ありません
    app.run(
        host='0.0.0.0',  # 外部からアクセス可能にする場合
        port=5000,       # ポート番号
        debug=True       # 開発時のみTrue、本番では False にしてください
    )
