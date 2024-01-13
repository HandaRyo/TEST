#python -m venv line
#
#
#
#LINE仮想環境
# .\line\Scripts\activate 
#c:/Users/HaNdARyo/Desktop/3年/TEST/line/Scripts/python.exe c:/Users/HaNdARyo/Desktop/3年/TEST/send.py
#flask run
#
#

import os
import time
from send import pre
from pathlib import Path
from flask import Flask, request, abort,redirect,url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
)


SAVE_DIR = "./static/images"   # 一時的に画像を保存するディレクトリ名
if not os.path.isdir(SAVE_DIR):
    os.mkdir(SAVE_DIR)

upload_folder = './uploads'

app = Flask(__name__)

line_bot_api = LineBotApi("kiJw2TMl176Ax4xySiBuUhiSwVXrfr3AXcVAufkpbVYhxlAu0AG/dtanQdDcDXEotWUt8BnTYa73LGVuloaZV8Yq75aXDSnRnVrSvD9k5aoqVgsr+yPUUkSlXvxiNyjSDi2F8sozfezf4qPXCW4TggdB04t89/1O/w1cDnyilFU=")  # config.pyで設定したチャネルアクセストークン
handler = WebhookHandler("c706f3fca546093a1ea334bb8ea8598f")  # config.pyで設定したチャネルシークレット

SRC_IMAGE_PATH = "static/images/{}.jpg"
MAIN_IMAGE_PATH = "static/images/{}_main.jpg"
PREVIEW_IMAGE_PATH = "static/images/{}_preview.jpg"
global_URL = {}
URLTEXT = None


@app.route("/")
def index():
    return "Hello World!"

#URL取得
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    global global_URL
    URLTEXT = event.message.text
    profile = line_bot_api.get_profile(event.source.user_id)
    userId = profile.user_id[:5]

    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text=global_URL))
    if URLTEXT == "QRコードを作成する":
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage("URLを入力して下さい。"))
    elif URLTEXT == "使い方":
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage("使用説明\nSTEP1:URLを入力して下さい。\nSTEP2:画像を送信して下さい。"))
    else:
        global_URL[userId] = URLTEXT
        line_bot_api.reply_message(
        event.reply_token, [
        TextSendMessage(text=URLTEXT),#URLのオウム返し
        TextSendMessage(text="次に画像を送信してください。")])

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

#画像の送信
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id#画像の格納
    profile = line_bot_api.get_profile(event.source.user_id)
    userId = profile.user_id[:5]

    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    main_image_path = MAIN_IMAGE_PATH.format(message_id)
    preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)

    # 画像を保存
    save_image(message_id, src_image_path)
    URLTEXT = global_URL[userId]

    # 画像の加工、保存
    # 処理
    pre(URLTEXT,src_image_path, main_image_path,preview_image_path)#send.pyのpre関数

    # # 画像の送信
    image_message = ImageSendMessage(
        original_content_url=f"https://really-strong-garfish.ngrok-free.app/{main_image_path}",
        preview_image_url=f"https://really-strong-garfish.ngrok-free.app/{preview_image_path}"
        
    )

    #app.logger.info(f"https://still-oddly-shad.ngrok-free.app/{main_image_path}")
    line_bot_api.reply_message(event.reply_token, image_message)

    #画像を削除する
    def delayed_delete():
        src_image_path.unlink()
        os.remove(main_image_path)
        os.remove(preview_image_path)
        del global_URL[userId]#変更
        print(global_URL)     #変更
    
    delay_seconds = 20
    time.sleep(delay_seconds)
    delayed_delete()

def save_image(message_id: str, save_path: str) -> None:
    """保存"""
    message_content = line_bot_api.get_message_content(message_id)
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

if __name__ == "__main__":
    # Flaskを起動
    app.run()
    