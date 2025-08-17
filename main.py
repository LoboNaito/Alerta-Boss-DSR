import discord
from discord.ext import commands, tasks
import asyncio
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from commands import setup_commands
from tasks import setup_raid_tasks
from data.digimon_manager import DigimonManager
from utils import obtener_tiempo_kst

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN/DISCORD_TOKEN not found in environment variables!")
    logger.error("📝 Please create a .env file with DISCORD_TOKEN=your_token_here")
    exit(1)

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class DSRBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="DSR Raid Timers | /raids"
            )
        )
        self.raid_channels = {}
        self.digimon_manager = DigimonManager()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("🔧 Setting up bot...")
        
        # Setup commands
        await setup_commands(self)
        
        # Sync slash commands
        try:
            if GUILD_ID:
                guild = discord.Object(id=int(GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"✅ Synced commands to guild {GUILD_ID}")
            else:
                await self.tree.sync()
                logger.info("✅ Synced commands globally")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
        
        # Setup raid monitoring tasks
        setup_raid_tasks(self)
        
    async def on_ready(self):
        """Called when bot is fully ready"""
        total_digimon = len(self.digimon_manager.get_all_digimon())
        logger.info(f"🤖 {self.user} is now online!")
        logger.info(f"📊 Connected to {len(self.guilds)} guild(s)")
        logger.info(f"🕐 Current KST time: {obtener_tiempo_kst().strftime('%Y-%m-%d %H:%M:%S KST')}")
        logger.info(f"⚔️ Monitoring {total_digimon} raid timers")
        
        # Update activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{total_digimon} Digimon raids | /raids"
        )
        await self.change_presence(activity=activity)
        
        # Start raid monitoring
        if not self.raid_monitor.is_running():
            self.raid_monitor.start()
            logger.info("🚀 Raid monitoring started")
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f"🎉 Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Try to find a suitable channel for raid alerts
        suitable_channels = [
            ch for ch in guild.text_channels 
            if any(keyword in ch.name.lower() for keyword in ['raid', 'timer', 'alert', 'general'])
            and ch.permissions_for(guild.me).send_messages
        ]
        
        if suitable_channels:
            channel = suitable_channels[0]
            self.raid_channels[guild.id] = channel.id
            
            embed = discord.Embed(
                title="🤖 DSR Bot - Sistema de Raids",
                description=(
                    "¡Hola! Soy el bot de alertas para raids de Digimon Super Rumble.\n\n"
                    "**Comandos principales:**\n"
                    "• `/raids` - Ver todos los raids con menú interactivo\n"
                    "• `/raid <nombre>` - Información específica de un raid\n"
                    "• `/kst` - Hora actual en KST\n\n"
                    "**Sistema de alertas:**\n"
                    "• Alertas automáticas cuando aparecen raids\n"
                    "• Avisos 20 minutos antes del spawn\n"
                    "• Sincronización exacta con tiempos KST\n\n"
                    "Usa `/setup_channel` para configurar el canal de alertas."
                ),
                color=0x00FFFF
            )
            embed.set_footer(text="DSR Spain • Sincronización KST")
            
            try:
                await channel.send(embed=embed)
                logger.info(f"📢 Sent welcome message to {guild.name}")
            except Exception as e:
                logger.warning(f"⚠️ Couldn't send welcome message to {guild.name}: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_IDS or user_id == self.owner_id

# Create bot instance
bot = DSRBot()

@tasks.loop(minutes=1)
async def raid_monitor():
    """Monitor raid spawns every minute"""
    try:
        from tasks import check_raids
        await check_raids(bot)
    except Exception as e:
        logger.error(f"❌ Error in raid monitor: {e}")

# Attach the task to the bot
bot.raid_monitor = raid_monitor

# Error handlers
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ No tengo los permisos necesarios para ejecutar este comando.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"❌ Error ejecutando comando: {error}")

@bot.event
async def on_application_command_error(interaction, error):
    """Handle slash command errors"""
    try:
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message("❌ No tengo los permisos necesarios para ejecutar este comando.", ephemeral=True)
        else:
            logger.error(f"Slash command error: {error}")
            message = f"❌ Error ejecutando comando: {str(error)[:100]}..."
            
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
    except Exception as e:
        logger.error(f"Error handling application command error: {e}")

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
