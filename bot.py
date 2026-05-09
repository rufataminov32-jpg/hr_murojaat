import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters,
)

# ─── SOZLAMALAR ──────────────────────────────────────────────────────────────

TOKEN   = os.environ["BOT_TOKEN"]
HR_ID   = int(os.environ["HR_ID"])

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAVZU, XABAR = range(2)

MAVZULAR = {
    "ish_haqi":  "💰 Ish haqi masalalari",
    "hujjat":    "📄 Hujjatlar va ma'lumotnoma",
    "shikoyat":  "📢 Shikoyat va takliflar",
    "boshqa":    "💬 Boshqa",
}


# ─── YORDAMCHI ───────────────────────────────────────────────────────────────

def mavzu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(nom, callback_data=kalit)]
        for kalit, nom in MAVZULAR.items()
    ])


# ─── FOYDALANUVCHI ───────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Salom! 👋\n\nHR bo'limiga murojaat qilish uchun mavzuni tanlang:",
        reply_markup=mavzu_keyboard(),
    )
    return MAVZU


async def mavzu_tanlandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kalit = query.data
    if kalit not in MAVZULAR:
        return MAVZU
    context.user_data["mavzu"] = MAVZULAR[kalit]
    await query.edit_message_text(
        f"Mavzu: *{MAVZULAR[kalit]}*\n\n"
        f"Murojaatingizni yozing. Xabaringiz HR bo'limiga yuboriladi. ✍️\n\n"
        f"/bekor — bekor qilish",
        parse_mode="Markdown",
    )
    return XABAR


async def xabar_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foydalanuvchi = update.effective_user
    mavzu = context.user_data.get("mavzu", "Noma'lum")
    matn = update.message.text

    # HR ga xabar yuborish
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

    # Avtomatik bosh menyuga qaytish
    await update.message.reply_text(
        "✅ Murojaatingiz HR bo'limiga yuborildi! Tez orada javob berishadi. 🙏\n\n"
        "Yana murojaat qilmoqchimisiz? Mavzuni tanlang:",
        reply_markup=mavzu_keyboard(),
    )
    return MAVZU


async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Murojaat bekor qilindi.",
        reply_markup=mavzu_keyboard(),
    )
    return MAVZU


# ─── HR JAVOBI ───────────────────────────────────────────────────────────────

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


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            MAVZU: [CallbackQueryHandler(mavzu_tanlandi, pattern="^(ish_haqi|hujjat|shikoyat|boshqa)$")],
            XABAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, xabar_qabul)],
        },
        fallbacks=[CommandHandler("bekor", bekor)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("javob", javob_ber))

    logger.info("HR murojaat bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
