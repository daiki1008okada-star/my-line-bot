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
            # スプレッドシートをCSV形式で取得
            csv_url = SHEET_URL.split('/edit')[0] + '/export?format=csv'
            
            # 見出しがない場合を考慮して、header=Noneで読み込む
            df = pd.read_csv(csv_url, header=None)
            
            # 1列目(index 0)を日付として解釈
            df[0] = pd.to_datetime(df[0], errors='coerce')
            
            # 2列目(index 1)を数値として解釈（B列）
            df[1] = pd.to_numeric(df[1], errors='coerce')

            # --- ここで「今月」の判定を柔軟にします ---
            # 本日が1月31日の場合でも、シートの2月のデータを見たい場合は
            # 下記のnowを「2月」として扱うか、一旦「全データ合計」でテストします
            
            # 【テスト用】一旦、日付を無視して「B列にある数字を全部足す」設定にします
            total_spent = df[1].sum()
            
            # 【本番用（月別にする場合）】
            # now = pd.Timestamp.now(tz='Asia/Tokyo')
            # total_spent = df[(df[0].dt.month == now.month)][1].sum()

            budget = 80000
            remaining = budget - total_spent
            
            msg = f"📊 利用状況確認\n──────────────\n設定予算：{budget:,}円\n現在の合計：{int(total_spent):,}円\n残り予算：{int(remaining):,}円"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"エラーが発生しました: {e}"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

