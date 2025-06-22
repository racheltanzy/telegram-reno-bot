from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("House_Reno_Expenses").sheet1

# Bot Handlers
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
        sheet.append_row([date, category, item, amount, notes])
        await update.message.reply_text(
            "Expense added! View here: https://docs.google.com/spreadsheets/d/193CMc6umAkjLgVlOIoLsud-cExLgDYAPl8svyA1XG1c/edit?usp=sharing"
        )
    except:
        await update.message.reply_text(
            "Format error. Use: `Item | Amount | Notes`",
            parse_mode="Markdown"
        )

# Main
app = ApplicationBuilder().token("8143805573:AAEqqg_r6t-S5ebW_ynmdYljW-bVXzC31kc").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
