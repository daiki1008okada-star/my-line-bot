import os
import pandas as pd
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- 設定（ここを書き換えてください） ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GBpmQGTcJMtwEBGHFgJ-k8kZ1Svj6b6COyKNE-q3H-k/edit?gid=0#gid=0"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 予算の初期値（再起動でこの数値に戻ります）
current_budget = 80000

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
    global current_budget
    text = event.message.text
    
    # --- 1. 予算設定の処理 ("予算 100000" など) ---
    if text.startswith("予算"):
        try:
            nums = re.sub(r'\D', '', text)
            if nums:
                current_budget = int(nums)
                msg = f"✅ 予算を {current_budget:,}円 に変更しました。\n(※再起動すると8万円に戻ります)"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                return
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"予算変更エラー: {e}"))
            return

    # --- 2. 集計の処理 ---
    if text == "集計":
        try:
            # スプレッドシートをCSV形式で読み込む
            csv_url = SHEET_URL.split('/edit')[0] + '/export?format=csv'
            df = pd.read_csv(csv_url, header=None)
            
            # A列(0)を日付、B列(1)を金額として変換
            df[0] = pd.to_datetime(df[0], errors='coerce')
            df[1] = pd.to_numeric(df[1], errors='coerce')

            # 今日の「年」と「月」を取得
            now = pd.Timestamp.now(tz='Asia/Tokyo')
            
            # スプレッドシートの中から、今月（1日〜末日）の行だけを抽出
            this_month_df = df[
                (df[0].dt.year == now.year) & 
                (df[0].dt.month == now.month)
            ]
            
            total_spent = this_month_df[1].sum()
            remaining = current_budget - total_spent
            
            msg = f"📅 {now.month}月の利用状況\n──────────────\n設定予算：{current_budget:,}円\n今月の合計：{int(total_spent):,}円\n残り予算：{int(remaining):,}円\n\n※確定メールを元に集計中"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"集計エラー: {e}\n※シートが空か、形式が違う可能性があります"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
