import asyncio
import websockets
import json
import os
import time
from datetime import datetime
from flask import Flask
from threading import Thread

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

# --- CONFIGURATION ---
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
CUSTOM_STATUS = "🔥 B2 ON TOP | guns.lol/17h40"
# --------------------

# Flask pour Render
app = Flask('')

@app.route('/')
def home():
    return "Discord Status Active! 🔥"

def run_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False, threaded=True)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

class DiscordSelfbot:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.heartbeat_interval = None
        self.session_id = None
        self.seq = None
        
    async def connect(self):
        """Connexion au Gateway Discord"""
        print("🔌 Connexion au Gateway Discord...", flush=True)
        
        try:
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    GATEWAY_URL,
                    max_size=10 * 1024 * 1024
                ),
                timeout=30.0
            )
            print("✅ WebSocket connecté", flush=True)
            
            # Recevoir Hello
            hello = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            hello_data = json.loads(hello)
            
            if hello_data['op'] == 10:
                self.heartbeat_interval = hello_data['d']['heartbeat_interval'] / 1000
                print(f"💓 Heartbeat: {self.heartbeat_interval}s", flush=True)
                
                # Démarrer heartbeat
                asyncio.create_task(self.heartbeat())
                
                # Identifier
                await self.identify()
                
                # Écouter les événements
                await self.listen()
                
        except asyncio.TimeoutError:
            print(f"⏱️  Timeout - Reconnexion dans 5s...", flush=True)
            await asyncio.sleep(5)
            await self.connect()
        except Exception as e:
            print(f"❌ Erreur: {e}", flush=True)
            await asyncio.sleep(5)
            await self.connect()
    
    async def identify(self):
        """Authentification"""
        print("🔑 Authentification...", flush=True)
        
        identify_payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": 0,
                "properties": {
                    "os": "windows",
                    "browser": "chrome",
                    "device": "pc"
                }
            }
        }
        
        await self.ws.send(json.dumps(identify_payload))
        print("📤 Payload envoyé", flush=True)
    
    async def heartbeat(self):
        """Heartbeats réguliers (silencieux)"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.ws.send(json.dumps({"op": 1, "d": self.seq}))
            except Exception as e:
                print(f"❌ Heartbeat erreur: {e}", flush=True)
                break
    
    async def update_status(self):
        """Mettre à jour le statut custom"""
        print("📡 Mise à jour du statut custom...", flush=True)
        
        status_payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [{
                    "type": 4,  # Type 4 = Custom Status
                    "state": CUSTOM_STATUS,
                    "name": "Custom Status",
                    "emoji": None
                }],
                "since": None,
                "afk": False
            }
        }
        
        try:
            await self.ws.send(json.dumps(status_payload))
            print(f"✅ Statut mis à jour: {CUSTOM_STATUS}", flush=True)
        except Exception as e:
            print(f"❌ Erreur: {e}", flush=True)
    
    async def listen(self):
        """Écouter les événements"""
        async for message in self.ws:
            data = json.loads(message)
            op = data['op']
            
            if data.get('s'):
                self.seq = data['s']
            
            # READY event
            if op == 0 and data['t'] == 'READY':
                user = data['d']['user']
                self.session_id = data['d']['session_id']
                print("=" * 60, flush=True)
                print(f"✅ CONNECTÉ: {user['username']}", flush=True)
                print(f"🔥 Statut: {CUSTOM_STATUS}", flush=True)
                print("=" * 60, flush=True)
                
                # Mettre à jour le statut
                await self.update_status()
                
                print("✨ Statut custom actif 24/7 !", flush=True)
                print("=" * 60, flush=True)
            
            # Reconnect
            elif op == 7:
                print("🔄 Reconnexion...", flush=True)
                await self.ws.close()
                await self.connect()

async def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("=" * 60, flush=True)
    print("🚀 Selfbot Discord - Statut Custom 24/7", flush=True)
    print("⚠️  Viole les ToS - Risque de ban", flush=True)
    print("=" * 60, flush=True)
    print(f"🔥 Statut: {CUSTOM_STATUS}", flush=True)
    print("=" * 60, flush=True)
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant !", flush=True)
        return
    
    print(f"🔑 Token OK ({len(TOKEN)} chars)", flush=True)
    
    bot = DiscordSelfbot(TOKEN)
    await bot.connect()

if __name__ == "__main__":
    keep_alive()
    print("🌐 Flask démarré", flush=True)
    time.sleep(2)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt", flush=True)
