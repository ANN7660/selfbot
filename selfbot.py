import requests
import time
import os
from datetime import datetime
from flask import Flask
from threading import Thread

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
    
    print("📡 Tentative de mise à jour de la présence...")
    
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
        print("🔄 Envoi de la requête à Discord...")
        response = requests.patch(url, json=payload, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Rich Presence mise à jour | {datetime.now().strftime('%H:%M:%S')}")
            return True
        elif response.status_code == 401:
            print(f"❌ Token invalide ! Vérifie ton DISCORD_TOKEN")
            return False
        elif response.status_code == 403:
            print(f"❌ Accès refusé (ban possible ou rate limit)")
            return False
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout - Discord ne répond pas")
        return False
    except Exception as e:
        print(f"❌ Erreur: {type(e).__name__}: {e}")
        return False

def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("🚀 Selfbot Discord Rich Presence")
    print("⚠️  Viole les ToS - Risque de ban")
    print("-" * 50)
    print(f"🎮 App: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("-" * 50)
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant dans les variables d'environnement !")
        print("📝 Ajoute-le dans Render → Environment")
        return
    
    print(f"🔑 Token trouvé (longueur: {len(TOKEN)} caractères)")
    print(f"🔑 Token commence par: {TOKEN[:20]}...")
    
    # Démarrer Flask pour keep-alive
    keep_alive()
    print("🌐 Serveur Flask démarré sur port 10000")
    print("-" * 50)
    
    # Première mise à jour
    success = update_presence(TOKEN)
    
    if success:
        print("✨ Présence activée avec succès !")
    else:
        print("⚠️ Échec de l'activation, nouvelle tentative dans 60s...")
    
    print("-" * 50)
    print("💡 Le bot va se rafraîchir toutes les 15 minutes")
    print("-" * 50)
    
    # Boucle de rafraîchissement
    while True:
        try:
            time.sleep(900)  # 15 minutes
            print(f"\n🔄 Rafraîchissement automatique - {datetime.now().strftime('%H:%M:%S')}")
            update_presence(TOKEN)
            
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt...")
            break
        except Exception as e:
            print(f"❌ Erreur dans la boucle: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
#
