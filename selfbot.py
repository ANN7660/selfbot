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
CLIENT_ID = '1410787199745888747'
LARGE_IMAGE = 'logo_b2'           # Grande image
SMALL_IMAGE = 'logo_petit_b2'     # Petite image
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
# --------------------

# Flask pour Render
app = Flask('')

@app.route('/')
def home():
    return "Discord Presence Active! ✨"

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
            # AUGMENTER LA LIMITE à 10MB pour recevoir le READY event
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    GATEWAY_URL,
                    max_size=10 * 1024 * 1024  # 10 MB au lieu de 1 MB
                ),
                timeout=30.0
            )
            print("✅ WebSocket connecté (limite 10MB)", flush=True)
            
            # Recevoir Hello
            hello = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            hello_data = json.loads(hello)
            
            if hello_data['op'] == 10:  # Hello
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
        """Authentification avec intents minimaux"""
        print("🔑 Authentification...", flush=True)
        
        identify_payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": 0,  # Aucun intent (on veut juste la présence)
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
                # Heartbeat envoyé sans affichage
            except Exception as e:
                print(f"❌ Heartbeat erreur: {e}", flush=True)
                break
    
    async def update_presence(self):
        """Mettre à jour la Rich Presence avec 2 images"""
        print("📡 Mise à jour Rich Presence...", flush=True)
        
        presence_payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [{
                    "type": 0,
                    "name": "B2 ON TOP",
                    "application_id": CLIENT_ID,
                    "details": "guns.lol/17h40",
                    "state": "",
                    "timestamps": {"start": int(time.time() * 1000)},
                    "assets": {
                        "large_image": LARGE_IMAGE,
                        "large_text": "B2 ON TOP",
                        "small_image": SMALL_IMAGE,
                        "small_text": "En ligne"
                    },
                    "buttons": ["guns lol b2"],
                    "metadata": {"button_urls": ["https://guns.lol/17h40"]}
                }],
                "since": None,
                "afk": False
            }
        }
        
        try:
            await self.ws.send(json.dumps(presence_payload))
            print("✅ Rich Presence mise à jour avec 2 images !", flush=True)
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
                print(f"🎮 Joue à: B2 ON TOP", flush=True)
                print(f"🖼️  Grande image: {LARGE_IMAGE}", flush=True)
                print(f"🔹 Petite image: {SMALL_IMAGE}", flush=True)
                print("=" * 60, flush=True)
                
                # Mettre à jour la présence
                await self.update_presence()
                
                print("✨ Rich Presence active !", flush=True)
                print("=" * 60, flush=True)
            
            # Reconnect
            elif op == 7:
                print("🔄 Reconnexion...", flush=True)
                await self.ws.close()
                await self.connect()

async def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("=" * 60, flush=True)
    print("🚀 Selfbot Discord Rich Presence", flush=True)
    print("⚠️  Viole les ToS - Risque de ban", flush=True)
    print("=" * 60, flush=True)
    print(f"🎮 App: {CLIENT_ID}", flush=True)
    print(f"🎯 Joue à: B2 ON TOP", flush=True)
    print(f"🖼️  Grande image: {LARGE_IMAGE}", flush=True)
    print(f"🔹 Petite image: {SMALL_IMAGE}", flush=True)
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
