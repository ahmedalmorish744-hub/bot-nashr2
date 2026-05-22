# Developer: Smith - Mustafa Hussein
# Modified for Railway - Full Features - No Forced Subscription
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, CallbackQuery, ForceReply,
    InlineKeyboardMarkup as Markup,
    InlineKeyboardButton as Button,
    InputMediaPhoto, InputMediaVideo
)
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid,
    PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid,
    UserNotParticipant, ChatWriteForbidden, BadMsgNotification
)
import os
import json
import asyncio
from asyncio import create_task, sleep
from datetime import datetime, timedelta
from pytz import timezone
from typing import Union
import threading
from flask import Flask

# ------------------ قراءة المتغيرات البيئية ------------------
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 8226014028))

# ------------------ إعدادات البوت ------------------
app = Client("autoPost", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_states = {}

# ------------------ أزرار رئيسية ------------------
homeMarkup = Markup([
    [Button("👤 حسابي", callback_data="account")],
    [Button("📋 السوبرات المضافة", callback_data="currentSupers"), Button("➕ إضافة سوبر", callback_data="newSuper")],
    [Button("⏱️ مدة النشر", callback_data="waitTime"), Button("📝 كليشة النشر", callback_data="newCaption")],
    [Button("⏹️ إيقاف النشر", callback_data="stopPosting"), Button("▶️ بدء النشر", callback_data="startPosting")],
    [Button("🛡️ تعليمات الأمان", callback_data="safety")]
])

# ------------------ دوال حفظ وقراءة JSON ------------------
def write(fp, data):
    with open(fp, "w") as f:
        json.dump(data, f, indent=2)

def read(fp):
    if not os.path.exists(fp):
        if fp == "channels.json":
            write(fp, [])
        else:
            write(fp, {})
    with open(fp) as f:
        try:
            return json.load(f)
        except:
            return [] if fp == "channels.json" else {}

users_db = "users.json"
channels_db = "channels.json"

def load_users():
    return read(users_db)

def save_users(data):
    write(users_db, data)

def get_user_data(user_id):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "subscription_end": (datetime.now() + timedelta(days=1)).isoformat(),
            "referrals_count": 0,
            "referred_by": None,
            "session": None,
            "groups": [],
            "caption": None,
            "waitTime": 60,
            "posting": False
        }
        save_users(users)
    return users[uid]

def update_user(user_id, data):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid].update(data)
        save_users(users)

def has_active_subscription(user_id):
    data = get_user_data(user_id)
    end_str = data.get("subscription_end")
    if not end_str:
        return False
    end = datetime.fromisoformat(end_str)
    return end > datetime.now()

def get_referral_link(user_id):
    bot_username = getattr(app, "me", None)
    username = bot_username.username if bot_username else "bot"
    return f"https://t.me/{username}?start=ref_{user_id}"

# ------------------ النشر التلقائي ------------------
async def posting(user_id):
    data = get_user_data(user_id)
    if not data.get("posting") or not data.get("session"):
        return
    
    try:
        client = Client(str(user_id), api_id=API_ID, api_hash=API_HASH, session_string=data["session"])
        await client.start()
        
        while data.get("posting") and has_active_subscription(user_id):
            wait = data.get("waitTime", 60)
            groups = data.get("groups", [])
            caption_data = data.get("caption")
            
            if caption_data is None:
                update_user(user_id, {"posting": False})
                await app.send_message(user_id, "تم إيقاف النشر بسبب عدم وجود كليشة.", reply_markup=Markup([[Button("إضافة كليشة", callback_data="newCaption")]]))
                break
                
            for group in groups:
                try:
                    if caption_data["type"] == "photo":
                        await client.send_photo(group, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    elif caption_data["type"] == "video":
                        await client.send_video(group, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    else:
                        await client.send_message(group, caption_data["text"])
                except ChatWriteForbidden:
                    try:
                        chat = await client.join_chat(group)
                        if caption_data["type"] == "photo":
                            await client.send_photo(chat.id, caption_data["file_id"], caption=caption_data.get("caption", ""))
                        elif caption_data["type"] == "video":
                            await client.send_video(chat.id, caption_data["file_id"], caption=caption_data.get("caption", ""))
                        else:
                            await client.send_message(chat.id, caption_data["text"])
                    except:
                        pass
                except Exception:
                    pass
            
            await sleep(wait)
            data = get_user_data(user_id)
            
        if data.get("posting") and not has_active_subscription(user_id):
            update_user(user_id, {"posting": False})
            await app.send_message(user_id, "انتهى اشتراكك أثناء النشر. تم الإيقاف.")
        
        await client.stop()
    except Exception as e:
        update_user(user_id, {"posting": False})

# ------------------ أوامر البوت ------------------
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        referrer_id = int(message.command[1].split("_")[1])
        if referrer_id != user_id:
            users = load_users()
            if str(referrer_id) in users and str(user_id) not in users:
                get_user_data(user_id)
                users = load_users()
                users[str(user_id)]["referred_by"] = referrer_id
                users[str(referrer_id)]["referrals_count"] = users[str(referrer_id)].get("referrals_count", 0) + 1
                if users[str(referrer_id)]["referrals_count"] >= 5:
                    end = datetime.now() + timedelta(days=30)
                    users[str(referrer_id)]["subscription_end"] = end.isoformat()
                    await app.send_message(referrer_id, f"مبروك! وصل عدد المدعوين 5، تم تمديد اشتراكك لمدة شهر.")
                save_users(users)
    
    get_user_data(user_id)
    await message.reply(f"أهلاً بك {message.from_user.first_name} في بوت النشر التلقائي المطور 🚀", reply_markup=homeMarkup)

@app.on_callback_query()
async def callback_handler(_, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "toHome":
        await callback.message.edit_text("القائمة الرئيسية", reply_markup=homeMarkup)
    elif data == "account":
        user_data = get_user_data(user_id)
        end_date = datetime.fromisoformat(user_data["subscription_end"]).strftime("%Y-%m-%d")
        text = (f"👤 معلومات حسابك:\n\n📅 ينتهي الاشتراك: {end_date}\n👥 عدد الإحالات: {user_data['referrals_count']} / 5\n🔗 رابط الإحالة: {get_referral_link(user_id)}")
        await callback.message.edit_text(text, reply_markup=Markup([[Button("🔑 تسجيل حساب", callback_data="login"), Button("🔄 تغيير الحساب", callback_data="changeAccount")],[Button("رجوع", callback_data="toHome")]]))
    elif data in ("login", "changeAccount"):
        user_states[user_id] = 'waiting_session'
        await callback.message.delete()
        await app.send_message(user_id, "أرسل الـ **String Session** الخاصة بحسابك:", reply_markup=ForceReply())
    elif data == "newSuper":
        user_states[user_id] = 'waiting_super_link'
        await callback.message.delete()
        await app.send_message(user_id, "أرسل رابط السوبر أو معرفه (مثال: @group):", reply_markup=ForceReply())
    elif data == "currentSupers":
        groups = get_user_data(user_id).get("groups", [])
        if not groups: return await callback.answer("لا توجد سوبرات مضافة", show_alert=True)
        markup = [[Button(f"🗑 {g}", callback_data=f"delSuper {g}")] for g in groups]
        markup.append([Button("رجوع", callback_data="toHome")])
        await callback.message.edit_text("السوبرات المضافة:", reply_markup=Markup(markup))
    elif data.startswith("delSuper"):
        group = data.split(None, 1)[1]
        groups = get_user_data(user_id).get("groups", [])
        if group in groups:
            groups.remove(group)
            update_user(user_id, {"groups": groups})
        await callback.answer("تم الحذف", show_alert=True)
        await callback.message.edit_text("القائمة الرئيسية", reply_markup=homeMarkup)
    elif data == "newCaption":
        user_states[user_id] = 'waiting_caption'
        await callback.message.delete()
        await app.send_message(user_id, "أرسل الكليشة (نص أو صورة أو فيديو):", reply_markup=ForceReply())
    elif data == "waitTime":
        user_states[user_id] = 'waiting_waittime'
        await callback.message.delete()
        await app.send_message(user_id, "أرسل مدة الانتظار بالثواني (أقل مدة 60):", reply_markup=ForceReply())
    elif data == "startPosting":
        data_user = get_user_data(user_id)
        if not data_user.get("session") or not data_user.get("groups"):
            return await callback.answer("أضف حساباً وسوبرات أولاً", show_alert=True)
        if data_user.get("posting"): return await callback.answer("النشر مفعل مسبقاً", show_alert=True)
        if not has_active_subscription(user_id): return await callback.answer("انتهى اشتراكك", show_alert=True)
        update_user(user_id, {"posting": True})
        create_task(posting(user_id))
        await callback.message.edit_text("✅ تم بدء النشر التلقائي", reply_markup=Markup([[Button("إيقاف النشر", callback_data="stopPosting"), Button("رجوع", callback_data="toHome")]]))
    elif data == "stopPosting":
        update_user(user_id, {"posting": False})
        await callback.message.edit_text("🛑 تم إيقاف النشر", reply_markup=homeMarkup)
    elif data == "safety":
        await callback.message.reply("🛡️ لا تشارك كود الدخول أو الجلسة مع أحد. استخدم البوت على مسؤوليتك.")

# ------------------ معالجة رسائل الحالات ------------------
@app.on_message(filters.private & ~filters.command("start"))
async def handle_states(client, message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state: return
    if state == 'waiting_session':
        update_user(user_id, {"session": message.text})
        await message.reply("✅ تم حفظ الجلسة بنجاح!", reply_markup=homeMarkup)
        del user_states[user_id]
    elif state == 'waiting_super_link':
        groups = get_user_data(user_id).get("groups", [])
        if message.text not in groups:
            groups.append(message.text)
            update_user(user_id, {"groups": groups})
        await message.reply(f"✅ تم إضافة {message.text}", reply_markup=homeMarkup)
        del user_states[user_id]
    elif state == 'waiting_caption':
        if message.photo: cp = {"type": "photo", "file_id": message.photo.file_id, "caption": message.caption or ""}
        elif message.video: cp = {"type": "video", "file_id": message.video.file_id, "caption": message.caption or ""}
        else: cp = {"type": "text", "text": message.text}
        update_user(user_id, {"caption": cp})
        await message.reply("✅ تم حفظ الكليشة بنجاح.", reply_markup=homeMarkup)
        del user_states[user_id]
    elif state == 'waiting_waittime':
        try:
            wait = int(message.text)
            update_user(user_id, {"waitTime": wait})
            await message.reply(f"✅ تم ضبط الوقت على {wait} ثانية.", reply_markup=homeMarkup)
            del user_states[user_id]
        except: await message.reply("⚠️ يرجى إرسال رقم صحيح.")

# ------------------ تشغيل Flask ------------------
flask_app = Flask(__name__)
@flask_app.route('/')
def index(): return "Bot is running on Railway!"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ------------------ بدء البوت ------------------
async def main():
    await app.start()
    users = load_users()
    for uid, data in users.items():
        if data.get("posting"): create_task(posting(int(uid)))
    await idle()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
