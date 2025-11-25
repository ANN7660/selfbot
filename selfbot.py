import discord
import asyncio
import os
from datetime import datetime

CLIENT_ID = '1410787199745888747'
IMAGE_NAME = 'logo_b2'

class RichPresenceSelfbot(discord.Client):
    def __init__(self):
        intents = discord.Intents.none()
        super().__init__(intents=intents)
        
    async def on_ready(self):
        print(f'✅ Connecté: {self.user.name} (ID: {self.user.id})')
        print(f'⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print("-" * 60)
        
        await self.update_rich_presence()
        
        # Boucle de rafraîchissement
        asyncio.create_task(self.refresh_loop())
    
    async def refresh_loop(self):
        """Rafraîchit la présence toutes les 15 minutes"""
        while True:
            await asyncio.sleep(900)  # 15 minutes
            print(f"\n🔄 Rafraîchissement - {datetime.now().strftime('%H:%M:%S')}")
            await self.update_rich_presence()
    
    async def update_rich_presence(self):
        """Met à jour la Rich Presence"""
        try:
            print("📡 Mise à jour de la Rich Presence...")
            
            # Créer l'activité
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name="HK X B2",
                application_id=int(CLIENT_ID),
                state="guns.lol/17h40",
                details="V1",
                timestamps={'start': int(datetime.now().timestamp())},
                assets={
                    'large_image': IMAGE_NAME,
                    'large_text': 'HK X B2',
                    'small_image': IMAGE_NAME,
                    'small_text': 'En ligne'
                },
                buttons=[{'label': 'guns lol b2', 'url': 'https://guns.lol/17h40'}]
            )
            
            await self.change_presence(status=discord.Status.online, activity=activity)
            print('✅ Rich Presence activée avec succès !')
            
        except Exception as e:
            print(f'❌ Erreur: {type(e).__name__}: {e}')

async def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    print("🚀 Selfbot Discord Rich Presence")
    print("⚠️  Viole les ToS Discord - Risque de ban")
    print("-" * 60)
    print(f"🎮 Application: {CLIENT_ID}")
    print(f"🖼️  Image: {IMAGE_NAME}")
    print("-" * 60)
    
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant !")
        return
    
    print(f"🔑 Token trouvé ({len(TOKEN)} caractères)")
    
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
    print("=" * 60)
    asyncio.run(main())
