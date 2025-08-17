import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
from .default_data import DEFAULT_DIGIMONS, EMBED_COLORS, TYPE_EMOJIS, REWARD_EMOJIS, ALERT_SETTINGS

logger = logging.getLogger(__name__)

class DigimonDateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def datetime_hook(json_dict):
    """JSON decoder hook to convert ISO datetime strings back to datetime objects"""
    for key, value in json_dict.items():
        if isinstance(value, str) and key == 'fecha_inicio':
            try:
                # Parse ISO format datetime and convert to KST
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = pytz.timezone('Asia/Seoul').localize(dt)
                else:
                    dt = dt.astimezone(pytz.timezone('Asia/Seoul'))
                json_dict[key] = dt
            except (ValueError, TypeError):
                logger.warning(f"Could not parse datetime: {value}")
    return json_dict

class DigimonManager:
    """Manages Digimon data with automatic loading and saving"""
    
    def __init__(self, data_file: str = "data/digimon_data.json"):
        self.data_file = data_file
        self.digimons = []
        self.load_data()
    
    def load_data(self):
        """Load Digimon data from file or create with defaults"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=datetime_hook)
                    self.digimons = data.get('digimons', DEFAULT_DIGIMONS.copy())
                    logger.info(f"✅ Loaded {len(self.digimons)} Digimon from {self.data_file}")
            else:
                # Create default data
                self.digimons = [digimon.copy() for digimon in DEFAULT_DIGIMONS]
                self.save_data()
                logger.info(f"📝 Created default data with {len(self.digimons)} Digimon")
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            logger.info("🔄 Using default Digimon data")
            self.digimons = [digimon.copy() for digimon in DEFAULT_DIGIMONS]
    
    def save_data(self):
        """Save current Digimon data to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.data_file) if os.path.dirname(self.data_file) else '.', exist_ok=True)
            
            data = {
                'digimons': self.digimons,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, cls=DigimonDateTimeEncoder)
                
            logger.info(f"💾 Saved {len(self.digimons)} Digimon to {self.data_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
            return False
    
    def get_all_digimon(self) -> List[Dict[str, Any]]:
        """Get all Digimon data"""
        return [digimon.copy() for digimon in self.digimons]
    
    def find_digimon(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a Digimon by name (case insensitive)"""
        name_lower = name.lower().strip()
        
        # Exact match first
        for digimon in self.digimons:
            if digimon['nombre'].lower() == name_lower:
                return digimon.copy()
        
        # Partial match
        for digimon in self.digimons:
            if name_lower in digimon['nombre'].lower():
                return digimon.copy()
        
        return None
    
    def add_digimon(self, digimon_data: Dict[str, Any]) -> bool:
        """Add a new Digimon"""
        try:
            # Validate required fields
            required_fields = ['nombre', 'tipo', 'mapa', 'recompensa', 'horarios', 'recurrencia_dias']
            for field in required_fields:
                if field not in digimon_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if Digimon already exists
            if self.find_digimon(digimon_data['nombre']):
                raise ValueError(f"Digimon '{digimon_data['nombre']}' already exists")
            
            # Set default values
            digimon_data.setdefault('tipo_icon', TYPE_EMOJIS.get(digimon_data['tipo'], '❓'))
            digimon_data.setdefault('recompensa_icon', REWARD_EMOJIS.get(digimon_data['recompensa'], '❓'))
            digimon_data.setdefault('color', self._get_default_color(digimon_data['tipo']))
            digimon_data.setdefault('imagen', '')
            
            # Convert date strings to datetime objects if needed
            if 'fecha_inicio' in digimon_data and isinstance(digimon_data['fecha_inicio'], str):
                KST = pytz.timezone('Asia/Seoul')
                dt = datetime.fromisoformat(digimon_data['fecha_inicio'].replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    digimon_data['fecha_inicio'] = KST.localize(dt)
                else:
                    digimon_data['fecha_inicio'] = dt.astimezone(KST)
            elif 'fecha_inicio' not in digimon_data:
                # Set default start date to now in KST
                KST = pytz.timezone('Asia/Seoul')
                digimon_data['fecha_inicio'] = datetime.now(KST)
            
            self.digimons.append(digimon_data)
            self.save_data()
            
            logger.info(f"✅ Added new Digimon: {digimon_data['nombre']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding Digimon: {e}")
            return False
    
    def update_digimon(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing Digimon"""
        try:
            digimon = None
            for d in self.digimons:
                if d['nombre'].lower() == name.lower():
                    digimon = d
                    break
            
            if not digimon:
                raise ValueError(f"Digimon '{name}' not found")
            
            # Update fields
            for key, value in updates.items():
                if key == 'fecha_inicio' and isinstance(value, str):
                    KST = pytz.timezone('Asia/Seoul')
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        value = KST.localize(dt)
                    else:
                        value = dt.astimezone(KST)
                digimon[key] = value
            
            # Update icons if type or reward changed
            if 'tipo' in updates:
                digimon['tipo_icon'] = TYPE_EMOJIS.get(digimon['tipo'], '❓')
                digimon['color'] = self._get_default_color(digimon['tipo'])
            
            if 'recompensa' in updates:
                digimon['recompensa_icon'] = REWARD_EMOJIS.get(digimon['recompensa'], '❓')
            
            self.save_data()
            logger.info(f"✅ Updated Digimon: {digimon['nombre']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating Digimon: {e}")
            return False
    
    def remove_digimon(self, name: str) -> bool:
        """Remove a Digimon"""
        try:
            original_count = len(self.digimons)
            self.digimons = [d for d in self.digimons if d['nombre'].lower() != name.lower()]
            
            if len(self.digimons) == original_count:
                raise ValueError(f"Digimon '{name}' not found")
            
            self.save_data()
            logger.info(f"🗑️ Removed Digimon: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing Digimon: {e}")
            return False
    
    def get_digimon_by_type(self, digimon_type: str) -> List[Dict[str, Any]]:
        """Get all Digimon of a specific type"""
        return [d.copy() for d in self.digimons if d['tipo'].lower() == digimon_type.lower()]
    
    def get_digimon_by_map(self, map_name: str) -> List[Dict[str, Any]]:
        """Get all Digimon from a specific map"""
        return [d.copy() for d in self.digimons if map_name.lower() in d['mapa'].lower()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about all Digimon"""
        types_count = {}
        rewards_count = {}
        maps_count = {}
        
        for digimon in self.digimons:
            # Count types
            tipo = digimon['tipo']
            types_count[tipo] = types_count.get(tipo, 0) + 1
            
            # Count rewards
            reward = digimon['recompensa']
            rewards_count[reward] = rewards_count.get(reward, 0) + 1
            
            # Count maps
            map_name = digimon['mapa']
            maps_count[map_name] = maps_count.get(map_name, 0) + 1
        
        return {
            'total_digimons': len(self.digimons),
            'types': types_count,
            'rewards': rewards_count,
            'maps': maps_count,
            'data_file': self.data_file,
            'last_updated': datetime.now().isoformat()
        }
    
    def export_digimon(self, name: str) -> Optional[Dict[str, Any]]:
        """Export a single Digimon's data for sharing"""
        digimon = self.find_digimon(name)
        if digimon:
            # Create a copy and convert datetime to string for JSON serialization
            export_data = digimon.copy()
            if 'fecha_inicio' in export_data and hasattr(export_data['fecha_inicio'], 'isoformat'):
                export_data['fecha_inicio'] = export_data['fecha_inicio'].isoformat()
            return export_data
        return None
    
    def import_digimon(self, digimon_data: Dict[str, Any], overwrite: bool = False) -> bool:
        """Import a Digimon from external data"""
        try:
            existing = self.find_digimon(digimon_data['nombre'])
            
            if existing and not overwrite:
                raise ValueError(f"Digimon '{digimon_data['nombre']}' already exists. Use overwrite=True to replace.")
            
            if existing and overwrite:
                # Remove existing and add new
                self.remove_digimon(digimon_data['nombre'])
            
            return self.add_digimon(digimon_data)
            
        except Exception as e:
            logger.error(f"❌ Error importing Digimon: {e}")
            return False
    
    def backup_data(self, backup_file: Optional[str] = None) -> bool:
        """Create a backup of current data"""
        try:
            if backup_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"data/backup_digimon_{timestamp}.json"
            
            # Create backup directory
            os.makedirs(os.path.dirname(backup_file) if os.path.dirname(backup_file) else '.', exist_ok=True)
            
            backup_data = {
                'digimons': self.digimons,
                'backup_created': datetime.now().isoformat(),
                'original_file': self.data_file,
                'version': '1.0'
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, cls=DigimonDateTimeEncoder)
            
            logger.info(f"💾 Created backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            return False
    
    def _get_default_color(self, digimon_type: str) -> int:
        """Get default color for Digimon type"""
        color_map = {
            'Data': 0x0099FF,    # Blue
            'Virus': 0xFF3366,   # Red
            'Vacuna': 0x00FF00   # Green
        }
        return color_map.get(digimon_type, 0x808080)  # Gray for unknown
