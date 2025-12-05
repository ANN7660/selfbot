import asyncio
import websockets
import json
import os
import time
import logging
from flask import Flask
from threading import Thread

# Configuration
CLIENT_ID = '1442957097385066707'
IMAGE_URL = 'hk_logo'
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "Discord Presence Active! ✨"

@app.route('/health')
def health():
    return {"status": "ok", "timestamp": time.time()}

def run_flask():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

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
        self.session_id = None
        self.heartbeat_task = None
        self.last_heartbeat_ack = True
        self.reconnect_attempts = 0
        self.consecutive_failures = 0
        self.presence_updated = False

    async def connect(self):
        """Connexion au gateway Discord avec gestion d'erreurs améliorée"""
        try:
            logger.info("Connexion au gateway Discord...")
            self.ws = await websockets.connect(
                GATEWAY_URL, 
                max_size=None,
                ping_interval=None,
                close_timeout=10
            )
            
            hello = json.loads(await self.ws.recv())
            
            if hello['op'] == 10:
                self.heartbeat_interval = hello['d']['heartbeat_interval'] / 1000
                logger.info(f"Heartbeat interval: {self.heartbeat_interval}s")
                
                if self.heartbeat_task and not self.heartbeat_task.done():
                    self.heartbeat_task.cancel()
                    try:
                        await self.heartbeat_task
                    except asyncio.CancelledError:
                        pass
                
                self.heartbeat_task = asyncio.create_task(self.heartbeat())
                
                if self.session_id and self.seq:
                    await self.resume()
                else:
                    await self.identify()
                
                self.reconnect_attempts = 0
                self.consecutive_failures = 0
                await self.listen()
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connexion fermée: {e.code} - {e.reason}")
            await self.handle_reconnect()
        except Exception as e:
            logger.error(f"Erreur de connexion: {e}")
            await self.handle_reconnect()

    async def handle_reconnect(self):
        """Gestion intelligente de la reconnexion avec backoff exponentiel"""
        self.reconnect_attempts += 1
        self.consecutive_failures += 1
        
        wait_time = min(5 * (2 ** min(self.consecutive_failures - 1, 5)), 300)
        logger.info(f"⏳ Reconnexion dans {wait_time}s (tentative #{self.reconnect_attempts})")
        await asyncio.sleep(wait_time)
        
        try:
            await self.connect()
        except Exception as e:
            logger.error(f"Échec de reconnexion: {e}")
            await self.handle_reconnect()

    async def identify(self):
        """Envoi du payload d'identification"""
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "os": "windows",
                    "browser": "chrome",
                    "device": "pc"
                },
                "compress": False,
                "large_threshold": 250,
                "presence": {
                    "status": "online",
                    "activities": [{
                        "type": 0,
                        "name": "🎄",
                        "details": "hk 🎄",
                        "assets": {
                            "large_image": IMAGE_URL,
                            "large_text": "hk 🎄",
                            "small_image": IMAGE_URL,
                            "small_text": "hk 🎄"
                        },
                        "buttons": ["👑", "🔫"],
                        "metadata": {
                            "button_urls": [
                                "https://discord.gg/Ncyqd7u2Q4",
                                "https://guns.lol/17h40"
                            ]
                        }
                    }],
                    "since": None,
                    "afk": False
                }
            }
        }
        await self.ws.send(json.dumps(payload))
        logger.info("Payload d'identification envoyé avec présence initiale")

    async def resume(self):
        """Reprise de session après déconnexion"""
        payload = {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.seq
            }
        }
        await self.ws.send(json.dumps(payload))
        logger.info("Tentative de reprise de session")

    async def heartbeat(self):
        """Envoi périodique du heartbeat avec détection d'ACK"""
        try:
            await asyncio.sleep(self.heartbeat_interval * 0.5)
            
            while True:
                if not self.last_heartbeat_ack:
                    logger.warning("Heartbeat ACK non reçu, reconnexion...")
                    await self.ws.close()
                    break
                
                self.last_heartbeat_ack = False
                heartbeat_payload = {"op": 1, "d": self.seq}
                await self.ws.send(json.dumps(heartbeat_payload))
                logger.debug(f"Heartbeat envoyé (seq: {self.seq})")
                
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            logger.info("Tâche heartbeat annulée")
        except Exception as e:
            logger.error(f"Erreur dans heartbeat: {e}")

    async def update_presence(self):
        """Mise à jour de la présence Discord avec boutons et images"""
        logger.info("🎯 Mise à jour de la présence avec boutons")
        
        payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [{
                    "type": 2,
                    "name": "hk jtm",
                    "details": "🎄",
                    "application_id": CLIENT_ID,
                    "assets": {
                        "large_image": IMAGE_URL,
                        "large_text": ".",
                        "small_image": IMAGE_URL,
                        "small_text": "."
                    },
                    "buttons": ["👑", "🔫"],
                    "metadata": {
                        "button_urls": [
                            "https://discord.gg/Ncyqd7u2Q4",
                            "https://guns.lol/17h40"
                        ]
                    }
                }],
                "since": None,
                "afk": False
            }
        }
        
        await self.ws.send(json.dumps(payload))
        self.presence_updated = True
        logger.info("✅ Présence mise à jour avec boutons et images")

    async def listen(self):
        """Écoute des événements du gateway"""
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                op = data.get('op')
                t = data.get('t')
                
                if data.get('s'):
                    self.seq = data['s']
                
                if op == 0:
                    await self.handle_dispatch(t, data['d'])
                elif op == 1:
                    await self.ws.send(json.dumps({"op": 1, "d": self.seq}))
                    logger.debug("Heartbeat immédiat envoyé")
                elif op == 7:
                    logger.info("Reconnexion demandée par Discord")
                    await self.ws.close()
                    break
                elif op == 9:
                    invalid = data.get('d', False)
                    logger.warning(f"Session invalide (resumable: {invalid})")
                    if not invalid:
                        self.session_id = None
                        self.seq = None
                    await asyncio.sleep(5)
                    await self.identify()
                elif op == 11:
                    self.last_heartbeat_ack = True
                    logger.debug("Heartbeat ACK reçu")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connexion fermée pendant l'écoute: {e.code}")
            raise
        except Exception as e:
            logger.error(f"Erreur dans listen: {e}", exc_info=True)
            raise

    async def handle_dispatch(self, event_type, data):
        """Gestion des événements dispatch"""
        if event_type == "READY":
            self.session_id = data['session_id']
            user = data['user']
            logger.info(f"✅ Connecté: {user['username']}#{user['discriminator']}")
            
            if not self.presence_updated:
                await asyncio.sleep(1)
                await self.update_presence()
                
        elif event_type == "RESUMED":
            logger.info("✅ Session reprise avec succès")
            await asyncio.sleep(1)
            await self.update_presence()

async def main():
    """Fonction principale"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("❌ DISCORD_TOKEN non défini dans les variables d'environnement")
        return

    logger.info("🚀 Démarrage du bot...")
    bot = DiscordSelfbot(token)

    while True:
        try:
            await bot.connect()
        except KeyboardInterrupt:
            logger.info("Arrêt du bot...")
            if bot.ws and not bot.ws.closed:
                await bot.ws.close()
            break
        except Exception as e:
            logger.error(f"Erreur dans la boucle principale: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    keep_alive()
    time.sleep(2)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Programme arrêté par l'utilisateur")