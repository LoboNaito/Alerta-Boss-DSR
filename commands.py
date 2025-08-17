import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict, Any
import logging
from utils import (
    obtener_todos_los_proximos_spawns, 
    obtener_tiempo_kst, 
    crear_embed_dsrworld, 
    buscar_digimon,
    obtener_estadisticas_raids,
    crear_dropdown_digimons
)
from data.default_data import EMBED_COLORS

logger = logging.getLogger(__name__)

class RaidDropdownView(discord.ui.View):
    """Vista con dropdown para selección de Digimon"""
    
    def __init__(self, spawns_info):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.spawns_info = spawns_info
        
        # Crear dropdown con los Digimon
        select = crear_dropdown_digimons(spawns_info)
        select.callback = self.dropdown_callback
        self.add_item(select)
    
    async def dropdown_callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona un Digimon del dropdown"""
        try:
            selected_key = interaction.data['values'][0]
            
            # Buscar el spawn seleccionado
            selected_spawn = None
            for spawn_info in self.spawns_info:
                if spawn_info['digimon_key'] == selected_key:
                    selected_spawn = spawn_info
                    break
            
            if not selected_spawn:
                await interaction.response.send_message("❌ Error: No se encontró el Digimon seleccionado.", ephemeral=True)
                return
            
            digimon = selected_spawn['digimon']
            tiempo_restante = selected_spawn['tiempo_restante']
            horario = selected_spawn['horario']
            
            # Crear embed detallado
            embed = crear_embed_dsrworld(digimon, tiempo_restante, "info")
            
            # Agregar información adicional
            embed.add_field(
                name="⏰ Horario específico",
                value=f"{horario['hora']:02d}:{horario['minuto']:02d} KST",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Recurrencia",
                value=f"Cada {digimon['recurrencia_dias']} día{'s' if digimon['recurrencia_dias'] > 1 else ''}",
                inline=True
            )
            
            embed.add_field(
                name="📅 Próximo Spawn",
                value=selected_spawn['spawn_time'].strftime("%Y-%m-%d %H:%M KST"),
                inline=True
            )
            
            # Mostrar todos los horarios si hay múltiples
            if len(digimon['horarios']) > 1:
                horarios_text = " • ".join([
                    f"{h['hora']:02d}:{h['minuto']:02d}" for h in digimon['horarios']
                ])
                embed.add_field(
                    name="⏲️ Todos los horarios",
                    value=f"{horarios_text} (KST)",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in dropdown callback: {e}")
            await interaction.response.send_message("❌ Error procesando la selección.", ephemeral=True)
    
    async def on_timeout(self):
        """Llamado cuando la vista expira"""
        for item in self.children:
            item.disabled = True

async def setup_commands(bot):
    """Configura todos los comandos del bot"""
    
    @bot.tree.command(name="raids", description="Muestra todos los próximos raids con menú interactivo")
    async def raids_command(interaction: discord.Interaction):
        """Comando /raids - Muestra lista de raids con dropdown"""
        try:
            await interaction.response.defer()
            
            spawns_info = obtener_todos_los_proximos_spawns(bot.digimon_manager)
            
            if not spawns_info:
                embed = discord.Embed(
                    title="📊 Raids Digimon",
                    description="❌ No hay información de raids disponible en este momento.",
                    color=EMBED_COLORS["error"]
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Crear embed principal
            embed = discord.Embed(
                title="☢️ Próximos Raids Digimon",
                description=(
                    "**Sistema de raids DSR - Formato dsrworldwiki.com**\n"
                    f"🕐 **Hora actual KST:** {obtener_tiempo_kst().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "**Próximos 6 raids:**\n"
                ),
                color=0x00FFFF,
                timestamp=obtener_tiempo_kst()
            )
            
            # Mostrar próximos 6 raids en el embed
            for i, spawn_info in enumerate(spawns_info[:6]):
                digimon = spawn_info['digimon']
                horario = spawn_info['horario']
                tiempo_formato = spawn_info['formato_tiempo']
                
                embed.add_field(
                    name=f"{i+1}. {digimon['nombre']} ({horario['hora']:02d}:{horario['minuto']:02d})",
                    value=(
                        f"**Tipo:** {digimon['tipo_icon']} {digimon['tipo']}\n"
                        f"**Respawn:** {tiempo_formato}"
                    ),
                    inline=True
                )
            
            embed.set_footer(text="Usa el menú desplegable para información detallada • DSR Spain")
            
            # Crear vista con dropdown
            view = RaidDropdownView(spawns_info)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in raids command: {e}")
            await interaction.followup.send("❌ Error obteniendo información de raids.", ephemeral=True)
    
    @bot.tree.command(name="raid", description="Información específica de un raid")
    async def raid_command(interaction: discord.Interaction, digimon: str):
        """Comando /raid - Busca información específica de un Digimon"""
        try:
            await interaction.response.defer()
            
            # Buscar el Digimon
            digimon_data = buscar_digimon(digimon, bot.digimon_manager)
            
            if not digimon_data:
                # Mostrar Digimons disponibles
                nombres_disponibles = [d['nombre'] for d in bot.digimon_manager.get_all_digimon()]
                embed = discord.Embed(
                    title="❌ Digimon no encontrado",
                    description=f"No se encontró un Digimon con el nombre `{digimon}`",
                    color=EMBED_COLORS["error"]
                )
                embed.add_field(
                    name="📋 Digimons disponibles:",
                    value="\n".join([f"• {nombre}" for nombre in nombres_disponibles]),
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener información de spawns para este Digimon
            spawns_info = obtener_todos_los_proximos_spawns(bot.digimon_manager)
            digimon_spawns = [
                spawn for spawn in spawns_info 
                if spawn['digimon']['nombre'] == digimon_data['nombre']
            ]
            
            if not digimon_spawns:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"No se pudo calcular el próximo spawn para {digimon_data['nombre']}",
                    color=EMBED_COLORS["error"]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Usar el próximo spawn (el primero en la lista ordenada)
            next_spawn = digimon_spawns[0]
            
            embed = crear_embed_dsrworld(
                digimon_data, 
                next_spawn['tiempo_restante'], 
                "info"
            )
            
            # Agregar información adicional
            embed.add_field(
                name="📅 Próximo Spawn",
                value=next_spawn['spawn_time'].strftime("%Y-%m-%d %H:%M KST"),
                inline=True
            )
            
            embed.add_field(
                name="🔄 Recurrencia",
                value=f"Cada {digimon_data['recurrencia_dias']} día{'s' if digimon_data['recurrencia_dias'] > 1 else ''}",
                inline=True
            )
            
            # Mostrar todos los horarios si hay múltiples
            if len(digimon_data['horarios']) > 1:
                horarios_text = " • ".join([
                    f"{h['hora']:02d}:{h['minuto']:02d}" for h in digimon_data['horarios']
                ])
                embed.add_field(
                    name="⏲️ Horarios de Spawn",
                    value=f"{horarios_text} (KST)",
                    inline=False
                )
                
                # Mostrar todos los próximos spawns
                if len(digimon_spawns) > 1:
                    proximos_text = "\n".join([
                        f"• **{spawn['horario']['hora']:02d}:{spawn['horario']['minuto']:02d}**: {spawn['formato_tiempo']}"
                        for spawn in digimon_spawns[:3]  # Máximo 3
                    ])
                    embed.add_field(
                        name="📊 Próximos spawns",
                        value=proximos_text,
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in raid command: {e}")
            await interaction.followup.send("❌ Error obteniendo información del raid.", ephemeral=True)
    
    @bot.tree.command(name="kst", description="Muestra la hora actual en KST")
    async def kst_command(interaction: discord.Interaction):
        """Comando /kst - Muestra hora actual KST"""
        try:
            ahora_kst = obtener_tiempo_kst()
            
            embed = discord.Embed(
                title="🕐 Hora Actual KST",
                description=f"**{ahora_kst.strftime('%Y-%m-%d %H:%M:%S')} (KST)**",
                color=EMBED_COLORS["success"],
                timestamp=ahora_kst
            )
            
            embed.add_field(
                name="📍 Zona Horaria",
                value="Korea Standard Time (UTC+9)",
                inline=True
            )
            
            embed.add_field(
                name="🌍 Usado por",
                value="Digimon Super Rumble",
                inline=True
            )
            
            embed.set_footer(text="DSR Spain • Formato dsrworldwiki.com")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in kst command: {e}")
            await interaction.response.send_message("❌ Error obteniendo hora KST.", ephemeral=True)
    
    @bot.tree.command(name="status", description="Estado del sistema (solo administradores)")
    async def status_command(interaction: discord.Interaction):
        """Comando /status - Estado del sistema (admin only)"""
        try:
            # Verificar permisos de administrador
            if not (interaction.user.guild_permissions.administrator or bot.is_admin(interaction.user.id)):
                await interaction.response.send_message("❌ Solo administradores pueden usar este comando.", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # Obtener estadísticas
            stats = obtener_estadisticas_raids(bot.digimon_manager)
            spawns_info = obtener_todos_los_proximos_spawns(bot.digimon_manager)
            
            embed = discord.Embed(
                title="📊 Estado del Sistema DSR",
                color=EMBED_COLORS["info"],
                timestamp=obtener_tiempo_kst()
            )
            
            # Información del bot
            embed.add_field(
                name="🤖 Bot Status",
                value=(
                    f"**Conectado:** ✅ Sí\n"
                    f"**Servidores:** {len(bot.guilds)}\n"
                    f"**Latencia:** {round(bot.latency * 1000)}ms"
                ),
                inline=True
            )
            
            # Información de raids
            embed.add_field(
                name="⚔️ Raids Monitoreados",
                value=(
                    f"**Total Digimons:** {stats['total_digimons']}\n"
                    f"**Próximos spawns:** {len(spawns_info)}\n"
                    f"**Tipos:** {len(stats['types'])}"
                ),
                inline=True
            )
            
            # Configuración de canales
            embed.add_field(
                name="📺 Canales Configurados",
                value=f"**Total:** {len(bot.raid_channels)}\n" +
                      "\n".join([f"• {bot.get_guild(guild_id).name if bot.get_guild(guild_id) else 'Unknown'}"
                                for guild_id in list(bot.raid_channels.keys())[:3]]) +
                      (f"\n... y {len(bot.raid_channels) - 3} más" if len(bot.raid_channels) > 3 else ""),
                inline=False
            )
            
            # Próximos raids
            if spawns_info:
                proximos_text = "\n".join([
                    f"• **{spawn['digimon']['nombre']}** ({spawn['horario']['hora']:02d}:{spawn['horario']['minuto']:02d}): {spawn['formato_tiempo']}"
                    for spawn in spawns_info[:5]
                ])
                embed.add_field(
                    name="⏰ Próximos 5 Raids",
                    value=proximos_text,
                    inline=False
                )
            
            # Estadísticas por tipo
            tipos_text = "\n".join([
                f"• **{tipo}**: {count}" for tipo, count in stats['types'].items()
            ])
            embed.add_field(
                name="📈 Distribución por Tipo",
                value=tipos_text or "Sin datos",
                inline=True
            )
            
            embed.set_footer(text="DSR Spain • Sistema de monitoreo automático")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await interaction.followup.send("❌ Error obteniendo estado del sistema.", ephemeral=True)
    
    @bot.tree.command(name="setup_channel", description="Configurar canal para alertas de raids (administradores)")
    async def setup_channel_command(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Comando /setup_channel - Configurar canal de alertas"""
        try:
            # Verificar permisos
            if not (interaction.user.guild_permissions.administrator or bot.is_admin(interaction.user.id)):
                await interaction.response.send_message("❌ Solo administradores pueden usar este comando.", ephemeral=True)
                return
            
            target_channel = channel or interaction.channel
            
            # Verificar permisos del bot en el canal
            if not target_channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.response.send_message("❌ No tengo permisos para enviar mensajes en ese canal.", ephemeral=True)
                return
            
            if not target_channel.permissions_for(interaction.guild.me).embed_links:
                await interaction.response.send_message("❌ No tengo permisos para enviar embeds en ese canal.", ephemeral=True)
                return
            
            # Configurar el canal
            bot.raid_channels[interaction.guild.id] = target_channel.id
            
            embed = discord.Embed(
                title="✅ Canal de Raids Configurado",
                description=f"Las alertas de raids se enviarán a {target_channel.mention}",
                color=EMBED_COLORS["success"]
            )
            
            embed.add_field(
                name="🔔 Tipos de Alertas",
                value=(
                    "• **Spawn Alert**: Cuando aparece un raid\n"
                    "• **Early Warning**: 20 minutos antes del spawn\n"
                    "• **Formato dsrworldwiki.com**: Información detallada"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Configuración",
                value=(
                    f"**Servidor:** {interaction.guild.name}\n"
                    f"**Canal:** {target_channel.name}\n"
                    f"**Configurado por:** {interaction.user.mention}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Enviar mensaje de confirmación al canal configurado
            if target_channel != interaction.channel:
                confirm_embed = discord.Embed(
                    title="🎯 Canal de Alertas DSR Configurado",
                    description="Este canal ha sido configurado para recibir alertas automáticas de raids de Digimon Super Rumble.",
                    color=EMBED_COLORS["info"]
                )
                await target_channel.send(embed=confirm_embed)
            
        except Exception as e:
            logger.error(f"Error in setup_channel command: {e}")
            await interaction.response.send_message("❌ Error configurando canal.", ephemeral=True)
    
    # Comandos de gestión de Digimon (admin only)
    @bot.tree.command(name="add_digimon", description="Agregar nuevo Digimon (administradores)")
    async def add_digimon_command(interaction: discord.Interaction, nombre: str, tipo: str, mapa: str, recompensa: str, 
                                 horarios: str, recurrencia_dias: int):
        """Comando /add_digimon - Agregar nuevo Digimon"""
        try:
            # Verificar permisos
            if not bot.is_admin(interaction.user.id):
                await interaction.response.send_message("❌ Solo administradores del bot pueden usar este comando.", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # Parsear horarios (formato: "19:30,21:30")
            try:
                horarios_list = []
                for horario_str in horarios.split(","):
                    hora, minuto = map(int, horario_str.strip().split(":"))
                    horarios_list.append({"hora": hora, "minuto": minuto})
            except ValueError:
                await interaction.followup.send("❌ Formato de horarios inválido. Usa formato HH:MM,HH:MM", ephemeral=True)
                return
            
            # Crear datos del Digimon
            digimon_data = {
                "nombre": nombre,
                "tipo": tipo,
                "mapa": mapa,
                "recompensa": recompensa,
                "horarios": horarios_list,
                "recurrencia_dias": recurrencia_dias
            }
            
            # Agregar Digimon
            if bot.digimon_manager.add_digimon(digimon_data):
                embed = discord.Embed(
                    title="✅ Digimon Agregado",
                    description=f"**{nombre}** ha sido agregado exitosamente al sistema.",
                    color=EMBED_COLORS["success"]
                )
                
                embed.add_field(name="Tipo", value=tipo, inline=True)
                embed.add_field(name="Mapa", value=mapa, inline=True)
                embed.add_field(name="Recompensa", value=recompensa, inline=True)
                embed.add_field(name="Horarios", value=horarios, inline=True)
                embed.add_field(name="Recurrencia", value=f"{recurrencia_dias} días", inline=True)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Error agregando Digimon. Verifica que no exista ya.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in add_digimon command: {e}")
            await interaction.followup.send("❌ Error agregando Digimon.", ephemeral=True)
    
    @bot.tree.command(name="remove_digimon", description="Remover Digimon existente (administradores)")
    async def remove_digimon_command(interaction: discord.Interaction, nombre: str):
        """Comando /remove_digimon - Remover Digimon"""
        try:
            # Verificar permisos
            if not bot.is_admin(interaction.user.id):
                await interaction.response.send_message("❌ Solo administradores del bot pueden usar este comando.", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # Verificar que existe
            digimon = bot.digimon_manager.find_digimon(nombre)
            if not digimon:
                await interaction.followup.send(f"❌ Digimon '{nombre}' no encontrado.", ephemeral=True)
                return
            
            # Remover Digimon
            if bot.digimon_manager.remove_digimon(nombre):
                embed = discord.Embed(
                    title="🗑️ Digimon Removido",
                    description=f"**{digimon['nombre']}** ha sido removido del sistema.",
                    color=EMBED_COLORS["error"]
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Error removiendo Digimon.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in remove_digimon command: {e}")
            await interaction.followup.send("❌ Error removiendo Digimon.", ephemeral=True)

    logger.info("✅ Comandos configurados exitosamente")
