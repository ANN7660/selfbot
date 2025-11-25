import asyncio
import websockets
import json
import os
import time
from datetime import datetime

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

# --- CONFIGURATION ---
CLIENT_ID = '1410787199745888747'
IMAGE_NAME = 'logo_b2'
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
# --------------------

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
                
                # Identifier
                await self.identify()
                
                # Écouter les événements
                await self.listen()
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            await asyncio.sleep(5)
            await self.connect()
    
    async def identify(self):
        """Envoyer le payload d'identification"""
        print("🔑 Authentification...")
        
        identify_payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": "online",
                    "activities": [{
                        "type": 0,
                        "name": "HK X B2",
                        "application_id": CLIENT_ID,
                        "details": "V1",
                        "state": "guns.lol/17h40",
                        "timestamps": {
                            "start": int(time.time())
                        },
                        "assets": {
                            "large_image": IMAGE_NAME,
                            "large_text": "HK X B2",
                            "small_image": IMAGE_NAME,
                            "small_text": "En ligne"
                        },
                        "buttons": ["guns lol b2"],
                        "metadata": {
                            "button_urls": ["https://guns.lol/17h40"]
                        }
                    }]
                }
            }
        }
        
        await self.ws.send(json.dumps(identify_payload))
        print("📤 Payload d'identification envoyé")
    
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
                print(f"💓 Heartbeat envoyé - {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"❌ Erreur heartbeat: {e}")
                break
    
    async def update_presence(self):
        """Mettre à jour la Rich Presence"""
        print("📡 Mise à jour de la Rich Presence...")
        
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
                        "start": int(time.time())
                    },
                    "assets": {
                        "large_image": IMAGE_NAME,
                        "large_text": "HK X B2",
                        "small_image": IMAGE_NAME,
                        "small_text": "En ligne"
                    },
                    "buttons": ["guns lol b2"],
                    "metadata": {
                        "button_urls": ["https://guns.lol/17h40"]
                    }
                }],
                "since": None,
                "afk": False
            }
        }
        
        try:
            await self.ws.send(json.dumps(presence_payload))
            print("✅ Rich Presence mise à jour")
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
                print(f"✅ Connecté: {user['username']} (ID: {user['id']})")
                print(f"📊 Session: {self.session_id}")
                print("-" * 60)
                print("✨ Rich Presence active !")
                print("💡 Rafraîchissement toutes les 15 minutes")
                print("-" * 60)
                
                # Démarrer le rafraîchissement automatique
                asyncio.create_task(self.refresh_loop())
            
            # Heartbeat ACK
            elif op == 11:
                pass  # Heartbeat acknowledged
            
            # Reconnect
            elif op == 7:
                print("🔄 Reconnexion demandée par Discord...")
                await self.ws.close()
                await self.connect()
    
    async def refresh_loop(self):
        """Rafraîchir la présence toutes les 15 minutes"""
        while True:
            await asyncio.sleep(900)  # 15 minutes
            print(f"\n🔄 Rafraîchissement automatique - {datetime.now().strftime('%H:%M:%S')}")
            await self.update_presence()

async def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("=" * 60)
    print("🚀 Selfbot Discord Rich Presence")
    print("⚠️  Viole les ToS Discord - Risque de ban")
    print("=" * 60)
    print(f"🎮 Application: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("=" * 60)
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant !")
        return
    
    print(f"🔑 Token trouvé ({len(TOKEN)} caractères)")
    print("=" * 60)
    
    bot = DiscordSelfbot(TOKEN)
    
    try:
        await bot.connect()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt...")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    asyncio.run(main())
