import requests
import time
import os
from datetime import datetime

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

# --- CONFIGURATION ---
CLIENT_ID = '1410787199745888747'  # ID de ton application Discord
IMAGE_NAME = 'logo_b2'  # Nom de ton image dans Art Assets
# --------------------

def update_presence(token):
    """Met à jour la Rich Presence via l'API Discord Gateway"""
    
    url = "https://discord.com/api/v9/users/@me/settings"
    
    # Payload avec la Rich Presence complète
    payload = {
        "activities": [{
            "type": 0,  # 0 = Joue à...
            "name": "HK X B2",  # Nom du jeu/activité
            "application_id": CLIENT_ID,  # Ton application
            "details": "V1",  # Ligne du haut
            "state": "guns.lol/17h40",  # Ligne du bas
            "timestamps": {
                "start": int(time.time() * 1000)  # Temps de début en millisecondes
            },
            "assets": {
                "large_image": IMAGE_NAME,  # Grande image
                "large_text": "HK X B2",  # Texte sur la grande image
                "small_image": IMAGE_NAME,  # Petite image
                "small_text": "En ligne"  # Texte sur la petite image
            },
            "buttons": [
                "guns lol b2"  # Texte du bouton (l'URL est définie dans l'app Discord)
            ],
            "metadata": {
                "button_urls": [
                    "https://guns.lol/17h40"  # URL du bouton
                ]
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
            print(f"✅ Rich Presence mise à jour avec succès !")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def maintain_presence():
    """Maintient la présence active en la rafraîchissant régulièrement"""
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ERREUR: Variable DISCORD_TOKEN non définie")
        print("📝 Sur Render: Ajoute DISCORD_TOKEN dans Environment Variables")
        return
    
    print("🚀 Démarrage du selfbot Discord avec Rich Presence...")
    print("⚠️  RAPPEL: Ceci viole les ToS Discord - Risque de ban")
    print("-" * 60)
    print(f"🎮 Application: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("-" * 60)
    
    # Première mise à jour
    if update_presence(TOKEN):
        print("✨ Rich Presence active avec images et boutons !")
        print("💡 Rafraîchissement automatique toutes les 15 minutes...")
    
    # Boucle de maintien
    while True:
        try:
            time.sleep(900)  # 15 minutes
            print("\n🔄 Rafraîchissement de la présence...")
            update_presence(TOKEN)
            
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt du selfbot...")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            time.sleep(60)

if __name__ == "__main__":
    maintain_presence()
