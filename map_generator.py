#!/usr/bin/env python3
"""
Cozy Claw - Procedural Map Generator
=====================================
Generates map.json with multiple biomes using simplex noise.

Biomes:
  - meadow (草地) — open grass, flowers, mushrooms
  - forest (森林) — dense trees, bushes, darker grass
  - water  (水塘) — ponds/lakes with beach edges
  - farm   (农场) — tilled dirt, crops, fences
  - path   (小路) — dirt paths connecting areas

The generator:
  1. Uses noise to create a height map
  2. Assigns biomes based on height thresholds
  3. Places structures (house, well, farm) in fixed zones
  4. Scatters decorations per biome rules
  5. Generates collision data
  6. Outputs map.json compatible with index.html
"""

import json
import math
import random
import argparse

try:
    from noise import snoise2
except ImportError:
    # Fallback: simple value noise if 'noise' package not installed
    def snoise2(x, y, octaves=1, persistence=0.5, lacunarity=2.0):
        """Simple fallback noise - not as good but works"""
        val = 0.0
        amp = 1.0
        freq = 1.0
        max_val = 0.0
        for _ in range(octaves):
            # Simple hash-based noise
            ix = int(math.floor(x * freq))
            iy = int(math.floor(y * freq))
            fx = x * freq - ix
            fy = y * freq - iy
            # Smoothstep
            fx = fx * fx * (3 - 2 * fx)
            fy = fy * fy * (3 - 2 * fy)
            # Hash corners
            def h(a, b): return ((a * 1619 + b * 31337 + 1013) & 0x7fffffff) / 0x7fffffff * 2 - 1
            n00 = h(ix, iy)
            n10 = h(ix+1, iy)
            n01 = h(ix, iy+1)
            n11 = h(ix+1, iy+1)
            nx0 = n00 * (1-fx) + n10 * fx
            nx1 = n01 * (1-fx) + n11 * fx
            val += (nx0 * (1-fy) + nx1 * fy) * amp
            max_val += amp
            amp *= persistence
            freq *= lacunarity
        return val / max_val


# === CONFIGURATION ===

TILE_SIZE = 16  # Base tile size in pixels
SCALE = 3       # Render scale (16px * 3 = 48px per tile on screen)
TILE_SCALED = TILE_SIZE * SCALE  # 48px

# Map size in tiles
MAP_COLS = 40   # 40 tiles * 48px = 1920px
MAP_ROWS = 40   # 40 tiles * 48px = 1920px

MAP_WIDTH = MAP_COLS * TILE_SCALED   # 1920
MAP_HEIGHT = MAP_ROWS * TILE_SCALED  # 1920

# Noise parameters
NOISE_SCALE = 0.08       # How zoomed in the noise is
NOISE_OCTAVES = 4
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0

# Biome thresholds (noise value ranges: roughly -1 to 1)
WATER_THRESHOLD = -0.25    # Below this = water
BEACH_THRESHOLD = -0.15    # Between water and this = beach/sand
MEADOW_THRESHOLD = 0.3     # Below this = meadow (open grass)
FOREST_THRESHOLD = 0.6     # Below this = light forest
# Above forest = dense forest

# Structure zones (in tile coords) — reserved areas where no random stuff spawns
HOUSE_ZONE = {'tx': 15, 'ty': 15, 'tw': 5, 'th': 5}     # Center-ish
FARM_ZONE = {'tx': 22, 'ty': 8, 'tw': 7, 'th': 7}        # Upper right
WELL_ZONE = {'tx': 18, 'ty': 22, 'tw': 3, 'th': 3}       # Below house
PICNIC_ZONE = {'tx': 6, 'ty': 20, 'tw': 4, 'th': 4}      # Left side
SPAWN_TX = 17  # Player spawn tile
SPAWN_TY = 20


# === GRASS TILE VARIANTS ===
# From Sprout Lands Grass.png (176x112, 16px grid = 11 cols x 7 rows)
# We use several inner grass variants for variety
GRASS_VARIANTS = [
    {'id': 'grass_a', 'source': 'Tilesets/Grass.png', 'x': 16, 'y': 16, 'w': 16, 'h': 16},  # center grass
    {'id': 'grass_b', 'source': 'Tilesets/Grass.png', 'x': 32, 'y': 16, 'w': 16, 'h': 16},  # variant
    {'id': 'grass_c', 'source': 'Tilesets/Grass.png', 'x': 16, 'y': 32, 'w': 16, 'h': 16},  # variant
    {'id': 'grass_d', 'source': 'Tilesets/Grass.png', 'x': 32, 'y': 32, 'w': 16, 'h': 16},  # variant
    {'id': 'grass_e', 'source': 'Tilesets/Grass.png', 'x': 0, 'y': 16, 'w': 16, 'h': 16},   # variant
    {'id': 'grass_f', 'source': 'Tilesets/Grass.png', 'x': 0, 'y': 32, 'w': 16, 'h': 16},   # variant
]

# Dark grass for forest biome (use the same tiles, renderer will tint)
FOREST_GRASS_VARIANTS = GRASS_VARIANTS  # Same tiles, but we'll add a 'biome' field

# Water middle tile
WATER_TILE = {'id': 'water_mid', 'source': 'Tilesets/Water.png', 'x': 16, 'y': 0, 'w': 16, 'h': 16}

# Path tiles (from Paths.png 64x64, 16px grid)
PATH_TILES = {
    'center': {'id': 'path_center', 'source': 'Objects/Paths.png', 'x': 16, 'y': 16, 'w': 16, 'h': 16},
    'h': {'id': 'path_h', 'source': 'Objects/Paths.png', 'x': 16, 'y': 16, 'w': 16, 'h': 16},
    'v': {'id': 'path_v', 'source': 'Objects/Paths.png', 'x': 16, 'y': 16, 'w': 16, 'h': 16},
}


# === TREE TYPES for different biomes ===
MEADOW_TREES = ['fruit1', 'fruit2', 'fruit3', 'small', 'bush']
FOREST_TREES = ['big', 'big2', 'huge', 'med2', 'med1', 'bush']
CHERRY_TREES = []  # Cherry trees are placed separately via generate_cherry_trees()

# Decoration frames (from Mushrooms, Flowers, Stones.png)
MEADOW_DECORATIONS = ['flower1', 'flower2', 'flower3', 'flower4', 'mushroom1']
FOREST_DECORATIONS = ['mushroom1', 'mushroom2', 'mushroom3', 'stone1']


def is_in_zone(tx, ty, zone, margin=1):
    """Check if tile (tx, ty) is inside a reserved zone (with margin)."""
    return (zone['tx'] - margin <= tx < zone['tx'] + zone['tw'] + margin and
            zone['ty'] - margin <= ty < zone['ty'] + zone['th'] + margin)


def is_reserved(tx, ty):
    """Check if a tile is in any reserved structure zone."""
    for zone in [HOUSE_ZONE, FARM_ZONE, WELL_ZONE, PICNIC_ZONE]:
        if is_in_zone(tx, ty, zone, margin=2):
            return True
    # Also reserve spawn area
    if abs(tx - SPAWN_TX) <= 2 and abs(ty - SPAWN_TY) <= 2:
        return True
    return False


def generate_biome_map(seed):
    """Generate a 2D array of biome types using noise."""
    random.seed(seed)
    noise_offset_x = random.uniform(0, 1000)
    noise_offset_y = random.uniform(0, 1000)

    biome_grid = []
    height_grid = []

    for ty in range(MAP_ROWS):
        row = []
        hrow = []
        for tx in range(MAP_COLS):
            # Get noise value
            nx = tx * NOISE_SCALE + noise_offset_x
            ny = ty * NOISE_SCALE + noise_offset_y
            h = snoise2(nx, ny,
                       octaves=NOISE_OCTAVES,
                       persistence=NOISE_PERSISTENCE,
                       lacunarity=NOISE_LACUNARITY)
            hrow.append(h)

            # Assign biome based on height
            if is_reserved(tx, ty):
                row.append('meadow')  # Reserved areas are always meadow
            elif h < WATER_THRESHOLD:
                row.append('water')
            elif h < BEACH_THRESHOLD:
                row.append('beach')
            elif h < MEADOW_THRESHOLD:
                row.append('meadow')
            elif h < FOREST_THRESHOLD:
                row.append('forest_light')
            else:
                row.append('forest_dense')

            # Ensure areas around structures are meadow
        biome_grid.append(row)
        height_grid.append(hrow)

    # Carve paths between structures
    carve_path(biome_grid, SPAWN_TX, SPAWN_TY, HOUSE_ZONE['tx'] + 2, HOUSE_ZONE['ty'] + 4)
    carve_path(biome_grid, HOUSE_ZONE['tx'] + 4, HOUSE_ZONE['ty'] + 2, FARM_ZONE['tx'], FARM_ZONE['ty'] + 3)
    carve_path(biome_grid, SPAWN_TX, SPAWN_TY, WELL_ZONE['tx'] + 1, WELL_ZONE['ty'] + 1)
    carve_path(biome_grid, SPAWN_TX, SPAWN_TY, PICNIC_ZONE['tx'] + 2, PICNIC_ZONE['ty'] + 2)

    # Add beach transition around water edges
    add_water_transitions(biome_grid)

    return biome_grid, height_grid


def add_water_transitions(biome_grid):
    """Add beach tiles around water edges for smooth transitions."""
    water_neighbors = set()
    for ty in range(len(biome_grid)):
        for tx in range(len(biome_grid[0])):
            if biome_grid[ty][tx] == 'water':
                # Check all 8 neighbors
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = ty + dy, tx + dx
                        if 0 <= ny < len(biome_grid) and 0 <= nx < len(biome_grid[0]):
                            if biome_grid[ny][nx] not in ('water', 'beach', 'path'):
                                water_neighbors.add((ny, nx))

    for (ty, tx) in water_neighbors:
        if not is_reserved(tx, ty):
            biome_grid[ty][tx] = 'beach'


def carve_path(biome_grid, x1, y1, x2, y2):
    """Carve a path between two points using L-shaped routing."""
    # Go horizontal first, then vertical
    cx, cy = x1, y1
    while cx != x2:
        if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
            biome_grid[cy][cx] = 'path'
            # Widen path slightly
            if cy + 1 < MAP_ROWS:
                biome_grid[cy + 1][cx] = 'path'
        cx += 1 if x2 > cx else -1

    while cy != y2:
        if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
            biome_grid[cy][cx] = 'path'
            if cx + 1 < MAP_COLS:
                biome_grid[cy][cx + 1] = 'path'
        cy += 1 if y2 > cy else -1


def generate_objects(biome_grid, seed):
    """Generate the tile objects array (ground tiles)."""
    random.seed(seed + 1)
    objects = []
    obj_id = 0

    for ty in range(MAP_ROWS):
        for tx in range(MAP_COLS):
            biome = biome_grid[ty][tx]
            px = tx * TILE_SCALED
            py = ty * TILE_SCALED

            if biome == 'water':
                asset_id = WATER_TILE['id']
            elif biome == 'path':
                asset_id = PATH_TILES['center']['id']
            elif biome == 'beach':
                # Beach uses lighter grass or path
                asset_id = random.choice(['grass_a', 'path_center'])
            else:
                # Grass variants for meadow and forest
                variant = random.choice(GRASS_VARIANTS)
                asset_id = variant['id']

            objects.append({
                'id': f'tile_{obj_id}',
                'assetId': asset_id,
                'tx': tx,
                'ty': ty,
                'biome': biome,
                'isAbovePlayer': False,
                'x': px,
                'y': py,
                'scale': SCALE,
                'w': TILE_SIZE,
                'h': TILE_SIZE
            })
            obj_id += 1

    return objects


def generate_trees(biome_grid, seed):
    """Scatter trees based on biome."""
    random.seed(seed + 2)
    trees = []

    # Margin: don't place trees within 3 tiles of map edge
    MARGIN = 3

    for ty in range(MARGIN, MAP_ROWS - MARGIN):
        for tx in range(MARGIN, MAP_COLS - MARGIN):
            if is_reserved(tx, ty):
                continue

            biome = biome_grid[ty][tx]
            px = tx * TILE_SCALED + TILE_SCALED // 2
            py = ty * TILE_SCALED + TILE_SCALED

            if biome == 'forest_dense':
                if random.random() < 0.25:
                    tree_type = random.choice(FOREST_TREES)
                    scale = random.uniform(1.8, 2.4)
                    trees.append({'x': px + random.randint(-8, 8),
                                  'y': py + random.randint(-4, 4),
                                  'type': tree_type, 'scale': round(scale, 1)})
            elif biome == 'forest_light':
                if random.random() < 0.12:
                    tree_type = random.choice(FOREST_TREES[:3])
                    scale = random.uniform(1.6, 2.2)
                    trees.append({'x': px + random.randint(-8, 8),
                                  'y': py + random.randint(-4, 4),
                                  'type': tree_type, 'scale': round(scale, 1)})
            elif biome == 'meadow':
                if random.random() < 0.03:
                    tree_type = random.choice(MEADOW_TREES)
                    scale = random.uniform(1.6, 2.2)
                    trees.append({'x': px + random.randint(-8, 8),
                                  'y': py + random.randint(-4, 4),
                                  'type': tree_type, 'scale': round(scale, 1)})

    return trees


def generate_decorations(biome_grid, seed):
    """Scatter flowers, mushrooms, stones."""
    random.seed(seed + 3)
    decorations = []

    for ty in range(MAP_ROWS):
        for tx in range(MAP_COLS):
            if is_reserved(tx, ty):
                continue

            biome = biome_grid[ty][tx]
            px = tx * TILE_SCALED + random.randint(0, TILE_SCALED)
            py = ty * TILE_SCALED + random.randint(0, TILE_SCALED)

            if biome == 'meadow':
                if random.random() < 0.08:
                    frame = random.choice(MEADOW_DECORATIONS)
                    decorations.append({'x': px, 'y': py, 'frame': frame,
                                        'scale': random.uniform(1.5, 2.5)})
            elif biome in ('forest_light', 'forest_dense'):
                if random.random() < 0.06:
                    frame = random.choice(FOREST_DECORATIONS)
                    decorations.append({'x': px, 'y': py, 'frame': frame,
                                        'scale': random.uniform(1.5, 2.5)})

    return decorations


def generate_collisions(biome_grid, trees):
    """Generate collision boxes for water tiles and tree trunks."""
    collisions = []

    # Water tile collisions
    for ty in range(MAP_ROWS):
        for tx in range(MAP_COLS):
            if biome_grid[ty][tx] == 'water':
                collisions.append({
                    'x': tx * TILE_SCALED,
                    'y': ty * TILE_SCALED,
                    'w': TILE_SCALED,
                    'h': TILE_SCALED
                })

    return collisions


def generate_cherry_trees(biome_grid, seed):
    """Place cherry blossom trees near the house area for that cozy vibe."""
    random.seed(seed + 4)
    cherry = []
    # Put a few cherry trees around the house
    house_cx = (HOUSE_ZONE['tx'] + HOUSE_ZONE['tw'] / 2) * TILE_SCALED
    house_cy = (HOUSE_ZONE['ty'] + HOUSE_ZONE['th'] / 2) * TILE_SCALED

    for _ in range(5):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(120, 250)
        cx = house_cx + math.cos(angle) * dist
        cy = house_cy + math.sin(angle) * dist
        tex = random.choice(['cherryBig', 'cherryBig2', 'cherryMed'])
        scale = random.uniform(2.0, 2.8)
        cherry.append({'x': round(cx), 'y': round(cy), 'texKey': tex, 'scale': round(scale, 1)})

    return cherry


def generate_map(seed=None):
    """Generate the complete map.json data."""
    if seed is None:
        seed = random.randint(0, 999999)
    print(f"Generating map with seed: {seed}")

    biome_grid, height_grid = generate_biome_map(seed)
    objects = generate_objects(biome_grid, seed)
    trees = generate_trees(biome_grid, seed)
    decorations = generate_decorations(biome_grid, seed)
    collisions = generate_collisions(biome_grid, trees)
    cherry_trees = generate_cherry_trees(biome_grid, seed)

    # Pixel coords for structures
    house_px = (HOUSE_ZONE['tx'] + HOUSE_ZONE['tw'] // 2) * TILE_SCALED
    house_py = (HOUSE_ZONE['ty'] + HOUSE_ZONE['th']) * TILE_SCALED
    well_px = (WELL_ZONE['tx'] + 1) * TILE_SCALED
    well_py = (WELL_ZONE['ty'] + 2) * TILE_SCALED
    picnic_px = (PICNIC_ZONE['tx'] + 1) * TILE_SCALED
    picnic_py = (PICNIC_ZONE['ty'] + 2) * TILE_SCALED
    farm_px = (FARM_ZONE['tx'] + FARM_ZONE['tw'] // 2) * TILE_SCALED
    farm_py = (FARM_ZONE['ty'] + 1) * TILE_SCALED

    # Build assets list (all tile definitions needed)
    assets = []
    seen_ids = set()
    for v in GRASS_VARIANTS:
        if v['id'] not in seen_ids:
            assets.append(v)
            seen_ids.add(v['id'])
    if WATER_TILE['id'] not in seen_ids:
        assets.append(WATER_TILE)
        seen_ids.add(WATER_TILE['id'])
    for k, v in PATH_TILES.items():
        if v['id'] not in seen_ids:
            assets.append(v)
            seen_ids.add(v['id'])

    map_data = {
        'mapConfig': {
            'width': MAP_WIDTH,
            'height': MAP_HEIGHT,
            'spawnX': SPAWN_TX * TILE_SCALED + TILE_SCALED // 2,
            'spawnY': SPAWN_TY * TILE_SCALED + TILE_SCALED // 2,
            'scale': SCALE,
            'tileSize': TILE_SIZE,
            'tileCols': MAP_COLS,
            'tileRows': MAP_ROWS,
            'seed': seed,
            'borderAssetId': ''
        },
        'biomeGrid': biome_grid,  # 2D array for the renderer to use
        'assets': assets,
        'objects': objects,
        'collisions': collisions,
        'house': {
            'x': house_px,
            'y': house_py,
            'scale': SCALE
        },
        'farm': {
            'x': farm_px,
            'y': farm_py,
            'cols': 3,
            'rows': 3,
            'cellSize': TILE_SCALED,
            'fences': {
                'top':    {'x': farm_px - TILE_SCALED * 2, 'y': farm_py - TILE_SCALED, 'count': 6, 'dir': 'h'},
                'bottom': {'x': farm_px - TILE_SCALED * 2, 'y': farm_py + TILE_SCALED * 3, 'count': 6, 'dir': 'h'},
                'left':   {'x': farm_px - TILE_SCALED * 2, 'y': farm_py - TILE_SCALED, 'count': 5, 'dir': 'v'},
                'right':  {'x': farm_px + TILE_SCALED * 2, 'y': farm_py - TILE_SCALED, 'count': 5, 'dir': 'v'},
            },
            'crops': [4, 5, 6, 12, 13, 14, 20, 21, 22]
        },
        'fences': [
            {'x': house_px - 120, 'y': house_py + 30, 'count': 6, 'dir': 'h'},
            {'x': house_px - 120, 'y': house_py + 30, 'count': 3, 'dir': 'v'},
            {'x': house_px + 80,  'y': house_py + 30, 'count': 3, 'dir': 'v'},
        ],
        'trees': trees,
        'cherryTrees': cherry_trees,
        'decorations': decorations,
        'well': {
            'x': well_px,
            'y': well_py,
            'scale': 2.5
        },
        'picnic': {
            'blanketX': picnic_px,
            'blanketY': picnic_py,
            'basketX': picnic_px + 15,
            'basketY': picnic_py - 10,
            'scale': 2.5
        },
        'animals': {
            'cookie': {'x': house_px + 20, 'y': house_py + 60, 'roamRadius': 100, 'speed': 0.8},
            'heihei': {'x': house_px - 150, 'y': house_py + 120, 'roamRadius': 80, 'speed': 0.5},
            'huahua': {'x': house_px + 120, 'y': house_py + 100, 'roamRadius': 80, 'speed': 0.4},
            'mumu':   {'x': house_px - 80, 'y': house_py + 180, 'roamRadius': 80, 'speed': 0.6},
        },
        'chickens': [
            {'x': farm_px - 20, 'y': farm_py + 20},
            {'x': farm_px + 30, 'y': farm_py + 60},
            {'x': farm_px + 10, 'y': farm_py + 90},
        ]
    }

    return map_data


def print_biome_preview(biome_grid):
    """Print ASCII preview of the biome map."""
    symbols = {
        'water': '~',
        'beach': '.',
        'meadow': ' ',
        'forest_light': '+',
        'forest_dense': '#',
        'path': '=',
    }
    print("\n=== Biome Map Preview ===")
    for row in biome_grid:
        print(''.join(symbols.get(b, '?') for b in row))
    print("Legend: ~water .beach (space)meadow +light_forest #dense_forest =path")


def main():
    global MAP_COLS, MAP_ROWS, MAP_WIDTH, MAP_HEIGHT

    parser = argparse.ArgumentParser(description='Generate Cozy Claw map')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--output', type=str, default='map.json', help='Output file')
    parser.add_argument('--preview', action='store_true', help='Print ASCII preview')
    parser.add_argument('--cols', type=int, default=MAP_COLS, help='Map columns')
    parser.add_argument('--rows', type=int, default=MAP_ROWS, help='Map rows')
    args = parser.parse_args()

    MAP_COLS = args.cols
    MAP_ROWS = args.rows
    MAP_WIDTH = MAP_COLS * TILE_SCALED
    MAP_HEIGHT = MAP_ROWS * TILE_SCALED

    map_data = generate_map(args.seed)

    if args.preview:
        print_biome_preview(map_data['biomeGrid'])

    # Write output
    with open(args.output, 'w') as f:
        json.dump(map_data, f)

    size_kb = len(json.dumps(map_data)) / 1024
    print(f"Generated {args.output}: {MAP_COLS}x{MAP_ROWS} tiles, {len(map_data['objects'])} objects, "
          f"{len(map_data['trees'])} trees, {len(map_data['decorations'])} decorations, "
          f"{size_kb:.0f}KB")


if __name__ == '__main__':
    main()
