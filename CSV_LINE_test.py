import os
import pandas as pd
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- 設定（環境変数から読み込み） ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

# ★ここにあなたのスプレッドシートの共有URLを貼ってください
# 例: "https://docs.google.com/spreadsheets/d/xxx/edit?usp=sharing"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GBpmQGTcJMtwEBGHFgJ-k8kZ1Svj6b6COyKNE-q3H-k/edit?gid=0#gid=0"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    
    if text == "集計":
        try:
            # スプレッドシートを読み込める形式（CSV出力形式）に変換
            # edit?usp=sharing 以降を削って export?format=csv に差し替える
            csv_url = SHEET_URL.split('/edit')[0] + '/export?format=csv'
            
            # スプレッドシートを読み込む
            df = pd.read_csv(csv_url)
            
            # 2列目（金額が入っている列）の合計を計算
            # appendRowで書き込んでいる場合、通常は2列目(インデックス1)に金額が入ります
            actual_payment = df.iloc[:, 1].sum()
            
            budget = 80000  # 予算（必要に応じて変更してください）
            remaining = budget - actual_payment
            
            msg = f"📅 今月の利用状況\n設定予算：{budget:,}円\n現在の合計：{int(actual_payment):,}円\n残り：{int(remaining):,}円"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        except Exception as e:
            # エラーが出た場合、LINEに原因を表示（デバッグ用）
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"エラー: {e}"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
