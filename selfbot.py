import asyncio
import websockets
import json
import os
import time
import logging
from threading import Thread
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import aiohttp

# ========== CONFIGURATION ==========
CLIENT_ID = "1443718920568700939"
IMAGE_NAME = "1443773833416020048"
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
DISCORD_API = "https://discord.com/api/v10"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== STOCKAGE DES COMMANDES ==========
commands = []
stats = {
    "total_commands": 0,
    "active_commands": 0,
    "total_executions": 0,
    "start_time": time.time()
}

# ========== COMMANDES PAR DÉFAUT ==========
def init_commands():
    global commands
    commands = [
        # Commandes basiques
        {"name": "?ping", "response": "🏓 Pong! Latence: {time}ms", "enabled": True, "count": 0},
        {"name": "?help", "response": "📋 **Commandes B2:**\n`?ping` `?info` `?stats` `?purge` `?embed` `?avatar` `?snipe` `?spam` `?raid` `?nuke` `?discord` `?guns` `?b2`", "enabled": True, "count": 0},
        {"name": "?info", "response": "ℹ️ **B2 Selfbot** | Version 2.0 | Uptime: {uptime}s | By Crown 👑", "enabled": True, "count": 0},
        
        # Utilitaires
        {"name": "?avatar", "response": "🖼️ Avatar récupéré!", "enabled": True, "count": 0},
        {"name": "?userinfo", "response": "👤 **Informations utilisateur**", "enabled": True, "count": 0},
        {"name": "?serverinfo", "response": "🏠 **Informations serveur**", "enabled": True, "count": 0},
        {"name": "?snipe", "response": "👻 Aucun message supprimé récemment", "enabled": True, "count": 0},
        {"name": "?embed", "response": "📰 Embed créé avec succès!", "enabled": True, "count": 0},
        
        # Modération (fake)
        {"name": "?purge", "response": "🗑️ Purge effectuée (simulation)", "enabled": True, "count": 0},
        {"name": "?clear", "response": "🧹 Messages nettoyés! (simulation)", "enabled": True, "count": 0},
        {"name": "?ban", "response": "🔨 Utilisateur banni (simulation)", "enabled": True, "count": 0},
        {"name": "?kick", "response": "👢 Utilisateur kick (simulation)", "enabled": True, "count": 0},
        
        # Fun & Spam
        {"name": "?spam", "response": "💥 Spam lancé! 🔥", "enabled": True, "count": 0},
        {"name": "?raid", "response": "⚔️ RAID MODE ACTIVATED 💀", "enabled": True, "count": 0},
        {"name": "?ascii", "response": "```\n▄▀█ █▀ █▀▀ █ █\n█▀█ ▄█ █▄▄ █ █\n```", "enabled": True, "count": 0},
        {"name": "?ghost", "response": "👻 Mode fantôme activé...", "enabled": True, "count": 0},
        {"name": "?fake", "response": "🎭 Message fake envoyé!", "enabled": True, "count": 0},
        
        # Toxic/Troll (FAKE - juste des messages)
        {"name": "?nuke", "response": "💣 NUKE DEPLOYED 💥💥💥 (fake lol)", "enabled": True, "count": 0},
        {"name": "?destroy", "response": "🔥 DESTRUCTION EN COURS... 💀 (simulation)", "enabled": True, "count": 0},
        {"name": "?hack", "response": "💻 Hacking in progress... █████░░░░░ 50% (fake)", "enabled": True, "count": 0},
        {"name": "?ddos", "response": "⚠️ DDoS simulation lancée (c'est du fake)", "enabled": True, "count": 0},
        
        # Liens & Socials
        {"name": "?discord", "response": "👑 **Crown Discord:** https://discord.gg/bC8Jcjdr3H", "enabled": True, "count": 0},
        {"name": "?guns", "response": "🔫 **Mon profil:** https://guns.lol/17h40", "enabled": True, "count": 0},
        {"name": "?b2", "response": "🌍 **B2 Community** - La meilleure team française 🍇🔥", "enabled": True, "count": 0},
        {"name": "?crown", "response": "👑 **CROWN GANG** - On est au top! 💯", "enabled": True, "count": 0},
        
        # Stats & Info
        {"name": "?stats", "response": "📊 **Stats:** Exécutions: {count} | Uptime: {uptime}s", "enabled": True, "count": 0},
        {"name": "?uptime", "response": "⏱️ Bot actif depuis: {uptime}s", "enabled": True, "count": 0},
        {"name": "?version", "response": "🆔 **B2 Selfbot v2.0** - Coded by Crown 👑", "enabled": True, "count": 0},
        
        # Autres (désactivés par défaut)
        {"name": "?nitro", "response": "💎 discord.gift/fakenitro (c'est fake mdr)", "enabled": False, "count": 0},
        {"name": "?token", "response": "🔑 Token grabber: [REDACTED] (fake évidemment)", "enabled": False, "count": 0},
        {"name": "?ip", "response": "🌐 IP Grabber activé (c'est du fake)", "enabled": False, "count": 0},
    ]
    update_stats()

def update_stats():
    global stats
    stats["total_commands"] = len(commands)
    stats["active_commands"] = sum(1 for cmd in commands if cmd["enabled"])

# ========== API FLASK ==========
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "🟢 Bot Discord actif avec Rich Presence + Commandes qui répondent!"

@app.route('/api/commands', methods=['GET'])
def get_commands():
    return jsonify({
        "success": True,
        "commands": commands,
        "stats": {
            **stats,
            "uptime": int(time.time() - stats["start_time"])
        }
    })

@app.route('/api/commands', methods=['POST'])
def add_command():
    data = request.json
    new_cmd = {
        "name": data.get("name"),
        "response": data.get("response"),
        "enabled": True,
        "count": 0
    }
    commands.append(new_cmd)
    update_stats()
    logger.info(f"➕ Commande ajoutée: {new_cmd['name']}")
    return jsonify({"success": True, "command": new_cmd})

@app.route('/api/commands/<int:index>', methods=['DELETE'])
def delete_command(index):
    if 0 <= index < len(commands):
        deleted = commands.pop(index)
        update_stats()
        logger.info(f"🗑️ Commande supprimée: {deleted['name']}")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Index invalide"}), 404

@app.route('/api/commands/<int:index>/toggle', methods=['POST'])
def toggle_command(index):
    if 0 <= index < len(commands):
        commands[index]["enabled"] = not commands[index]["enabled"]
        update_stats()
        status = "activée" if commands[index]["enabled"] else "désactivée"
        logger.info(f"🔄 Commande {status}: {commands[index]['name']}")
        return jsonify({"success": True, "enabled": commands[index]["enabled"]})
    return jsonify({"success": False, "error": "Index invalide"}), 404

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    """Lance un serveur web pour garder le bot actif"""
    t = Thread(target=run_flask, daemon=True)
    t.start()
    logger.info(f"🌐 API démarrée sur le port 8080")

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
        self.http_session = None

    async def send_message(self, channel_id, content):
        """Envoie un message via l'API REST Discord"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
        
        url = f"{DISCORD_API}/channels/{channel_id}/messages"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        payload = {"content": content}
        
        try:
            async with self.http_session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Message envoyé dans le channel {channel_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Erreur envoi message ({resp.status}): {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi: {e}")
            return False

    async def connect(self):
        """Boucle de connexion principale avec logique de reconnexion"""
        max_retries = 10
        
        while self.should_reconnect and self.reconnect_count < max_retries:
            try:
                self.ws = await websockets.connect(GATEWAY_URL, max_size=None)
                logger.info("✅ Connecté au Gateway Discord")
                self.reconnect_count = 0
                
                await self.identify()
                await self.listen()
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ Connexion fermée: {e}")
                self.reconnect_count += 1
                wait_time = min(5 * self.reconnect_count, 30)
                logger.info(f"🔄 Reconnexion dans {wait_time}s... (tentative {self.reconnect_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
                self.reconnect_count += 1
                await asyncio.sleep(10)
            
            finally:
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
        
        if self.reconnect_count >= max_retries:
            logger.error("❌ Nombre maximum de reconnexions atteint")

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
        """Envoie des heartbeats réguliers"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval / 1000)
                heartbeat = {"op": 1, "d": self.sequence}
                await self.ws.send(json.dumps(heartbeat))
                logger.debug("💓 Heartbeat envoyé")
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
                    
                    elif event_type == "MESSAGE_CREATE":
                        await self.handle_message(d)
                
                # Heartbeat ACK
                elif op == 11:
                    logger.debug("✅ Heartbeat ACK")
                
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
                    logger.warning("🔄 Reconnexion demandée")
                    raise websockets.exceptions.ConnectionClosed(1000, "Reconnect")
                
            except json.JSONDecodeError:
                logger.error("❌ Erreur JSON")
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")

    async def handle_message(self, data):
        """Gère les commandes et ENVOIE les réponses"""
        content = data.get("content", "")
        author = data.get("author", {})
        author_id = author.get("id")
        channel_id = data.get("channel_id")
        
        if not content or not author_id or not channel_id:
            return
        
        # Cherche une commande correspondante
        for cmd in commands:
            if cmd["enabled"] and content.startswith(cmd["name"]):
                cmd["count"] += 1
                stats["total_executions"] += 1
                
                # Formate la réponse avec variables dynamiques
                response = cmd["response"]
                response = response.replace("{time}", str(int(time.time() * 1000) % 1000))
                response = response.replace("{uptime}", str(int(time.time() - stats["start_time"])))
                response = response.replace("{count}", str(stats["total_executions"]))
                
                logger.info(f"🎯 Commande détectée: {cmd['name']} (#{cmd['count']})")
                
                # 🔥 ENVOIE LA RÉPONSE DANS LE CHANNEL 🔥
                await self.send_message(channel_id, response)
                break

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
        if self.http_session:
            await self.http_session.close()
        if self.ws:
            await self.ws.close()
        logger.info("👋 Connexion fermée")


async def main():
    """Fonction principale"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("❌ Variable DISCORD_TOKEN manquante")
        logger.info("💡 Ajoute ton token dans les variables d'environnement")
        return

    logger.info("🚀 Démarrage du selfbot Discord COMPLET...")
    logger.info("✅ Rich Presence + Détection + ENVOI de réponses activé!")
    logger.warning("⚠️ Les selfbots violent les CGU de Discord - utilisez à vos risques")
    
    init_commands()
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
