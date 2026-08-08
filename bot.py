import os
import time
import urllib.request
from dotenv import load_dotenv
from flask import Flask, send_file, make_response
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
    # тот же самый index.html, что отдаёт GitHub Pages — одна копия, не расходится
    resp = make_response(send_file("index.html"))
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


def keep_awake():
    """Render на бесплатном тарифе усыпляет сервис после ~15 мин без запросов,
    а вместе с ним засыпает и бот. Пингуем сами себя, чтобы не засыпал."""
    if not APP_URL:
        return
    base = APP_URL.rsplit("/app", 1)[0]
    while True:
        time.sleep(600)  # каждые 10 минут
        try:
            urllib.request.urlopen(base, timeout=30).read(1)
        except Exception as e:
            print(f"[keep-awake] пинг не прошёл: {e!r}")


def main():
    # веб-часть (Mini App + health-check Render) поднимаем один раз и не трогаем,
    # даже если у бота ниже будут временные проблемы с polling
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_awake, daemon=True).start()

    while True:
        try:
            app = Application.builder().token(TG_TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            app.add_handler(MessageHandler(filters.Regex("^🔄 Старт$"), on_start_button))
            app.add_handler(MessageHandler(filters.Regex("^👤 Профиль$"), on_profile_button))
            print("Бот запущен, жду сообщений...")
            app.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"[bot] упал с ошибкой: {e!r}, перезапуск через 5 секунд")
            time.sleep(5)


if __name__ == "__main__":
    main()
