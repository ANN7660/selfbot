import asyncio
import websockets
import json
import os
import time
import logging
from threading import Thread
from flask import Flask

# ========== CONFIGURATION ==========
CLIENT_ID = "1443718920568700939"
IMAGE_NAME = "1443773833416020048"
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

# Configuration WebSocket
WEBSOCKET_CONFIG = {
    "ping_interval": 20,      # Ping toutes les 20s
    "ping_timeout": 10,       # Timeout de 10s pour le pong
    "close_timeout": 10,      # Timeout de 10s pour la fermeture
    "max_size": 2**20,        # 1MB max par message
}

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== SERVEUR WEB POUR KEEP-ALIVE ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Bot Discord actif !"

def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def keep_alive():
    """Lance un serveur web pour garder le Repl actif"""
    t = Thread(target=run_flask, daemon=True)
    t.start()
    logger.info("🌐 Serveur web démarré sur le port 8080")

# ========== MONITEUR DE CONNEXION ==========
class ConnectionMonitor:
    def __init__(self):
        self.connected_at = None
        self.disconnections = 0
        self.last_disconnect = None
        self.total_uptime = 0
        
    def on_connect(self):
        self.connected_at = time.time()
        if self.disconnections > 0:
            logger.info(f"📊 Statistiques: {self.disconnections} déconnexions totales")
        
    def on_disconnect(self):
        if self.connected_at:
            uptime = time.time() - self.connected_at
            self.total_uptime += uptime
            self.disconnections += 1
            self.last_disconnect = time.time()
            
            logger.info(f"📊 Session terminée après {uptime:.1f}s")
            if self.disconnections > 1:
                logger.info(f"📊 Uptime total: {self.total_uptime:.1f}s")
                logger.info(f"📊 Moyenne par session: {self.total_uptime / self.disconnections:.1f}s")

# ========== SELFBOT DISCORD ==========
class DiscordSelfbot:
    def __init__(self, token):
        self.token = token.strip()
        self.ws = None
        self.heartbeat_interval = None
        self.session_id = None
        self.sequence = None
        self.heartbeat_task = None
        self.should_reconnect = True
        self.reconnect_count = 0
        self.last_heartbeat_ack = True
        self.heartbeat_timeout = 60
        self.monitor = ConnectionMonitor()

    def log_close_code(self, code):
        """Explique les codes de fermeture Discord"""
        close_codes = {
            1000: "Normal closure",
            1001: "Going away",
            1006: "Abnormal closure (no close frame)",
            4000: "Unknown error",
            4001: "Unknown opcode",
            4002: "Decode error",
            4003: "Not authenticated",
            4004: "Authentication failed (invalid token)",
            4005: "Already authenticated",
            4007: "Invalid seq",
            4008: "Rate limited",
            4009: "Session timed out",
            4010: "Invalid shard",
            4011: "Sharding required",
            4012: "Invalid API version",
            4013: "Invalid intent(s)",
            4014: "Disallowed intent(s)"
        }
        
        if code in close_codes:
            logger.error(f"   📋 Signification: {close_codes[code]}")
        else:
            logger.error(f"   📋 Code inconnu: {code}")

    async def connect(self):
        """Boucle de connexion principale avec logique de reconnexion"""
        max_retries = 10
        retry_delays = [5, 10, 15, 30, 60, 120, 300, 600, 900, 1800]
        
        while self.should_reconnect and self.reconnect_count < max_retries:
            try:
                self.ws = await websockets.connect(
                    GATEWAY_URL,
                    **WEBSOCKET_CONFIG
                )
                logger.info("✅ Connecté au Gateway Discord")
                self.monitor.on_connect()
                self.reconnect_count = 0
                
                await self.identify()
                await self.listen()
                
            except websockets.exceptions.ConnectionClosedOK as e:
                logger.info(f"✅ Connexion fermée proprement")
                logger.info(f"   Code: {e.code}")
                logger.info(f"   Raison: {e.reason or 'Non spécifiée'}")
                self.monitor.on_disconnect()
                
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(f"❌ Connexion fermée avec erreur")
                logger.error(f"   Code: {e.code}")
                logger.error(f"   Raison: {e.reason or 'Non spécifiée'}")
                self.log_close_code(e.code)
                self.monitor.on_disconnect()
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ Connexion fermée: {e.reason or 'no close frame received or sent'}")
                if hasattr(e, 'code'):
                    logger.warning(f"   Code: {e.code}")
                    self.log_close_code(e.code)
                logger.warning(f"   Raison: {e.reason or 'Non spécifiée'}")
                self.monitor.on_disconnect()
                
            except Exception as e:
                logger.error(f"❌ Erreur inattendue: {type(e).__name__}: {e}")
                self.monitor.on_disconnect()
            
            finally:
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
            
            # Reconnexion avec backoff exponentiel
            if self.should_reconnect and self.reconnect_count < max_retries:
                self.reconnect_count += 1
                delay = retry_delays[min(self.reconnect_count - 1, len(retry_delays) - 1)]
                logger.info(f"🔄 Reconnexion dans {delay}s... (tentative {self.reconnect_count}/{max_retries})")
                await asyncio.sleep(delay)
        
        if self.reconnect_count >= max_retries:
            logger.critical("💀 Nombre maximum de reconnexions atteint")

    async def identify(self):
        """Envoie le payload d'identification avec Rich Presence"""
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
                    "activities": [
                        {
                            "type": 5,
                            "application_id": CLIENT_ID,
                            "name": "B2 🌍",
                            "details": "🎄 restez branché 🎄",
                            "state": "B2 ON TOP 🍇",
                            "assets": {
                                "large_image": IMAGE_NAME,
                                "large_text": "HK ??"
                            },
                            "buttons": ["👑 CROWN", "🔫 GUNS.LOL"],
                            "metadata": {
                                "button_urls": [
                                    "https://discord.gg/bC8Jcjdr3H",
                                    "https://guns.lol/17h40"
                                ]
                            }
                        }
                    ],
                    "since": None,
                    "afk": False
                }
            }
        }
        await self.ws.send(json.dumps(payload))
        logger.info("📤 Identification avec Rich Presence envoyée")

    async def update_presence(self):
        """Met à jour la Rich Presence"""
        payload = {
            "op": 3,
            "d": {
                "status": "online",
                "activities": [
                    {
                        "type": 5,
                        "application_id": CLIENT_ID,
                        "name": "B2 🌍",
                        "details": "🎄 restez branché 🎄",
                        "state": "B2 ON TOP 🍇",
                        "assets": {
                            "large_image": IMAGE_NAME,
                            "large_text": "B2 Community"
                        },
                        "buttons": ["👑 CROWN", "🔫 GUNS.LOL"],
                        "metadata": {
                            "button_urls": [
                                "https://discord.gg/bC8Jcjdr3H",
                                "https://guns.lol/17h40"
                            ]
                        }
                    }
                ],
                "since": None,
                "afk": False
            }
        }
        await self.ws.send(json.dumps(payload))
        logger.info("✅ Rich Presence mise à jour")

    async def send_heartbeat(self):
        """Envoie des heartbeats réguliers avec timeout"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval / 1000)
                
                # Vérifier si le dernier heartbeat a reçu un ACK
                if not self.last_heartbeat_ack:
                    logger.warning("⚠️ Aucun ACK reçu pour le dernier heartbeat")
                    await self.ws.close(code=1000, reason="Heartbeat timeout")
                    break
                
                self.last_heartbeat_ack = False
                
                # Envoyer le heartbeat avec timeout
                heartbeat = {"op": 1, "d": self.sequence}
                
                await asyncio.wait_for(
                    self.ws.send(json.dumps(heartbeat)),
                    timeout=self.heartbeat_timeout
                )
                
                logger.debug(f"💓 Heartbeat envoyé (seq: {self.sequence})")
                
            except asyncio.TimeoutError:
                logger.error("❌ Timeout lors de l'envoi du heartbeat")
                await self.ws.close(code=1000, reason="Heartbeat send timeout")
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur heartbeat: {e}")
                break

    async def listen(self):
        """Écoute les messages du Gateway Discord"""
        async for message in self.ws:
            try:
                data = json.loads(message)
                op = data.get("op")
                d = data.get("d")
                
                if data.get("s"):
                    self.sequence = data["s"]
                
                # Hello - démarre le heartbeat
                if op == 10:
                    self.heartbeat_interval = d["heartbeat_interval"]
                    logger.info(f"💓 Intervalle heartbeat: {self.heartbeat_interval}ms")
                    self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
                
                # Dispatch - événements Discord
                elif op == 0:
                    event_type = data.get("t")
                    
                    if event_type == "READY":
                        user = d.get("user", {})
                        username = user.get("username", "Inconnu")
                        logger.info(f"🎉 Connecté en tant que: {username} (ID: {user.get('id')})")
                        self.session_id = d.get("session_id")
                        await self.update_presence()
                        
                    elif event_type == "RESUMED":
                        logger.info("🔄 Session reprise")
                
                # Heartbeat ACK
                elif op == 11:
                    self.last_heartbeat_ack = True
                    logger.debug("✅ Heartbeat ACK reçu")
                
                # Demande de heartbeat immédiat
                elif op == 1:
                    await self.ws.send(json.dumps({"op": 1, "d": self.sequence}))
                
                # Session invalide
                elif op == 9:
                    can_resume = d if isinstance(d, bool) else False
                    if can_resume:
                        await self.resume()
                    else:
                        logger.warning("⚠️ Session invalide, reconnexion...")
                        await asyncio.sleep(5)
                        await self.identify()
                
                # Reconnect demandé
                elif op == 7:
                    logger.warning("🔄 Reconnexion demandée par Discord")
                    raise websockets.exceptions.ConnectionClosed(1000, "Reconnect requested")
                
            except json.JSONDecodeError:
                logger.error("❌ Erreur décodage JSON")
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement: {e}")

    async def resume(self):
        """Reprend une session existante"""
        if not self.session_id:
            return
        
        payload = {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.sequence
            }
        }
        await self.ws.send(json.dumps(payload))
        logger.info("📤 Reprise de session")

    async def close(self):
        """Ferme proprement la connexion"""
        self.should_reconnect = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.ws:
            await self.ws.close()
        logger.info("👋 Connexion fermée")


async def main():
    """Fonction principale"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("❌ Variable DISCORD_TOKEN manquante")
        logger.info("💡 Ajoute ton token dans les Secrets (Replit)")
        return

    logger.info("🚀 Démarrage du selfbot Discord avec Rich Presence...")
    logger.warning("⚠️ Les selfbots violent les CGU de Discord - utilisez à vos risques")
    
    keep_alive()
    
    bot = DiscordSelfbot(token)
    
    try:
        await bot.connect()
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé")
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Programme arrêté")
