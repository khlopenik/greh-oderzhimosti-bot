import os
from dotenv import load_dotenv
from flask import Flask, render_template, make_response
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading

load_dotenv()
TG_TOKEN = os.environ.get("TG_TOKEN")
APP_URL = os.environ.get("APP_URL", "")  # https-адрес Mini App, пусто пока нет хостинга

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return "Грех Одержимости бот работает."


@flask_app.route("/app")
def mini_app():
    resp = make_response(render_template("app.html"))
    # без кеша — Telegram WebView иначе может показывать старую версию после обновлений
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


def main_keyboard():
    rows = [[KeyboardButton("🔄 Старт"), KeyboardButton("👤 Профиль")]]
    if APP_URL:
        rows.append([KeyboardButton("📖 Приложение", web_app=WebAppInfo(url=APP_URL))])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


WELCOME = (
    "Привет! Это бот «Грех Одержимости» — интерактивные истории, где решаешь ты.\n\n"
    "Сейчас доступна первая история: «Разлучники»."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = WELCOME
    if not APP_URL:
        text += "\n\n(Кнопка с приложением появится, как только подключим хостинг.)"
    await update.message.reply_text(text, reply_markup=main_keyboard())


async def on_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def on_profile_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Профиль появится, когда подключим аккаунты и экономику (алмазы/чашечки). Пока в разработке.",
        reply_markup=main_keyboard(),
    )


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)


def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^🔄 Старт$"), on_start_button))
    app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), on_profile_button))
    print("Бот запущен, жду сообщений...")
    app.run_polling()


if __name__ == "__main__":
    main()
