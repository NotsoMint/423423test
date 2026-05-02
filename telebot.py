import re
import asyncio
import requests
import base64
import random
import string
import os
from urllib.parse import quote
from telethon import TelegramClient, events, Button
import discord

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

SOURCE_CHANNEL = -1003873615850
TARGET_CHANNELS = [-1003819166391, -1003918374586]

BACKUP_LINK = "https://t.me/+JRMQTwvuyok5YmFl"

SHRINKME_API = os.getenv("SHRINKME_API")
LINKVERTISE_ID = os.getenv("LINKVERTISE_ID")

client = TelegramClient("bot", API_ID, API_HASH)

# ===== DISCORD =====
intents = discord.Intents.default()
discord_client = discord.Client(intents=intents)

class LinkButtons(discord.ui.View):
    def __init__(self, sm, lv, backup):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(label="🔥 ShrinkMe", url=sm))
        self.add_item(discord.ui.Button(label="💰 Linkvertise", url=lv))
        self.add_item(discord.ui.Button(label="📦 Backup", url=backup))

async def send_to_discord(title, size, file_path, sm, lv):
    await discord_client.wait_until_ready()
    ch = discord_client.get_channel(DISCORD_CHANNEL_ID)

    embed = discord.Embed(
        title="🔥 New Drop",
        description=f"✨ {title} ✨\n\n────────────\n📦 File Size: {size}\n────────────",
        color=0x00ffcc
    )
    embed.set_footer(text="👇 Get Link Below 👇")

    if file_path:
        file = discord.File(file_path, filename="img.jpg")
        embed.set_image(url="attachment://img.jpg")

        await ch.send(
            file=file,
            embed=embed,
            view=LinkButtons(sm, lv, BACKUP_LINK)
        )
    else:
        await ch.send(
            embed=embed,
            view=LinkButtons(sm, lv, BACKUP_LINK)
        )

# ===== SHRINKME =====
def shrinkme(url):
    try:
        encoded = quote(url, safe='')
        r = requests.get(f"https://shrinkme.io/api?api={SHRINKME_API}&url={encoded}", timeout=10)
        return r.json().get("shortenedUrl", url)
    except:
        return url

# ===== LINKVERTISE =====
def linkvertise(url):
    try:
        encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        rand = random.randint(100, 999)
        return f"https://link-to.net/{LINKVERTISE_ID}/{rand}/dynamic?r={encoded}"
    except:
        return url

# ===== RENTRY =====
def create_rentry(title, size, link):
    try:
        s = requests.Session()
        s.get("https://rentry.co")
        csrf = s.cookies.get_dict().get("csrftoken")

        slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        content = f"# 🔥 {title}\n\n📦 File Size: {size}\n\n---\n\n👉 {link}"

        res = s.post(
            "https://rentry.co/api/new",
            data={
                "csrfmiddlewaretoken": csrf,
                "url": slug,
                "text": content
            },
            headers={"Referer": "https://rentry.co"}
        )

        j = res.json()
        if "url" in j:
            return "https://rentry.co/" + j["url"]

    except Exception as e:
        print("Rentry error:", e)

    return None

# ===== EXTRACT =====
def extract_link(text):
    m = re.search(r'(https?://\S+)', text)
    return m.group(1) if m else None

def extract_size(text):
    m = re.search(r'(\d+(?:\.\d+)?)\s?(GB|MB|TB)', text, re.I)
    return m.group(0) if m else "Unknown"

def extract_title(text):
    t = re.sub(r'(\d+(?:\.\d+)?)\s?(GB|MB|TB)', '', text, flags=re.I)
    return t.strip().split("\n")[0]

# ===== HANDLER =====
@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    text = event.raw_text or ""

    main = extract_link(text)
    if not main:
        return

    size = extract_size(text)
    title = extract_title(text)

    rentry = create_rentry(title, size, main) or main

    sm = shrinkme(rentry)
    lv = linkvertise(rentry)

    buttons = [
        [Button.url("🔥 ShrinkMe", sm)],
        [Button.url("💰 Linkvertise", lv)],
        [Button.url("📦 Backup", BACKUP_LINK)]
    ]

    caption = f"""🔥 New Drop

✨ {title} ✨

────────────

📦 File Size: {size}

────────────

👇 Get Link Below 👇
"""

    file_path = None

    if event.message.media:
        file_path = await event.download_media()

    # TELEGRAM
    for ch in TARGET_CHANNELS:
        try:
            if file_path:
                await client.send_file(ch, file_path, caption=caption, buttons=buttons)
            else:
                await client.send_message(ch, caption, buttons=buttons)
        except Exception as e:
            print("TG Error:", e)

    # DISCORD
    try:
        await send_to_discord(title, size, file_path, sm, lv)
    except Exception as e:
        print("Discord error:", e)

# ===== RUN =====
async def start_discord():
    await discord_client.start(DISCORD_TOKEN)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot started")

    asyncio.create_task(start_discord())

    await client.run_until_disconnected()

# 24/7 SAFE LOOP
while True:
    try:
        asyncio.run(main())
    except Exception as e:
        print("Restarting...", e)