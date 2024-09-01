import logging
import os
import sys
import time

import qrcode
import telebot
import uuid
import flask
from flask import Flask


WEBHOOK_URL = "owiejfs"
app = Flask(__name__)

# Configure logging to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


logger = logging.getLogger(__name__)
bot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])


@app.route("/" + WEBHOOK_URL, methods=["POST"])
def webhook():
    if flask.request.headers.get("content-type") == "application/json":
        json_string = flask.request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    else:
        flask.abort(403)


def text_to_qr_code(text):
    """Generates a QR code from the given text and saves it as an image."""
    file_name = str(uuid.uuid4()) + ".png"
    qr = qrcode.QRCode(
        version=1,  # Adjust the version for larger QR codes
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction level
        box_size=35,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_name)
    return file_name


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hi! Send me any text and get back qr code")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"processing {message.text}")
    file_name = text_to_qr_code(message.text)
    photo_file = open(file_name, "rb")
    bot.send_photo(message.chat.id, photo_file)
    os.remove(file_name)
    logger.info("cleanup complete")


if __name__ == "__main__":
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    webhook_info = bot.get_webhook_info()
    if os.environ.get("BASE_URL") + "/" + WEBHOOK_URL != webhook_info.url:
        logging.info("webhook url changed")
        bot.remove_webhook()
        time.sleep(0.1)
        # Set webhook
        bot.set_webhook(url=os.environ.get("BASE_URL") + "/" + WEBHOOK_URL)
    else:
        logging.info("leave webhook url unchanged")

    # Start flask server
    # app.run(host="0.0.0.0", port=8080, debug=False)
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
