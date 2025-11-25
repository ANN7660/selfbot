import discord
import asyncio
import os
from datetime import datetime

# ⚠️ ATTENTION: Utiliser un selfbot viole les ToS Discord
# Risque de BAN PERMANENT de ton compte

class CustomPresence(discord.Client):
    def __init__(self):
        # Intents minimaux pour éviter la détection
        intents = discord.Intents.none()
        super().__init__(intents=intents)
        
    async def on_ready(self):
        print(f'✅ Connecté en tant que {self.user.name} ({self.user.id})')
        print(f'⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('🔄 Mise à jour de la présence...')
        
        try:
            # Créer l'activité custom
            activity = discord.Activity(
                type=discord.ActivityType.playing,  # "Joue à..."
                name="V1",  # Le nom du jeu
                state="HK X B2",  # État custom
                details="guns.lol/17h40",  # Détails
                timestamps={
                    'start': int(datetime.now().timestamp())
                },
                # Pour les boutons et images, il faut une vraie app Discord
                # Les selfbots ne peuvent pas afficher de Rich Presence complète
            )
            
            await self.change_presence(
                status=discord.Status.online,  # En ligne
                activity=activity
            )
            
            print('✨ Présence mise à jour avec succès !')
            print('💡 Le bot reste actif. Ctrl+C pour arrêter.')
            
        except Exception as e:
            print(f'❌ Erreur lors de la mise à jour: {e}')
    
    async def on_message(self, message):
        # Ne rien faire, juste rester connecté
        pass

async def main():
    # Récupérer le token depuis les variables d'environnement (pour Render)
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ERREUR: Variable d'environnement DISCORD_TOKEN non définie")
        print("📝 Sur Render: Ajoute DISCORD_TOKEN dans Environment Variables")
        return
    
    client = CustomPresence()
    
    try:
        # Se connecter avec le token utilisateur (selfbot)
        await client.start(TOKEN, bot=False)  # bot=False = selfbot
    except discord.LoginFailure:
        print("❌ Token invalide ou compte banni")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    print("🚀 Démarrage du selfbot Discord...")
    print("⚠️  RAPPEL: Ceci viole les ToS Discord - Risque de ban")
    print("-" * 50)
    
    asyncio.run(main())