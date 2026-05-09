import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

TOKEN = os.environ["BOT_TOKEN"]
HR_ID = int(os.environ["HR_ID"])

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAVZULAR = {
    "ish_haqi":  "💰 Ish haqi masalalari",
    "hujjat":    "📄 Hujjatlar va ma'lumotnoma",
    "shikoyat":  "📢 Shikoyat va takliflar",
    "boshqa":    "💬 Boshqa",
}

def mavzu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(nom, callback_data=f"mavzu_{kalit}")]
        for kalit, nom in MAVZULAR.items()
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Salom! 👋\n\nHR bo'limiga murojaat qilish uchun mavzuni tanlang:",
        reply_markup=mavzu_keyboard(),
    )

async def mavzu_tanlandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kalit = query.data.replace("mavzu_", "")
    if kalit not in MAVZULAR:
        return
    context.user_data["mavzu"] = MAVZULAR[kalit]
    context.user_data["kutilmoqda"] = True
    await query.edit_message_text(
        f"Mavzu: *{MAVZULAR[kalit]}*\n\n"
        f"Murojaatingizni yozing. Xabaringiz HR bo'limiga yuboriladi. ✍️",
        parse_mode="Markdown",
    )

async def xabar_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Faqat mavzu tanlagan foydalanuvchilar uchun
    if not context.user_data.get("kutilmoqda"):
        await update.message.reply_text(
            "Murojaat qilish uchun mavzuni tanlang:",
            reply_markup=mavzu_keyboard(),
        )
        return

    foydalanuvchi = update.effective_user
    mavzu = context.user_data.get("mavzu", "Noma'lum")
    matn = update.message.text

    ism = foydalanuvchi.full_name
    username = f"@{foydalanuvchi.username}" if foydalanuvchi.username else "username yo'q"
    user_id = foydalanuvchi.id

    hr_xabar = (
        f"📬 *Yangi murojaat!*\n\n"
        f"👤 Ism: {ism}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📌 Mavzu: {mavzu}\n\n"
        f"💬 *Xabar:*\n{matn}"
    )

    await context.bot.send_message(
        chat_id=HR_ID,
        text=hr_xabar,
        parse_mode="Markdown",
    )

    context.user_data.clear()
    logger.info("Yangi murojaat: %s (%s) — %s", ism, user_id, mavzu)

    await update.message.reply_text(
        "✅ Murojaatingiz HR bo'limiga yuborildi! Tez orada javob berishadi. 🙏\n\n"
        "Yana murojaat qilmoqchimisiz? Mavzuni tanlang:",
        reply_markup=mavzu_keyboard(),
    )

async def javob_ber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != HR_ID:
        return
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Foydalanish: `/javob <user_id> <matn>`\n\n"
            "Masalan: `/javob 123456789 Hujjatingiz tayyor!`",
            parse_mode="Markdown",
        )
        return
    try:
        user_id = int(args[0])
        matn = " ".join(args[1:])
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 *HR bo'limidan javob:*\n\n{matn}",
            parse_mode="Markdown",
        )
        await update.message.reply_text("✅ Javob yuborildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("javob", javob_ber))
    app.add_handler(CallbackQueryHandler(mavzu_tanlandi, pattern="^mavzu_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xabar_qabul))

    logger.info("HR murojaat bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
