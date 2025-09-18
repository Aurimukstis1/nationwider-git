import json
import arcade
import arcade.gui
import numpy
import os
import noise
import math
import random
from PIL import Image
from typing import Any

"""
Utility functions and classes for map and nation management.

This helper module provides utilities for working with map data, icons, and nation attributes:

- Grid class for managing 2D map data arrays
- Icon classes for military and civilian map markers 
- File handling functions for loading/saving attributes and map data
- Color mapping constants for biomes, countries, climate, etc.
- Helper functions for coordinate conversion and pixel operation
"""

class Icon:
    """An icon on the map using a texture.
    
    This class provides base functionality for map icons, with specialized subclasses
    for civilian and military icons.
    """
    class Misc(arcade.Sprite):
        """A miscellaneous icon that can be placed on the map.
        
        Args:
            path_or_texture (arcade.texture, optional): Texture to use for the icon. Defaults to None.
            scale (float, optional): Scale factor for the icon size. Defaults to 1.
            center (tuple, optional): (x,y) position to place icon. Defaults to (None,None).
            angle (float, optional): Rotation angle in degrees. Defaults to 0.
            icon_id (int, optional): ID indicating icon type. Defaults to 0.
            unique_id (int, optional): Unique identifier for this specific icon. Defaults to 0.
        """
        def __init__(self,
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None),
                    angle:float = 0,
                    icon_id:int = 0,
                    unique_id:int = 0,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], angle, **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id

    class Civilian(arcade.Sprite):
        """A civilian icon that can be placed on the map.
        
        Args:
            path_or_texture (arcade.texture, optional): Texture to use for the icon. Defaults to None.
            scale (float, optional): Scale factor for the icon size. Defaults to 1.
            center (tuple, optional): (x,y) position to place icon. Defaults to (None,None).
            angle (float, optional): Rotation angle in degrees. Defaults to 0.
            icon_id (int, optional): ID indicating icon type. Defaults to 0.
            unique_id (int, optional): Unique identifier for this specific icon. Defaults to 0.
            **kwargs: Additional keyword arguments passed to arcade.Sprite.
        """
        def __init__(self,
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None), 
                    angle:float = 0,
                    icon_id:int = 0,
                    unique_id:int = 0,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], angle, **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id

    class Decorator(arcade.BasicSprite):
        """A decorator icon that floats above the attached icon."""
        def __init__(self,
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None),
                    icon_id:int = 0,
                    unique_id:int = 0,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id
            self.alpha = 155

    class Military(arcade.Sprite):
        """A military icon that can be placed on the map.
        
        Args:
            path_or_texture (arcade.texture, optional): Texture to use for the icon. Defaults to None.
            scale (float, optional): Scale factor for the icon size. Defaults to 1.
            center (tuple, optional): (x,y) position to place icon. Defaults to (None,None).
            angle (float, optional): Rotation angle in degrees. Defaults to 0.
            icon_id (int, optional): ID indicating icon type. Defaults to 0.
            unique_id (int, optional): Unique identifier for this specific icon. Defaults to 0.
            country_id (int, optional): ID of the country this unit belongs to. Defaults to 0.
            angle_rot (float, optional): Additional rotation angle. Defaults to 0.
            quality (int, optional): Quality/condition value of the unit. Defaults to 1.
            **kwargs: Additional keyword arguments passed to arcade.Sprite.
        """
        def __init__(self,
                    path_or_texture:arcade.texture = None,
                    scale:float = 1,
                    center:tuple = (None,None),
                    angle:float = 0,
                    icon_id:int = 0,
                    unique_id:int = 0,
                    country_id:int = 0,
                    angle_rot:float = 0,
                    quality:int = 1,
                    decorator_ids:list = None,
                    **kwargs):
            super().__init__(path_or_texture, scale, center[0], center[1], angle, **kwargs)
            self.icon_id = icon_id
            self.unique_id = unique_id
            self.country_id = country_id
            self.angle_rot = angle_rot
            self.quality = quality
            self.decorator_ids = [] if decorator_ids is None else list(decorator_ids)
            
            self.decorators = []

class Shape():
    """A class representing a shape made up of connected points.

    The Shape class stores a list of points that define a shape, along with a unique identifier.
    It is used to draw line shapes on the map.

    Attributes:
        shape (list): List of points (x,y tuples) defining the shape
        unique_id (int): Random unique identifier between 10000-99999

    Args:
        input_shape (list, optional): Initial list of points for the shape. Defaults to empty list.
    """
    def __init__(self, input_shape:list = []):
        self.shape = input_shape
        self.unique_id:int = random.randrange(10000,99999)

class InformationLayer():
    """
    An abstract class for information layers with no grid, containing just icons and lines.
    """
    def __init__(self, name:str):
        self.name = name
        self.shapes = []
        self.scene = arcade.Scene()
        self.scene.add_sprite_list("0")
        # ---
        self.canvas = self.scene.get_sprite_list("0")

    def wipe(self):
        self.shapes.clear()
        self.canvas.clear()

    def add_icon(self, icon:Icon):
        self.canvas.append(icon)

    def add_shape(self, shape:Shape):
        self.shapes.append(shape)

    def remove_shape(self, shape:Shape):
        self.shapes.remove(shape)

    def get_icons(self) -> list[arcade.Sprite | arcade.BasicSprite]:
        return self.canvas

class Toast(arcade.gui.UILabel):
    """A temporary notification label that automatically removes itself after a duration.

    The Toast class displays a text notification that automatically fades away after
    a specified duration. It inherits from arcade.gui.UILabel.

    Attributes:
        text (str): The text to display in the notification
        duration (float): How long in seconds before the notification disappears
        time (float): Internal timer tracking how long notification has been shown

    Args:
        text (str): The text to display
        duration (float, optional): Duration in seconds to show notification. Defaults to 2.0
        **kwargs: Additional keyword arguments passed to UILabel parent class
    """
    def __init__(self, text: str, duration: float = 2.0, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.duration = duration
        self.time = 0

    def on_update(self, dt):
        """Update the notification timer and remove if duration exceeded.
        
        Args:
            dt (float): Time elapsed since last update in seconds
        """
        self.time += dt

        if self.time > self.duration:
            self.parent.remove(self)

class GridLayer():
    """A 2D grid layer for storing map data.

    The GridLayer class represents a 2D grid of uint8 values used to store various map layers
    like terrain, political boundaries, climate zones etc.

    Attributes:
        grid_size (tuple[int, int]): Size of the grid as (width, height) tuple
        grid (numpy.ndarray): 2D numpy array of uint8 values representing the grid data

    Args:
        grid_size (tuple[int, int]): Size to initialize the grid as (width, height)
    """
    def __init__(self, grid_size: tuple[int, int]):
        self.grid_size = grid_size
        self.grid = numpy.empty((grid_size[0], grid_size[1]), dtype=numpy.uint8)
    
def find_files_simple(directory: str) -> list[str]:
    """
    Recursively get paths of all files in a specified directory.

    Args:
        directory (str): Path to the root directory to search

    Returns:
        list[str]: List of full file paths for all files found
    """
    return [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files
    ]

def find_files_iter(directory: str):
    """
    Recursively get paths of all files in a specified directory.

    Args:
        directory (str): Path to the root directory to search

    Returns:
        str: string generator yielding file paths for each file found
    """
    for root, _, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

def get_attributes() -> dict:
    """Load and return attributes from the local attributes.json file.
    
    Reads the attributes dictionary from local_data/attributes.json and returns it.
    
    Returns:
        dict: Dictionary containing the attributes loaded from the JSON file
    
    Raises:
        FileNotFoundError: If attributes.json file does not exist
        json.JSONDecodeError: If attributes.json contains invalid JSON
    """
    try:
        with open('local_data/attributes.json') as attributes_file:
            attributes = json.load(attributes_file)
            print(f"O- local attributes accessed: {attributes}")
            return attributes
    except FileNotFoundError:
        print("X- attributes.json file not found")
        raise
    except json.JSONDecodeError:
        print("X- invalid JSON in attributes.json") 
        raise

def set_attributes(attribute_name: str, value: Any) -> None:
    """Update an attribute value in the local attributes.json file.
    
    Opens the attributes.json file, updates the specified attribute with the new value,
    and writes the updated dictionary back to the file.

    Args:
        attribute_name (str): Name of the attribute to update
        value (Any): New value to set for the attribute

    Raises:
        FileNotFoundError: If attributes.json file does not exist
        json.JSONDecodeError: If attributes.json contains invalid JSON
    """
    try:
        # Read current attributes
        with open('local_data/attributes.json', 'r') as f:
            attributes = json.load(f)
        
        # Update attribute
        attributes[attribute_name] = value
        
        # Write back updated attributes
        with open('local_data/attributes.json', 'w') as f:
            json.dump(attributes, f)
            
        print(f"O- local attributes updated: {attributes}")
            
    except FileNotFoundError:
        print("X- attributes.json file not found")
        raise
    except json.JSONDecodeError:
        print("X- invalid JSON in attributes.json")
        raise

def get_pixel_coordinates(image_path: str) -> list[tuple[int, int]]:
    """Get coordinates of non-black pixels in an image.
    
    Opens an image file and returns a list of (x,y) coordinates for all pixels 
    that have any RGB value greater than 0.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        list[tuple[int, int]]: List of (x,y) coordinate tuples for non-black pixels
        
    Raises:
        FileNotFoundError: If image file does not exist
    """
    img = Image.open(image_path)
    img_array = numpy.array(img)
    height, width = img_array.shape[:2]
    
    coordinates = []
    for y in range(height):
        for x in range(width):
            if img_array[y, x].any() > 0:
                # Flip y coordinate since image origin is top-left
                rel_y = (width - 1) - y
                coordinates.append((x, rel_y))
    
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

def closest_color(target_rgb: tuple[int, int, int], color_dict: dict[int, tuple[int, int, int]]) -> int:
    """
    Finds the ID of the closest RGB color in color_dict to the target_rgb using Euclidean distance.

    Args:
        target_rgb: Tuple of (R, G, B) values to match against
        color_dict: Dictionary mapping IDs to (R, G, B) tuples
    
    Returns:
        The ID from color_dict whose RGB value is closest to target_rgb
    """
    def euclidean_distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors"""
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5

    return min(color_dict.items(), key=lambda x: euclidean_distance(target_rgb, x[1]))[0]

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
    1: (0, 0, 121), # average -100C
    2: (0, 35, 135), # average -90C
    3: (8, 43, 142), # average -80C
    4: (31, 66, 162), # average -70C
    5: (40, 75, 170), # average -60C
    6: (52, 92, 188), # average -50C
    7: (86, 137, 236), # average -40C
    8: (99, 155, 255), # average -30C
    9: (78, 146, 186), # average -20C
    10:(60, 134, 128), # average -10C
    # ---
    11:(55, 148, 110), # average +0C/32F
    # ---
    12:(105, 170, 45), # average +10C/50F
    13:(120, 210, 35), # average +20C/68F
    14:(203, 240, 50), # average +30C/86F
    15:(250, 240, 55), # average +40C/104F
    16:(233, 198, 54), # average +50C/122F
    17:(233, 130, 45), # average +60C/140F
    18:(236, 61, 23), # average +70C/158F
    19:(203, 44, 25), # average +80C/176F
    20:(237, 10, 10), # average +90C/194F
    21:(255, 0, 0), # average +100C/212F
}

TEMPERATURE_PALETTE = {
    'erase/none': 0,
    # ---
    'average -100C/-148F': 1,
    'average -90C/-130F': 2,
    'average -80C/-112F': 3,
    'average -70C/-94F': 4,
    'average -60C/-76F': 5,
    'average -50C/-58F': 6,
    'average -40C/-40F': 7,
    'average -30C/-22F': 8,
    'average -20C/+4F': 9,
    'average -10C/+14F': 10,
    'average +0C/+32F': 11,  
    'average +10C/+50F': 12,
    'average +20C/+68F': 13,
    'average +30C/+86F': 14,
    'average +40C/+104F': 15,
    'average +50C/+122F': 16,
    'average +60C/+140F': 17,
    'average +70C/+158F': 18,
    'average +80C/+176F': 19,
    'average +90C/+194F': 20,
    'average +100C/+212F': 21
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
    # ---
    4: "icons/info/str_progress_0",
    5: "icons/info/str_progress_1",
    6: "icons/info/str_progress_2",
    7: "icons/info/str_progress_3",
    8: "icons/info/str_progress_4",
    9: "icons/info/str_progress_5",
}

DECORATOR_ICON_ID_MAP = {
    0: "icons/decorators/axe",
    1: "icons/decorators/bow",
    2: "icons/decorators/circle",
    3: "icons/decorators/cube",
    4: "icons/decorators/flintlock",
    5: "icons/decorators/hammer",
    6: "icons/decorators/hexagon",
    7: "icons/decorators/lance",
    8: "icons/decorators/mace",
    9: "icons/decorators/musket",
    10: "icons/decorators/octagon",
    11: "icons/decorators/pentagon",
    12: "icons/decorators/shield",
    13: "icons/decorators/spear",
    14: "icons/decorators/sword",
    15: "icons/decorators/triangle",
    # additionals
    16: "icons/decorators/claymore",
    17: "icons/decorators/falchion",
    18: "icons/decorators/gladius",
    19: "icons/decorators/jian",
    20: "icons/decorators/longsword",
    21: "icons/decorators/shortsword"
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
    print("Utility functions and classes for map and nation management.\nAre you sure you ran the right file?")