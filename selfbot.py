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
IMAGE_NAME = 'logo_b2'
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
# --------------------

# Flask pour Render
app = Flask('')

@app.route('/')
def home():
    return "Discord Presence Active! ✨"

def run_flask():
    """Flask en mode thread avec suppression des logs"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False, threaded=True)

def keep_alive():
    """Démarrer Flask en thread daemon"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    # PAS de sleep ici - on laisse le thread principal continuer

class DiscordSelfbot:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.heartbeat_interval = None
        self.session_id = None
        self.seq = None
        
    async def connect(self):
        """Connexion au Gateway Discord"""
        print("🔌 Connexion au Gateway Discord...")
        
        try:
            self.ws = await websockets.connect(GATEWAY_URL)
            print("✅ WebSocket connecté")
            
            # Recevoir Hello et configurer heartbeat
            hello = await self.ws.recv()
            hello_data = json.loads(hello)
            
            if hello_data['op'] == 10:  # Hello
                self.heartbeat_interval = hello_data['d']['heartbeat_interval'] / 1000
                print(f"💓 Heartbeat interval: {self.heartbeat_interval}s")
                
                # Démarrer heartbeat
                asyncio.create_task(self.heartbeat())
                
                # Identifier (payload MINIMAL)
                await self.identify()
                
                # Écouter les événements
                await self.listen()
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            await asyncio.sleep(5)
            await self.connect()
    
    async def identify(self):
        """Envoyer le payload d'identification MINIMAL"""
        print("🔑 Authentification...")
        
        # Payload ULTRA simplifié pour éviter "message too big"
        identify_payload = {
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
        
        await self.ws.send(json.dumps(identify_payload))
        print("📤 Payload envoyé")
    
    async def heartbeat(self):
        """Envoyer des heartbeats réguliers"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                heartbeat_payload = {
                    "op": 1,
                    "d": self.seq
                }
                await self.ws.send(json.dumps(heartbeat_payload))
                print(f"💓 Heartbeat - {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"❌ Erreur heartbeat: {e}")
                break
    
    async def update_presence(self):
        """Mettre à jour la Rich Presence APRÈS connexion"""
        print("📡 Mise à jour Rich Presence...")
        
        presence_payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [{
                    "type": 0,
                    "name": "HK X B2",
                    "application_id": CLIENT_ID,
                    "details": "V1",
                    "state": "guns.lol/17h40",
                    "timestamps": {
                        "start": int(time.time() * 1000)
                    },
                    "assets": {
                        "large_image": IMAGE_NAME,
                        "large_text": "HK X B2"
                    }
                }],
                "since": None,
                "afk": False
            }
        }
        
        try:
            await self.ws.send(json.dumps(presence_payload))
            print("✅ Rich Presence mise à jour !")
        except Exception as e:
            print(f"❌ Erreur mise à jour: {e}")
    
    async def listen(self):
        """Écouter les événements du Gateway"""
        async for message in self.ws:
            data = json.loads(message)
            op = data['op']
            
            # Sauvegarder le numéro de séquence
            if data.get('s'):
                self.seq = data['s']
            
            # Ready event
            if op == 0 and data['t'] == 'READY':
                user = data['d']['user']
                self.session_id = data['d']['session_id']
                print("=" * 60)
                print(f"✅ CONNECTÉ: {user['username']} (ID: {user['id']})")
                print(f"📊 Session: {self.session_id[:20]}...")
                print("=" * 60)
                
                # Mettre à jour la présence MAINTENANT
                await self.update_presence()
                
                print("✨ Rich Presence active avec images !")
                print("💡 Rafraîchissement toutes les 15 minutes")
                print("=" * 60)
                
                # Démarrer le rafraîchissement automatique
                asyncio.create_task(self.refresh_loop())
            
            # Heartbeat ACK
            elif op == 11:
                pass  # OK
            
            # Reconnect
            elif op == 7:
                print("🔄 Reconnexion demandée...")
                await self.ws.close()
                await self.connect()
    
    async def refresh_loop(self):
        """Rafraîchir toutes les 15 minutes"""
        while True:
            await asyncio.sleep(900)  # 15 min
            print(f"\n🔄 Rafraîchissement - {datetime.now().strftime('%H:%M:%S')}")
            await self.update_presence()

async def main():
    print("DEBUG: Entrée dans main()", flush=True)
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("=" * 60, flush=True)
    print("🚀 Selfbot Discord Rich Presence", flush=True)
    print("⚠️  Viole les ToS Discord - Risque de ban", flush=True)
    print("=" * 60, flush=True)
    print(f"🎮 Application: {CLIENT_ID}", flush=True)
    print(f"🖼️  Image: {IMAGE_NAME}", flush=True)
    print("=" * 60, flush=True)
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant !", flush=True)
        return
    
    print(f"🔑 Token trouvé ({len(TOKEN)} caractères)", flush=True)
    print("=" * 60, flush=True)
    
    print("DEBUG: Création du bot...", flush=True)
    bot = DiscordSelfbot(TOKEN)
    
    print("DEBUG: Avant bot.connect()", flush=True)
    try:
        await bot.connect()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt...", flush=True)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("🚀 Démarrage du Selfbot Discord", flush=True)
    print("=" * 60, flush=True)
    
    # Démarrer Flask en arrière-plan
    keep_alive()
    print("🌐 Flask lancé en arrière-plan sur port", os.getenv('PORT', 10000), flush=True)
    
    # Petit délai pour que Flask bind le port
    print("⏳ Attente 3s pour que Flask s'initialise...", flush=True)
    time.sleep(3)
    
    print("🤖 Lancement du bot Discord...", flush=True)
    print("=" * 60, flush=True)
    print("DEBUG: Avant asyncio.run()", flush=True)
    
    # Démarrer le bot Discord sur le thread principal
    try:
        asyncio.run(main())
        print("DEBUG: Après asyncio.run()", flush=True)
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt...", flush=True)
    except Exception as e:
        print(f"❌ ERREUR FATALE: {e}", flush=True)
        import traceback
        traceback.print_exc()
