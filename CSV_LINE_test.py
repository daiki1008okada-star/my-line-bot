import os
import pandas as pd
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINEの設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

# ★ここにコピーしたスプレッドシートのURLを貼ってください！
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
            # スプレッドシートをCSV形式で読み込む魔法のURL変換
            csv_url = SHEET_URL.split('/edit')[0] + '/export?format=csv'
            
            # データを読み込む
            df = pd.read_csv(csv_url)
            
            # 金額が入っている列（通常は2列目＝index 1）の合計を計算
            # 数値以外のゴミが混じっても大丈夫なように数値化
            total_spent = pd.to_numeric(df.iloc[:, 1], errors='coerce').sum()
            
            budget = 80000  # あなたの月間予算
            remaining = budget - total_spent
            
            msg = f"💳 最新の利用状況\n──────────────\n設定予算：{budget:,}円\n現在の合計：{int(total_spent):,}円\n残り予算：{int(remaining):,}円"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"データ取得エラー: {e}"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
