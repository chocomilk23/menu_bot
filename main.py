import discord
import os
import random
import json
import aiohttp
import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

MENU_FILE = "menu.json"

# 메뉴 파일 불러오기
def load_menu():
    try:
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# 메뉴 저장
def save_menu():
    with open(MENU_FILE, "w", encoding="utf-8") as f:
        json.dump(menu_list, f, ensure_ascii=False, indent=2)

menu_list = load_menu()

MAX_MSG_LEN = 1900  # 디스코드 메시지 제한보다 살짝 여유

async def send_long_message(channel, text):
    chunks = [text[i:i+MAX_MSG_LEN] for i in range(0, len(text), MAX_MSG_LEN)]
    for chunk in chunks:
        await channel.send(chunk)

@client.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {client.user}")
    client.loop.create_task(start_web_server())
    client.loop.create_task(ping_self())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    if content.startswith('!추가'):
        parts = content.split(maxsplit=1)
        if len(parts) == 2:
            menu = parts[1].strip()
            if menu:
                menu_list.append(menu)
                save_menu()
                await message.channel.send(f'✅ 메뉴 "{menu}" 추가됨!')
            else:
                await message.channel.send('⚠️ 메뉴 이름을 입력해 주세요.')
    elif content == '!목록':
        if menu_list:
            chunk = ""
            chunks = []

            for i, m in enumerate(menu_list, 1):
                line = f"{i}. {m}\n"
                # 1900자를 넘기면 chunk를 쪼개서 저장
                if len(chunk) + len(line) > 1900:
                    chunks.append(chunk)
                    chunk = ""
                chunk += line
            # 마지막 chunk가 남아있으면 추가
            if chunk:
                chunks.append(chunk)

            # 순차적으로 메시지 전송
            for idx, part in enumerate(chunks, 1):
                await message.channel.send(f'🍽️ 메뉴 목록 ({idx}/{len(chunks)}):\n{part}')
        else:
            await message.channel.send("⚠️ 아직 메뉴가 없어요!")

    elif content == '!추천':
        if menu_list:
            menu = random.choice(menu_list)
            await message.channel.send(f'🥁 오늘의 추천 메뉴는... **{menu}**!')
        else:
            await message.channel.send("⚠️ 추천할 메뉴가 없어요!")
    elif content.startswith('!삭제'):
        parts = content.split(maxsplit=1)
        if len(parts) == 2:
            menu_to_delete = parts[1].strip()
            if menu_to_delete in menu_list:
                menu_list.remove(menu_to_delete)
                save_menu()
                await message.channel.send(f'🗑️ 메뉴 "{menu_to_delete}" 삭제됨.')
            else:
                await message.channel.send(f'⚠️ 메뉴 "{menu_to_delete}"가 목록에 없어요.')

# 웹서버 (Health check용)
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port=8080)
    await site.start()

# Self-ping
async def ping_self():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            if RENDER_URL:
                async with aiohttp.ClientSession() as session:
                    await session.get(f"{RENDER_URL}/health")
        except Exception as e:
            print(f"[Ping 오류] {e}")
        await asyncio.sleep(180)  # 3분마다


client.run(TOKEN)
