import requests
import time
import os
from datetime import datetime
from flask import Flask
from threading import Thread

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

# --- CONFIGURATION ---
CLIENT_ID = '1410787199745888747'
IMAGE_NAME = 'logo_b2'
# --------------------

# Keep-alive pour Render
app = Flask('')

@app.route('/')
def home():
    return "Discord Presence Active! ✨"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

def update_presence(token):
    """Met à jour la Rich Presence via l'API Discord"""
    
    url = "https://discord.com/api/v9/users/@me/settings"
    
    payload = {
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
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.patch(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Rich Presence mise à jour | {datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant")
        return
    
    print("🚀 Selfbot Discord Rich Presence")
    print("⚠️  Viole les ToS - Risque de ban")
    print("-" * 50)
    print(f"🎮 App: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("-" * 50)
    
    # Démarrer Flask pour keep-alive
    keep_alive()
    print("🌐 Serveur Flask démarré sur port 10000")
    
    # Première mise à jour
    if update_presence(TOKEN):
        print("✨ Présence activée !")
    
    # Boucle de rafraîchissement
    while True:
        try:
            time.sleep(900)  # 15 minutes
            print("\n🔄 Rafraîchissement...")
            update_presence(TOKEN)
            
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt...")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
