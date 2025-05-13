from array import array
from functools import partial
import math
import random
import time
import arcade
import arcade.gui
import arcade.gui.widgets
import numpy as np
import nation_utils as nutil
from PIL import Image

import nation_utils as na

WIDTH, HEIGHT = 1920, 1080
SCREEN_SIZE = (WIDTH, HEIGHT)
RESIZED_SIZE = 1920, 1080

ICON_ID_MAP = {
    0:"icons/units/vessel_raft",
    1:"icons/units/vessel_cog",
    2:"icons/units/vessel_yawl",
    3:"icons/units/vessel_brig",
    4:"icons/units/vessel_corvette",
    5:"icons/units/vessel_frigate",
    6:"icons/units/vessel_cruiser",
    7:"icons/units/vessel_battleship",
    8:"icons/units/vessel_dreadnought",
    9:"icons/units/vessel_carrier",
    # -
    10:"icons/units/unit_artillery",
    11:"icons/units/unit_cavalry",
    12:"icons/units/unit_heavy_artillery",
    13:"icons/units/unit_heavy_cavalry",
    14:"icons/units/unit_heavy_infantry",
    15:"icons/units/unit_infantry",
    16:"icons/units/unit_ranged_cavalry",
    17:"icons/units/unit_ranged_infantry",
    18:"icons/units/unit_skirmishers",
    # -
    19:"icons/info/info_spikes",
    20:"icons/info/info_gate",
    21:"icons/info/info_wall",
    22:"icons/info/info_trench",
    23:"icons/info/info_bridge"
}

TILE_ID_MAP = {
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

QUALITY_COLOR_MAP = {
    1: (125,125,125),
    2: (150,150,150),
    3: (175,175,175),
    4: (200,200,200),
    5: (255,255,255)
}

# -

class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)
        self.camera                 = arcade.camera.Camera2D(); 
        self.camera.position        = (0,0)
        self.resized_size           = 1920, 1080
        self.camera_speed           = 0.0, 0.0
        self.zoomed_speed_mod_adder = 0.0
        self.zoomed_speed_mod       = 1.0
        self.zoom_speed             = 0.0
        self.last_pressed_screen    = None
        self.last_pressed_world     = None
        self.current_position_screen= None
        self.current_position_world = None
        self.selected_world_icon    = None
        self.selected_tile_id       = 0
        self.editing_mode           = False
        self.editing_mode_size      = 1
        self.rotating_the_icon      = False
        self.moving_the_icon        = False
        self.selected_icon_id       = None
        self.previous_angle         = 0
        self.drawing_line_start     = None
        self.drawing_line_end       = None

        self.terrain_scene          = arcade.Scene()
        self.info_scene             = arcade.Scene()

        self.terrain_scene.add_sprite_list("0")
        self.info_scene.add_sprite_list("0")
        self.info_scene_list = []

        self.terrain_layer = nutil.GridLayer((200,200))
        self.terrain_layer.grid[:] = np.zeros((200,200),dtype=np.uint8)
        self.icons = {
            'locations': [],
            'trenches': [],
            'bridges': [],
            'walls': []
        }

        self.ui = arcade.gui.UIManager()
        self.ui.enable()

        load_menu_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.load_menu_buttons = load_menu_anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="center", anchor_y="center")
        savefiles = nutil.get_all_files('battlemap_data')

        if savefiles:
            for i, savefile in enumerate(savefiles):
                save_file_button = arcade.gui.UIFlatButton(width=300,height=64,text=f"{savefile}")

                self.load_menu_buttons.add(save_file_button)

                @save_file_button.event
                def on_click(event: arcade.gui.UIOnClickEvent, savename=savefile, index=i):
                    self.on_clicked_load(savename)
                    self.load_menu_buttons.clear()
        else:
            self.setup()

        center_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.popupmenu_buttons = center_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=4),
            anchor_x="center",
            anchor_y="center"
        )
        self.popupmenu_buttons.visible = False

        save_button = arcade.gui.UIFlatButton(width=200,height=64,text="Save map")
        @save_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.on_clicked_save()
        self.popupmenu_buttons.add(save_button)

        self.icon_data_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.icon_description = self.icon_data_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False,
                space_between=2
            ),
            anchor_x="center",
            anchor_y="bottom"
        )

        self.mouse_click_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.mouse_click_anchor.visible = False
        self.menu_options = self.mouse_click_anchor.add(
            arcade.gui.UIGridLayout(
                column_count=10,
                row_count=10,
                vertical_spacing=1,
                horizontal_spacing=1
                ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="center"
        )

        icon_names = [
            "raft", "cog", "yawl", "brig", "corvette",
            "frigate", "cruiser", "battleship", "dreadnought", "carrier",
            "artillery", "cavarly", "heavy artillery", "heavy cavalry", "heavy infantry",
            "infantry", "ranged cavalry", "ranged infantry", "skirmishers", "spikes",
            "gate", "wall", "trench", "bridge"
        ]

        self.buttons = []

        for idx, name in enumerate(icon_names):
            icon_texture = arcade.load_texture(f"{ICON_ID_MAP.get(idx)}.png")
            button = arcade.gui.UIFlatButton(text="", width=64, height=64)
            button.add(
                child=arcade.gui.UIImage(texture=icon_texture, width=64, height=64),
                anchor_x="center",
                anchor_y="center"
            )
            self.menu_options.add(button, idx % 10, idx // 10)
            self.buttons.append(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, name=name):
                self.selected_icon_id = idx
                self.on_notification_toast(f"Selected {name}")

        bottom_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        biome_palette_buttons = bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        biome_palette_buttons.visible = False

        anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        layer_buttons = anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=4),
            anchor_x="right",
            anchor_y="top"
        )
        self.toasts = anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="left", anchor_y="top")
        self.toasts.with_padding(all=10)

        geographic_palette_icon = arcade.load_texture("icons/geo_palette_icon.png")
        biome_palette_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        biome_palette_toggle.add(
            child=arcade.gui.UIImage(
                texture=geographic_palette_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        @biome_palette_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            biome_palette_buttons.visible = not biome_palette_buttons.visible

        layer_buttons.add(biome_palette_toggle)

        self.pallete = {
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

        for i, (biome_name, biome_id) in enumerate(self.pallete.items()):
            rgb = TILE_ID_MAP.get(biome_id,0)
            rgba= rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32,width=32,style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3])),
                "hover" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5,rgba[1]+5,rgba[2]+5,rgba[3])),
                "press" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3]-50))
                })
            biome_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=biome_id, name=biome_name):
                self.selected_tile_id = idx
                self.on_notification_toast(f"Selected {name}")

    def on_notification_toast(self, message:str="", warn:bool=False, error:bool=False, success:bool=False):
        toast = nutil.Toast(message, duration=2)

        toast.update_font(
            font_color=arcade.uicolor.BLACK,
            font_size=12,
            bold=True
        )

        toast.with_background(color=arcade.uicolor.BLUE_PETER_RIVER)
        if success == True:
            toast.with_background(color=arcade.uicolor.GREEN_EMERALD)
        if warn == True:
            toast.with_background(color=arcade.uicolor.YELLOW_ORANGE)
        if error == True:
            toast.with_background(color=arcade.uicolor.RED_POMEGRANATE)

        toast.with_padding(all=10)

        self.toasts.add(toast)

    def find_element_near(self, x, y, elements, position_extractor=lambda elem: elem.position, radius=5):
        if not elements:
            return None
        
        # Calculate distance to point x, y
        def distance(elem):
            pos = position_extractor(elem)
            return math.sqrt((pos[0] - x) ** 2 + (pos[1] - y) ** 2)
        
        # Filter elements within radius
        elements_within_radius = [elem for elem in elements if distance(elem) <= radius]
        
        if not elements_within_radius:
            return None
            
        # Return closest element
        return min(elements_within_radius, key=distance)
    
    def find_line_near(self, x, y, radius=5):
        """Finds closest line within given radius."""
        if not self.icons['lines']:
            return None
        
        lines_within_radius = [
            line for line in self.icons['lines']
            if math.sqrt((line[0][0] - x) ** 2 + (line[0][1] - y) ** 2) <= radius
        ]

        if not lines_within_radius:
            return None
        
        return min(
            lines_within_radius,
            key=lambda line: math.sqrt((line[0][0] - x) ** 2 + (line[0][1] - y) ** 2)
        )

    def on_clicked_load(self, filename: str):
        loaded_data = np.load(filename,allow_pickle=True)
        print(f"loading {filename}")
        loaded_ground_data = loaded_data['battlemap_a']
        self.terrain_layer.grid[:]= loaded_ground_data

        icons_array = loaded_data['battlemap_c']
        self.icons = icons_array.item()

        self.setup()

    def on_clicked_save(self):
        try:
            self.on_notification_toast("Trying to save map ...")
            ground_grid = np.empty((200,200),dtype=np.uint8)

            def extract_id(cell):
                return cell.id_ if isinstance(cell, nutil.Tile) else cell
            
            extract_attribute = np.vectorize(extract_id, otypes=[np.uint8])
            ground_grid = extract_attribute(self.terrain_layer.grid)

            np.savez_compressed(f"battlemap_data/battlemap_{time.localtime().tm_year}_{time.localtime().tm_mon}_{time.localtime().tm_mday}_{time.localtime().tm_hour}_{time.localtime().tm_min}_{time.localtime().tm_sec}.npz",
                                battlemap_a=ground_grid,
                                battlemap_c=np.array(self.icons)
                                )
            self.on_notification_toast("Saved map ...",success=True)
        except Exception as e: 
            self.on_notification_toast("Failed to save map ... "+str(e),error=True)

    def setup(self):
        print("?- Loading map")
        for x in range(200):
            if x % 50 == 0:
                print(f"O- Progress: {x} rows loaded...")
            for y in range(200):
                tile_id_value = self.terrain_layer.grid[x][y]
                pixel_rgb = TILE_ID_MAP.get(tile_id_value,(0,0,127))
                world_x = (x * 20)
                world_y = (y * 20)

                tile = nutil.Tile(20, 20, world_x, world_y, pixel_rgb+(255,), tile_id_value)

                self.terrain_scene.add_sprite("0",tile)
            
                self.terrain_layer.grid[x][y] = tile

        print("?- Loading icons [1/1] ---")
        for icon in self.icons['locations']:
            icon_path = str(ICON_ID_MAP.get(icon['id']))+".png"
            icon_object = nutil.Icon(icon_path,1,
                           icon['x'],
                           icon['y'],
                           0.0,
                           icon['id'],
                           icon['angle_rot'],
                           icon['unique_id'],
                           icon['country_id'],
                           icon['quality']
                        )
            icon_object.angle = icon['angle_rot']
            self.info_scene.add_sprite("0",icon_object)
            self.info_scene_list.append(icon_object)

    def on_resize(self, width, height):
        self.resized_size = width, height
        print(f"resized {width} and {height}")
        return super().on_resize(width, height)

    def on_update(self, dt):
        self.camera.position += (self.camera_speed[0]*self.zoomed_speed_mod, self.camera_speed[1]*self.zoomed_speed_mod)

        self.camera.zoom += self.zoom_speed*self.camera.zoom

        self.zoomed_speed_mod = max(self.zoomed_speed_mod+self.zoomed_speed_mod_adder, 0.01)
        self.zoomed_speed_mod = min(self.zoomed_speed_mod, 2.0)

        for icon in self.info_scene_list:
            icon.color = QUALITY_COLOR_MAP.get(icon.quality, (255,0,0,255))

    def on_draw(self):
        self.camera.use() 
        self.clear() 
        self.terrain_scene.draw(pixelated=True)

        for start, end in self.icons['trenches']:
            arcade.draw_line(start[0],start[1],end[0],end[1],(125,84,68,255),line_width=16)
        for start, end in self.icons['walls']:
            arcade.draw_line(start[0],start[1],end[0],end[1],(150,150,150,255),line_width=32)
        for start, end in self.icons['bridges']:
            arcade.draw_line(start[0],start[1],end[0],end[1],(100,100,100,255),line_width=16)

        if self.drawing_line_start and self.drawing_line_end is None:
            arcade.draw_line(self.drawing_line_start[0],self.drawing_line_start[1],self.current_position_world[0],self.current_position_world[1],(255,0,0,255),line_width=2)

        self.info_scene.draw(pixelated=True)
        
        if self.selected_world_icon:
            if self.rotating_the_icon:
                arcade.draw_circle_outline(self.selected_world_icon.position[0],self.selected_world_icon.position[1],max(32-(self.camera.zoom*3),4),(255,255,255,255),1,0,12)
            elif self.moving_the_icon:
                arcade.draw_circle_outline(self.selected_world_icon.position[0],self.selected_world_icon.position[1],max(32-(self.camera.zoom*3),4),(255,255,255,255),1,0,4)
            else:
                arcade.draw_circle_outline(self.selected_world_icon.position[0],self.selected_world_icon.position[1],max(32-(self.camera.zoom*3),4),(255,255,255,255),1,0,6)

        if self.current_position_world:
            if self.editing_mode == True:
                crosshair_size = (self.editing_mode_size*2)
                crosshair_sprite = arcade.Sprite("icons/crosshair.png",(crosshair_size,crosshair_size),self.current_position_world[0],self.current_position_world[1],0)
                arcade.draw_sprite(crosshair_sprite,pixelated=True)
                arcade.draw_lbwh_rectangle_outline(round(self.current_position_world[0]/20)*20-10,round(self.current_position_world[1]/20)*20-10,20,20,(255,255,255,255),1)
            else:
                arcade.draw_lbwh_rectangle_outline(round(self.current_position_world[0]/20)*20-10,round(self.current_position_world[1]/20)*20-10,20,20,(255,255,255,255),1)

        self.ui.draw()

    def on_key_press(self, symbol, modifier):
        if symbol   == arcade.key.W or symbol == arcade.key.UP:
            self.camera_speed = (self.camera_speed[0], 10.0)
        elif symbol == arcade.key.A or symbol == arcade.key.LEFT:
            self.camera_speed = (-10.0, self.camera_speed[1])
        elif symbol == arcade.key.S or symbol == arcade.key.DOWN:
            self.camera_speed = (self.camera_speed[0], -10.0)
        elif symbol == arcade.key.D or symbol == arcade.key.RIGHT:
            self.camera_speed = (10.0, self.camera_speed[1])

        if symbol   == arcade.key.KEY_0:
            self.zoomed_speed_mod_adder = 0.01
        if symbol   == arcade.key.KEY_9:
            self.zoomed_speed_mod_adder = -0.01

        if symbol   == arcade.key.F:
            self.set_fullscreen(not self.fullscreen)
        if symbol   == arcade.key.T:
            self.on_notification_toast("Test toast.")
        if symbol   == arcade.key.O:
            self.editing_mode = not self.editing_mode
        if symbol   == arcade.key.M:
            if self.rotating_the_icon == True:
                self.rotating_the_icon = False
                self.moving_the_icon = True
            else:
                self.moving_the_icon = not self.moving_the_icon
        if symbol   == arcade.key.R:
            if self.moving_the_icon == True:
                self.moving_the_icon = False
                self.rotating_the_icon = True
            else:
                self.rotating_the_icon = not self.rotating_the_icon
        if symbol   == arcade.key.E:
            self.mouse_click_anchor.visible = not self.mouse_click_anchor.visible
        if symbol   == arcade.key.ESCAPE:
            self.popupmenu_buttons.visible = not self.popupmenu_buttons.visible

        if symbol == arcade.key.MINUS or symbol == arcade.key.NUM_SUBTRACT:
            if self.camera.zoom >= 0.1 and self.camera.zoom <= 0.125:
                pass
            else:
                self.zoom_speed = -0.01
        if symbol == arcade.key.EQUAL or symbol == arcade.key.NUM_ADD:
            self.zoom_speed = 0.01

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.W or symbol == arcade.key.S or symbol == arcade.key.UP or symbol == arcade.key.DOWN:
            self.camera_speed = (self.camera_speed[0], 0.0)
        elif symbol == arcade.key.A or symbol == arcade.key.D or symbol == arcade.key.LEFT or symbol == arcade.key.RIGHT:
            self.camera_speed = (0.0, self.camera_speed[1])

        if symbol == arcade.key.EQUAL or symbol == arcade.key.NUM_ADD:
            self.zoom_speed = 0.0
        if symbol == arcade.key.MINUS or symbol == arcade.key.NUM_SUBTRACT:
            self.zoom_speed = 0.0

        if symbol == arcade.key.KEY_0 or symbol == arcade.key.KEY_9:
            self.zoomed_speed_mod_adder = 0

    def on_mouse_press(self, x, y, button, modifiers):
        if button is arcade.MOUSE_BUTTON_RIGHT:
            if self.selected_icon_id or self.selected_icon_id == 0:
                self.selected_icon_id = None
                self.on_notification_toast("Deselected icon id.",warn=True)
        if button is arcade.MOUSE_BUTTON_LEFT:
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
            world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x) 
            world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
            self.last_pressed_world = (world_x, world_y)
            tile_x = round(world_x / 20)
            tile_y = round(world_y / 20)

            if self.editing_mode == True:
                list_of_tiles = np.zeros((self.editing_mode_size,self.editing_mode_size), dtype=object)
                list_of_tile_positions = []

                half_size = self.editing_mode_size // 2
                radius = half_size

                for x_offset in range(self.editing_mode_size):
                    for y_offset in range(self.editing_mode_size):
                        x_ = tile_x + (x_offset - half_size)
                        y_ = tile_y + (y_offset - half_size)

                        distance = ((x_offset - half_size) + 0.5) ** 2 + ((y_offset - half_size) + 0.5) ** 2

                        if not self.editing_mode_size == 1:
                            if distance <= (radius + 0.5) ** 2:
                                list_of_tiles[x_offset, y_offset] = self.terrain_layer.__getitem__((x_,y_))
                                list_of_tile_positions.append((x_,y_))
                            else:
                                list_of_tiles[x_offset, y_offset] = None 
                        else:
                            list_of_tiles[x_offset, y_offset] = self.terrain_layer.__getitem__((tile_x,tile_y))
                            list_of_tile_positions.append((tile_x,tile_y))

                for x_ in range(self.editing_mode_size):
                    for y_ in range(self.editing_mode_size):
                        if not list_of_tiles[x_][y_] is None:
                            pixel_rgba = TILE_ID_MAP.get(self.selected_tile_id,(0,0,0)) + (255,)
                            list_of_tiles[x_][y_].color = pixel_rgba
                            list_of_tiles[x_][y_].id_ = self.selected_tile_id
                        else:
                            print(f"no tiles returned to selection ...")
            else:
                if self.selected_icon_id or self.selected_icon_id == 0:
                    if self.selected_icon_id == 21:
                        if self.drawing_line_start is None:
                            self.drawing_line_start = (world_x,world_y)
                        else:
                            self.drawing_line_end = (world_x,world_y)
                            self.icons['walls'].append((self.drawing_line_start,self.drawing_line_end))
                            self.drawing_line_start = None
                            self.drawing_line_end = None
                    elif self.selected_icon_id == 22:
                        if self.drawing_line_start is None:
                            self.drawing_line_start = (world_x,world_y)
                        else:
                            self.drawing_line_end = (world_x,world_y)
                            self.icons['trenches'].append((self.drawing_line_start,self.drawing_line_end))
                            self.drawing_line_start = None
                            self.drawing_line_end = None     
                    elif self.selected_icon_id == 23:
                        if self.drawing_line_start is None:
                            self.drawing_line_start = (world_x,world_y)
                        else:
                            self.drawing_line_end = (world_x,world_y)
                            self.icons['bridges'].append((self.drawing_line_start,self.drawing_line_end))
                            self.drawing_line_start = None
                            self.drawing_line_end = None
                    else:
                        icon_path = str(ICON_ID_MAP.get(self.selected_icon_id))+".png"
                        generated_unique_id:int = random.randrange(1000,9999)
                        icon = nutil.Icon(icon_path,1,world_x,world_y,0.0,self.selected_icon_id,0,generated_unique_id,0,1)
                        self.info_scene.add_sprite("0",icon)
                        self.info_scene_list.append(icon)
                        self.icons["locations"].append({
                            "id": self.selected_icon_id,
                            "x": world_x,
                            "y": world_y,
                            "angle_rot": 0,
                            "unique_id": generated_unique_id,
                            "country_id": 0,
                            "quality": 1
                        })

                nearby_icon = self.find_element_near(world_x, world_y, elements=self.info_scene_list, radius=24)
                if nearby_icon:
                    self.selected_world_icon = nearby_icon
                    nearby_icon_dict = None
                    nearby_icon_dict_index = 0
                    for icon in self.icons['locations']:
                        if icon['unique_id'] == nearby_icon.unique_id:
                            nearby_icon_dict = icon
                            self.on_notification_toast(f"Found icon;{nearby_icon_dict_index};quality={nearby_icon_dict['quality']};")
                            break
                        else:
                            nearby_icon_dict_index+=1
                    self.icon_description.clear()
                    move_button_icon            = arcade.load_texture("icons/move_icon.png")
                    remove_button_icon          = arcade.load_texture("icons/remove_icon.png")
                    rotate_button_icon          = arcade.load_texture("icons/rotate_icon.png")
                    rotate_reset_button_icon    = arcade.load_texture("icons/rotate_reset_icon.png")
                    up_button_icon              = arcade.load_texture("icons/up_icon.png")
                    down_button_icon            = arcade.load_texture("icons/down_icon.png")
                    move_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    move_button.add(
                        child=arcade.gui.UIImage(
                            texture=move_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )
                    
                    remove_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    remove_button.add(
                        child=arcade.gui.UIImage(
                            texture=remove_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )
                    
                    rotate_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    rotate_button.add(
                        child=arcade.gui.UIImage(
                            texture=rotate_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )
                    
                    rotate_reset_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    rotate_reset_button.add(
                        child=arcade.gui.UIImage(
                            texture=rotate_reset_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )
                    
                    upgrade_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    upgrade_button.add(
                        child=arcade.gui.UIImage(
                            texture=up_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    downgrade_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    downgrade_button.add(
                        child=arcade.gui.UIImage(
                            texture=down_button_icon,
                            width =64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    @downgrade_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        if nearby_icon.quality > 1:
                            nearby_icon.quality -= 1
                            nearby_icon_dict['quality'] -= 1
                            self.on_notification_toast("downgraded icon")
                        else:
                            self.on_notification_toast(f"icon is already at {nearby_icon.quality} !",error=True)

                    @upgrade_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        if nearby_icon.quality < 5:
                            nearby_icon.quality += 1
                            nearby_icon_dict['quality'] += 1
                            self.on_notification_toast("upgraded icon")
                        else:
                            self.on_notification_toast(f"icon is already at {nearby_icon.quality} !",error=True)

                    @rotate_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        self.rotating_the_icon = not self.rotating_the_icon

                    @rotate_reset_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        self.selected_world_icon.angle = 0
                        nearby_icon_dict['angle_rot'] = 0

                    @move_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        self.moving_the_icon = not self.moving_the_icon

                    @remove_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        self.info_scene_list.remove(self.selected_world_icon)
                        abc = self.info_scene.get_sprite_list("0")
                        abc.remove(self.selected_world_icon)
                        self.icons['locations'].pop(nearby_icon_dict_index)
                        self.icon_description.clear()
                        self.on_notification_toast("Successfully removed icon.")

                        self.selected_world_icon = None

                    self.icon_description.add(move_button)
                    self.icon_description.add(remove_button)
                    self.icon_description.add(rotate_button)
                    self.icon_description.add(rotate_reset_button)
                    self.icon_description.add(upgrade_button)
                    self.icon_description.add(downgrade_button)
                else:
                    self.selected_world_icon = None
                    self.icon_description.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons is arcade.MOUSE_BUTTON_RIGHT:
            self.camera.position -= (dx / self.camera.zoom, dy / self.camera.zoom)
        if buttons is arcade.MOUSE_BUTTON_LEFT:
            camera_x, camera_y = self.camera.position
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
            # Conversion from screen coordinates to world coordinates
            world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + camera_x) 
            world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + camera_y)
            # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset
            tile_x = round(world_x / 20)
            tile_y = round(world_y / 20)

            self.current_position_world = (world_x, world_y)
            if self.rotating_the_icon:
                try:
                    current_angle = math.atan2(world_x - self.selected_world_icon.position[0], world_y - self.selected_world_icon.position[1])
                    delta_angle = (((current_angle - self.previous_angle + math.pi) % (2 * math.pi)) - math.pi) * (180/math.pi)
                    self.selected_world_icon.angle += delta_angle
                    self.previous_angle = current_angle

                    index = 0
                    for icon in self.icons['locations']:
                        if icon['x'] == self.selected_world_icon.position[0] and icon['y'] == self.selected_world_icon.position[1]:
                            icon['angle_rot'] += delta_angle
                        else:
                            index+=1
                except:
                    self.on_notification_toast("Couldn't rotate [cannot find icon] ...", warn=True)

            if self.editing_mode == True:
                list_of_tiles = np.zeros((self.editing_mode_size,self.editing_mode_size), dtype=object)
                list_of_tile_positions = []

                half_size = self.editing_mode_size // 2
                radius = half_size

                for x_offset in range(self.editing_mode_size):
                    for y_offset in range(self.editing_mode_size):
                        x_ = tile_x + (x_offset - half_size)
                        y_ = tile_y + (y_offset - half_size)

                        distance = ((x_offset - half_size) + 0.5) ** 2 + ((y_offset - half_size) + 0.5) ** 2

                        if not self.editing_mode_size == 1:
                            if distance <= (radius + 0.5) ** 2:
                                list_of_tiles[x_offset, y_offset] = self.terrain_layer.__getitem__((x_,y_))
                                list_of_tile_positions.append((x_,y_))
                            else:
                                list_of_tiles[x_offset, y_offset] = None 
                        else:
                            list_of_tiles[x_offset, y_offset] = self.terrain_layer.__getitem__((tile_x,tile_y))
                            list_of_tile_positions.append((tile_x,tile_y))

                for x_ in range(self.editing_mode_size):
                    for y_ in range(self.editing_mode_size):
                        if not list_of_tiles[x_][y_] is None:
                            pixel_rgba = TILE_ID_MAP.get(self.selected_tile_id,(0,0,0)) + (255,)
                            list_of_tiles[x_][y_].color = pixel_rgba
                            list_of_tiles[x_][y_].id_ = self.selected_tile_id
                        else:
                            print(f"no tiles returned to selection ...")
            else:
                if self.moving_the_icon == True:
                    index = 0
                    for icon in self.icons['locations']:
                        if icon['x'] == self.selected_world_icon.position[0] and icon['y'] == self.selected_world_icon.position[1]:
                            icon['x'] = world_x
                            icon['y'] = world_y
                        else:
                            index+=1
                    self.selected_world_icon.position = (world_x,world_y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button is arcade.MOUSE_BUTTON_LEFT:
            self.last_pressed_world = None
            self.last_pressed_screen = None
            self.previous_angle = 0

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.editing_mode == False:
            if self.camera.zoom >= 0.1 and self.camera.zoom <= 0.125:
                if scroll_y == 1.0:
                    self.camera.zoom += 0.1*self.camera.zoom
                    self.zoomed_speed_mod -= 0.01
            else:
                if scroll_y == 1.0:
                    self.camera.zoom += 0.1*self.camera.zoom
                    self.zoomed_speed_mod -= 0.01

                if scroll_y == -1.0:
                    self.camera.zoom -= 0.1*self.camera.zoom
                    self.zoomed_speed_mod += 0.01
        else:
            if self.editing_mode_size == 1:
                if scroll_y == 1.0:
                    self.editing_mode_size += 1
            else:
                self.editing_mode_size += int(scroll_y)
        
    def on_mouse_motion(self, x, y, dx, dy):
        diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
        world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x) 
        world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
        self.current_position_world = (world_x, world_y)


def main():
    print("GAME INITIALIZING ...")
    game = Game(WIDTH, HEIGHT, "NATIONWIDER-BATTLEMAP")
    arcade.run()


if __name__ == "__main__":
    main()