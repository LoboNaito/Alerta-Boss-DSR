import datetime
import pytz
import discord
import logging
from typing import Optional, List, Dict, Any
from data.default_data import KST, EMBED_COLORS, TYPE_EMOJIS, REWARD_EMOJIS

logger = logging.getLogger(__name__)

def obtener_tiempo_kst() -> datetime.datetime:
    """Obtiene la hora actual en zona horaria KST"""
    return datetime.datetime.now(KST)

def obtener_proximo_spawn(digimon: Dict[str, Any], now: Optional[datetime.datetime] = None) -> Optional[datetime.datetime]:
    """
    Calcula la próxima aparición más cercana de un Digimon en zona horaria KST.
    
    Args:
        digimon: Diccionario con información del Digimon
        now: Fecha/hora actual (opcional)
    
    Returns:
        datetime objeto con el próximo spawn o None si hay error
    """
    try:
        if now is None:
            now = obtener_tiempo_kst()
        
        # Asegurar que now esté en KST
        if now.tzinfo is None:
            now = KST.localize(now)
        elif now.tzinfo != KST:
            now = now.astimezone(KST)
        
        proximo_spawn = None
        
        for horario in digimon["horarios"]:
            # Crear candidato con la fecha de inicio pero horario específico
            spawn_candidato = digimon["fecha_inicio"].replace(
                hour=horario["hora"],
                minute=horario["minuto"],
                second=0,
                microsecond=0
            )
            
            # Avanzar hasta encontrar el próximo spawn después de ahora
            while spawn_candidato <= now:
                spawn_candidato += datetime.timedelta(days=digimon["recurrencia_dias"])
                
            # Seleccionar el spawn más cercano
            if proximo_spawn is None or spawn_candidato < proximo_spawn:
                proximo_spawn = spawn_candidato
                
        return proximo_spawn
        
    except Exception as e:
        logger.error(f"Error calculando próximo spawn para {digimon.get('nombre', 'Unknown')}: {e}")
        return None

def formato_tiempo_dsrworld(tiempo_restante: datetime.timedelta) -> str:
    """
    Formatea el tiempo restante exactamente como dsrworldwiki.com
    
    Args:
        tiempo_restante: Tiempo restante hasta el spawn
    
    Returns:
        String formateado del tiempo restante
    """
    if tiempo_restante.total_seconds() <= 0:
        return "¡DISPONIBLE AHORA!"
    
    total_segundos = int(tiempo_restante.total_seconds())
    dias = total_segundos // (24 * 3600)
    horas = (total_segundos % (24 * 3600)) // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    
    if dias > 0:
        if dias == 1:
            return "1 Day (KST)"
        else:
            return f"{dias} Days (KST)"
    else:
        return f"{horas}h {minutos}m {segundos}s (KST)"

def crear_embed_dsrworld(digimon: Dict[str, Any], tiempo_restante: Optional[datetime.timedelta] = None, tipo_alerta: str = "info") -> discord.Embed:
    """
    Crea un embed con el formato visual de dsrworldwiki.com
    
    Args:
        digimon: Diccionario con información del Digimon
        tiempo_restante: Tiempo restante hasta el spawn (opcional)
        tipo_alerta: Tipo de alerta ("spawn", "warning", "info")
    
    Returns:
        Discord embed formateado
    """
    try:
        # Seleccionar color según tipo de alerta o tipo de Digimon
        color = EMBED_COLORS.get(tipo_alerta, digimon.get("color", 0x00FFFF))
        
        embed = discord.Embed(color=color)
        
        # Título según tipo de alerta
        if tipo_alerta == "spawn":
            embed.title = f"🔥 ¡{digimon['nombre']} Raid ha aparecido! ⚔️"
            embed.description = "**El Digimon ha aparecido en el juego.**\n"
        elif tipo_alerta == "warning":
            embed.title = f"⏰ ¡{digimon['nombre']} aparecerá pronto!"
            embed.description = "**El Digimon aparecerá en 20 minutos.**\n"
        else:
            embed.title = f"📊 {digimon['nombre']} - Información de Raid"
            embed.description = ""
        
        # Información detallada
        tipo_emoji = TYPE_EMOJIS.get(digimon['tipo'], digimon.get('tipo_icon', '❓'))
        recompensa_emoji = REWARD_EMOJIS.get(digimon['recompensa'], digimon.get('recompensa_icon', '❓'))
        
        info_fields = [
            ("**Tipo:**", f"{tipo_emoji} {digimon['tipo']}"),
            ("**Mapa:**", digimon['mapa']),
            ("**Recompensa:**", f"{recompensa_emoji} {digimon['recompensa']}")
        ]
        
        if tiempo_restante:
            tiempo_formateado = formato_tiempo_dsrworld(tiempo_restante)
            info_fields.append(("**Respawn:**", tiempo_formateado))
        
        # Agregar campos al embed
        for name, value in info_fields:
            embed.add_field(name=name, value=value, inline=True)
        
        # Agregar imagen si está disponible
        if "imagen" in digimon and digimon["imagen"]:
            embed.set_thumbnail(url=digimon["imagen"])
        
        # Footer con información adicional
        ahora_kst = obtener_tiempo_kst()
        embed.set_footer(
            text=f"Actualizado: {ahora_kst.strftime('%Y-%m-%d %H:%M:%S KST')} • dsrworldwiki.com format"
        )
        
        return embed
        
    except Exception as e:
        logger.error(f"Error creando embed para {digimon.get('nombre', 'Unknown')}: {e}")
        
        # Embed de fallback en caso de error
        error_embed = discord.Embed(
            title="❌ Error creando información",
            description=f"No se pudo generar la información para {digimon.get('nombre', 'Unknown')}",
            color=EMBED_COLORS["error"]
        )
        return error_embed

def obtener_todos_los_proximos_spawns(digimon_manager=None) -> List[Dict[str, Any]]:
    """
    Obtiene información de todos los próximos spawns ordenados por tiempo
    
    Args:
        digimon_manager: DigimonManager instance (optional)
    
    Returns:
        Lista de diccionarios con información de spawns
    """
    if digimon_manager is None:
        from data.digimon_manager import DigimonManager
        digimon_manager = DigimonManager()
    
    DIGIMONS = digimon_manager.get_all_digimon()
    
    ahora = obtener_tiempo_kst()
    spawns_info = []
    
    for digimon in DIGIMONS:
        try:
            # Calcular todos los spawns para este Digimon
            for horario in digimon["horarios"]:
                temp_digimon = digimon.copy()
                temp_digimon["horarios"] = [horario]  # Solo este horario específico
                
                proximo_spawn = obtener_proximo_spawn(temp_digimon, ahora)
                if proximo_spawn is None:
                    continue
                    
                tiempo_restante = proximo_spawn - ahora
                
                # Crear identificador único para múltiples horarios del mismo Digimon
                digimon_key = f"{digimon['nombre']}_{horario['hora']}_{horario['minuto']}"
                
                spawn_info = {
                    'digimon': digimon,
                    'horario': horario,
                    'spawn_time': proximo_spawn,
                    'tiempo_restante': tiempo_restante,
                    'formato_tiempo': formato_tiempo_dsrworld(tiempo_restante),
                    'digimon_key': digimon_key
                }
                
                spawns_info.append(spawn_info)
                
        except Exception as e:
            logger.error(f"Error procesando spawns para {digimon.get('nombre', 'Unknown')}: {e}")
    
    # Ordenar por tiempo restante
    spawns_info.sort(key=lambda x: x['tiempo_restante'])
    
    return spawns_info

def buscar_digimon(nombre: str, digimon_manager=None) -> Optional[Dict[str, Any]]:
    """
    Busca un Digimon por nombre (búsqueda flexible)
    
    Args:
        nombre: Nombre del Digimon a buscar
        digimon_manager: DigimonManager instance (optional)
    
    Returns:
        Diccionario del Digimon o None si no se encuentra
    """
    if digimon_manager is None:
        from data.digimon_manager import DigimonManager
        digimon_manager = DigimonManager()
    
    return digimon_manager.find_digimon(nombre)

def obtener_estadisticas_raids(digimon_manager=None) -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de los raids
    
    Args:
        digimon_manager: DigimonManager instance (optional)
    
    Returns:
        Diccionario con estadísticas
    """
    if digimon_manager is None:
        from data.digimon_manager import DigimonManager
        digimon_manager = DigimonManager()
    
    stats = digimon_manager.get_statistics()
    
    stats['current_time_kst'] = obtener_tiempo_kst()
    return stats

def crear_dropdown_digimons(spawns_info: List[Dict[str, Any]], max_options: int = 25) -> discord.ui.Select:
    """
    Crea un dropdown con los Digimon disponibles
    
    Args:
        spawns_info: Lista de información de spawns
        max_options: Máximo número de opciones (Discord límite: 25)
    
    Returns:
        Componente Select de Discord
    """
    options = []
    seen_digimons = set()
    
    for spawn_info in spawns_info[:max_options]:
        digimon = spawn_info['digimon']
        horario = spawn_info['horario']
        
        # Evitar duplicados del mismo Digimon
        digimon_key = spawn_info['digimon_key']
        if digimon_key in seen_digimons:
            continue
        seen_digimons.add(digimon_key)
        
        # Crear etiqueta con tiempo
        tiempo_formateado = spawn_info['formato_tiempo']
        label = f"{digimon['nombre']} ({horario['hora']:02d}:{horario['minuto']:02d})"
        
        # Truncar si es muy largo
        if len(label) > 100:
            label = label[:97] + "..."
        
        description = f"{digimon['tipo']} • {tiempo_formateado}"
        if len(description) > 100:
            description = description[:97] + "..."
        
        option = discord.SelectOption(
            label=label,
            description=description,
            value=digimon_key,
            emoji=TYPE_EMOJIS.get(digimon['tipo'], '❓')
        )
        options.append(option)
    
    # Crear el Select component
    select = discord.ui.Select(
        placeholder="Selecciona un Digimon para ver información detallada...",
        options=options,
        min_values=1,
        max_values=1
    )
    
    return select
