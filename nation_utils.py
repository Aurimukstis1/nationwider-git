import json
import multiprocessing
import time
import arcade
import arcade.gui
import numpy
import os
from PIL import Image

tile_texture = arcade.load_texture('local_data/sprite_texture.png')

class Icon(arcade.Sprite):
    """An icon on the map using a texture."""
    def __init__(self, path_or_texture = None, scale = 1, center_x = 0, center_y = 0, angle = 0, icon_id = 0, angle_rot = 0, unique_id = 1000, country_id = 0, quality = 1, **kwargs):
        super().__init__(path_or_texture, scale, center_x, center_y, angle, **kwargs)
        self.icon_id = icon_id
        self.unique_id = unique_id
        self.angle_rot = angle_rot
        self.country_id = country_id
        self.quality = quality

class Toast(arcade.gui.UILabel):
    """Info notification."""
    def __init__(self, text: str, duration: float = 2.0, **kwargs):
        super().__init__(**kwargs)
        self.text     = text
        self.duration = duration
        self.time     = 0

    def on_update(self, dt):
        self.time += dt

        if self.time > self.duration:
            self.parent.remove(self)

# class Tile(arcade.SpriteSolidColor):
#     __slots__ = ('id_',)
#     def __init__(self, width, height, x, y, color, id_):
#         super().__init__(width, height, x, y, color=color)
#         self.id_ = id_

class Tile(arcade.BasicSprite):
    def __init__(self, size = 1, center_x = 0, center_y = 0, id_ = 0, **kwargs):
        super().__init__(texture=tile_texture, scale=size, center_x=center_x, center_y=center_y, visible=True, **kwargs)
        self.id_ = id_

class GridLayer():
    """Suggestion from @typefoo"""
    def __init__(self, grid_size: tuple[int, int], tile_size: int = 10):
        self.tile_size = tile_size
        self.grid_size = grid_size
        self.grid = numpy.empty((grid_size[0], grid_size[1]), dtype=object)
        self.grid_width, self.grid_height = grid_size

    def __getitem__(self, grid_point: tuple[int, int]):
        x, y = grid_point
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.grid[x][y]
        return None
    
def get_all_files(directory):
    all_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
            
    return all_files

def get_attributes() -> dict:
    """Getting an attribute from the local file"""
    attributes_dictionary = None
    with open('local_data/attributes.json') as attributes_file:
        attributes_dictionary = json.load(attributes_file)
    print(f"O- local attributes accessed: {attributes_dictionary}")
    return attributes_dictionary

def set_attributes(attribute_name:str, input):
    """Setting an attribute in the local file"""
    attributes_dictionary = None
    with open('local_data/attributes.json', 'r') as attributes_file:
        attributes_dictionary = json.load(attributes_file)

    attributes_dictionary[f'{attribute_name}'] = input

    with open('local_data/attributes.json', 'w') as attributes_file:
        json.dump(attributes_dictionary, attributes_file)
        print(f"O- local attributes accessed: {attributes_dictionary}")

def get_pixel_coordinates(image_path:str) -> list:
    img = Image.open(image_path)

    img_array = numpy.array(img)

    coordinates = []
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if img_array[y, x].any() > 0:
                rel_y = (img.size[0]-1) - y
                rel_x = x
                coordinates.append((rel_x, rel_y))
    
    return coordinates

def compute_tiles_wrapper(coords, terrain_layer, political_layer, precomputed_terrain_colors, precomputed_political_colors, direction):
    x_start, x_end, y_start, y_end = coords
    return compute_tiles(terrain_layer, political_layer, x_start, x_end, y_start, y_end, 0, direction, precomputed_terrain_colors, precomputed_political_colors)

def compute_tiles(upper_layer, political_layer, x_start, x_end, y_start, y_end, map_name):
    print(f"?- precomputing {map_name} hemisphere {x_start,y_start} {x_start,x_end}")
    offset_y_ = 0
    if map_name == "south":
        offset_y_ = -6000
    timee = time.time()
    temp_tiles = []

    grid_terrain = upper_layer.grid
    grid_political = political_layer.grid

    for x in range(x_start, x_end):
        if x % 100 == 0:
            print(f"O- {round((x / x_end) * 100)}% {map_name} computed ...")

        terrain_row = grid_terrain[x]
        political_row = grid_political[x]

        for y in range(y_start, y_end):
            tile_id = terrain_row[y]
            political_tile_id = political_row[y]

            world_x = x * 20
            world_y = (y * 20) + offset_y_

            terrain_alpha = 0 if tile_id == 0 else 255
            political_alpha = 100 if tile_id == 0 else 255

            tile = Tile(20, world_x, world_y, id_=tile_id)
            tile.color = TILE_ID_MAP.get(tile_id,(255,255,255)) + (terrain_alpha,)
            political_tile = Tile(20, world_x, world_y, id_=political_tile_id)
            political_tile.color = POLITICAL_ID_MAP.get(political_tile_id,(255,255,255)) + (political_alpha,)

            temp_tiles.append((tile, political_tile, x, y))

    print(f"Process {multiprocessing.current_process().name} finished computing {map_name} in {time.time()-timee} s")
    return temp_tiles

def compute_lower_wrapper(coords, layer, terrain_colors):
    x_start, x_end, y_start, y_end = coords
    return compute_lower_tiles(layer, x_start, x_end, y_start, y_end, terrain_colors)

def compute_lower_tiles(layer, x_start, x_end, y_start, y_end, terrain_colors):
    print(f"?- precomputing higher detail {x_start,y_start} {x_start,y_end}")
    timer = time.time()
    temp_tiles_list = []
    grid_terrain = layer.grid

    for x in range(x_start, x_end):
        if x % 100 == 0:
            print(f"O- process : {multiprocessing.current_process} = {round((x_start / x_end) * 100, 3)}%")
        terrain_row = grid_terrain[x]
        for y in range(y_start, y_end):
            tile_id = terrain_row[y]
            world_x = x * 20
            world_y = y * 20
            terrain_alpha = 0 if tile_id == 0 else 255
            tile = Tile(20, 20, world_x, world_y, (*terrain_colors[tile_id], terrain_alpha), tile_id)
            temp_tiles_list.append((tile,x,y))

    print(f"Process {multiprocessing.current_process().name} finished computing in {time.time()-timer} s")
    return temp_tiles_list

#---
TILE_ID_MAP         = {
    255: (0, 0, 0),       # CLEAR TILE [ NONE ]
    254: (53, 53, 53),    # POLITICAL LAND
    253: (53, 53, 53),    # POLITICAL WATER
    0: (0, 0, 127),       # WATER
    1: (99, 173, 95),     # COLD PLAINS
    2: (52, 72, 40),      # BOREAL FOREST
    3: (10, 87, 6),       # DECIDUOUS FOREST
    4: (16, 59, 17),      # CONIFEROUS FOREST
    5: (64, 112, 32),     # TROPICAL FOREST
    6: (80, 96, 48),      # SWAMPLAND
    7: (7, 154, 0),       # PLAINS
    8: (12, 172, 0),      # PRAIRIE
    9: (124, 156, 0),     # SAVANNA
    10: (80, 80, 64),     # MARSHLAND
    11: (64, 80, 80),     # MOOR
    12: (112, 112, 64),   # STEPPE
    13: (64, 64, 16),     # TUNDRA
    14: (255, 186, 0),    # MAGMA
    15: (112, 80, 96),    # CANYONS
    16: (132, 132, 132),  # MOUNTAINS
    17: (112, 112, 96),   # STONE DESERT
    18: (64, 64, 57),     # CRAGS
    19: (192, 192, 192),  # SNOWLANDS
    20: (224, 224, 224),  # ICE PLAINS
    21: (112, 112, 32),   # BRUSHLAND
    22: (253, 157, 24),   # RED SANDS
    23: (238, 224, 192),  # SALT FLATS
    24: (255, 224, 160),  # COASTAL DESERT
    25: (255, 208, 144),  # DESERT
    26: (128, 64, 0),     # WETLAND
    27: (59, 29, 10),     # MUDLAND
    28: (84, 65, 65),     # HIGHLANDS/FOOTHILLS
    # SOUTH MAP ADDITIONS
    29: (170, 153, 153),  # ABYSSAL WASTE
    30: (182, 170, 191),  # PALE WASTE
    31: (51, 102, 153),   # ELYSIAN FOREST
    32: (10, 59, 59),     # ELYSIAN JUNGLE
    33: (203, 99, 81),    # VOLCANIC WASTES
    34: (121, 32, 32),    # IGNEOUS ROCKLAND
    35: (59, 10, 10),     # CRIMSON FOREST
    36: (192, 176, 80),   # FUNGAL FOREST
    37: (153, 204, 0),    # SULFURIC FIELDS
    38: (240, 240, 187),  # LIMESTONE DESERT
    39: (255, 163, 255),  # DIVINE FIELDS
    40: (170, 48, 208),   # DIVINE MEADOW
    41: (117, 53, 144),   # DIVINE WOODLAND
    42: (102, 32, 137)    # DIVINE EDEN
}

POLITICAL_ID_MAP    = {
    0   :   (53, 53, 53), # wilderness
    1   :   (121, 7, 18),
    2   :   (42, 86, 18),
    3   :   (183, 197, 215),
    4   :   (20, 209, 136),
    5   :   (193, 38, 38),
    6   :   (63, 63, 116), # Aurimukstis1
    7   :   (10, 41, 93),
    8   :   (18, 158, 165),
    9   :   (20, 55, 17),
    10  :   (196, 153, 0),
    11  :   (243, 104, 6),
    12  :   (84, 198, 223),
    13  :   (95, 22, 151),
    14  :   (48, 114, 214),
    15  :   (78, 104, 77),
    16  :   (0, 112, 141),
    17  :   (243, 145, 51)
}

ICON_ID_MAP         = {
    0: "icons/structures/str_village",
    1: "icons/structures/str_town",
    2: "icons/structures/str_city",
    3: "icons/structures/str_metro",
    4: "icons/structures/str_outpost",
    5: "icons/structures/str_keep",
    6: "icons/structures/str_fortress",
    7: "icons/structures/str_bastion",
    # -
    8: "icons/info/info_note",
    9: "icons/info/info_line",
    # - 
    10:"icons/units/vessel_raft",
    11:"icons/units/vessel_cog",
    12:"icons/units/vessel_yawl",
    13:"icons/units/vessel_brig",
    14:"icons/units/vessel_corvette",
    15:"icons/units/vessel_frigate",
    16:"icons/units/vessel_cruiser",
    17:"icons/units/vessel_battleship",
    18:"icons/units/vessel_dreadnought",
    19:"icons/units/vessel_carrier",
    # -
    20:"icons/units/unit_artillery",
    21:"icons/units/unit_cavalry",
    22:"icons/units/unit_heavy_artillery",
    23:"icons/units/unit_heavy_cavalry",
    24:"icons/units/unit_heavy_infantry",
    25:"icons/units/unit_infantry",
    26:"icons/units/unit_ranged_cavalry",
    27:"icons/units/unit_ranged_infantry",
    28:"icons/units/unit_skirmishers",
    # -
}

QUALITY_COLOR_MAP   = {
    1: (125,125,125),
    2: (150,150,150),
    3: (175,175,175),
    4: (200,200,200),
    5: (255,255,255)
}

BIOME_PALETTE = {
    # --- 
    "WATER": 0,
    "COLD_PLAINS": 1,
    "BOREAL_FOREST": 2,
    "DECIDUOUS_FOREST": 3,
    # --- 
    "CONIFEROUS_FOREST": 4,
    "TROPICAL_FOREST": 5,
    "SWAMPLAND": 6,
    "PLAINS": 7,
    # --- 
    "PRAIRIE": 8,
    "SAVANNA": 9,
    "MARSHLAND": 10,
    "MOOR": 11,
    # --- 
    "STEPPE": 12,
    "TUNDRA": 13,
    "MAGMA": 14,
    "CANYONS": 15,
    # --- 
    "MOUNTAINS": 16,
    "STONE_DESERT": 17,
    "CRAGS": 18,
    "SNOWLANDS": 19,
    # --- 
    "ICE_PLAINS": 20,
    "BRUSHLAND": 21,
    "RED_SANDS": 22,
    "SALT_FLATS": 23,
    # --- 
    "COASTAL_DESERT": 24,
    "DESERT": 25,
    "WETLAND": 26,
    "MUDLAND": 27,
    # --- 
    "HIGHLANDS": 28,
    "ABYSSAL_WASTE": 29,
    "PALE_WASTE": 30,
    "ELYSIAN_FOREST": 31,
    # --- 
    "ELYSIAN_JUNGLE": 32,
    "VOLCANIC_WASTES": 33,
    "IGNEOUS_ROCKLAND": 34,
    "CRIMSON_FOREST": 35,
    # --- 
    "FUNGAL_FOREST": 36,
    "SULFURIC_FIELDS": 37,
    "LIMESTONE_DESERT": 38,
    "DIVINE_FIELDS": 39,
    # --- 
    "DIVINE_MEADOW": 40,
    "DIVINE_WOODLAND": 41,
    "DIVINE_EDEN": 42
    # ...
    # --- 
}

COUNTRY_PALETTE =  {
    "wilderness"        : 0,
    "DragonEgglol"      : 1,
    "Hoovyzepoot"       : 2,
    "Watboi"            : 3,
    "ASimpleCreator"    : 4,
    "Catarmour"         : 5,
    "Aurimukstis1"      : 6,
    "Tuna"              : 7,
    "Rubidianlabs"      : 8,
    "LightningBMW"      : 9,
    "N2H4"              : 10,
    "Loiosh"            : 11,
    "Antigrain"         : 12,
    "AVeryBigNurd"      : 13,
    "Superbantom"       : 14,
    "NuttyMCNuttzz"     : 15,
    "Raven314"          : 16,
    "Spikey_boy"        : 17
}


if __name__ == "__main__":
    print("""nation-utils, custom python file for holding reused code for several files.""")