import discord
import datetime
import asyncio
import logging
from typing import Dict, Any, Optional
from utils import (
    obtener_tiempo_kst,
    obtener_proximo_spawn,
    crear_embed_dsrworld,
    obtener_todos_los_proximos_spawns
)
from data.default_data import ALERT_SETTINGS

logger = logging.getLogger(__name__)

def setup_raid_tasks(bot):
    """Configura las tareas de monitoreo de raids"""
    logger.info("🔧 Configurando tareas de raid monitoring...")

async def check_raids(bot):
    """
    Función principal que verifica raids y envía alertas
    Llamada cada minuto por el task loop en main.py
    """
    try:
        ahora = obtener_tiempo_kst().replace(second=0, microsecond=0)
        logger.debug(f"🔍 Verificando raids a las {ahora.strftime('%H:%M:%S KST')}")
        
        digimons = bot.digimon_manager.get_all_digimon()
        for digimon in digimons:
            await check_single_digimon(bot, digimon, ahora)
        
        # Log de estado cada 10 minutos
        if ahora.minute % 10 == 0:
            await log_status_update(bot, ahora)
            
    except Exception as e:
        logger.error(f"❌ Error en check_raids: {e}")

async def check_single_digimon(bot, digimon: Dict[str, Any], ahora: datetime.datetime):
    """Verifica un Digimon específico para alertas"""
    try:
        # Verificar cada horario del Digimon
        for horario in digimon["horarios"]:
            # Crear una copia temporal con solo este horario
            temp_digimon = digimon.copy()
            temp_digimon["horarios"] = [horario]
            
            proximo_spawn = obtener_proximo_spawn(temp_digimon, ahora)
            if proximo_spawn is None:
                continue
            
            # Calcular tiempo de aviso temprano
            aviso_temprano = proximo_spawn - datetime.timedelta(
                minutes=ALERT_SETTINGS["early_warning_minutes"]
            )
            
            # Verificar si es momento de alerta de aparición exacta
            if ahora == proximo_spawn and ALERT_SETTINGS["spawn_alert"]:
                await send_spawn_alert(bot, digimon, horario)
            
            # Verificar si es momento de aviso temprano
            elif ahora == aviso_temprano:
                await send_warning_alert(bot, digimon, horario, proximo_spawn)
                
    except Exception as e:
        logger.error(f"❌ Error verificando {digimon.get('nombre', 'Unknown')}: {e}")

async def send_spawn_alert(bot, digimon: Dict[str, Any], horario: Dict[str, int]):
    """Envía alerta cuando aparece un raid"""
    try:
        embed = crear_embed_dsrworld(digimon, None, "spawn")
        
        # Agregar información específica del horario
        embed.add_field(
            name="⏰ Horario",
            value=f"{horario['hora']:02d}:{horario['minuto']:02d} KST",
            inline=True
        )
        
        content = ""
        if ALERT_SETTINGS["mention_everyone"]:
            content = "@everyone"
        
        # Enviar a todos los canales configurados
        sent_count = await send_to_raid_channels(bot, embed, content)
        
        logger.info(f"🔥 Enviada alerta de spawn: {digimon['nombre']} ({horario['hora']:02d}:{horario['minuto']:02d}) a {sent_count} canal(es)")
        
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de spawn para {digimon.get('nombre', 'Unknown')}: {e}")

async def send_warning_alert(bot, digimon: Dict[str, Any], horario: Dict[str, int], spawn_time: datetime.datetime):
    """Envía aviso temprano de raid"""
    try:
        tiempo_restante = datetime.timedelta(minutes=ALERT_SETTINGS["early_warning_minutes"])
        embed = crear_embed_dsrworld(digimon, tiempo_restante, "warning")
        
        # Agregar información específica
        embed.add_field(
            name="⏰ Horario exacto",
            value=f"{horario['hora']:02d}:{horario['minuto']:02d} KST",
            inline=True
        )
        
        embed.add_field(
            name="📅 Fecha y hora",
            value=spawn_time.strftime("%Y-%m-%d %H:%M KST"),
            inline=True
        )
        
        # Enviar a todos los canales configurados
        sent_count = await send_to_raid_channels(bot, embed)
        
        logger.info(f"⏰ Enviado aviso de 20min: {digimon['nombre']} ({horario['hora']:02d}:{horario['minuto']:02d}) a {sent_count} canal(es)")
        
    except Exception as e:
        logger.error(f"❌ Error enviando aviso temprano para {digimon.get('nombre', 'Unknown')}: {e}")

async def send_to_raid_channels(bot, embed: discord.Embed, content: str = "") -> int:
    """
    Envía un mensaje a todos los canales de raid configurados
    
    Returns:
        Número de canales a los que se envió exitosamente
    """
    sent_count = 0
    
    for guild in bot.guilds:
        try:
            channel_id = bot.raid_channels.get(guild.id)
            
            if not channel_id:
                # Intentar encontrar un canal adecuado automáticamente
                channel_id = await find_suitable_channel(guild)
                if channel_id:
                    bot.raid_channels[guild.id] = channel_id
            
            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel and channel.permissions_for(guild.me).send_messages:
                    await channel.send(content, embed=embed)
                    sent_count += 1
                else:
                    # Canal no válido, limpiarlo
                    if guild.id in bot.raid_channels:
                        del bot.raid_channels[guild.id]
                    logger.warning(f"⚠️ Canal no válido para {guild.name}, removido de configuración")
                    
        except discord.Forbidden:
            logger.warning(f"⚠️ Sin permisos para enviar mensaje en {guild.name}")
        except discord.HTTPException as e:
            logger.warning(f"⚠️ Error HTTP enviando mensaje a {guild.name}: {e}")
        except Exception as e:
            logger.error(f"❌ Error enviando a {guild.name}: {e}")
    
    return sent_count

async def find_suitable_channel(guild: discord.Guild) -> Optional[int]:
    """
    Busca un canal adecuado para alertas de raid en un servidor
    
    Returns:
        ID del canal encontrado o None
    """
    try:
        # Buscar canales con nombres relacionados con raids
        suitable_keywords = ['raid', 'timer', 'alert', 'dsr', 'digimon', 'bot']
        
        for keyword in suitable_keywords:
            for channel in guild.text_channels:
                if (keyword in channel.name.lower() and 
                    channel.permissions_for(guild.me).send_messages and
                    channel.permissions_for(guild.me).embed_links):
                    logger.info(f"📍 Canal encontrado automáticamente para {guild.name}: {channel.name}")
                    return channel.id
        
        # Si no encuentra canal específico, usar el primer canal donde tenga permisos
        for channel in guild.text_channels:
            if (channel.permissions_for(guild.me).send_messages and
                channel.permissions_for(guild.me).embed_links):
                logger.info(f"📍 Usando canal por defecto para {guild.name}: {channel.name}")
                return channel.id
                
    except Exception as e:
        logger.error(f"❌ Error buscando canal adecuado en {guild.name}: {e}")
    
    return None

async def log_status_update(bot, ahora: datetime.datetime):
    """Log de estado cada 10 minutos para debugging"""
    try:
        spawns_info = obtener_todos_los_proximos_spawns()
        
        logger.info("📊 === Estado del sistema ===")
        logger.info(f"🕐 Hora actual KST: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🤖 Bot conectado: {'✅' if bot.is_ready() else '❌'}")
        logger.info(f"🌐 Servidores: {len(bot.guilds)}")
        logger.info(f"📺 Canales configurados: {len(bot.raid_channels)}")
        
        if spawns_info:
            proximo = spawns_info[0]
            tiempo_restante = proximo['tiempo_restante'].total_seconds()
            horas = int(tiempo_restante // 3600)
            minutos = int((tiempo_restante % 3600) // 60)
            
            logger.info(f"⏰ Próximo raid: {proximo['digimon']['nombre']} en {horas}h {minutos}m")
            
            # Mostrar próximos 3 raids
            for i, spawn in enumerate(spawns_info[:3]):
                digimon = spawn['digimon']
                horario = spawn['horario']
                tiempo = spawn['spawn_time'].strftime('%H:%M')
                logger.info(f"   {i+1}. {digimon['nombre']} ({horario['hora']:02d}:{horario['minuto']:02d}) - {tiempo} KST")
        
        logger.info("📊 === Fin estado ===")
        
    except Exception as e:
        logger.error(f"❌ Error en log de estado: {e}")

# Función auxiliar para testing manual
async def test_raid_alert(bot, digimon_nombre: str, alert_type: str = "spawn"):
    """
    Función de prueba para enviar alertas manualmente
    
    Args:
        bot: Instancia del bot
        digimon_nombre: Nombre del Digimon para probar
        alert_type: Tipo de alerta ("spawn" o "warning")
    """
    try:
        # Buscar el Digimon usando el manager del bot
        digimon_data = bot.digimon_manager.find_digimon(digimon_nombre)
        
        if not digimon_data:
            logger.error(f"❌ Digimon de prueba no encontrado: {digimon_nombre}")
            return
        
        # Usar el primer horario para la prueba
        horario = digimon_data['horarios'][0]
        
        if alert_type == "spawn":
            await send_spawn_alert(bot, digimon_data, horario)
        elif alert_type == "warning":
            spawn_time = obtener_tiempo_kst() + datetime.timedelta(minutes=20)
            await send_warning_alert(bot, digimon_data, horario, spawn_time)
        
        logger.info(f"✅ Alerta de prueba enviada: {digimon_nombre} ({alert_type})")
        
    except Exception as e:
        logger.error(f"❌ Error en alerta de prueba: {e}")
