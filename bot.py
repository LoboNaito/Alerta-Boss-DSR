import discord
from discord.ext import tasks, commands
import datetime
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Lista de Digimons con la clave "imagen"
DIGIMONS = [
    {
        "nombre": "Omegamon",
        "horarios": [
            {"hora": 14, "minuto": 30}
        ],
        "canal_id": 1406452070516527286,
        "recurrencia_dias": 14,
        "fecha_inicio": datetime.datetime(2025, 8, 10),
        "imagen": "https://i.imgur.com/GtWndog.png" # URL de ejemplo, cámbiala
    },
    {
        "nombre": "Ophanimon",
        "horarios": [
            {"hora": 16, "minuto": 0}
        ],
        "canal_id": 1406452070516527286,
        "recurrencia_dias": 14,
        "fecha_inicio": datetime.datetime(2025, 8, 9),
        "imagen": "https://i.imgur.com/suLZegh.png" # URL de ejemplo, cámbiala
    },
    {
        "nombre": "Gomamon",
        "horarios": [
            {"hora": 16, "minuto": 0},
            {"hora": 18, "minuto": 0}
        ],
        "canal_id": 1406452070516527286,
        "recurrencia_dias": 1,
        "fecha_inicio": datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0),
        "imagen": "https://i.imgur.com/0ZvqAgn.png" # URL de ejemplo, cámbiala
    },
    {
        "nombre": "Pumpkinmon",
        "horarios": [
            {"hora": 12, "minuto": 30},
            {"hora": 14, "minuto": 30}
        ],
        "canal_id": 1406452070516527286,
        "recurrencia_dias": 1,
        "fecha_inicio": datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0),
        "imagen": "https://i.imgur.com/99xbJrR.png" # URL de ejemplo, cámbiala
    },
    {
        "nombre": "BlackSeraphimon",
        "horarios": [
            {"hora": 16, "minuto": 0}
        ],
        "canal_id": 1406452070516527286,
        "recurrencia_dias": 14,
        "fecha_inicio": datetime.datetime(2025, 8, 16),
        "imagen": "https://i.imgur.com/pzZlUkZ.png" # URL de ejemplo, cámbiala
    }
]

def obtener_proximo_spawn(digimon, now):
    """Calcula la próxima aparición más cercana de un Digimon."""
    proximo_spawn = None
    
    for horario in digimon["horarios"]:
        proximo_spawn_candidato = digimon["fecha_inicio"].replace(
            hour=horario["hora"],
            minute=horario["minuto"],
            second=0,
            microsecond=0
        )
        
        while proximo_spawn_candidato < now:
            proximo_spawn_candidato += datetime.timedelta(days=digimon["recurrencia_dias"])
            
        if proximo_spawn is None or proximo_spawn_candidato < proximo_spawn:
            proximo_spawn = proximo_spawn_candidato
            
    return proximo_spawn

@tasks.loop(minutes=1)
async def check_digimon_time():
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    
    for digimon in DIGIMONS:
        proximo_spawn = obtener_proximo_spawn(digimon, now)
        aviso_temprano = proximo_spawn - datetime.timedelta(minutes=20)
        
        # Alerta de aparición
        if now == proximo_spawn:
            canal = bot.get_channel(digimon["canal_id"])
            if canal:
                embed = discord.Embed(
                    title=f"¡ALERTA! ¡{digimon['nombre']} Raid ha aparecido! ⚔️",
                    description=f"El Digimon ha aparecido en el juego.",
                    color=discord.Color.red()
                )
                if "imagen" in digimon:
                    embed.set_thumbnail(url=digimon["imagen"])
                await canal.send(embed=embed)
            else:
                print(f"Error: No se encontró el canal con ID {digimon['canal_id']}")
        
        # Alerta temprana de 20 minutos
        elif now == aviso_temprano:
            canal = bot.get_channel(digimon["canal_id"])
            if canal:
                embed = discord.Embed(
                    title=f"¡Aviso! {digimon['nombre']} Raid aparecerá pronto. ⏳",
                    description=f"El Digimon aparecerá en **20 minutos**.",
                    color=discord.Color.yellow()
                )
                if "imagen" in digimon:
                    embed.set_thumbnail(url=digimon["imagen"])
                await canal.send(embed=embed)
            else:
                print(f"Error: No se encontró el canal con ID {digimon['canal_id']}")
                        
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    check_digimon_time.start()

@bot.command()
async def tiempo(ctx, nombre_digimon: str):
    digimon_encontrado = None
    for digimon in DIGIMONS:
        if digimon["nombre"].lower() == nombre_digimon.lower():
            digimon_encontrado = digimon
            break
    
    if digimon_encontrado is None:
        await ctx.send(f"No se encontró el Digimon '{nombre_digimon}'.")
        return
    
    now = datetime.datetime.now()
    proximo_spawn = obtener_proximo_spawn(digimon_encontrado, now)
    
    tiempo_restante = proximo_spawn - now
    dias = tiempo_restante.days
    horas = int((tiempo_restante.total_seconds() % 86400) // 3600)
    minutos = int((tiempo_restante.total_seconds() % 3600) // 60)
    segundos = int(tiempo_restante.total_seconds() % 60)
    
    embed = discord.Embed(
        title=f"Tiempo restante para {digimon_encontrado['nombre']} Raid",
        description=f"Próxima aparición: **{proximo_spawn.strftime('%A a las %H:%M')}**",
        color=discord.Color.blue()
    )
    if "imagen" in digimon_encontrado:
        embed.set_thumbnail(url=digimon_encontrado["imagen"])
    embed.add_field(name="Queda", value=f"{dias} días, {horas} horas, {minutos} minutos y {segundos} segundos.")
    
    await ctx.send(embed=embed)

bot.run(os.environ.get('BOT_TOKEN'))