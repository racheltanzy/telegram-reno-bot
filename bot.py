import os
import json
import datetime
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import CellFormat, NumberFormat, format_cell_range

# === Flask to keep Render alive ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
worksheet = client.open("House_Reno_Expenses").sheet1

# Apply money formatting only once
if worksheet.acell('F1').value != 'formatted':
    money_format = CellFormat(
        numberFormat=NumberFormat(type="NUMBER", pattern="$#,##0.00")
    )
    format_cell_range(worksheet, 'D2:D1000', money_format)
    worksheet.update('F1', [['formatted']])

# === Telegram Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Plumbing", callback_data="Plumbing"),
         InlineKeyboardButton("Electrical", callback_data="Electrical")],
        [InlineKeyboardButton("Carpentry", callback_data="Carpentry")],
        [InlineKeyboardButton("Painting", callback_data="Painting"),
         InlineKeyboardButton("Flooring", callback_data="Flooring")],
        [InlineKeyboardButton("Others", callback_data="Others")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a category:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    context.user_data['category'] = category
    await query.edit_message_text(
        text=f"Category selected: {category}\n\nNow send:\n`Item | Amount | Notes`",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.user_data.get('category')
    if not category:
        await update.message.reply_text("Please select a category first by typing /start")
        return
    try:
        item, amount, notes = [x.strip() for x in update.message.text.split("|")]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        worksheet.append_row([date, category, item, amount, notes])
        await update.message.reply_text(
            "Expense added! View here: https://docs.google.com/spreadsheets/d/193CMc6umAkjLgVlOIoLsud-cExLgDYAPl8svyA1XG1c/edit?usp=sharing"
        )
    except:
        await update.message.reply_text(
            "Format error. Use: `Item | Amount | Notes`",
            parse_mode="Markdown"
        )

# === Main ===
if __name__ == '__main__':
    # Run dummy web server in background
    threading.Thread(target=run_flask).start()

    # Start Telegram bot
    bot_app = ApplicationBuilder().token("8143805573:AAEqqg_r6t-S5ebW_ynmdYljW-bVXzC31kc").build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot_app.run_polling()
