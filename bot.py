import telebot
import json
import time
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ---------------- CONFIG ----------------
API_TOKEN = "7962612818:AAH_nMUVgvXQqUX1q9PSfNw_SYl9922duEs"
bot = telebot.TeleBot(API_TOKEN)

CHANNEL_1 = "small_earn"   # without @
CHANNEL_2 = "Refer_Earn_Bots" # without @

ADMIN_IDS = [7935004807]  # Replace with your admin Telegram ID

DB_FILE = "users.json"

# ---------------- DATABASE ----------------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

users = load_db()   # <-- yahan database load horaha hai

# ✅ Safety check: make sure every user has 'last_daily'
for uid, data in users.items():
    if "last_daily" not in data:
        data["last_daily"] = 0
save_db()

def get_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "points": 0,
            "referrals": 0,
            "last_daily": 0,
            "withdrawals": []
        }
        save_db()
    return users[str(user_id)]

# ---------------- FORCE JOIN CHECK ----------------
def force_join(uid):
    try:
        valid_status = ["member", "administrator", "creator"]

        # First channel check
        m1 = bot.get_chat_member(CHANNEL_1, user_id)
        if m1.status not in valid_status:
            return False

        # Second channel check
        m2 = bot.get_chat_member(CHANNEL_2, user_id)
        if m2.status not in valid_status:
            return False

        return True

    except Exception as e:
        print(f"[ForceJoinError] {e}")
        return False 

# --------------- START ----------------
# --------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    uname = message.from_user.username or ""   # agar user ne username set kiya hai to use lo
    args = message.text.split()  # ✅ yahan args define kar diya

    # Agar naya user hai to add karo
    if uid not in users:
        users[uid] = {
            "points": 0,
            "username": uname,
            "referrals": 0
        }
        save_db()
    else:
        # update username if changed
        users[uid]["username"] = uname
        save_db()


    # Referral Tracking
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != str(user_id):  # self-referral block
            ref_user = get_user(ref_id)
            ref_user["points"] += 20
            ref_user["referrals"] += 1
            save_db()
            bot.send_message(int(ref_id), f"🎉 You earned +20 points from your referral!")

    # Always show force join buttons first
    show_force_join(uid)


# ---------------- FORCE JOIN ----------------
def show_force_join(user_id):
    buttons = [
        [InlineKeyboardButton("1️⃣ Join Earning Channel", url="https://t.me/small_earn")],
        [InlineKeyboardButton("2️⃣ Join Backup Channel", url="https://t.me/Refer_Earn_Bots")],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="joined_done")],
    ]
    markup = InlineKeyboardMarkup(buttons)
    bot.send_message(user_id,
                     "🚨 Please join our official channels to unlock the bot!",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "joined_done")
def joined_done(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)  # Remove force join section
    show_main_menu(user_id)  # Directly unlock menu

# ---------------- MAIN MENU ----------------
def show_main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎁 Daily Gift"), KeyboardButton("📊 My Points"))
    markup.row(KeyboardButton("👥 Referral System"), KeyboardButton("💳 Withdraw"))
    bot.send_message(user_id, "✅ Welcome to the Main Menu!", reply_markup=markup)

# ---------------- DAILY GIFT ----------------
@bot.message_handler(func=lambda m: m.text == "🎁 Daily Gift")
def daily_gift(message):
    user = get_user(message.chat.id)
    now = time.time()
    if now - user["last_daily"] >= 86400:  # 24h
        user["points"] += 10
        user["last_daily"] = now
        save_db()
        bot.send_message(message.chat.id, "🎉 You claimed +10 daily points!")
    else:
        remaining = int(86400 - (now - user["last_daily"])) // 3600
        bot.send_message(message.chat.id, f"⏳ You already claimed! Try again in {remaining} hours.")

# ---------------- MY POINTS ----------------
@bot.message_handler(func=lambda m: m.text == "📊 My Points")
def my_points(message):
    user = get_user(message.chat.id)
    bot.send_message(message.chat.id, f"💰 Your Current Balance: {user['points']} Points")

# ---------------- REFERRAL ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Referral System")
def referral(message):
    user_id = message.chat.id
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    user = get_user(user_id)
    bot.send_message(user_id, f"👥 Your Referral Link:\n{link}\n\n📊 Total Referrals: {user['referrals']}")

# ---------------- WITHDRAW ----------------
@bot.message_handler(func=lambda m: m.text == "💳 Withdraw")
def withdraw(message):
    user = get_user(message.chat.id)
    if user["points"] < 600:
        bot.send_message(message.chat.id, "❌ Minimum 600 points required to withdraw.")
    else:
        buttons = [
            [InlineKeyboardButton("🏦 Bank Transfer", callback_data="pay_bank")],
            [InlineKeyboardButton("💳 UPI", callback_data="pay_upi")],
            [InlineKeyboardButton("🎮 Google Play", callback_data="pay_gplay")],
            [InlineKeyboardButton("🛒 Amazon Voucher", callback_data="pay_amazon")]
        ]
        bot.send_message(message.chat.id, "💳 Select your payout option:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_withdraw(call):
    user_id = call.message.chat.id
    payout_type = call.data.replace("pay_", "")
    bot.send_message(user_id, "📸 Please send a screenshot with points + payout details.")
    bot.register_next_step_handler(call.message, lambda m: save_withdraw(user_id, payout_type, m))

def save_withdraw(user_id, payout_type, message):
    user = get_user(user_id)
    user["withdrawals"].append({"type": payout_type, "screenshot": message.photo[-1].file_id if message.photo else "N/A"})
    save_db()
    bot.send_message(user_id, "⏳ Your request is sent to admin. Processing in 2-4 hours.")
    for admin in ADMIN_IDS:
        bot.forward_message(admin, user_id, message.message_id)

# ---------------- ADMIN PANEL ----------------
ADMIN_IDS = [7935004807]   # <-- apna Telegram numeric ID yahan daalo

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🔑 Admin Commands:\n"
            "/addpoints <user_id> <amount>\n"
            "/deductpoints <user_id> <amount>\n"
            "/broadcast <message>\n"
            "/userpoints <user_id>\n"
            "/checkpoints @username"
        )
    else:
        bot.send_message(message.chat.id, "❌ You are not an admin.")

# Add Points
@bot.message_handler(commands=['addpoints'])
def add_points(message):
    if message.chat.id in ADMIN_IDS:
        try:
            _, uid, amt = message.text.split()
            uid, amt = int(uid), int(amt)
            user = get_user(uid)
            user["points"] += amt
            save_db()
            bot.send_message(uid, f"✅ Admin added {amt} points to your account.")
            bot.send_message(message.chat.id, f"✅ {amt} points added to {uid}")
        except:
            bot.send_message(message.chat.id, "⚠️ Usage: /addpoints <user_id> <amount>")

# Deduct Points
@bot.message_handler(commands=['deductpoints'])
def deduct_points(message):
    if message.chat.id in ADMIN_IDS:
        try:
            _, uid, amt = message.text.split()
            uid, amt = int(uid), int(amt)
            user = get_user(uid)
            user["points"] -= amt
            save_db()
            bot.send_message(uid, f"⚠️ Admin deducted {amt} points from your account.")
            bot.send_message(message.chat.id, f"✅ Deducted {amt} points from {uid}")
        except:
            bot.send_message(message.chat.id, "⚠️ Usage: /deductpoints <user_id> <amount>")

# Broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id in ADMIN_IDS:
        text = message.text.replace("/broadcast", "").strip()
        if not text:
            bot.send_message(message.chat.id, "⚠️ Usage: /broadcast <message>")
            return
        for uid, data in users.items():   # 🔥 fixed here
            try:
                bot.send_message(int(uid), f"📢 {text}")
            except:
                pass
        bot.send_message(message.chat.id, "✅ Broadcast sent!")

# User Points (by user_id)
@bot.message_handler(commands=['userpoints'])
def user_points(message):
    if message.chat.id in ADMIN_IDS:
        try:
            _, uid = message.text.split()
            uid = int(uid)
            user = get_user(uid)
            bot.send_message(
                message.chat.id,
                f"👤 User ID: {uid}\n💰 Points: {user['points']}\n🔗 Referrals: {user.get('referrals', 0)}"
            )
        except:
            bot.send_message(message.chat.id, "⚠️ Usage: /userpoints <user_id>")

# ✅ Check Points (by username)
@bot.message_handler(commands=['checkpoints'])
def check_points(message):
    if message.chat.id in ADMIN_IDS:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Usage: /checkpoints @username")
            return

        username = parts[1].replace("@", "").strip().lower()
        target_user = None

        # loop through users dict to find matching username
        for uid, data in users.items():
            if data.get("username", "").lower() == username:
                target_user = (uid, data)
                break

        if target_user:
            uid, data = target_user
            points = data.get("points", 0)
            referrals = data.get("referrals", 0)
            bot.send_message(message.chat.id, f"👤 @{username}\n💰 Points: {points}\n🔗 Referrals: {referrals}")
        else:
            bot.send_message(message.chat.id, f"❌ User @{username} not found in database.")

# ================== Advanced Admin Commands ==================

# 🕒 Pending Withdrawals
@bot.message_handler(commands=['pending'])
def pending_requests(message):
    if message.chat.id in ADMIN_IDS:
        pending = [f"👤 {data.get('username','')} | ID: {uid} | 💰 {data.get('pending_withdraw',0)} Points"
                   for uid, data in users.items() if data.get("status") == "PENDING"]
        if pending:
            bot.send_message(message.chat.id, "⏳ Pending Withdrawals:\n" + "\n".join(pending))
        else:
            bot.send_message(message.chat.id, "✅ No pending withdrawals right now.")

# ✅ Approve Payout
@bot.message_handler(commands=['approve'])
def approve_payout(message):
    if message.chat.id in ADMIN_IDS:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "⚠️ Usage: /approve <user_id> <amount>")
            return

        uid, amount = parts[1], int(parts[2])
        if uid in users and users[uid].get("status") == "PENDING":
            users[uid]["status"] = "APPROVED"
            users[uid]["points"] -= amount
            save_db()
            bot.send_message(message.chat.id, f"✅ Payout Approved for {uid} ({amount} points).")
            bot.send_message(uid, f"🎉 Your payout of {amount} points has been approved!")
        else:
            bot.send_message(message.chat.id, "❌ No pending request found for this user.")

# 🏆 Top 10 Users
@bot.message_handler(commands=['top10'])
def top_users(message):
    if message.chat.id in ADMIN_IDS:
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
        if not sorted_users:
            bot.send_message(message.chat.id, "❌ No users found.")
            return
        msg = "🏆 Top 10 Users:\n"
        for i, (uid, data) in enumerate(sorted_users, start=1):
            msg += f"{i}. @{data.get('username','N/A')} | {data.get('points',0)} Points\n"
        bot.send_message(message.chat.id, msg)

# 📊 Bot Statistics
@bot.message_handler(commands=['stats'])
def bot_stats(message):
    if message.chat.id in ADMIN_IDS:
        total_users = len(users)
        total_points = sum(data.get("points", 0) for data in users.values())
        total_referrals = sum(data.get("referrals", 0) for data in users.values())
        pending_count = sum(1 for data in users.values() if data.get("status") == "PENDING")

        stats_msg = (
            f"📊 Bot Statistics:\n"
            f"👥 Total Users: {total_users}\n"
            f"💰 Total Points Circulated: {total_points}\n"
            f"🔗 Total Referrals: {total_referrals}\n"
            f"⏳ Pending Withdrawals: {pending_count}"
        )
        bot.send_message(message.chat.id, stats_msg)

# 💸 Direct Payout Trigger (Trackable)
@bot.message_handler(commands=['id'])
def payout_direct(message):
    if message.chat.id in ADMIN_IDS:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Usage: /id <user_id>")
            return

        uid = parts[1]
        if uid in users:
            users[uid]["status"] = "PENDING"
            save_db()
            bot.send_message(message.chat.id, f"⏳ Payout initiated for {uid}. Waiting for confirmation...")
            bot.send_message(uid, "💸 Your payout request has been received and is pending admin approval.")
        else:
            bot.send_message(message.chat.id, "❌ User not found.")

# ---------------- RUN BOT ----------------
print("🤖 Bot is running...")

import time
while True:
    try:
        bot.polling(non_stop=True, timeout=60)
    except Exception as e:
        print(f"⚠️ Error occurred: {e}")
        time.sleep(5)  # wait 5 sec before retry
