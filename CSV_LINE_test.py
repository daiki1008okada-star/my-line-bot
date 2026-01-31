import os
import pandas as pd
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- LINE設定（環境変数から読み込むのがサーバーの鉄則です） ---
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

BUDGET_FILE = "budget_config.txt"
CSV_FILE = "enavi202602(3688).csv"

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

    # 1. 予算設定の処理
    if "予算" in text:
        try:
            # 「予算 80000」から数字だけ抜く
            amount = re.sub(r'\D', '', text)
            with open(BUDGET_FILE, "w") as f:
                f.write(amount)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"予算を{amount}円に設定しました！"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="予算設定に失敗しました。"))

    # 2. 集計の処理
    elif text == "集計":
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE, encoding='utf-8')
            actual_payment = df['2月支払金額'].dropna().sum()
            
            budget = 50000
            if os.path.exists(BUDGET_FILE):
                with open(BUDGET_FILE, "r") as f: budget = int(f.read().strip())
            
            remaining = budget - actual_payment
            msg = f"📅 2月度集計\n設定予算：{budget:,}円\n引落予定：{int(actual_payment):,}円\n残り：{int(remaining):,}円"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="CSVファイルがまだサーバーにありません。"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))