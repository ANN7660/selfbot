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

# ========== STOCKAGE DES DONNÉES ==========
commands = []
stats = {
    "total_commands": 0,
    "active_commands": 0,
    "total_executions": 0,
    "start_time": time.time()
}

# Système de snipe
deleted_messages = {}
edited_messages = {}
removed_reactions = {}

# ========== COMMANDES MEGA COMPLÈTES ==========
def init_commands():
    global commands
    commands = [
        # === COMMANDES BASIQUES ===
        {"name": "?ping", "response": "🏓 Pong! Latence: {time}ms", "enabled": True, "count": 0, "color": 0x00FF00},
        {"name": "?help", "response": "📋 **Commandes B2:**\n`?ping` `?info` `?stats` `?purge` `?embed` `?avatar` `?snipe` `?spam` `?raid` `?nuke` `?discord` `?guns` `?b2`", "enabled": True, "count": 0, "color": 0x5865F2},
        {"name": "?info", "response": "ℹ️ **B2 Selfbot** | Version 3.0 MEGA | Uptime: {uptime}s | By Crown 👑", "enabled": True, "count": 0, "color": 0x3498DB},
        
        # === UTILITAIRES ===
        {"name": "?avatar", "response": "🖼️ Avatar récupéré!", "enabled": True, "count": 0, "color": 0x9B59B6},
        {"name": "?userinfo", "response": "👤 **Informations utilisateur**", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?serverinfo", "response": "🏠 **Informations serveur**", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?snipe", "response": "👻 Aucun message supprimé récemment", "enabled": True, "count": 0, "color": 0x95A5A6},
        {"name": "?embed", "response": "📰 Embed créé avec succès!", "enabled": True, "count": 0, "color": 0xF39C12},
        
        # === GESTION DES MESSAGES ===
        {"name": "?edit", "response": "✏️ Message édité!", "enabled": True, "count": 0, "color": 0xE67E22},
        {"name": "?delete", "response": "🗑️ Message supprimé!", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?quote", "response": "💬 Message cité!", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?copy", "response": "📋 Message copié!", "enabled": True, "count": 0, "color": 0x1ABC9C},
        
        # === RÉACTIONS AUTOMATIQUES ===
        {"name": "?reactall", "response": "😂 Réactions ajoutées!", "enabled": True, "count": 0, "color": 0xF1C40F},
        {"name": "?unreact", "response": "❌ Réactions supprimées!", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?reactraid", "response": "💥 Raid de réactions lancé!", "enabled": True, "count": 0, "color": 0xFF0000},
        
        # === EMBEDS PERSONNALISÉS ===
        {"name": "?announceembed", "response": "📢 Annonce créée!", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?infoembed", "response": "ℹ️ Info embed créé!", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?warningembed", "response": "⚠️ Warning embed créé!", "enabled": True, "count": 0, "color": 0xF39C12},
        {"name": "?errorembed", "response": "❌ Error embed créé!", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?customembed", "response": "🎨 Embed personnalisé créé!", "enabled": True, "count": 0, "color": 0x9B59B6},
        
        # === IMAGES & MÉDIAS ===
        {"name": "?sendimg", "response": "🖼️ Image envoyée!", "enabled": True, "count": 0, "color": 0x9B59B6},
        {"name": "?gif", "response": "🎞️ GIF envoyé!", "enabled": True, "count": 0, "color": 0xE91E63},
        {"name": "?sticker", "response": "😀 Sticker envoyé!", "enabled": True, "count": 0, "color": 0xF1C40F},
        {"name": "?screenshot", "response": "📸 Screenshot pris!", "enabled": True, "count": 0, "color": 0x607D8B},
        
        # === RÉCUPÉRATION D'INFOS ===
        {"name": "?whois", "response": "🔍 Informations utilisateur récupérées!", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?servericon", "response": "🏠 Icône du serveur récupérée!", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?banner", "response": "🎨 Bannière récupérée!", "enabled": True, "count": 0, "color": 0x9B59B6},
        {"name": "?roles", "response": "🎭 Liste des rôles récupérée!", "enabled": True, "count": 0, "color": 0x11806A},
        {"name": "?members", "response": "👥 Liste des membres récupérée!", "enabled": True, "count": 0, "color": 0x206694},
        {"name": "?channels", "response": "📝 Liste des channels récupérée!", "enabled": True, "count": 0, "color": 0x71368A},
        
        # === MODÉRATION (FAKE) ===
        {"name": "?purge", "response": "🗑️ Purge effectuée (simulation)", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?clear", "response": "🧹 Messages nettoyés! (simulation)", "enabled": True, "count": 0, "color": 0x95A5A6},
        {"name": "?ban", "response": "🔨 Utilisateur banni (simulation)", "enabled": True, "count": 0, "color": 0x992D22},
        {"name": "?kick", "response": "👢 Utilisateur kick (simulation)", "enabled": True, "count": 0, "color": 0xE67E22},
        
        # === SPAM & FLOOD ===
        {"name": "?spam", "response": "💥 Spam lancé! 🔥", "enabled": True, "count": 0, "color": 0xFF0000},
        {"name": "?raid", "response": "⚔️ RAID MODE ACTIVATED 💀", "enabled": True, "count": 0, "color": 0x8B0000},
        {"name": "?massping", "response": "📢 Mass ping lancé!", "enabled": False, "count": 0, "color": 0xFF6347},
        {"name": "?flood", "response": "🌊 Flood activé!", "enabled": False, "count": 0, "color": 0x1E90FF},
        {"name": "?slowspam", "response": "🐌 Spam lent activé!", "enabled": True, "count": 0, "color": 0xFFD700},
        {"name": "?copyspam", "response": "📋 Spam de copie lancé!", "enabled": False, "count": 0, "color": 0xFF8C00},
        
        # === AUTO-RÉPONSES ===
        {"name": "?afk", "response": "💤 Mode AFK activé!", "enabled": True, "count": 0, "color": 0x95A5A6},
        {"name": "?autoresponse", "response": "🤖 Auto-réponse configurée!", "enabled": True, "count": 0, "color": 0x00CED1},
        {"name": "?autoreact", "response": "⚡ Auto-réaction activée!", "enabled": True, "count": 0, "color": 0xFFD700},
        
        # === FUN & MEMES ===
        {"name": "?8ball", "response": "🎱 Réponse magique: Oui, certainement!", "enabled": True, "count": 0, "color": 0x9B59B6},
        {"name": "?coinflip", "response": "🪙 Pile!", "enabled": True, "count": 0, "color": 0xF39C12},
        {"name": "?dice", "response": "🎲 Vous avez fait: 6!", "enabled": True, "count": 0, "color": 0xE74C3C},
        {"name": "?mock", "response": "🤡 tExTe MoCkÉ!", "enabled": True, "count": 0, "color": 0xFF69B4},
        {"name": "?reverse", "response": "🔄 txeT esreveR!", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?emojify", "response": "😂 Texte émojifié!", "enabled": True, "count": 0, "color": 0xFFD700},
        {"name": "?zalgo", "response": "👹 T̴̢̛e̸x̶t̴e̷ ̵Z̸a̷l̶g̴o̴!", "enabled": True, "count": 0, "color": 0x8B0000},
        {"name": "?ascii", "response": "```\n▄▀█ █▀ █▀▀ █ █\n█▀█ ▄█ █▄▄ █ █\n```", "enabled": True, "count": 0, "color": 0x34495E},
        {"name": "?ghost", "response": "👻 Mode fantôme activé...", "enabled": True, "count": 0, "color": 0x95A5A6},
        {"name": "?fake", "response": "🎭 Message fake envoyé!", "enabled": True, "count": 0, "color": 0xE91E63},
        
        # === TOXIC/TROLL (FAKE) ===
        {"name": "?nuke", "response": "💣 NUKE DEPLOYED 💥💥💥 (fake lol)", "enabled": True, "count": 0, "color": 0xFF0000},
        {"name": "?destroy", "response": "🔥 DESTRUCTION EN COURS... 💀 (simulation)", "enabled": True, "count": 0, "color": 0x8B0000},
        {"name": "?hack", "response": "💻 Hacking in progress... █████░░░░░ 50% (fake)", "enabled": True, "count": 0, "color": 0x00FF00},
        {"name": "?ddos", "response": "⚠️ DDoS simulation lancée (c'est du fake)", "enabled": True, "count": 0, "color": 0xFF4500},
        
        # === RAID/TROLL AVANCÉ (DÉSACTIVÉ) ===
        {"name": "?massdm", "response": "📨 Mass DM lancé!", "enabled": False, "count": 0, "color": 0xFF1493},
        {"name": "?serverspam", "response": "💥 Server spam activé!", "enabled": False, "count": 0, "color": 0xFF0000},
        {"name": "?channelspam", "response": "📝 Channel spam lancé!", "enabled": False, "count": 0, "color": 0xFF6347},
        {"name": "?rolesspam", "response": "🎭 Roles spam activé!", "enabled": False, "count": 0, "color": 0xFF4500},
        
        # === NITRO/BOOST FAKE ===
        {"name": "?nitro", "response": "💎 discord.gift/fakenitro (c'est fake mdr)", "enabled": False, "count": 0, "color": 0xFF73FA},
        {"name": "?fakenitro", "response": "💎 discord.gift/fakeN1tr0xXx (c'est fake mdr)", "enabled": True, "count": 0, "color": 0xFF73FA},
        {"name": "?fakeboost", "response": "🚀 Serveur boosté! (fake lol)", "enabled": True, "count": 0, "color": 0xF47FFF},
        {"name": "?token", "response": "🔑 Token grabber: [REDACTED] (fake évidemment)", "enabled": False, "count": 0, "color": 0x992D22},
        {"name": "?ip", "response": "🌐 IP Grabber activé (c'est du fake)", "enabled": False, "count": 0, "color": 0xFF4500},
        
        # === LOGS & SNIPE ===
        {"name": "?editsnipe", "response": "✏️ Dernier message édité récupéré!", "enabled": True, "count": 0, "color": 0xE67E22},
        {"name": "?reactionsnipe", "response": "😂 Dernière réaction supprimée récupérée!", "enabled": True, "count": 0, "color": 0xF1C40F},
        {"name": "?clearsnipe", "response": "🧹 Historique snipe nettoyé!", "enabled": True, "count": 0, "color": 0x95A5A6},
        
        # === CALCULATEUR & UTILS ===
        {"name": "?calc", "response": "🔢 Résultat: 42", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?base64", "response": "🔐 Texte encodé en base64!", "enabled": True, "count": 0, "color": 0x34495E},
        {"name": "?qr", "response": "📱 QR Code généré!", "enabled": True, "count": 0, "color": 0x27AE60},
        {"name": "?shorten", "response": "🔗 URL raccourcie!", "enabled": True, "count": 0, "color": 0x3498DB},
        
        # === SERVEUR INFO ===
        {"name": "?boosts", "response": "🚀 Niveau de boost: 2 (14 boosts)", "enabled": True, "count": 0, "color": 0xF47FFF},
        {"name": "?emojis", "response": "😀 Liste des emojis du serveur!", "enabled": True, "count": 0, "color": 0xFFD700},
        {"name": "?bots", "response": "🤖 Liste des bots du serveur!", "enabled": True, "count": 0, "color": 0x607D8B},
        
        # === ASCII ART ===
        {"name": "?ascii2", "response": "```\n██████╗ ██████╗ \n██╔══██╗╚════██╗\n██████╔╝ █████╔╝\n██╔══██╗██╔═══╝ \n██████╔╝███████╗\n╚═════╝ ╚══════╝\n```", "enabled": True, "count": 0, "color": 0x34495E},
        {"name": "?crown", "response": "```\n   _____ _____   ______          ___   _ \n  / ____|  __ \\ / __ \\ \\        / / \\ | |\n | |    | |__) | |  | \\ \\  /\\  / /|  \\| |\n | |    |  _  /| |  | |\\ \\/  \\/ / | . ` |\n | |____| | \\ \\| |__| | \\  /\\  /  | |\\  |\n  \\_____|_|  \\_\\\\____/   \\/  \\/   |_| \\_|\n```", "enabled": True, "count": 0, "color": 0xFFD700},
        
        # === RICH PRESENCE ===
        {"name": "?rpcgaming", "response": "🎮 Rich Presence: Gaming activée!", "enabled": True, "count": 0, "color": 0x593695},
        {"name": "?rpcmusic", "response": "🎵 Rich Presence: Music activée!", "enabled": True, "count": 0, "color": 0x1DB954},
        {"name": "?rpcstreaming", "response": "📺 Rich Presence: Streaming activée!", "enabled": True, "count": 0, "color": 0x9146FF},
        {"name": "?rpccustom", "response": "✨ Rich Presence personnalisée activée!", "enabled": True, "count": 0, "color": 0x5865F2},
        
        # === STATUS CHANGER ===
        {"name": "?online", "response": "🟢 Status: En ligne", "enabled": True, "count": 0, "color": 0x43B581},
        {"name": "?idle", "response": "🟡 Status: Inactif", "enabled": True, "count": 0, "color": 0xFAA61A},
        {"name": "?dnd", "response": "🔴 Status: Ne pas déranger", "enabled": True, "count": 0, "color": 0xF04747},
        {"name": "?invisible", "response": "⚫ Status: Invisible", "enabled": True, "count": 0, "color": 0x747F8D},
        
        # === BACKUP & EXPORT ===
        {"name": "?backup", "response": "💾 Backup du serveur créé!", "enabled": False, "count": 0, "color": 0x206694},
        {"name": "?export", "response": "📤 Messages exportés!", "enabled": True, "count": 0, "color": 0x11806A},
        {"name": "?clone", "response": "👯 Serveur cloné!", "enabled": False, "count": 0, "color": 0x992D22},
        
        # === LIENS & SOCIALS ===
        {"name": "?discord", "response": "👑 **Crown Discord:** https://discord.gg/bC8Jcjdr3H", "enabled": True, "count": 0, "color": 0x5865F2},
        {"name": "?guns", "response": "🔫 **Mon profil:** https://guns.lol/17h40", "enabled": True, "count": 0, "color": 0xFF0000},
        {"name": "?b2", "response": "🌍 **B2 Community** - La meilleure team française 🍇🔥", "enabled": True, "count": 0, "color": 0x9B59B6},
        
        # === STATS ===
        {"name": "?stats", "response": "📊 **Stats:** Exécutions: {count} | Uptime: {uptime}s", "enabled": True, "count": 0, "color": 0x3498DB},
        {"name": "?uptime", "response": "⏱️ Bot actif depuis: {uptime}s", "enabled": True, "count": 0, "color": 0x1ABC9C},
        {"name": "?version", "response": "🆔 **B2 Selfbot v3.0 MEGA** - Coded by Crown 👑", "enabled": True, "count": 0, "color": 0xE91E63},
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
    return "🟢 B2 Selfbot MEGA v3.0 - ACTIF avec 100+ commandes!"

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
        "count": 0,
        "color": data.get("color", 0x5865F2)
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

@app.route('/api/snipe/<channel_id>', methods=['GET'])
def get_snipe(channel_id):
    """Récupère les messages snipés d'un channel"""
    return jsonify({
        "deleted": deleted_messages.get(channel_id, None),
        "edited": edited_messages.get(channel_id, None),
        "reactions": removed_reactions.get(channel_id, None)
    })

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    """Lance le serveur Flask"""
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
        self.user_id = None

    async def send_message(self, channel_id, content, use_embed=True, color=None):
        """Envoie un message (texte simple OU embed)"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
        
        url = f"{DISCORD_API}/channels/{channel_id}/messages"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        
        # 🔥 SI use_embed = True, envoie en EMBED
        if use_embed:
            embed = {
                "description": content,
                "color": color or 0x5865F2,
                "footer": {
                    "text": "B2 Selfbot v3.0 | By Crown 👑"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            payload = {"embeds": [embed]}
        else:
            # Sinon message texte classique
            payload = {"content": content}
        
        try:
            async with self.http_session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Message envoyé dans {channel_id}")
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Erreur envoi ({resp.status}): {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Erreur envoi: {e}")
            return None

    async def send_embed(self, channel_id, title, description, color=0x5865F2, thumbnail=None, image=None, fields=None):
        """Envoie un embed personnalisé avancé"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
        
        url = f"{DISCORD_API}/channels/{channel_id}/messages"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "B2 Selfbot v3.0"}
        }
        
        if thumbnail:
            embed["thumbnail"] = {"url": thumbnail}
        if image:
            embed["image"] = {"url": image}
        if fields:
            embed["fields"] = fields
        
        payload = {"embeds": [embed]}
        
        try:
            async with self.http_session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    logger.info("✅ Embed avancé envoyé!")
                    return await resp.json()
                else:
                    logger.error(f"❌ Erreur embed: {await resp.text()}")
                    return None
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return None

    async def add_reaction(self, channel_id, message_id, emoji):
        """Ajoute une réaction à un message"""
        url = f"{DISCORD_API}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        headers = {"Authorization": self.token}
        
        try:
            async with self.http_session.put(url, headers=headers) as resp:
                if resp.status == 204:
                    logger.info(f"✅ Réaction {emoji} ajoutée")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Erreur réaction: {e}")
            return False

    async def delete_message(self, channel_id, message_id):
        """Supprime un message"""
        url = f"{DISCORD_API}/channels/{channel_id}/messages/{message_id}"
        headers = {"Authorization": self.token}
        
        try:
            async with self.http_session.delete(url, headers=headers) as resp:
                return resp.status == 204
        except Exception as e:
            logger.error(f"❌ Erreur suppression: {e}")
            return False

    async def edit_message(self, channel_id, message_id, new_content):
        """Édite un message"""
        url = f"{DISCORD_API}/channels/{channel_id}/messages/{message_id}"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        payload = {"content": new_content}
        
        try:
            async with self.http_session.patch(url, headers=headers, json=payload) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"❌ Erreur édition: {e}")
            return False

    async def get_channel_messages(self, channel_id, limit=50):
        """Récupère les messages d'un channel"""
        url = f"{DISCORD_API}/channels/{channel_id}/messages?limit={limit}"
        headers = {"Authorization": self.token}
        
        try:
            async with self.http_session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération messages: {e}")
            return []

    async def get_user_info(self, user_id):
        """Récupère les infos d'un utilisateur"""
        url = f"{DISCORD_API}/users/{user_id}"
        headers = {"Authorization": self.token}
        
        try:
            async with self.http_session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"❌ Erreur récupération utilisateur: {e}")
            return None

    async def connect(self):
        """Boucle de connexion avec reconnexion automatique"""
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
                logger.info(f"🔄 Reconnexion dans {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
                self.reconnect_count += 1
                await asyncio.sleep(10)
            
            finally:
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
        
        if self.reconnect_count >= max_retries:
            logger.error("❌ Trop de tentatives de reconnexion")

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
        logger.info("📤 Identification envoyée")

    async def update_presence(self, status="online", activity_name="B2 🌍", details="restez branché", state="B2 ON TOP 🍇"):
        """Met à jour la Rich Presence"""
        payload = {
            "op": 3,
            "d": {
                "status": status,
                "activities": [
                    {
                        "type": 5,
                        "application_id": CLIENT_ID,
                        "name": activity_name,
                        "details": details,
                        "state": state,
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
        """Envoie des heartbeats"""
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
        
    async def listen(self): # Ligne 544
        """Écoute les événements Discord"""
        async for message in self.ws: # <-- Le code DOIT commencer ici, avec une indentation (4 espaces ou une tabulation)
            try:
                data = json.loads(message)
                op = data.get("op")
                d = data.get("d")
                
                if data.get("s"):
                    self.sequence = data["s"]
                
                # Hello
                if op == 10:
                    self.heartbeat_interval = d["heartbeat_interval"]
                    logger.info(f"💓 Heartbeat: {self.heartbeat_interval}ms")
                    self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
                # ... (le reste de la fonction)
                
                # Dispatch
                elif op == 0:
                    event_type = data.get("t")
                    
                    if event_type == "READY":
                        user = d.get("user", {})
                        self.user_id = user.get("id")
                        username = user.get("username", "Inconnu")
                        logger.info(f"🎉 Connecté: {username} (ID: {self.user_id})")
                        self.session_id = d.get("session_id")
                        await self.update_presence()
                    
                    elif event_type == "RESUMED":
                        logger.info("🔄 Session reprise")
                    
                    elif event_type == "MESSAGE_CREATE":
                        await self.handle_message(d)
                    
                    # 👻 SNIPE: Message supprimé
                    elif event_type == "MESSAGE_DELETE":
                        channel_id = d.get("channel_id")
                        deleted_messages[channel_id] = {
                            "id": d.get("id"),
                            "time": datetime.now().isoformat()
                        }
                        logger.debug(f"👻 Message supprimé dans {channel_id}")
                    
                    # ✏️ SNIPE: Message édité
                    elif event_type == "MESSAGE_UPDATE":
                        channel_id = d.get("channel_id")
                        content = d.get("content")
                        if content:
                            edited_messages[channel_id] = {
                                "content": content,
                                "author": d.get("author", {}).get("username", "Inconnu"),
                                "time": datetime.now().isoformat()
                            }
                            logger.debug(f"✏️ Message édité dans {channel_id}")
                    
                    # 😂 SNIPE: Réaction supprimée
                    elif event_type == "MESSAGE_REACTION_REMOVE":
                        channel_id = d.get("channel_id")
                        emoji = d.get("emoji", {}).get("name", "❓")
                        removed_reactions[channel_id] = {
                            "emoji": emoji,
                            "time": datetime.now().isoformat()
                        }
                        logger.debug(f"😂 Réaction supprimée: {emoji}")
                
                # Heartbeat ACK
                elif op == 11:
                    logger.debug("✅ Heartbeat ACK")
                
                # Demande heartbeat
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
                
                # Reconnect
                elif op == 7:
                    logger.warning("🔄 Reconnexion demandée")
                    raise websockets.exceptions.ConnectionClosed(1000, "Reconnect")
                
            except json.JSONDecodeError:
                logger.error("❌ Erreur JSON")
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")

    async def handle_message(self, data):
        """🔥 GÈRE TOUTES LES COMMANDES ET ENVOIE LES RÉPONSES EN EMBED 🔥"""
        content = data.get("content", "")
        author = data.get("author", {})
        author_id = author.get("id")
        channel_id = data.get("channel_id")
        message_id = data.get("id")
        
        if not content or not author_id or not channel_id:
            return
        
        # Ne répond qu'à ses propres messages (selfbot)
        if author_id != self.user_id:
            return
        
        # Cherche une commande correspondante
        for cmd in commands:
            if cmd["enabled"] and content.startswith(cmd["name"]):
                cmd["count"] += 1
                stats["total_executions"] += 1
                
                # Formate la réponse
                response = cmd["response"]
                response = response.replace("{time}", str(int(time.time() * 1000) % 1000))
                response = response.replace("{uptime}", str(int(time.time() - stats["start_time"])))
                response = response.replace("{count}", str(stats["total_executions"]))
                
                logger.info(f"🎯 Commande: {cmd['name']} (#{cmd['count']})")
                
                # 🔥 ENVOIE LA RÉPONSE EN EMBED 🔥
                color = cmd.get("color", 0x5865F2)
                await self.send_message(channel_id, response, use_embed=True, color=color)
                
                # ===== ACTIONS SPÉCIALES =====
                
                # ?snipe - Affiche les messages supprimés
                if cmd["name"] == "?snipe":
                    snipe_data = deleted_messages.get(channel_id)
                    if snipe_data:
                        await self.send_message(
                            channel_id,
                            f"👻 **Message supprimé**\nID: {snipe_data['id']}\nHeure: {snipe_data['time']}",
                            use_embed=True,
                            color=0x95A5A6
                        )
                
                # ?editsnipe - Affiche les messages édités
                elif cmd["name"] == "?editsnipe":
                    edit_data = edited_messages.get(channel_id)
                    if edit_data:
                        await self.send_message(
                            channel_id,
                            f"✏️ **Message édité**\nAuteur: {edit_data['author']}\nContenu: {edit_data['content']}\nHeure: {edit_data['time']}",
                            use_embed=True,
                            color=0xE67E22
                        )
                
                # ?reactionsnipe - Affiche les réactions supprimées
                elif cmd["name"] == "?reactionsnipe":
                    react_data = removed_reactions.get(channel_id)
                    if react_data:
                        await self.send_message(
                            channel_id,
                            f"😂 **Réaction supprimée**\nEmoji: {react_data['emoji']}\nHeure: {react_data['time']}",
                            use_embed=True,
                            color=0xF1C40F
                        )
                
                # ?clearsnipe - Nettoie l'historique
                elif cmd["name"] == "?clearsnipe":
                    deleted_messages.clear()
                    edited_messages.clear()
                    removed_reactions.clear()
                
                # ?purge - Supprime ses propres messages
                elif cmd["name"] == "?purge":
                    try:
                        amount = int(content.split()[1]) if len(content.split()) > 1 else 10
                        messages = await self.get_channel_messages(channel_id, limit=100)
                        
                        deleted = 0
                        for msg in messages:
                            if msg['author']['id'] == self.user_id and deleted < amount:
                                await self.delete_message(channel_id, msg['id'])
                                deleted += 1
                                await asyncio.sleep(0.5)
                        
                        logger.info(f"🗑️ {deleted} messages supprimés")
                    except Exception as e:
                        logger.error(f"❌ Erreur purge: {e}")
                
                # ?avatar - Récupère l'avatar
                elif cmd["name"] == "?avatar":
                    mentions = data.get("mentions", [])
                    if mentions:
                        user = mentions[0]
                        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=1024"
                        await self.send_embed(
                            channel_id,
                            f"Avatar de {user['username']}",
                            f"[Cliquez ici]({avatar_url})",
                            color=0x9B59B6,
                            image=avatar_url
                        )
                
                # ?whois - Infos utilisateur
                elif cmd["name"] == "?whois":
                    mentions = data.get("mentions", [])
                    if mentions:
                        user = mentions[0]
                        user_info = await self.get_user_info(user['id'])
                        if user_info:
                            await self.send_embed(
                                channel_id,
                                f"👤 {user_info.get('username')}",
                                f"ID: `{user_info['id']}`\nTag: {user_info.get('discriminator', 'N/A')}",
                                color=0x3498DB,
                                thumbnail=f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png"
                            )
                
                # ?react - Ajoute réaction au dernier message
                elif cmd["name"] == "?reactall":
                    messages = await self.get_channel_messages(channel_id, limit=2)
                    if len(messages) > 1:
                        emojis = ["👍", "❤️", "😂", "🔥", "✅"]
                        for emoji in emojis:
                            await self.add_reaction(channel_id, messages[1]['id'], emoji)
                            await asyncio.sleep(0.3)
                
                # ?online/idle/dnd/invisible - Change le status
                elif cmd["name"] in ["?online", "?idle", "?dnd", "?invisible"]:
                    status_map = {
                        "?online": "online",
                        "?idle": "idle",
                        "?dnd": "dnd",
                        "?invisible": "invisible"
                    }
                    await self.update_presence(status=status_map[cmd["name"]])
                
                # ?rpcgaming/music/streaming - Change la RPC
                elif cmd["name"] == "?rpcgaming":
                    await self.update_presence(
                        activity_name="🎮 Gaming",
                        details="En train de jouer",
                        state="GG EZ"
                    )
                elif cmd["name"] == "?rpcmusic":
                    await self.update_presence(
                        activity_name="🎵 Music",
                        details="En train d'écouter",
                        state="Vibing 🎧"
                    )
                elif cmd["name"] == "?rpcstreaming":
                    await self.update_presence(
                        activity_name="📺 Streaming",
                        details="En live",
                        state="twitch.tv/crown"
                    )
                
                break

    async def resume(self):
        """Reprend une session"""
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
        """Ferme la connexion"""
        self.should_reconnect = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.http_session:
            await self.http_session.close()
        if self.ws:
            await self.ws.close()
        logger.info("👋 Connexion fermée")


# ========== FONCTION PRINCIPALE ==========
async def main():
    """Point d'entrée principal"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("❌ Variable DISCORD_TOKEN manquante!")
        logger.info("💡 Ajoute ton token dans les variables d'environnement")
        return

    logger.info("=" * 60)
    logger.info("🚀 B2 SELFBOT MEGA v3.0 - DÉMARRAGE")
    logger.info("=" * 60)
    logger.info("✅ Rich Presence activée")
    logger.info("✅ 100+ commandes chargées")
    logger.info("✅ Réponses en EMBED activées")
    logger.info("✅ Système de snipe activé")
    logger.info("✅ API Flask activée")
    logger.warning("⚠️ Les selfbots violent les CGU Discord - Risque de ban!")
    logger.info("=" * 60)
    
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
