import os, sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

DB=os.getenv("DB_PATH","coinuz.db")
WEB_APP_URL=os.getenv("WEB_APP_URL","https://oyinu255-cyber.github.io/Khorezm/")
db=sqlite3.connect(DB,check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,coins INTEGER NOT NULL DEFAULT 0,clicks INTEGER NOT NULL DEFAULT 0)")
db.execute("CREATE TABLE IF NOT EXISTS transfers(id INTEGER PRIMARY KEY AUTOINCREMENT,sender_id INTEGER,receiver_id INTEGER,amount INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
db.commit()

def upsert(u):
    db.execute("""INSERT INTO users(id,username,first_name) VALUES(?,?,?)
    ON CONFLICT(id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",(u.id,u.username or "",u.first_name or ""))
    db.commit()

def user(uid):
    return db.execute("SELECT id,username,first_name,coins,clicks FROM users WHERE id=?",(uid,)).fetchone()

def by_username(name):
    return db.execute("SELECT id,username,first_name,coins FROM users WHERE lower(username)=?",(name.lstrip("@").lower(),)).fetchone()

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user; upsert(u); r=user(u.id)
    kb=[[InlineKeyboardButton("🎮 O‘ynash",web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("👤 Profil",callback_data="profile"),InlineKeyboardButton("📤 Coin yuborish",callback_data="send")]]
    await update.message.reply_text(f"Salom, {u.first_name}! 👋\n\nUsername: @{r[1] or 'username yo‘q'}\n🪙 Coin: {r[3]}",reply_markup=InlineKeyboardMarkup(kb))

async def profile(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user; upsert(u); r=user(u.id)
    await update.message.reply_text(f"👤 Profil\nUsername: @{r[1] or 'username yo‘q'}\n🪙 Coin: {r[3]}\n🖱 Bosishlar: {r[4]}")

async def send_help(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Coin yuborish:\n/sendcoin @username 50\n\nQabul qiluvchi botda /start yuborgan bo‘lishi kerak.")

async def sendcoin(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user; upsert(u)
    if len(context.args)!=2: return await update.message.reply_text("Misol: /sendcoin @ali123 50")
    target,amt=context.args
    try: amount=int(amt)
    except: return await update.message.reply_text("Coin miqdori son bo‘lishi kerak.")
    if amount<=0: return await update.message.reply_text("Miqdor 0 dan katta bo‘lishi kerak.")
    receiver=by_username(target)
    if not receiver: return await update.message.reply_text("Bu username bilan foydalanuvchi topilmadi.")
    sender=user(u.id)
    if receiver[0]==u.id: return await update.message.reply_text("O‘zingizga yubora olmaysiz.")
    if sender[3]<amount: return await update.message.reply_text(f"Coin yetarli emas. Balans: {sender[3]} 🪙")
    db.execute("UPDATE users SET coins=coins-? WHERE id=?",(amount,u.id))
    db.execute("UPDATE users SET coins=coins+? WHERE id=?",(amount,receiver[0]))
    db.execute("INSERT INTO transfers(sender_id,receiver_id,amount) VALUES(?,?,?)",(u.id,receiver[0],amount))
    db.commit()
    await update.message.reply_text(f"✅ {amount} 🪙 @{receiver[1]} ga yuborildi.")

async def buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.data=="profile":
        r=user(q.from_user.id); await q.message.reply_text(f"👤 @{r[1] or 'username yo‘q'}\n🪙 {r[3]} coin")
    else: await q.message.reply_text("📤 /sendcoin @username miqdor\nMasalan: /sendcoin @ali123 50")

token=os.getenv("BOT_TOKEN")
if not token: raise RuntimeError("BOT_TOKEN environment variable kerak")
app=Application.builder().token(token).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("profile",profile))
app.add_handler(CommandHandler("sendcoin",sendcoin))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()
