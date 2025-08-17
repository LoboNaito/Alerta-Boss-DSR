# DSR Discord Bot - Deployment para Katabump

Bot de Discord completo para Digimon Super Rumble con sistema de alertas automáticas y gestión avanzada de raids.

## 🚀 Instalación en Katabump

### 1. Subir archivos
Sube todos los archivos del proyecto a tu servidor Katabump:
- `main.py` (archivo principal)
- `commands.py` (comandos del bot)
- `tasks.py` (sistema de alertas)
- `utils.py` (utilidades)
- `config.py` (configuración legacy)
- `data/` (carpeta con gestión de datos)
- `Procfile` (configuración de Katabump)

### 2. Configurar variables de entorno
En el panel de Katabump, configura estas variables:

```
DISCORD_TOKEN=tu_token_del_bot_discord
ADMIN_IDS=id_usuario1,id_usuario2
```

### 3. Instalar dependencias
Las dependencias se instalan automáticamente según el Procfile:
- discord.py>=2.5.0
- python-dotenv>=1.0.0
- pytz>=2023.0
- aiohttp>=3.8.0

### 4. Ejecutar el bot
El bot se ejecutará automáticamente usando el Procfile incluido.

## 📊 Características

- **Comandos slash**: `/raids`, `/raid`, `/kst`, `/status`
- **Alertas automáticas**: 20 minutos antes + notificación exacta
- **7 Digimon configurados** con horarios exactos en KST
- **Gestión automática de datos** con respaldos JSON
- **Interfaz interactiva** con menús desplegables

## 🔧 Configuración del Bot Discord

1. Crea una aplicación en https://discord.com/developers/applications
2. Crea un bot y copia el token
3. Invita el bot con estos permisos:
   - Enviar mensajes
   - Usar comandos slash
   - Insertar enlaces
   - Mencionar @everyone

## 📁 Estructura de archivos

```
├── main.py              # Punto de entrada
├── commands.py          # Comandos slash
├── tasks.py             # Sistema de alertas
├── utils.py             # Utilidades
├── config.py            # Configuración legacy
├── data/
│   ├── __init__.py
│   ├── digimon_manager.py
│   ├── default_data.py
│   └── digimon_data.json (auto-generado)
├── Procfile            # Configuración Katabump
└── README_KATABUMP.md  # Este archivo
```

## ⚔️ Digimon Monitoreados

- **Pumpkinmon** (Data) - 19:30, 21:30 KST diario
- **Datamon** (Virus) - 20:40 KST diario  
- **Gotsumon** (Data) - 23:00, 01:00 KST diario
- **BlackSeraphimon** (Virus) - 16:00 KST cada 5 días
- **Omegamon** (Vacuna) - 14:30 KST cada 6 días
- **Ophanimon** (Vacuna) - 16:00 KST cada 12 días
- **Megidramon** (Virus) - 16:00 KST cada 13 días

## 🆘 Soporte

El bot incluye logs detallados para debugging. Revisa la consola de Katabump para cualquier error.