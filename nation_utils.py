import json
import arcade
import arcade.gui
import numpy
import os
import noise
import math
import random
from PIL import Image

tile_texture = arcade.load_texture('local_data/sprite_texture.png')

class Icon:
    """An icon on the map using a texture."""
    class Civilian(arcade.Sprite):
        def __init__(self,
                    # necessary:
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None),
                    angle:float = 0,
                    # custom:
                    icon_id:int = 0,
                    unique_id:int = 0,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], angle, **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id

    class Military(arcade.Sprite):
        def __init__(self,
                    # necessary:
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None),
                    angle:float = 0,
                    # custom:
                    icon_id:int = 0,
                    unique_id:int = 0,
                    country_id:int = 0,
                    angle_rot:float = 0,
                    quality:int = 1,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], angle, **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id
            self.country_id = country_id
            self.angle_rot = angle_rot
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

class Tile(arcade.BasicSprite):
    def __init__(self, size = 1, center_x = 0, center_y = 0, id_ = 0, **kwargs):
        super().__init__(texture=tile_texture, scale=size, center_x=center_x, center_y=center_y, visible=True, **kwargs)
        self.id_ = id_

class Shape():
    def __init__(self, input_shape:list = []):
        self.shape = input_shape
        self.unique_id:int = random.randrange(10000,99999)

class GridLayer():
    """Suggestion from @typefoo"""
    def __init__(self, grid_size: tuple[int, int]):
        self.grid_size = grid_size
        self.grid = numpy.empty((grid_size[0], grid_size[1]), dtype=numpy.uint8)
    
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

def generate_blob_coordinates(width, height, scale=0.1, threshold=0.7, octaves=6, persistence=0.5, lacunarity=10.0, seed=None) -> list:
    if seed is None:
        seed = numpy.random.randint(0, 10000)

    coordinates = []

    for y in range(height):
        for x in range(width):
            nx = x * scale
            ny = y * scale
            value = noise.pnoise2(nx,
                                  ny,
                                  octaves=octaves,
                                  persistence=persistence,
                                  lacunarity=lacunarity,
                                  repeatx=width,
                                  repeaty=height,
                                  base=seed)
            norm_val = (value + 0.5)
            if norm_val > threshold:
                coordinates.append((x, y))

    return coordinates

def closest_color(target_rgb, color_dict):
    """
    Finds the ID of the closest RGB color in color_dict to the target_rgb.

    :param target_rgb: Tuple of (R, G, B) values to match.
    :param color_dict: Dictionary mapping IDs to (R, G, B) tuples.
    :return: ID of the closest matching color.
    """
    def euclidean_distance(c1, c2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
    
    return min(color_dict, key=lambda k: euclidean_distance(target_rgb, color_dict[k]))

#---
CLIMATE_ID_MAP = {
    0: (0, 0, 0), #none
    # --- A 
    1: (0, 0, 255), #Af (Rainforest)
    2: (0, 120, 255), #Am (Monsoon)
    3: (70, 170, 250), #Aw (Savanna, dry winter)
    4: (121, 186, 236), #As (Savanna, dry summer)
    # --- B
    5: (255, 0, 0), # BWh (Arid desert) (Hot)
    6: (255, 150, 150), # BWk (Arid desert) (Cold)
    7: (245, 165, 0), # BSh (Semi-arid steppe) (Hot)
    8: (255, 220, 100), # BSk (Semi-arid steppe) (Cold)
    # --- C
    9: (150, 255, 150), # Cwa (Dry winter) (Hot summer)
    10:(100, 200, 100), # Cwb (Dry winter) (Warm summer)
    11:(50, 150, 50), # Cwc (Dry winter) (Cold summer)

    12:(200, 255, 80), # Cfa (No dry season) (Hot summer)
    13:(100, 255, 80), # Cfb (No dry season) (Warm summer)
    14:(50, 200, 0), # Cfc (No dry season) (Cold summer)

    15:(255, 255, 0), # Csa (Dry summer) (Hot summer)
    16:(200, 200, 0), # Csb (Dry summer) (Warm summer)
    17:(150, 150, 0), # Csc (Dry summer) (Cold summer)
    # --- D
    18:(170, 175, 255), # Dwa (Dry winter) (Hot summer)
    19:(90, 120, 220), # Dwb (Dry winter) (Warm summer)
    20:(75, 80, 180), # Dwc (Dry winter) (Cold summer)
    21:(50, 0, 135), # Dwd (Dry winter) (Very cold winter)

    22:(0, 255, 255), # Dfa (No dry season) (Hot summer)
    23:(55, 200, 255), # Dfb (No dry season) (Warm summer)
    24:(0,125,125), # Dfc (No dry season) (Cold summer)
    25:(0, 70, 95), # Dfd (No dry season) (Very cold winter)

    26:(255, 0, 255), # Dsa (Dry summer) (Hot summer)
    27:(200, 0, 200), # Dsb (Dry summer) (Warm summer)
    28:(150, 50, 150), # Dsc (Dry summer) (Cold summer)
    29:(150, 100, 150), # Dsd (Dry summer) (Very cold winter)
    # --- E
    30:(178, 178, 178), # ET (Tundra)
    31:(102, 102, 102), # EF (Ice cap)
}

TEMPERATURE_ID_MAP = {
    0: (0, 0, 0), #none
    # ---
    1: (0, 35, 135),
    2: (40, 75, 170),
    3: (65, 100, 195),
    4: (90, 125, 225),
    # ---
    5: (45, 130, 90),
    6: (105, 170, 45),
    7: (120, 210, 35),
    8: (130, 225, 40),
    # ---
    9: (250, 240, 55)
}

TEMPERATURE_PALETTE = {
    'erase/none': 0,
    'average -40C/-40F': 1,
    'average -30C/-22F': 2,
    'average -20C/+4F': 3,
    'average -10C/+14F': 4,
    'average +0C/+32F': 5,
    'average +10C/+50F': 6,
    'average +20C/+68F': 7,
    'average +30C/+86F': 8,
    'average +40C/+104F': 9
}

TILE_ID_MAP         = {
    255: (0, 0, 0),       # CLEAR TILE [ NONE ]
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
    17  :   (213, 145, 51),
    # ---
    18  :   (150, 110, 40),
    19  :   (30, 135, 117),
    20  :   (145, 145, 145),
    21  :   (180, 52, 111),
    22  :   (225, 225, 225),
    23  :   (61, 96, 29),
    24  :   (200, 166, 0),
    25  :   (97, 97, 84),
    26  :   (17, 49, 14),
    27  :   (212, 54, 69),
    28  :   (45, 29, 95)
}

CIVILIAN_ICON_ID_MAP = {
    0: "icons/structures/str_village",
    1: "icons/structures/str_town",
    2: "icons/structures/str_city",
    3: "icons/structures/str_metro",
}

MILITARY_ICON_ID_MAP = {
    0: "icons/structures/str_outpost",
    1: "icons/structures/str_keep",
    2: "icons/structures/str_fortress",
    3: "icons/structures/str_bastion",
    # - 
    4:"icons/units/vessel_raft",
    5:"icons/units/vessel_cog",
    6:"icons/units/vessel_yawl",
    7:"icons/units/vessel_brig",
    8:"icons/units/vessel_corvette",
    9:"icons/units/vessel_frigate",
    10:"icons/units/vessel_cruiser",
    11:"icons/units/vessel_battleship",
    12:"icons/units/vessel_dreadnought",
    13:"icons/units/vessel_carrier",
    # -
    14:"icons/units/unit_artillery",
    15:"icons/units/unit_cavalry",
    16:"icons/units/unit_heavy_artillery",
    17:"icons/units/unit_heavy_cavalry",
    18:"icons/units/unit_heavy_infantry",
    19:"icons/units/unit_infantry",
    20:"icons/units/unit_ranged_cavalry",
    21:"icons/units/unit_ranged_infantry",
    22:"icons/units/unit_skirmishers",
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
    "unclaimed"         : 0,
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
    "Spikey_boy"        : 17,
    # ---
    "AI_PLACEHOLDER_0"  : 18,
    "AI_PLACEHOLDER_1"  : 19,
    "AI_PLACEHOLDER_2"  : 20,
    "AI_PLACEHOLDER_3"  : 21,
    "AI_PLACEHOLDER_4"  : 22,
    "AI_PLACEHOLDER_5"  : 23,
    "AI_PLACEHOLDER_6"  : 24,
    "AI_PLACEHOLDER_7"  : 25,
    "AI_PLACEHOLDER_8"  : 26,
    "AI_PLACEHOLDER_9"  : 27,
    "AI_PLACEHOLDER_10" : 28
}

CLIMATE_PALETTE = {
    'Erase/none': 0,
    # --- A ---
    'Af Tropical rainforest climate': 1,
    'Am Tropical monsoon climate': 2,
    'Aw Savanna dry winter': 3,
    'As Savanna dry summer': 4,
    # --- B ---
    'BWh Hot desert climate': 5,
    'BWk Cold desert climate': 6,
    'BSh Hot semi-arid climate': 7,
    'BSk Cold semi-arid climate': 8,
    # --- C ---
    'Cwa Monsoon-influenced humid subtropical climate': 9,
    'Cwb Subtropical highland climate': 10,
    'Cwc Cold subtropical highland climate': 11,
    'Cfa Humid subtropical climate': 12,
    'Cfb Temperate oceanic climate': 13,
    'Cfc Subpolar oceanic climate': 14,
    'Csa Hot-summer Mediterranean climate': 15,
    'Csb Warm-summer Mediterranean climate': 16,
    'Csc Cold-summer Mediterranean climate': 17,
    # --- D ---
    'Dwa Monsoon-influenced hot-summer humid continental climate': 18,
    'Dwb Monsoon-influenced warm-summer humid continental climate': 19,
    'Dwc Monsoon-influenced subarctic climate': 20,
    'Dwd Monsoon-influenced extremely cold subarctic climate': 21,
    'Dfa Hot-summer humid continental climate': 22,
    'Dfb Warm-summer humid continental climate': 23,
    'Dfc Subarctic climate': 24,
    'Dfd Extremely cold subarctic climate': 25,
    'Dsa Mediterranean-influenced hot-summer humid continental climate': 26,
    'Dsb Mediterranean-influenced warm-summer humid continental climate': 27,
    'Dsc Mediterranean-influenced subarctic climate': 28,
    'Dsd Mediterranean-influenced extremely cold subarctic climate': 29,
    # --- E ---
    'ET Tundra climate': 30,
    'EF Ice cap climate': 31
}

if __name__ == "__main__":
    print("""nation-utils, custom python file for holding reused code for several files.""")