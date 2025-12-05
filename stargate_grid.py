"""
STARGATE GRID — 12-NODE GLOBAL LATTICE

Gary Leckey & GitHub Copilot | November 2025
Ported from TypeScript: stargateGrid.ts

12 Sacred Sites forming a global resonance grid for Earth-based
market correlation and geomagnetic influence on trading patterns.

Each node has specific coordinates, frequencies, and numerological significance.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import math

# ============================================================================
# STARGATE GRID — 12 GLOBAL NODES
# ============================================================================

@dataclass
class StargateNode:
    """A node in the global Stargate Grid"""
    id: str
    name: str
    lat: float
    lon: float
    frequency: float
    element: str
    numerology: int
    description: str
    activation_time: str  # UTC time when node is most active


# The 12 Stargate Nodes (from stargateGrid.ts)
STARGATE_NODES: List[StargateNode] = [
    StargateNode(
        id='STONEHENGE',
        name='Stonehenge',
        lat=51.1789,
        lon=-1.8262,
        frequency=7.83,
        element='Earth',
        numerology=1,
        description='Ancient timekeeper, Schumann anchor',
        activation_time='00:00'
    ),
    StargateNode(
        id='GIZA',
        name='Great Pyramid of Giza',
        lat=29.9792,
        lon=31.1342,
        frequency=432.0,
        element='Fire',
        numerology=3,
        description='Harmonic resonator, frequency amplifier',
        activation_time='02:00'
    ),
    StargateNode(
        id='ULURU',
        name='Uluru',
        lat=-25.3444,
        lon=131.0369,
        frequency=528.0,
        element='Earth',
        numerology=5,
        description='Heart of Gaia, love frequency emitter',
        activation_time='04:00'
    ),
    StargateNode(
        id='MACHU_PICCHU',
        name='Machu Picchu',
        lat=-13.1631,
        lon=-72.5450,
        frequency=639.0,
        element='Air',
        numerology=7,
        description='Cloud gateway, social harmonic',
        activation_time='06:00'
    ),
    StargateNode(
        id='ANGKOR_WAT',
        name='Angkor Wat',
        lat=13.4125,
        lon=103.8670,
        frequency=741.0,
        element='Water',
        numerology=9,
        description='Awakening temple, clarity beacon',
        activation_time='08:00'
    ),
    StargateNode(
        id='SEDONA',
        name='Sedona Vortex',
        lat=34.8697,
        lon=-111.7610,
        frequency=396.0,
        element='Fire',
        numerology=11,
        description='Liberation vortex, fear transmuter',
        activation_time='10:00'
    ),
    StargateNode(
        id='MOUNT_SHASTA',
        name='Mount Shasta',
        lat=41.3099,
        lon=-122.3106,
        frequency=852.0,
        element='Spirit',
        numerology=2,
        description='Third eye peak, vision amplifier',
        activation_time='12:00'
    ),
    StargateNode(
        id='GLASTONBURY',
        name='Glastonbury Tor',
        lat=51.1442,
        lon=-2.6987,
        frequency=417.0,
        element='Water',
        numerology=4,
        description='Heart chakra of Earth, transformation gate',
        activation_time='14:00'
    ),
    StargateNode(
        id='EASTER_ISLAND',
        name='Easter Island',
        lat=-27.1127,
        lon=-109.3497,
        frequency=963.0,
        element='Spirit',
        numerology=6,
        description='Crown portal, unity consciousness',
        activation_time='16:00'
    ),
    StargateNode(
        id='TIBET',
        name='Mount Kailash',
        lat=31.0675,
        lon=81.3119,
        frequency=285.0,
        element='Earth',
        numerology=8,
        description='Root stabilizer, cellular renewal',
        activation_time='18:00'
    ),
    StargateNode(
        id='BERMUDA',
        name='Bermuda Triangle',
        lat=25.0000,
        lon=-71.0000,
        frequency=174.0,
        element='Water',
        numerology=10,
        description='Dimensional gateway, time flux',
        activation_time='20:00'
    ),
    StargateNode(
        id='NORTH_POLE',
        name='Magnetic North',
        lat=86.0,
        lon=147.0,
        frequency=1.0,
        element='Aether',
        numerology=12,
        description='Polar axis, magnetic anchor',
        activation_time='22:00'
    ),
]


class StargateGrid:
    """
    STARGATE GRID — Global Resonance Network
    
    Uses 12 sacred sites to calculate geomagnetic influence
    on market conditions based on time of day and planetary alignments.
    """
    
    def __init__(self):
        self.nodes = STARGATE_NODES
        self.active_node: Optional[StargateNode] = None
        self.grid_coherence = 0.0
        
    def get_active_node(self, utc_hour: Optional[int] = None) -> StargateNode:
        """
        Get currently active node based on UTC hour
        
        Each node has a 2-hour activation window
        """
        if utc_hour is None:
            utc_hour = datetime.utcnow().hour
        
        # Each node is active for 2 hours (12 nodes × 2 hours = 24 hours)
        node_index = utc_hour // 2
        self.active_node = self.nodes[node_index]
        return self.active_node
    
    def calculate_grid_coherence(self) -> float:
        """
        Calculate overall grid coherence based on:
        - Active node frequency
        - Time alignment
        - Numerological resonance
        """
        now = datetime.utcnow()
        active = self.get_active_node(now.hour)
        
        # Base coherence from active node
        freq_factor = active.frequency / 1000  # Normalize
        
        # Time alignment factor (how close to node's peak activation)
        activation_hour = int(active.activation_time.split(':')[0])
        time_diff = abs(now.hour - activation_hour)
        time_factor = 1.0 - (time_diff / 12)  # Max 1.0 at exact time
        
        # Numerological factor (primes and master numbers get boost)
        numerology = active.numerology
        if numerology in [1, 3, 7, 11]:
            num_factor = 1.2
        elif numerology in [2, 5, 9]:
            num_factor = 1.1
        else:
            num_factor = 1.0
        
        # Day of week factor (weekends have different energy)
        weekday = now.weekday()
        if weekday in [5, 6]:  # Weekend
            day_factor = 0.9
        else:
            day_factor = 1.0
        
        self.grid_coherence = min(1.0, freq_factor * time_factor * num_factor * day_factor)
        return self.grid_coherence
    
    def get_node_by_id(self, node_id: str) -> Optional[StargateNode]:
        """Get a specific node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_nearest_node(self, lat: float, lon: float) -> Tuple[StargateNode, float]:
        """
        Find nearest Stargate node to given coordinates
        Returns node and distance in km
        """
        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate distance between two points on Earth"""
            R = 6371  # Earth's radius in km
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
        
        nearest = self.nodes[0]
        min_distance = haversine(lat, lon, nearest.lat, nearest.lon)
        
        for node in self.nodes[1:]:
            distance = haversine(lat, lon, node.lat, node.lon)
            if distance < min_distance:
                min_distance = distance
                nearest = node
        
        return nearest, min_distance
    
    def get_trading_modifier(self, exchange_location: str = 'GLOBAL') -> float:
        """
        Get trading modifier based on exchange location and active node
        
        Exchange locations: 'NYSE', 'LSE', 'TOKYO', 'HONG_KONG', 'GLOBAL'
        """
        # Exchange coordinates
        exchange_coords = {
            'NYSE': (40.7069, -74.0089),      # New York
            'LSE': (51.5014, -0.1419),        # London
            'TOKYO': (35.6817, 139.7671),     # Tokyo
            'HONG_KONG': (22.2833, 114.1500), # Hong Kong
            'GLOBAL': (0.0, 0.0),             # Equator/Prime Meridian
        }
        
        coords = exchange_coords.get(exchange_location, (0.0, 0.0))
        nearest_node, distance = self.get_nearest_node(coords[0], coords[1])
        
        # Base modifier from grid coherence
        coherence = self.calculate_grid_coherence()
        
        # Distance factor (closer to node = stronger influence)
        distance_factor = 1.0 / (1.0 + distance / 5000)  # 5000km half-life
        
        # Frequency resonance between nearest and active node
        active = self.get_active_node()
        freq_ratio = min(active.frequency, nearest_node.frequency) / max(active.frequency, nearest_node.frequency)
        
        # Combined modifier (0.8 to 1.3 range)
        modifier = 0.9 + (coherence * 0.2) + (distance_factor * 0.1) + (freq_ratio * 0.1)
        
        return max(0.8, min(1.3, modifier))
    
    def get_element_influence(self) -> Dict[str, float]:
        """
        Calculate elemental influence from the grid
        
        Returns influence scores for each element
        """
        elements = {'Earth': 0, 'Fire': 0, 'Water': 0, 'Air': 0, 'Spirit': 0, 'Aether': 0}
        
        now = datetime.utcnow()
        active = self.get_active_node(now.hour)
        
        # Active node has strongest influence
        elements[active.element] += 0.5
        
        # Adjacent nodes have secondary influence
        active_idx = self.nodes.index(active)
        prev_node = self.nodes[(active_idx - 1) % 12]
        next_node = self.nodes[(active_idx + 1) % 12]
        
        elements[prev_node.element] += 0.25
        elements[next_node.element] += 0.25
        
        return elements
    
    def display_status(self) -> str:
        """Display current grid status"""
        active = self.get_active_node()
        coherence = self.calculate_grid_coherence()
        elements = self.get_element_influence()
        dominant_element = max(elements, key=elements.get)
        
        return (
            f"🌍 STARGATE GRID | "
            f"Active: {active.name} ({active.id}) | "
            f"Freq: {active.frequency} Hz | "
            f"Element: {dominant_element} | "
            f"Coherence: {coherence:.3f} | "
            f"Numerology: {active.numerology}"
        )
    
    def get_grid_summary(self) -> Dict:
        """Get full grid summary"""
        active = self.get_active_node()
        coherence = self.calculate_grid_coherence()
        elements = self.get_element_influence()
        
        return {
            'active_node': {
                'id': active.id,
                'name': active.name,
                'frequency': active.frequency,
                'element': active.element,
                'numerology': active.numerology,
            },
            'coherence': coherence,
            'elements': elements,
            'trading_modifier': self.get_trading_modifier(),
            'timestamp': datetime.utcnow().isoformat(),
        }


# ============================================================================
# LEYLINE CONNECTIONS
# ============================================================================

LEYLINE_CONNECTIONS = [
    ('STONEHENGE', 'GLASTONBURY', 'Michael Line'),
    ('STONEHENGE', 'GIZA', 'Ancient Alignment'),
    ('GIZA', 'TIBET', 'Himalayan Arc'),
    ('ULURU', 'EASTER_ISLAND', 'Pacific Line'),
    ('SEDONA', 'MOUNT_SHASTA', 'Pacific Crest'),
    ('MACHU_PICCHU', 'EASTER_ISLAND', 'Nazca Extension'),
    ('ANGKOR_WAT', 'TIBET', 'Dragon Line'),
    ('GLASTONBURY', 'BERMUDA', 'Atlantic Bridge'),
    ('NORTH_POLE', 'TIBET', 'Polar Axis'),
    ('GIZA', 'ANGKOR_WAT', 'Temple Belt'),
]


def get_leyline_activity(grid: StargateGrid) -> List[Dict]:
    """
    Calculate activity level of each leyline based on active nodes
    """
    active = grid.get_active_node()
    leyline_activity = []
    
    for start_id, end_id, name in LEYLINE_CONNECTIONS:
        start_node = grid.get_node_by_id(start_id)
        end_node = grid.get_node_by_id(end_id)
        
        if not start_node or not end_node:
            continue
        
        # Activity is higher if active node is on this leyline
        if active.id in [start_id, end_id]:
            activity = 1.0
        else:
            # Check if frequencies resonate
            freq_ratio = min(start_node.frequency, end_node.frequency) / max(start_node.frequency, end_node.frequency)
            activity = freq_ratio * 0.5
        
        leyline_activity.append({
            'name': name,
            'start': start_id,
            'end': end_id,
            'activity': activity,
            'combined_frequency': (start_node.frequency + end_node.frequency) / 2,
        })
    
    return sorted(leyline_activity, key=lambda x: x['activity'], reverse=True)


# Test/Demo
if __name__ == "__main__":
    grid = StargateGrid()
    
    print("=" * 70)
    print("🌍 STARGATE GRID — 12-NODE GLOBAL LATTICE 🌍")
    print("=" * 70)
    print()
    
    # Current status
    print(grid.display_status())
    print()
    
    # Full summary
    summary = grid.get_grid_summary()
    print(f"Active Node: {summary['active_node']['name']}")
    print(f"Frequency: {summary['active_node']['frequency']} Hz")
    print(f"Element: {summary['active_node']['element']}")
    print(f"Numerology: {summary['active_node']['numerology']}")
    print(f"Grid Coherence: {summary['coherence']:.3f}")
    print(f"Trading Modifier: {summary['trading_modifier']:.3f}")
    print()
    
    # Element influence
    print("Elemental Influence:")
    for element, influence in summary['elements'].items():
        bar = '█' * int(influence * 20)
        print(f"  {element:8s}: {bar} ({influence:.2f})")
    print()
    
    # Leyline activity
    print("Active Leylines:")
    leylines = get_leyline_activity(grid)
    for ley in leylines[:5]:
        activity_bar = '█' * int(ley['activity'] * 10)
        print(f"  {ley['name']:20s}: {activity_bar} ({ley['activity']:.2f}) | {ley['combined_frequency']:.1f} Hz")
    print()
    
    # All nodes
    print("─" * 70)
    print("ALL STARGATE NODES:")
    print("─" * 70)
    for node in STARGATE_NODES:
        print(f"  {node.id:15s} | {node.frequency:6.1f} Hz | {node.element:7s} | {node.numerology:2d} | {node.description}")
