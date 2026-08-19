import os, re, random, asyncio, logging, sqlite3
from datetime import datetime, timedelta
from html import escape as html_escape
import aiosqlite
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = 34162330
API_HASH = '3bb051fd52ebd9b40999d16070589fc2'
BOT_TOKEN = '8822939635:AAHIoAOxTpZkfT9SxGfgFD7V2YIgoQr7jp0'
ADMINS = [8810172664, 6282695098]
MEDIA_DIR = 'media'
os.makedirs(MEDIA_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
telethon_client = TelegramClient('reader_session', API_ID, API_HASH)
premium_client = TelegramClient('premium_session', API_ID, API_HASH)
PUBLISH_ERR = None
PREMIUM_ERR = None
DBG = ''
DBG_LIST = []

class DB:
    def __init__(self, path='auto_pub.db'):
        self.path = path
    async def init(self):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, key TEXT UNIQUE, value TEXT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS sources (id INTEGER PRIMARY KEY, username TEXT UNIQUE)")
            await conn.execute("CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY, admin_id INTEGER, created_at TEXT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS batch_posts (id INTEGER PRIMARY KEY, batch_id INTEGER, source TEXT, msg_id INTEGER, text TEXT, media INTEGER, status TEXT DEFAULT 'pending', fmt TEXT, foot TEXT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY, post_id INTEGER, scheduled_at TEXT, target_chat INTEGER)")
            await conn.execute("CREATE TABLE IF NOT EXISTS published (id INTEGER PRIMARY KEY, source TEXT, msg_id INTEGER, published_at TEXT, UNIQUE(source, msg_id))")
            async with conn.execute("PRAGMA table_info(batch_posts)") as cur:
                cols = [row[1] for row in await cur.fetchall()]
            if 'is_spoiler' not in cols:
                await conn.execute("ALTER TABLE batch_posts ADD COLUMN is_spoiler INTEGER DEFAULT 0")
            for k, v in [('min_interval','60'),('max_interval','120'),('batch_size','5'),('main_channel','-1004461131517'),('footer',''),('format','bold'),('emoji','1'),('emoji_tag',''),('cap_emoji','0'),('cap_emoji_tag',''),('id_emoji_tag',''), ('cap_emoji_count', '5')]:
                await conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            await conn.commit()
    async def get(self, key):
        async with aiosqlite.connect(self.path) as conn:
            cur = await conn.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = await cur.fetchone()
            return row[0] if row else None
    async def set(self, key, value):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            await conn.commit()

db = DB()

class States(StatesGroup):
    add_source = State()
    set_interval = State()
    set_batch_size = State()
    set_main_channel = State()
    set_footer = State()
    set_gfoot = State()
    set_pfoot = State()
    set_ptext = State()
    set_time_all = State()
    set_emoji_tag = State()
    set_cap_emoji = State()
    set_id_emoji = State()
    set_cap_emoji_count = State()
    set_sp_id_emoji = State()

def clean_text(text):
    if not text: return ''
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def format_text(text, mode):
    parts = re.split(r'(<tg-emoji[^>]*>.*?</tg-emoji>)', text or '')
    t = ''.join(p if p.startswith('<tg-emoji') else html_escape(p) for p in parts)
    if mode == 'bold': return f"<b>{t}</b>"
    if mode == 'blockquote': return f"<blockquote>{t}</blockquote>"
    if mode == 'bold_blockquote': return f"<blockquote><b>{t}</b></blockquote>"
    return t

def extract_tags(message):
    if not message.entities: return (message.text or '').strip()
    tags = [e for e in message.entities if e.type == 'custom_emoji' and e.custom_emoji_id]
    if not tags: return (message.text or '').strip()
    u = (message.text or '').encode('utf-16-le')
    res, last = [], 0
    for e in tags:
        res.append(u[last*2:e.offset*2].decode('utf-16-le', 'ignore'))
        ch = u[e.offset*2:(e.offset+e.length)*2].decode('utf-16-le', 'ignore') or '⭐'
        res.append(f'<tg-emoji emoji-id="{e.custom_emoji_id}">{ch}</tg-emoji>')
        last = e.offset + e.length
    res.append(u[last*2:].decode('utf-16-le', 'ignore'))
    return ''.join(res).strip()

def truncate_html(s, limit):
    if len(s) <= limit: return s
    cut = s[:limit]
    lt = cut.rfind('<'); gt = cut.rfind('>')
    if lt > gt: cut = cut[:lt]
    opens = re.findall(r'<(b|blockquote)>', cut)
    close = ''.join(f'</{t}>' for t in reversed(opens))
    return cut.rstrip() + '…' + close

def is_admin(uid): return uid in ADMINS

def menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")]])

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 دسته جدید", callback_data="new_batch")],
        [InlineKeyboardButton(text="🚀 نهایی‌سازی و انتشار تاییدشده‌ها", callback_data="finalize")],
        [InlineKeyboardButton(text="👁️ لیست تایید شده‌ها", callback_data="approved_list")],
        [InlineKeyboardButton(text="📅 زمان‌بندی‌ها", callback_data="schedules")],
        [InlineKeyboardButton(text="➕ افزودن منابع", callback_data="add_source")],
        [InlineKeyboardButton(text="📋 لیست منابع", callback_data="list_sources")],
        [InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="settings")],
        [InlineKeyboardButton(text="📊 آمار", callback_data="stats")],
    ])

async def show_menu(chat_id):
    await bot.send_message(chat_id, "🤖 ربات انتشار خودکار", reply_markup=main_menu_kb())

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("دسترسی غیرمجاز.")
    await show_menu(message.chat.id)

@router.callback_query(F.data == "menu")
async def cb_menu(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text("🤖 ربات انتشار خودکار", reply_markup=main_menu_kb())
    except Exception:
        try: await callback.message.delete()
        except Exception: pass
        await show_menu(callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "stats")
async def cb_stats(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        src = (await (await conn.execute("SELECT COUNT(*) FROM sources")).fetchone())[0]
        pub = (await (await conn.execute("SELECT COUNT(*) FROM published")).fetchone())[0]
        sch = (await (await conn.execute("SELECT COUNT(*) FROM schedules")).fetchone())[0]
        app = (await (await conn.execute("SELECT COUNT(*) FROM batch_posts WHERE status='approved'")).fetchone())[0]
    await bot.send_message(callback.from_user.id, f"📊 آمار:\nمنابع: {src}\nمنتشر شده: {pub}\nتایید شده در انتظار: {app}\nزمان‌بندی شده: {sch}", reply_markup=menu_kb())
    await callback.answer()

@router.callback_query(F.data == "add_source")
async def cb_add_source(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "نام‌های کاربری منابع را بفرست:", reply_markup=menu_kb())
    await state.set_state(States.add_source)
    await callback.answer()

@router.message(States.add_source)
async def msg_add_source(message: types.Message, state: FSMContext):
    items = message.text.replace(',', ' ').split()
    added, dup = 0, 0
    async with aiosqlite.connect('auto_pub.db') as conn:
        for s in items:
            s = s.strip()
            if s.startswith('http'): s = s.split('/')[-1]
            s = s.lstrip('@').strip('/').rstrip('.')
            if not s: continue
            try:
                await conn.execute("INSERT INTO sources (username) VALUES (?)", (s,))
                added += 1
            except sqlite3.IntegrityError:
                dup += 1
        await conn.commit()
    await message.answer(f"✅ {added} منبع اضافه شد | {dup} تکراری.", reply_markup=menu_kb())
    await state.clear()

@router.callback_query(F.data == "list_sources")
async def cb_list_sources(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        rows = await (await conn.execute("SELECT id, username FROM sources")).fetchall()
    if not rows:
        await bot.send_message(callback.from_user.id, "⚠️ منبعی ثبت نشده.", reply_markup=menu_kb())
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"❌ {r[1]}", callback_data=f"del_src_{r[0]}")] for r in rows])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")])
        await bot.send_message(callback.from_user.id, "📋 منابع:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("del_src_"))
async def cb_del_src(callback: types.CallbackQuery):
    sid = int(callback.data.split("_")[2])
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("DELETE FROM sources WHERE id=?", (sid,))
        await conn.commit()
    await callback.answer("✅ حذف شد.")

def settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱️ بازه", callback_data="set_interval"), InlineKeyboardButton(text="📢 کانال", callback_data="set_main_channel")],
        [InlineKeyboardButton(text="📝 فوتر", callback_data="set_footer"), InlineKeyboardButton(text="🎨 فرمت", callback_data="set_format")],
        [InlineKeyboardButton(text="⭐ ایموجی اول", callback_data="set_emoji_tag"), InlineKeyboardButton(text="⭐ روشن/خاموش", callback_data="toggle_emoji")],
        [InlineKeyboardButton(text="✨ ایموجی کپشن", callback_data="set_cap_emoji"), InlineKeyboardButton(text="✨ روشن/خاموش", callback_data="toggle_cap_emoji")],
        [InlineKeyboardButton(text="🔢 تعداد ایموجی کپشن", callback_data="set_cap_emoji_count")],
        [InlineKeyboardButton(text="🆔 ایموجی ایدی", callback_data="set_id_emoji")],
        [InlineKeyboardButton(text="⚠️ ایموجی ایدی اسپویلر", callback_data="set_sp_id_emoji")],
        [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")],
    ])

async def send_settings(callback):
    vals = {}
    for k in ['min_interval','max_interval','main_channel','footer','format','emoji','cap_emoji']:
        vals[k] = await db.get(k)
    text = f"⚙️ تنظیمات:\nبازه: {vals['min_interval']}-{vals['max_interval']} دقیقه\nکانال: {vals['main_channel']}\nفرمت: {vals['format']}\nفوتر: {vals['footer'] or '(خالی)'}\n⭐ ایموجی اول کپشن: {'✅' if vals['emoji']=='1' else '❌'}\n✨ ایموجی کپشن: {'✅' if vals['cap_emoji']=='1' else '❌'}"
    try:
        await callback.message.edit_text(text, reply_markup=settings_kb())
    except Exception:
        await bot.send_message(callback.from_user.id, text, reply_markup=settings_kb())

@router.callback_query(F.data == "settings")
async def cb_settings(callback: types.CallbackQuery):
    await send_settings(callback)
    await callback.answer()

@router.callback_query(F.data == "set_interval")
async def cb_set_interval(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "بازه به دقیقه: min max")
    await state.set_state(States.set_interval)
    await callback.answer()

@router.message(States.set_interval)
async def msg_set_interval(message: types.Message, state: FSMContext):
    try:
        a, b = map(int, message.text.split())
        await db.set('min_interval', a); await db.set('max_interval', b)
        await message.answer("✅ ذخیره شد.", reply_markup=menu_kb())
    except Exception:
        await message.answer("❌ فرمت اشتباه.")
    await state.clear()

@router.callback_query(F.data == "set_batch_size")
async def cb_set_batch_size(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "تعداد پست هر دسته:")
    await state.set_state(States.set_batch_size)
    await callback.answer()

@router.message(States.set_batch_size)
async def msg_set_batch_size(message: types.Message, state: FSMContext):
    try:
        await db.set('batch_size', int(message.text))
        await message.answer("✅ ذخیره شد.", reply_markup=menu_kb())
    except Exception:
        await message.answer("❌ عدد نامعتبر.")
    await state.clear()

@router.callback_query(F.data == "set_main_channel")
async def cb_set_main_channel(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "آیدی کانال اصلی:")
    await state.set_state(States.set_main_channel)
    await callback.answer()

@router.message(States.set_main_channel)
async def msg_set_main_channel(message: types.Message, state: FSMContext):
    await db.set('main_channel', message.text.strip())
    await message.answer("✅ ذخیره شد.", reply_markup=menu_kb())
    await state.clear()

@router.callback_query(F.data == "set_footer")
async def cb_set_footer(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "متن فوتر پیش‌فرض (اختیاری):")
    await state.set_state(States.set_footer)
    await callback.answer()

@router.message(States.set_footer)
async def msg_set_footer(message: types.Message, state: FSMContext):
    await db.set('footer', extract_tags(message))
    await message.answer("✅ ذخیره شد.", reply_markup=menu_kb())
    await state.clear()

@router.callback_query(F.data == "set_format")
async def cb_set_format(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bold", callback_data="fmt_bold")],
        [InlineKeyboardButton(text="Bold+Blockquote", callback_data="fmt_bold_blockquote")],
        [InlineKeyboardButton(text="Blockquote", callback_data="fmt_blockquote")],
        [InlineKeyboardButton(text="ساده", callback_data="fmt_plain")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings")],
    ])
    await bot.send_message(callback.from_user.id, "فرمت پیش‌فرض:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("fmt_"))
async def cb_fmt(callback: types.CallbackQuery):
    await db.set('format', callback.data[4:])
    await callback.answer("✅ ذخیره شد.")

@router.callback_query(F.data == "toggle_emoji")
async def cb_emoji(callback: types.CallbackQuery):
    cur = await db.get('emoji')
    await db.set('emoji', '0' if cur == '1' else '1')
    await callback.answer("✅ تغییر کرد.")
    await send_settings(callback)

@router.callback_query(F.data == "toggle_cap_emoji")
async def cb_toggle_cap_emoji(callback: types.CallbackQuery):
    cur = await db.get('cap_emoji')
    await db.set('cap_emoji', '0' if cur == '1' else '1')
    await callback.answer("✅ تغییر کرد.")
    await send_settings(callback)

async def show_emoji_view(chat_id):
    tag = (await db.get('emoji_tag')) or ''
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش", callback_data="edit_emoji_tag"), InlineKeyboardButton(text="🗑 حذف", callback_data="del_emoji_tag")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings")],
    ])
    await bot.send_message(chat_id, f"ایموجی‌های فعلی:\n{tag or '(خالی)'}", reply_markup=kb)

@router.callback_query(F.data == "set_emoji_tag")
async def cb_set_emoji_tag(callback: types.CallbackQuery):
    await show_emoji_view(callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "edit_emoji_tag")
async def cb_edit_emoji_tag(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, 'خود ایموجی(های) پریمیوم را بفرست (از بخش پریمیوم کیبورد ایموجی) — آیدی خودکار استخراج می‌شود:')
    await state.set_state(States.set_emoji_tag)
    await callback.answer()

@router.callback_query(F.data == "del_emoji_tag")
async def cb_del_emoji_tag(callback: types.CallbackQuery):
    await db.set('emoji_tag', '')
    await callback.answer("✅ حذف شد.")
    await show_emoji_view(callback.from_user.id)

async def show_cap_view(chat_id):
    tag = (await db.get('cap_emoji_tag')) or ''
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش", callback_data="edit_cap_emoji"), InlineKeyboardButton(text="🗑 حذف", callback_data="del_cap_emoji")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings")],
    ])
    await bot.send_message(chat_id, f"ایموجی‌های کپشن فعلی:\n{tag or '(خالی)'}", reply_markup=kb)

@router.callback_query(F.data == "set_cap_emoji")
async def cb_set_cap_emoji(callback: types.CallbackQuery):
    await show_cap_view(callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "edit_cap_emoji")
async def cb_edit_cap_emoji(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "ایموجی‌های پریمیوم کپشن را بفرست:")
    await state.set_state(States.set_cap_emoji)
    await callback.answer()

@router.callback_query(F.data == "del_cap_emoji")
async def cb_del_cap_emoji(callback: types.CallbackQuery):
    await db.set('cap_emoji_tag', '')
    await callback.answer("✅ حذف شد.")
    await show_cap_view(callback.from_user.id)

@router.message(States.set_cap_emoji)
async def msg_set_cap_emoji(message: types.Message, state: FSMContext):
    tags = []
    if message.entities:
        u = (message.text or '').encode('utf-16-le')
        for e in message.entities:
            if e.type == 'custom_emoji' and e.custom_emoji_id:
                try:
                    ch = u[e.offset*2:(e.offset+e.length)*2].decode('utf-16-le', 'ignore') or '⭐'
                except Exception:
                    ch = '⭐'
                tags.append(f'<tg-emoji emoji-id="{e.custom_emoji_id}">{ch}</tg-emoji>')
    if not tags and message.text:
        tags = [message.text.strip()]
    tag = "|||||".join(tags) if tags else message.text.strip()
    await db.set('cap_emoji_tag', tag)
    await db.set('cap_emoji', '1')
    await message.answer(f"✅ ذخیره و فعال شد:\n{tag}", reply_markup=menu_kb())
    await state.clear()

async def show_id_view(chat_id):
    tag = (await db.get('id_emoji_tag')) or ''
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش", callback_data="edit_id_emoji"), InlineKeyboardButton(text="🗑 حذف", callback_data="del_id_emoji")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings")],
    ])
    await bot.send_message(chat_id, f"ایموجی ایدی فعلی:\n{tag or '(خالی)'}", reply_markup=kb)

@router.callback_query(F.data == "set_id_emoji")
async def cb_set_id_emoji(callback: types.CallbackQuery):
    await show_id_view(callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "edit_id_emoji")
async def cb_edit_id_emoji(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "ایموجی پریمیوم برای خط ایدی کانال بفرست:")
    await state.set_state(States.set_id_emoji)
    await callback.answer()

@router.callback_query(F.data == "del_id_emoji")
async def cb_del_id_emoji(callback: types.CallbackQuery):
    await db.set('id_emoji_tag', '')
    await callback.answer("✅ حذف شد.")
    await show_id_view(callback.from_user.id)

@router.message(States.set_id_emoji)
async def msg_set_id_emoji(message: types.Message, state: FSMContext):
    tags = []
    if message.entities:
        u = (message.text or '').encode('utf-16-le')
        for e in message.entities:
            if e.type == 'custom_emoji' and e.custom_emoji_id:
                try:
                    ch = u[e.offset*2:(e.offset+e.length)*2].decode('utf-16-le', 'ignore') or '⭐'
                except Exception:
                    ch = '⭐'
                tags.append(f'<tg-emoji emoji-id="{e.custom_emoji_id}">{ch}</tg-emoji>')
    tag = " ".join(tags) if tags else message.text.strip()
    await db.set('id_emoji_tag', tag)
    await message.answer(f"✅ ذخیره شد:\n{tag}", reply_markup=menu_kb())
    await state.clear()

@router.message(States.set_emoji_tag)
async def msg_set_emoji_tag(message: types.Message, state: FSMContext):
    tags = []
    if message.entities:
        u = (message.text or '').encode('utf-16-le')
        for e in message.entities:
            if e.type == 'custom_emoji' and e.custom_emoji_id:
                try:
                    ch = u[e.offset*2:(e.offset+e.length)*2].decode('utf-16-le', 'ignore') or '⭐'
                except Exception:
                    ch = '⭐'
                tags.append(f'<tg-emoji emoji-id="{e.custom_emoji_id}">{ch}</tg-emoji>')
    tag = " ".join(tags) if tags else message.text.strip()
    await db.set('emoji_tag', tag)
    await message.answer(f"✅ ذخیره شد:\n{tag}", reply_markup=menu_kb())
    await state.clear()

async def get_media_path(source, msg_id):
    path = os.path.join(MEDIA_DIR, f"{source.strip('@')}_{msg_id}.jpg")
    if os.path.exists(path): return path
    if not telethon_client.is_connected():
        await telethon_client.connect()
    try:
        entity = await telethon_client.get_entity(source)
        msg = await telethon_client.get_messages(entity, ids=msg_id)
        if msg and msg.media:
            await telethon_client.download_media(msg, path)
            return path if os.path.exists(path) else None
    except Exception as e:
        logger.error(f"media dl: {e}")
    return None

@router.callback_query(F.data == "new_batch")
async def cb_new_batch(callback: types.CallbackQuery):
    await callback.answer("در حال ساخت دسته...")
    await generate_batch(callback.from_user.id)

async def generate_batch(chat_id):
    if not telethon_client.is_connected():
        await telethon_client.connect()
    async with aiosqlite.connect('auto_pub.db') as conn:
        sources = await (await conn.execute("SELECT id, username FROM sources")).fetchall()
        used = set()
        for r in await (await conn.execute("SELECT source, msg_id FROM published")).fetchall():
            used.add((r[0], r[1]))
        for r in await (await conn.execute("SELECT source, msg_id FROM batch_posts")).fetchall():
            used.add((r[0], r[1]))
    if not sources:
        return await bot.send_message(chat_id, "⚠️ منبعی نیست.", reply_markup=menu_kb())
    pool = []
    for sid, uname in sources:
        uname = uname.strip()
        if uname.startswith('http'): uname = uname.split('/')[-1]
        uname = uname.lstrip('@').strip('/').rstrip('.')
        photos, textpost = [], None
        try:
            entity = await telethon_client.get_entity(uname)
            async for m in telethon_client.iter_messages(entity, limit=100):
                if not m: continue
                if (uname, m.id) in used: continue
                if isinstance(m.media, MessageMediaPhoto) and clean_text(m.text):
                    photos.append((uname, m.id, clean_text(m.text)))
                    if len(photos) >= 2: break
                elif not m.media and m.text and textpost is None:
                    textpost = (uname, m.id, clean_text(m.text))
        except Exception as e:
            logger.error(f"fetch {uname}: {e}")
        pool.extend(photos if photos else ([textpost] if textpost else []))
    if not pool:
        return await bot.send_message(chat_id, "⚠️ پستی پیدا نشد.", reply_markup=menu_kb())
    size = int(await db.get('batch_size'))
    chosen = random.sample(pool, min(size, len(pool)))
    async with aiosqlite.connect('auto_pub.db') as conn:
        cur = await conn.execute("INSERT INTO batches (admin_id, created_at) VALUES (?, ?)", (chat_id, datetime.now().isoformat()))
        batch_id = cur.lastrowid
        ids = []
        for uname, mid, txt in chosen:
            cur2 = await conn.execute("INSERT INTO batch_posts (batch_id, source, msg_id, text, media) VALUES (?,?,?,?,1)", (batch_id, uname, mid, txt))
            ids.append(cur2.lastrowid)
        await conn.commit()
    await bot.send_message(chat_id, f"🎲 {len(ids)} پست برای بررسی:", reply_markup=menu_kb())
    for pid in ids:
        await send_preview(chat_id, pid)

async def send_preview(chat_id, pid):
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT source, msg_id, text, media, is_spoiler FROM batch_posts WHERE id=?", (pid,))).fetchone()
    if not row: return
    source, mid, text, media, is_spoiler = row
    kb = preview_kb(pid, is_spoiler)
    if media:
        path = await get_media_path(source, mid)
        if path:
            await bot.send_photo(chat_id, FSInputFile(path), caption=text or None, reply_markup=kb)
            return
    await bot.send_message(chat_id, text or "(بدون متن)", reply_markup=kb)

async def after_review(chat_id, batch_id):
    async with aiosqlite.connect('auto_pub.db') as conn:
        left = (await (await conn.execute("SELECT COUNT(*) FROM batch_posts WHERE batch_id=? AND status='pending'", (batch_id,))).fetchone())[0]
    if left == 0:
        await show_finalize(chat_id)

@router.callback_query(F.data.startswith("approve_"))
async def cb_approve(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[1])
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT batch_id FROM batch_posts WHERE id=?", (pid,))).fetchone()
        await conn.execute("UPDATE batch_posts SET status='approved' WHERE id=?", (pid,))
        await conn.commit()
    try: await callback.message.delete()
    except Exception: pass
    await after_review(callback.from_user.id, row[0])
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def cb_reject(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[1])
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT batch_id FROM batch_posts WHERE id=?", (pid,))).fetchone()
        await conn.execute("UPDATE batch_posts SET status='rejected' WHERE id=?", (pid,))
        await conn.commit()
    try: await callback.message.delete()
    except Exception: pass
    await after_review(callback.from_user.id, row[0])
    await callback.answer()

async def show_finalize(chat_id):
    async with aiosqlite.connect('auto_pub.db') as conn:
        n = (await (await conn.execute("SELECT COUNT(*) FROM batch_posts WHERE status='approved'")).fetchone())[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 تغییر فونت کلی", callback_data="gfmt"), InlineKeyboardButton(text="📝 فوتر کلی", callback_data="gfoot")],
        [InlineKeyboardButton(text="✏️ ویرایش تکی پست‌ها", callback_data="edit_list")],
        [InlineKeyboardButton(text="🚀 انتشار پست‌های نهایی", callback_data="pub_final"), InlineKeyboardButton(text="📅 زمان‌بندی همه", callback_data="sched_all")],
        [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")],
    ])
    await bot.send_message(chat_id, f"✅ {n} پست تایید شده. تغییرات نهایی:", reply_markup=kb)

@router.callback_query(F.data == "finalize")
async def cb_finalize(callback: types.CallbackQuery):
    await show_finalize(callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "gfmt")
async def cb_gfmt(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bold", callback_data="gfset_bold")],
        [InlineKeyboardButton(text="Bold+Blockquote", callback_data="gfset_bold_blockquote")],
        [InlineKeyboardButton(text="Blockquote", callback_data="gfset_blockquote")],
        [InlineKeyboardButton(text="ساده", callback_data="gfset_plain")],
        [InlineKeyboardButton(text="🔙", callback_data="finalize")],
    ])
    await bot.send_message(callback.from_user.id, "فونت کلی پست‌های تایید شده:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("gfset_"))
async def cb_gfset(callback: types.CallbackQuery):
    mode = callback.data.split("_", 1)[1]
    await db.set('format', mode)
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET fmt=? WHERE status='approved'", (mode,))
        await conn.commit()
    await callback.answer("✅ فونت کلی اعمال شد.")
    await show_finalize(callback.from_user.id)

@router.callback_query(F.data == "gfoot")
async def cb_gfoot(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "متن فوتر کلی را بفرست (می‌توانی ایموجی پریمیوم هم بگذاری):")
    await state.set_state(States.set_gfoot)
    await callback.answer()

@router.message(States.set_gfoot)
async def msg_gfoot(message: types.Message, state: FSMContext):
    t = extract_tags(message)
    await db.set('footer', t)
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET foot=? WHERE status='approved'", (t,))
        await conn.commit()
    await message.answer("✅ آیدی/فوتر کلی اعمال شد.", reply_markup=menu_kb())
    await show_finalize(message.chat.id)
    await state.clear()

@router.callback_query(F.data == "edit_list")
async def cb_edit_list(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        rows = await (await conn.execute("SELECT id, text FROM batch_posts WHERE status='approved' ORDER BY id")).fetchall()
    if not rows:
        await bot.send_message(callback.from_user.id, "⚠️ پست تایید شده‌ای نیست.", reply_markup=menu_kb())
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"✏️ #{r[0]} {(r[1] or '')[:25]}", callback_data=f"edit_{r[0]}")] for r in rows])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 نهایی‌سازی", callback_data="finalize")])
        await bot.send_message(callback.from_user.id, "✏️ پست را انتخاب کن:", reply_markup=kb)
    await callback.answer()

async def show_edit(chat_id, pid):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 فونت", callback_data=f"pfmt_{pid}"), InlineKeyboardButton(text="📝 فوتر", callback_data=f"pfoot_{pid}")],
        [InlineKeyboardButton(text="✏️ ویرایش متن", callback_data=f"ptext_{pid}")],
        [InlineKeyboardButton(text="🔙 نهایی‌سازی", callback_data="finalize")],
    ])
    await bot.send_message(chat_id, f"✏️ ویرایش پست #{pid}:", reply_markup=kb)

@router.callback_query(F.data.startswith("edit_"))
async def cb_edit(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[1])
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT source, msg_id, text, media FROM batch_posts WHERE id=?", (pid,))).fetchone()
    if row:
        source, mid, text, media = row
        if media:
            path = await get_media_path(source, mid)
            if path:
                await bot.send_photo(callback.from_user.id, FSInputFile(path), caption=text or None)
            else:
                await bot.send_message(callback.from_user.id, text or "")
        else:
            await bot.send_message(callback.from_user.id, text or "")
    await show_edit(callback.from_user.id, pid)
    await callback.answer()

@router.callback_query(F.data.startswith("pfmt_"))
async def cb_pfmt(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bold", callback_data=f"pfset_{pid}_bold")],
        [InlineKeyboardButton(text="Bold+Blockquote", callback_data=f"pfset_{pid}_bold_blockquote")],
        [InlineKeyboardButton(text="Blockquote", callback_data=f"pfset_{pid}_blockquote")],
        [InlineKeyboardButton(text="ساده", callback_data=f"pfset_{pid}_plain")],
        [InlineKeyboardButton(text="🔙", callback_data=f"edit_{pid}")],
    ])
    await bot.send_message(callback.from_user.id, "فونت این پست:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("pfset_"))
async def cb_pfset(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[1])
    mode = callback.data.split("_", 2)[2]
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET fmt=? WHERE id=?", (mode, pid))
        await conn.commit()
    await callback.answer("✅ اعمال شد.")
    await show_edit(callback.from_user.id, pid)

@router.callback_query(F.data.startswith("pfoot_"))
async def cb_pfoot(callback: types.CallbackQuery, state: FSMContext):
    pid = int(callback.data.split("_")[1])
    await state.update_data(pid=pid)
    await bot.send_message(callback.from_user.id, "فوتر این پست را بفرست:")
    await state.set_state(States.set_pfoot)
    await callback.answer()

@router.message(States.set_pfoot)
async def msg_pfoot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get('pid')
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET foot=? WHERE id=?", (extract_tags(message), pid))
        await conn.commit()
    await message.answer("✅ اعمال شد.", reply_markup=menu_kb())
    await state.clear()

@router.callback_query(F.data.startswith("ptext_"))
async def cb_ptext(callback: types.CallbackQuery, state: FSMContext):
    pid = int(callback.data.split("_")[1])
    await state.update_data(pid=pid)
    await bot.send_message(callback.from_user.id, "متن/کپشن جدید این پست را بفرست:")
    await state.set_state(States.set_ptext)
    await callback.answer()

@router.message(States.set_ptext)
async def msg_ptext(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get('pid')
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET text=? WHERE id=?", (extract_tags(message), pid))
        await conn.commit()
    await message.answer("✅ متن اعمال شد.", reply_markup=menu_kb())
    await state.clear()

@router.callback_query(F.data == "pub_final")
async def cb_pub_final(callback: types.CallbackQuery):
    await callback.answer("در حال انتشار...")
    asyncio.create_task(publish_all_approved(callback.from_user.id))

async def publish_all_approved(chat_id):
    global PUBLISH_ERR, PREMIUM_ERR, DBG
    try:
        PREMIUM_ERR = None
        async with aiosqlite.connect('auto_pub.db') as conn:
            ids = [r[0] for r in await (await conn.execute("SELECT id FROM batch_posts WHERE status='approved' ORDER BY id")).fetchall()]
        n = 0
        for pid in ids:
            if await do_publish(pid): n += 1
            await asyncio.sleep(2)
        msg = f"✅ {n} از {len(ids)} پست نهایی منتشر شد."
        if n < len(ids): msg += f"\n❌ خطا: {PUBLISH_ERR or 'نامشخص'}"
        elif PREMIUM_ERR: msg += f"\n⚠️ اکانت پریمیوم نفرستاد ({PREMIUM_ERR[:150]}) — پست‌ها بدون ایموجی پریمیوم رفتند. اکانت پریمیوم را عضو کانال کن!"
        DBG_LIST.clear()
        msg += "\n🔍 " + " | ".join(DBG_LIST[-8:])
        await bot.send_message(chat_id, msg, reply_markup=menu_kb())
    except Exception as e:
        PUBLISH_ERR = str(e)
        logger.error(f"publish_all: {e}")
        await bot.send_message(chat_id, f"❌ خطا: {e}", reply_markup=menu_kb())

async def do_publish(pid):
    global PUBLISH_ERR, PREMIUM_ERR, DBG
    NL = chr(10)
    try:
        async with aiosqlite.connect('auto_pub.db') as conn:
            row = await (await conn.execute("SELECT source, msg_id, text, media, fmt, foot, is_spoiler FROM batch_posts WHERE id=?", (pid,))).fetchone()
        if not row:
            PUBLISH_ERR = "پست پیدا نشد"
            return False
        source, mid, text, media, pfmt, pfoot, is_spoiler = row
        is_spoiler = bool(is_spoiler)
        fmt = pfmt or await db.get('format')
        footer = pfoot if pfoot is not None else await db.get('footer')
        emoji = await db.get('emoji') == '1'
        ch = (await db.get('main_channel')).strip()
        try: channel = int(ch)
        except ValueError: channel = ch
        def tlen(s): return len(s.encode('utf-16-le')) // 2
        def strip_prem(s):
            return re.sub(r'<tg-emoji[^>]*>([^<]*)</tg-emoji>', lambda mm: mm.group(1), s)
        body_full = format_text(text or '', fmt)
        cap_footer = ''
        if (await db.get('cap_emoji')) == '1' and not is_spoiler:
            pool = list(dict.fromkeys(t.strip() for t in ((await db.get('cap_emoji_tag')) or '').split('|||||') if t.strip()))
            if pool:
                cap_footer = NL + ''.join(random.sample(pool, min(int(await db.get('cap_emoji_count') or 5), len(pool), 10)))
        tag = (await db.get('emoji_tag')) or ''
        pre = (tag + " ") if (emoji and tag) else ""
        ch_name = str(channel)
        try:
            chat = await bot.get_chat(channel)
            if getattr(chat, 'username', None): ch_name = '@' + chat.username
        except Exception:
            try:
                if not telethon_client.is_connected(): await telethon_client.connect()
                ent = await telethon_client.get_entity(channel)
                if getattr(ent, 'username', None): ch_name = '@' + ent.username
            except Exception:
                pass
        idtag = (await db.get('id_emoji_tag')) or ''
        m = re.match(r'<tg-emoji[^>]*>.*?</tg-emoji>', idtag)
        if not m: m = re.match(r'<tg-emoji[^>]*>.*?</tg-emoji>', tag)
        em = m.group(0) if m else ''
        em_used = ((await db.get('sp_id_emoji')) or '🆔') if is_spoiler else em
        ch_part = f"{NL}{NL}<blockquote>{em_used} <b>{ch_name}</b></blockquote>"
        foot_part = f"{NL}{NL}<blockquote>{footer}</blockquote>" if footer else ""
        allowed = 1024 - tlen(pre) - tlen(foot_part) - tlen(ch_part) - tlen(cap_footer) - 60
        body = truncate_html(body_full, max(200, allowed))
        def build_caption(b):
            if media:
                cb = b + cap_footer
            else:
                cb = (f"<tg-spoiler>{b}</tg-spoiler>" if is_spoiler else b) + cap_footer
            return pre + cb + foot_part + ch_part
        caption = build_caption(body)
        guard = 0
        while tlen(caption) > 1024 and guard < 10:
            allowed -= 60
            body = truncate_html(body_full, max(100, allowed))
            caption = build_caption(body)
            guard += 1
        path = None
        if media:
            path = await get_media_path(source, mid)
        sent = False
        sent_via = 'none'
        prem_exists = os.path.exists('premium_session.session')
        if is_spoiler and path:
            cap2 = strip_prem(caption)
            try:
                await bot.send_photo(channel, FSInputFile(path), caption=cap2, parse_mode=ParseMode.HTML, has_spoiler=True)
                sent = True
                sent_via = 'bot-photo'
            except Exception as e1:
                PUBLISH_ERR = str(e1)
        elif is_spoiler and not path:
            def u16(s): return len(s.encode('utf-16-le')) // 2
            head = strip_prem(pre)
            P = text or ''
            foot_text = strip_prem(footer) if footer else ''
            id_em = strip_prem(em_used) if em_used else '🆔'
            NL2 = NL + NL
            for ent_set in (['bold','blockquote','spoiler'], ['spoiler']):
                if sent: break
                ents = []
                cap = head + P
                off = u16(head)
                L = u16(P)
                for t in ent_set:
                    ents.append(types.MessageEntity(type=t, offset=off, length=L))
                if foot_text:
                    cap += NL2
                    f_off = u16(cap)
                    cap += foot_text
                    ents.append(types.MessageEntity(type='blockquote', offset=f_off, length=u16(foot_text)))
                cap += NL2
                idpart = id_em + ' ' + ch_name
                id_off = u16(cap)
                cap += idpart
                ents.append(types.MessageEntity(type='blockquote', offset=id_off, length=u16(idpart)))
                ents.append(types.MessageEntity(type='bold', offset=u16(cap) - u16(ch_name), length=u16(ch_name)))
                try:
                    await bot.send_message(channel, cap, entities=ents)
                    sent = True
                    sent_via = 'bot-text-spoiler-' + '+'.join(ent_set)
                except Exception as e1:
                    PUBLISH_ERR = str(e1)
        else:
            if '<tg-emoji' in caption and prem_exists:
                for attempt in range(3):
                    try:
                        if not premium_client.is_connected(): await premium_client.connect()
                        if path:
                            await premium_client.send_file(channel, path, caption=caption, parse_mode='html')
                        else:
                            await premium_client.send_message(channel, caption, parse_mode='html')
                        sent = True
                        sent_via = 'premium'
                        break
                    except Exception as e2:
                        PREMIUM_ERR = str(e2)
                        await asyncio.sleep(2)
            if not sent:
                cap2 = strip_prem(caption)
                try:
                    if path:
                        await bot.send_photo(channel, FSInputFile(path), caption=cap2, parse_mode=ParseMode.HTML)
                    else:
                        await bot.send_message(channel, cap2, parse_mode=ParseMode.HTML)
                    sent = True
                    sent_via = 'bot'
                except Exception as e1:
                    PUBLISH_ERR = str(e1)
        if not sent:
            plain = re.sub(r'<[^>]+>', '', caption)
            if path:
                await bot.send_photo(channel, FSInputFile(path), caption=plain, has_spoiler=is_spoiler)
            else:
                await bot.send_message(channel, plain)
            sent_via = 'plain'
        DBG_LIST.append(f"#{pid} sp={int(is_spoiler)} cap={int(bool(cap_footer))} via={sent_via}")
        async with aiosqlite.connect('auto_pub.db') as conn:
            await conn.execute("UPDATE batch_posts SET status='published' WHERE id=?", (pid,))
            await conn.execute("INSERT OR IGNORE INTO published (source, msg_id, published_at) VALUES (?,?,?)", (source, mid, datetime.now().isoformat()))
            await conn.commit()
        return True
    except Exception as ex:
        PUBLISH_ERR = str(ex)
        logger.error(f"publish error: {ex}")
        return False

@router.callback_query(F.data == "sched_all")
async def cb_sched_all(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "زمان برای همه پست‌های تایید شده:\nمثال: 16:00 today")
    await state.set_state(States.set_time_all)
    await callback.answer()

@router.message(States.set_time_all)
async def msg_set_time_all(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        h, mi = map(int, parts[0].split(':'))
        day = parts[1] if len(parts) > 1 else 'today'
        target = datetime.now().replace(hour=h, minute=mi, second=0, microsecond=0)
        if day == 'tomorrow': target += timedelta(days=1)
        elif target <= datetime.now(): target += timedelta(days=1)
        channel = int(await db.get('main_channel'))
        async with aiosqlite.connect('auto_pub.db') as conn:
            ids = [r[0] for r in await (await conn.execute("SELECT id FROM batch_posts WHERE status='approved'")).fetchall()]
            for pid in ids:
                await conn.execute("INSERT INTO schedules (post_id, scheduled_at, target_chat) VALUES (?,?,?)", (pid, target.isoformat(), channel))
                await conn.execute("UPDATE batch_posts SET status='scheduled' WHERE id=?", (pid,))
            await conn.commit()
        await message.answer(f"✅ {len(ids)} پست برای {target.strftime('%m-%d %H:%M')} زمان‌بندی شد.", reply_markup=menu_kb())
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")
    await state.clear()

@router.callback_query(F.data == "approved_list")
async def cb_approved(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        app = await (await conn.execute("SELECT id, text FROM batch_posts WHERE status='approved' ORDER BY id DESC LIMIT 15")).fetchall()
        sch = await (await conn.execute("SELECT b.id, b.text, s.scheduled_at FROM batch_posts b JOIN schedules s ON s.post_id=b.id ORDER BY s.scheduled_at LIMIT 15")).fetchall()
    lines = ["✅ تایید شده در انتظار انتشار:"] + [f"• #{r[0]} {(r[1] or '')[:35]}" for r in app]
    lines += ["", "📅 زمان‌بندی شده:"] + [f"• #{r[0]} ⏰{r[2][11:16]} {(r[1] or '')[:25]}" for r in sch]
    if not app and not sch: lines = ["لیست خالی است — همه منتشر شده‌اند ✅"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧹 پاک کردن لیست تایید شده", callback_data="clear_approved")], [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")]])
    await bot.send_message(callback.from_user.id, "\n".join(lines), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "clear_approved")
async def cb_clear_approved(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("UPDATE batch_posts SET status='rejected' WHERE status='approved'")
        await conn.commit()
    await callback.answer("✅ لیست خالی شد.")
    await show_menu(callback.from_user.id)

@router.callback_query(F.data == "schedules")
async def cb_schedules(callback: types.CallbackQuery):
    async with aiosqlite.connect('auto_pub.db') as conn:
        rows = await (await conn.execute("SELECT s.id, s.scheduled_at, b.text FROM schedules s JOIN batch_posts b ON b.id=s.post_id ORDER BY s.scheduled_at")).fetchall()
    if not rows:
        await bot.send_message(callback.from_user.id, "⚠️ خالی است.", reply_markup=menu_kb())
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"🚀 {r[1][11:16]} {(r[2] or '')[:15]}", callback_data=f"now_sch_{r[0]}"), InlineKeyboardButton(text="❌", callback_data=f"del_sch_{r[0]}")] for r in rows])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🚀 انتشار همه", callback_data="pub_all_sch")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")])
        await bot.send_message(callback.from_user.id, "📅 زمان‌بندی‌ها:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("del_sch_"))
async def cb_del_sch(callback: types.CallbackQuery):
    sid = int(callback.data.split("_")[2])
    async with aiosqlite.connect('auto_pub.db') as conn:
        await conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
        await conn.commit()
    await callback.answer("✅ حذف شد.")

@router.callback_query(F.data.startswith("now_sch_"))
async def cb_now_sch(callback: types.CallbackQuery):
    await callback.answer("در حال انتشار...")
    sid = int(callback.data.split("_")[2])
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT post_id FROM schedules WHERE id=?", (sid,))).fetchone()
        await conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
        await conn.commit()
    ok = False
    if row: ok = await do_publish(row[0])
    await bot.send_message(callback.from_user.id, "✅ منتشر شد." if ok else "❌ خطا.", reply_markup=menu_kb())

@router.callback_query(F.data == "pub_all_sch")
async def cb_pub_all_sch(callback: types.CallbackQuery):
    await callback.answer("در حال انتشار...")
    asyncio.create_task(publish_all_scheduled(callback.from_user.id))

async def publish_all_scheduled(chat_id):
    global PUBLISH_ERR, PREMIUM_ERR, DBG
    try:
        async with aiosqlite.connect('auto_pub.db') as conn:
            rows = await (await conn.execute("SELECT id, post_id FROM schedules ORDER BY id")).fetchall()
        n = 0
        for sid, pid in rows:
            if await do_publish(pid): n += 1
            async with aiosqlite.connect('auto_pub.db') as conn:
                await conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
                await conn.commit()
        msg = f"✅ {n} از {len(rows)} پست منتشر شد."
        if n < len(rows): msg += f"\n❌ خطا: {PUBLISH_ERR or 'نامشخص'}"
        elif PREMIUM_ERR: msg += f"\n⚠️ اکانت پریمیوم نفرستاد ({PREMIUM_ERR[:150]}) — بدون ایموجی پریمیوم. اکانت پریمیوم را عضو کانال کن!"
        await bot.send_message(chat_id, msg, reply_markup=menu_kb())
    except Exception as e:
        PUBLISH_ERR = str(e)
        logger.error(f"publish_all_sch: {e}")
        await bot.send_message(chat_id, f"❌ خطا: {e}", reply_markup=menu_kb())

async def scheduler():
    while True:
        try:
            async with aiosqlite.connect('auto_pub.db') as conn:
                due = await (await conn.execute("SELECT id, post_id FROM schedules WHERE scheduled_at <= ?", (datetime.now().isoformat(),))).fetchall()
                for sid, pid in due:
                    await do_publish(pid)
                    await conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
                await conn.commit()
        except Exception as e:
            logger.error(f"scheduler: {e}")
        await asyncio.sleep(30)

async def auto_batch():
    while True:
        lo = int(await db.get('min_interval')); hi = int(await db.get('max_interval'))
        await asyncio.sleep(random.randint(lo, hi) * 60)
        for aid in ADMINS:
            try: await generate_batch(aid)
            except Exception as e: logger.error(f"auto batch: {e}")

async def main():
    await db.init()
    await telethon_client.start()
    if os.path.exists('premium_session.session'):
        try:
            await premium_client.start()
            logger.info("premium client ready")
        except Exception as e:
            logger.error(f"premium start: {e}")
    asyncio.create_task(scheduler())
    asyncio.create_task(auto_batch())
    await dp.start_polling(bot)


@router.callback_query(F.data == "set_cap_emoji_count")
async def cb_set_cap_emoji_count(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "تعداد ایموجی‌های کپشن که رندوم انتخاب شوند (مثلا 5):")
    await state.set_state(States.set_cap_emoji_count)
    await callback.answer()

@router.message(States.set_cap_emoji_count)
async def msg_set_cap_emoji_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1: count = 1
        await db.set('cap_emoji_count', count)
        await message.answer(f"✅ ذخیره شد: {count} ایموجی.", reply_markup=menu_kb())
    except Exception:
        await message.answer("❌ عدد نامعتبر.")
    await state.clear()

def preview_kb(pid, is_spoiler):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تایید", callback_data=f"approve_{pid}"), InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{pid}")],
        [InlineKeyboardButton(text=f"⚠️ اسپویلر: {'روشن ✅' if is_spoiler else 'خاموش ❌'}", callback_data=f"toggle_spoiler_{pid}")]
    ])

@router.callback_query(F.data.startswith("toggle_spoiler_"))
async def cb_toggle_spoiler(callback: types.CallbackQuery):
    pid = int(callback.data.split("_")[2])
    async with aiosqlite.connect('auto_pub.db') as conn:
        row = await (await conn.execute("SELECT is_spoiler FROM batch_posts WHERE id=?", (pid,))).fetchone()
        new_status = 0 if (row and row[0]) else 1
        await conn.execute("UPDATE batch_posts SET is_spoiler=? WHERE id=?", (new_status, pid))
        await conn.commit()
    try:
        await callback.message.edit_reply_markup(reply_markup=preview_kb(pid, new_status))
    except Exception:
        pass
    await callback.answer(f"اسپویلر {'روشن ✅' if new_status else 'خاموش ❌'}")


@router.callback_query(F.data == "set_sp_id_emoji")
async def cb_set_sp_id_emoji(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback.from_user.id, "یک ایموجی ساده برای ایدی پست‌های اسپویلردار بفرست (مثل 🆔):")
    await state.set_state(States.set_sp_id_emoji)
    await callback.answer()

@router.message(States.set_sp_id_emoji)
async def msg_set_sp_id_emoji(message: types.Message, state: FSMContext):
    await db.set('sp_id_emoji', message.text.strip())
    await message.answer(f"✅ ذخیره شد: {message.text.strip()}", reply_markup=menu_kb())
    await state.clear()

if __name__ == "__main__":
    asyncio.run(main())
