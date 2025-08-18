# Contenido del archivo scheduled_tasks.py
import discord
from discord.ext import commands, tasks

# El ID del canal donde quieres que se envíe el mensaje
# Reemplaza con el ID de tu canal
CHANNEL_ID = 1406450978667888712

class ScheduledTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"La extensión ScheduledTasks ha sido cargada.")
        self.enviar_mensaje_programado.start()

    @tasks.loop(days=2)
    async def enviar_mensaje_programado(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("¡Hola! Este es mi mensaje de recordatorio automático cada 2 días de que debes tanto cambiarlo a 3 ahora como de acceder a https://dashboard.katabump.com/ para renovar tu suscripcion para mi.")

# La función 'setup' es necesaria para que el bot pueda cargar el Cog
async def setup(bot):
    await bot.add_cog(ScheduledTasks(bot))