
# self.py mis à jour avec ton nouveau CLIENT_ID
import asyncio
import websockets
import json
import os
import time
from datetime import datetime
from flask import Flask
from threading import Thread

CLIENT_ID = '1442957097385066707'
IMAGE_NAME = 'logo_b2'

GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

app = Flask('')

@app.route('/')
def home():
    return "Discord Presence Active! ✨"

def run_flask():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

class DiscordSelfbot:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.heartbeat_interval = None
        self.seq = None

    async def connect(self):
        try:
            self.ws = await websockets.connect(GATEWAY_URL)
            hello = json.loads(await self.ws.recv())

            if hello['op'] == 10:
                self.heartbeat_interval = hello['d']['heartbeat_interval'] / 1000
                asyncio.create_task(self.heartbeat())
                await self.identify()
                await self.listen()
        except:
            await asyncio.sleep(5)
            await self.connect()

    async def identify(self):
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "os": "windows",
                    "browser": "chrome",
                    "device": "pc"
                }
            }
        }
        await self.ws.send(json.dumps(payload))

    async def heartbeat(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            await self.ws.send(json.dumps({"op": 1, "d": self.seq}))

    async def update_presence(self):
        start_timestamp = int(time.time() * 1000) - (9999 * 3600 * 1000)

        payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [{
                    "type": 0,
                    "name": "🌍 B2 ON TOP",
                    "application_id": CLIENT_ID,
                    "details": "🔥 B2 GANG",
                    "state": "guns.lol/17h40",
                    "timestamps": {
                        "start": start_timestamp
                    },
                    "assets": {
                        "large_image": IMAGE_NAME,
                        "large_text": "B2 ON TOP"
                    }
                }],
                "since": None,
                "afk": False
            }
        }
        await self.ws.send(json.dumps(payload))

    async def listen(self):
        async for msg in self.ws:
            data = json.loads(msg)
            if data.get('s'):
                self.seq = data['s']
            if data['op'] == 0 and data['t'] == "READY":
                await self.update_presence()

async def main():
    token = os.getenv("DISCORD_TOKEN")
    bot = DiscordSelfbot(token)
    await bot.connect()

if __name__ == "__main__":
    keep_alive()
    time.sleep(2)
    asyncio.run(main())
