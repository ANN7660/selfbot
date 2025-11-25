import discord
import asyncio
import os
from datetime import datetime

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

# --- CONFIGURATION ---
CLIENT_ID = '1410787199745888747'  # ID de ton application Discord
IMAGE_NAME = 'logo_b2'  # Nom de ton image dans Art Assets
# --------------------

class RichPresenceSelfbot(discord.Client):
    def __init__(self):
        intents = discord.Intents.none()
        super().__init__(intents=intents)
        
    async def on_ready(self):
        print(f'✅ Connecté en tant que {self.user.name} ({self.user.id})')
        print(f'⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print("-" * 60)
        
        await self.update_rich_presence()
        
        # Boucle de rafraîchissement
        while True:
            await asyncio.sleep(900)  # 15 minutes
            print(f"\n🔄 Rafraîchissement... {datetime.now().strftime('%H:%M:%S')}")
            await self.update_rich_presence()
    
    async def update_rich_presence(self):
        """Met à jour la Rich Presence avec images et boutons"""
        try:
            # Créer l'activité Rich Presence
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name="HK X B2",  # Nom principal
                application_id=CLIENT_ID,
                state="guns.lol/17h40",  # Ligne du bas
                details="V1",  # Ligne du haut
                timestamps={
                    'start': int(datetime.now().timestamp())
                },
                assets={
                    'large_image': IMAGE_NAME,
                    'large_text': 'HK X B2',
                    'small_image': IMAGE_NAME,
                    'small_text': 'En ligne'
                },
                buttons=[{
                    'label': 'guns lol b2',
                    'url': 'https://guns.lol/17h40'
                }]
            )
            
            await self.change_presence(
                status=discord.Status.online,
                activity=activity
            )
            
            print('✨ Rich Presence mise à jour avec succès !')
            
        except Exception as e:
            print(f'❌ Erreur lors de la mise à jour: {e}')

async def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ERREUR: Variable DISCORD_TOKEN non définie")
        print("📝 Ajoute DISCORD_TOKEN dans les Environment Variables de Render")
        return
    
    print("🚀 Démarrage du selfbot Discord avec Rich Presence...")
    print("⚠️  RAPPEL: Ceci viole les ToS Discord - Risque de ban")
    print("-" * 60)
    print(f"🎮 Application: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("-" * 60)
    
    client = RichPresenceSelfbot()
    
    try:
        await client.start(TOKEN, bot=False)
    except discord.LoginFailure:
        print("❌ Token invalide ou compte banni")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if not client.is_closed():
            await client.close()

if __name__ == "__main__":
    asyncio.run(main())
