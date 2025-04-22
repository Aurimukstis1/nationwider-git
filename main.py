import itertools
import arcade
import arcade.gui
import arcade.gui.widgets
import math
import numpy as np
import random
import nation_utils as na
import time
import chunk_gpu as cgpu
from PIL import Image
# display settings; ts pmo fr rn 
WIDTH, HEIGHT = 1920, 1080
SCREEN_SIZE = (WIDTH, HEIGHT)

if __name__ == "__main__":
    print("?- checking for imagefiles ...")
    try:
        geography_layer_button_icon = arcade.load_texture("icons/geo_map_icon.png")
        geography_palette_button_icon = arcade.load_texture("icons/geo_palette_icon.png")

        political_layer_button_icon = arcade.load_texture("icons/pol_map_icon.png")
        political_palette_button_icon = arcade.load_texture("icons/pol_palette_icon.png")

        information_layer_button_icon = arcade.load_texture("icons/inf_map_icon.png")

        climate_layer_button_icon = arcade.load_texture("icons/climate_layer_button_icon.png")
        climate_palette_button_icon = arcade.load_texture("icons/climate_palette_button_icon.png")

        brush_deselect_icon_texture = arcade.load_texture('icons/brush_deselect_icon.png')
        brush_random_icon_texture = arcade.load_texture('icons/brush_random_icon.png')

        spring_toggle_button_icon = arcade.load_texture('icons/spring_layer_button_icon.png')
        summer_toggle_button_icon = arcade.load_texture('icons/summer_layer_button_icon.png')
        autumn_toggle_button_icon = arcade.load_texture('icons/autumn_layer_button_icon.png')
        winter_toggle_button_icon = arcade.load_texture('icons/winter_layer_button_icon.png')

        temperature_palette_button_icon = arcade.load_texture('icons/temperature_palette_button_icon.png')
        print("O- imagefiles found and loaded")
    except:
        print(f"X- {Exception}/imagefiles not found")

# ---

class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)
        self.ui = arcade.gui.UIManager()
        self.ui.enable()
        self.camera                 = arcade.camera.Camera2D(); 
        self.camera.position        = (0,0)
        self.camera_speed           = 0.0, 0.0
        self.zoomed_speed_mod_adder = 0.0
        self.zoomed_speed_mod       = 1.0
        self.zoom_speed             = 0.0
        self.resized_size           = 1920, 1080

        self.terrain_scene          = None
        self.last_pressed_screen    = None
        self.last_pressed_world     = None
        self.current_position_screen= None
        self.current_position_world = None
        self.selection_rectangle_size=1
        self.last_interacted_tile   = None
        self.political_background   = True
        self.selected_lower_id      = 0
        self.selected_country_id    = 0
        self.editing_mode           = False
        self.editing_mode_size      = 4
        self.selected_brush         = None

        self.previous_angle         = 0
        self.selected_climate_id    = None

        self.drawing_line_start     = None
        self.drawing_line_end       = None

        self.grid_assistance        = False

        self.biome_visibility       = True
        self.country_visibility     = True
        self.climate_visibility     = False

        self.selected_layer         = None

        self.has_map_been_loaded    = False

        self.political_layer        = na.GridLayer((600,300))
        self.upper_terrain_layer    = na.GridLayer((600,300))
        self.lower_terrain_layer    = na.GridLayer((12000,6000))

        self.s_political_layer      = na.GridLayer((600,300))
        self.s_upper_terrain_layer  = na.GridLayer((600,300))
        self.s_lower_terrain_layer  = na.GridLayer((12000,6000))

        self.north_climate_layer    = na.GridLayer((600,300))
        self.south_climate_layer    = na.GridLayer((600,300))

        self.north_temperature_layer_q1 = na.GridLayer((600,300))
        self.south_temperature_layer_q1 = na.GridLayer((600,300))

        self.north_temperature_layer_q2 = na.GridLayer((600,300))
        self.south_temperature_layer_q2 = na.GridLayer((600,300))

        self.north_temperature_layer_q3 = na.GridLayer((600,300))
        self.south_temperature_layer_q3 = na.GridLayer((600,300))

        self.north_temperature_layer_q4 = na.GridLayer((600,300))
        self.south_temperature_layer_q4 = na.GridLayer((600,300))

        self.q1_temperature_visibility = False
        self.q2_temperature_visibility = False
        self.q3_temperature_visibility = False
        self.q4_temperature_visibility = False

        self.selected_icon_type     = None
        self.selected_icon_id       = None
        self.selected_world_icon    = None
        self.selected_temperature_id= 0
        self.moving_the_icon        = False
        self.rotating_the_icon      = False
        self.selected_line_tool     = False
        self.last_pressed_line_point= None
        self.current_shape          = []
        self.final_shape            = []
        self.military_icons = {
            'locations': []
        }
        self.military_lines = {
            'locations': []
        }
        self.civilian_icons = {
            'locations': []
        }
        self.civilian_lines = {
            'locations': []
        }

        self.misc_lines_1 = {'locations': []}
        self.misc_lines_2 = {'locations': []}
        self.misc_lines_3 = {'locations': []}
        self.misc_lines_4 = {'locations': []}
        self.misc_lines_1_visibility = True
        self.misc_lines_2_visibility = True
        self.misc_lines_3_visibility = True
        self.misc_lines_4_visibility = True

        self.shape_layers = [self.military_lines,self.civilian_lines,self.misc_lines_1,self.misc_lines_2,self.misc_lines_3,self.misc_lines_4]
        self.civilian_information_layer = arcade.Scene()
        self.military_information_layer = arcade.Scene()
        self.civilian_information_layer.add_sprite_list("0")
        self.military_information_layer.add_sprite_list("0")
        self.information_icons_list = []

        self.bottom_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.right_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.center_anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        self.icon_box = self.center_anchor.add(arcade.gui.UIBoxLayout(space_between=8, vertical=False), anchor_x="center", anchor_y="center")
        self.icon_civilian_grid = self.icon_box.add(
            arcade.gui.UIGridLayout(
                column_count=5,
                row_count=5,
                vertical_spacing=4,
                horizontal_spacing=4
                ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(20,20,20,255)),
            anchor_x="center",
            anchor_y="center"
        )
        self.icon_military_grid = self.icon_box.add(
            arcade.gui.UIGridLayout(
                column_count=5,
                row_count=5,
                vertical_spacing=4,
                horizontal_spacing=4
                ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(20,20,20,255)),
            anchor_x="center",
            anchor_y="center"
        )
        self.icon_box.visible = False

        self.selected_icon_edit_box = self.bottom_anchor.add(arcade.gui.UIBoxLayout(space_between=0, vertical=False), anchor_x="center", anchor_y="bottom")

        self.keybinds_box = self.center_anchor.add(arcade.gui.UIBoxLayout(space_between=0), anchor_x="center", anchor_y="center")
        self.is_keybind_box_disabled = False

        self.load_menu_buttons = self.center_anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="center", anchor_y="center")
        savefiles = na.get_all_files('map_data')

        attributes_data = na.get_attributes()
        self.is_keybind_box_disabled = attributes_data['keybinds_disable']

        if savefiles:
            for i, savefile in enumerate(savefiles):
                save_file_button = arcade.gui.UIFlatButton(width=300,height=64,text=f"{savefile}")

                self.load_menu_buttons.add(save_file_button)

                @save_file_button.event
                def on_click(event: arcade.gui.UIOnClickEvent, savename=savefile, index=i):
                    self.on_clicked_load(savename)
                    self.load_menu_buttons.clear()
        else:
            print("I- NO MAPS WERE FOUND / LOADING DEFAULT ...")
            self.on_clicked_load('local_data/default_mapdata.npz')

        self.toasts = self.center_anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="left", anchor_y="top")
        self.toasts.with_padding(all=10)
        self.on_notification_toast(f"toast system initialized", success=True)

        self.custom_brushes = self.icon_box.add(
            arcade.gui.UIGridLayout(
                column_count=10,
                row_count=10,
                vertical_spacing=2,
                horizontal_spacing=2
                ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(20,20,20,255)),
            anchor_x="center",
            anchor_y="center"
        )
        self.default_brushes = self.icon_box.add(arcade.gui.UIBoxLayout(space_between=2, vertical=True).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(20,20,20,255)), anchor_x="center", anchor_y="center")

        brush_deselect_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
        brush_deselect_button.add(
            child=arcade.gui.UIImage(texture=brush_deselect_icon_texture, width=48, height=48),
            anchor_x="center",
            anchor_y="center"
        )
        @brush_deselect_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_brush = None
            self.on_notification_toast(f"deselected brush")
        self.default_brushes.add(brush_deselect_button)

        brush_random_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
        brush_random_button.add(
            child=arcade.gui.UIImage(texture=brush_random_icon_texture, width=48, height=48),
            anchor_x="center",
            anchor_y="center"
        )
        @brush_random_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_brush = 1
            self.on_notification_toast(f"selected procedural brush")
        self.default_brushes.add(brush_random_button)

        line_tool_select_button = arcade.gui.UIFlatButton(text="line", width=64, height=64)
        @line_tool_select_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_line_tool = True
            self.on_notification_toast("selected line tool")
        self.default_brushes.add(line_tool_select_button)

        line_tool_deselect_button = arcade.gui.UIFlatButton(text="no line", width=64, height=64)
        @line_tool_deselect_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_line_tool = None
            self.on_notification_toast("deselected line tool")
        self.default_brushes.add(line_tool_deselect_button)

        civilian_icon_names = [
            "village", "town", "city", "metro"
        ]

        military_icon_names = [
            "outpost", "keep", "fortress", "bastion", "raft",
            "cog", "yawl", "brig", "corvette", "frigate",
            "cruiser", "battleship", "dreadnought", "carrier", "artillery",
            "cavarly", "heavy artillery", "heavy cavalry", "heavy infantry", "infantry",
            "ranged cavalry", "ranged infantry", "skirmishers"
        ]

        for idx, name in enumerate(civilian_icon_names):
            icon_texture = arcade.load_texture(f"{na.CIVILIAN_ICON_ID_MAP.get(idx)}.png")
            button = arcade.gui.UIFlatButton(text="", width=64, height=64)
            button.add(
                child=arcade.gui.UIImage(texture=icon_texture, width=48, height=48),
                anchor_x="center",
                anchor_y="center"
            )
            self.icon_civilian_grid.add(button, idx % 5, idx // 5)
            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, name=name):
                self.selected_icon_id = idx
                self.selected_icon_type='civilian'
                self.on_notification_toast(f"Selected {idx} {name}")

        for idx, name in enumerate(military_icon_names):
            icon_texture = arcade.load_texture(f"{na.MILITARY_ICON_ID_MAP.get(idx)}.png")
            button = arcade.gui.UIFlatButton(text="", width=64, height=64)
            button.add(
                child=arcade.gui.UIImage(texture=icon_texture, width=48, height=48),
                anchor_x="center",
                anchor_y="center"
            )
            self.icon_military_grid.add(button, idx % 5, idx // 5)
            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, name=name):
                self.selected_icon_id = idx
                self.selected_icon_type='military'
                self.on_notification_toast(f"Selected {idx} {name}")

        layers_box = self.right_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=8),
            anchor_x="right",
            anchor_y="top"
        )
        layer_toggle_buttons = layers_box.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1)
        )
        palette_toggle_buttons = layers_box.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1)
        )

        biome_palette_buttons = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        biome_palette_buttons.visible = False
        country_palette_buttons = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        country_palette_buttons.visible = False
        climate_palette_buttons = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        climate_palette_buttons.visible = False
        temperature_palette_buttons = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        temperature_palette_buttons.visible = False

        self.escape_buttons = self.center_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=4),
            anchor_x="center",
            anchor_y="center"
        )
        self.escape_buttons.visible = False
        save_button = arcade.gui.UIFlatButton(width=200,height=64,text="Save map")
        @save_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.on_clicked_save()
        self.escape_buttons.add(save_button)

        for i, (biome_name, biome_id) in enumerate(na.BIOME_PALETTE.items()):
            rgb = na.TILE_ID_MAP.get(biome_id,0)
            rgba= rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32,width=32,style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3])),
                "hover" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5,rgba[1]+5,rgba[2]+5,rgba[3])),
                "press" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3]-50))
                })
            biome_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=biome_id, name=biome_name):
                self.selected_lower_id = idx
                self.on_notification_toast(f"Selected {name}")

        for i, (country_owner, country_id) in enumerate(na.COUNTRY_PALETTE.items()):
            rgb = na.POLITICAL_ID_MAP.get(country_id,0)
            rgba= rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32,width=32,style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3])),
                "hover" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5,rgba[1]+5,rgba[2]+5,rgba[3])),
                "press" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3]-50))
                })
            country_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=country_id, name=country_owner):
                self.selected_country_id = idx
                self.on_notification_toast(f"Selected {name}")

        for i, (climate_name, climate_id) in enumerate(na.CLIMATE_PALETTE.items()):
            rgb = na.CLIMATE_ID_MAP.get(climate_id,0)
            rgba= rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32,width=32,style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3])),
                "hover" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5,rgba[1]+5,rgba[2]+5,rgba[3])),
                "press" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3]-50))
                })
            climate_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=climate_id, name=climate_name):
                self.selected_climate_id = idx
                self.on_notification_toast(f"Selected {name}")

        for i, (temperature_name, temperature_id) in enumerate(na.TEMPERATURE_PALETTE.items()):
            rgb = na.TEMPERATURE_ID_MAP.get(temperature_id,0)
            rgba= rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32,width=32,style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3])),
                "hover" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5,rgba[1]+5,rgba[2]+5,rgba[3])),
                "press" : arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0],rgba[1],rgba[2],rgba[3]-50))
                })
            temperature_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=temperature_id, name=temperature_name):
                self.selected_temperature_id = idx
                self.on_notification_toast(f"Selected {name}")

        # --- choices
        biome_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64)
        biome_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=geography_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        political_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64)
        political_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=political_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        climate_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64)
        climate_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=climate_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        
        temperature_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64)
        temperature_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=temperature_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        # ---

        # --- toggles
        misc_layer_4_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        misc_layer_4_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        misc_layer_4_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        misc_layer_4_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        misc_layer_4_buttons.add(misc_layer_4_select)
        misc_layer_4_buttons.add(misc_layer_4_toggle)
        @misc_layer_4_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.misc_lines_4_visibility = not self.misc_lines_4_visibility
        @misc_layer_4_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'misc_layer_4'
            self.on_notification_toast("selected misc_layer_4")

        misc_layer_3_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        misc_layer_3_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        misc_layer_3_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        misc_layer_3_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        misc_layer_3_buttons.add(misc_layer_3_select)
        misc_layer_3_buttons.add(misc_layer_3_toggle)
        @misc_layer_3_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.misc_lines_3_visibility = not self.misc_lines_3_visibility
        @misc_layer_3_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'misc_layer_3'
            self.on_notification_toast("selected misc_layer_3")

        misc_layer_2_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        misc_layer_2_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        misc_layer_2_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        misc_layer_2_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        misc_layer_2_buttons.add(misc_layer_2_select)
        misc_layer_2_buttons.add(misc_layer_2_toggle)
        @misc_layer_2_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.misc_lines_2_visibility = not self.misc_lines_2_visibility
        @misc_layer_2_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'misc_layer_2'
            self.on_notification_toast("selected misc_layer_2")

        misc_layer_1_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        misc_layer_1_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        misc_layer_1_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        misc_layer_1_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        misc_layer_1_buttons.add(misc_layer_1_select)
        misc_layer_1_buttons.add(misc_layer_1_toggle)
        @misc_layer_1_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.misc_lines_1_visibility = not self.misc_lines_1_visibility
        @misc_layer_1_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'misc_layer_1'
            self.on_notification_toast("selected misc_layer_1")


        civilian_information_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        civilian_information_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        civilian_information_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        civilian_information_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        civilian_information_buttons.add(civilian_information_select)
        civilian_information_buttons.add(civilian_information_toggle)
        @civilian_information_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            layer__ = self.civilian_information_layer.get_sprite_list("0")
            layer__.visible = not layer__.visible
        @civilian_information_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'civilian_information_layer'
            self.on_notification_toast("selected civilian_information_layer")

        military_information_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        military_information_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        military_information_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        military_information_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        military_information_buttons.add(military_information_select)
        military_information_buttons.add(military_information_toggle)
        @military_information_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            layer__ = self.military_information_layer.get_sprite_list("0")
            layer__.visible = not layer__.visible
        @military_information_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'military_information_layer'
            self.on_notification_toast("selected military_information_layer")

        political_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        political_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        political_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        political_toggle.add(
            child=arcade.gui.UIImage(
                texture=political_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        political_buttons.add(political_layer_select)
        political_buttons.add(political_toggle)
        @political_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.country_visibility = not self.country_visibility
        @political_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'political_layer'
            self.on_notification_toast("selected political_layer")

        temperature_q4_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        temperature_q4_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        temperature_q4_toggle = arcade.gui.UIFlatButton(text="q4 temp", width=64, height=32)
        temperature_q4_buttons.add(temperature_q4_layer_select)
        temperature_q4_buttons.add(temperature_q4_toggle)
        @temperature_q4_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.q4_temperature_visibility = not self.q4_temperature_visibility
        @temperature_q4_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'temperature_layer_q4'
            self.on_notification_toast("selected temperature q4 layer")

        temperature_q3_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        temperature_q3_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        temperature_q3_toggle = arcade.gui.UIFlatButton(text="q3 temp", width=64, height=32)
        temperature_q3_buttons.add(temperature_q3_layer_select)
        temperature_q3_buttons.add(temperature_q3_toggle)
        @temperature_q3_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.q3_temperature_visibility = not self.q3_temperature_visibility
        @temperature_q3_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'temperature_layer_q3'
            self.on_notification_toast("selected temperature q3 layer")

        temperature_q2_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        temperature_q2_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        temperature_q2_toggle = arcade.gui.UIFlatButton(text="q2 temp", width=64, height=32)
        temperature_q2_buttons.add(temperature_q2_layer_select)
        temperature_q2_buttons.add(temperature_q2_toggle)
        @temperature_q2_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.q2_temperature_visibility = not self.q2_temperature_visibility
        @temperature_q2_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'temperature_layer_q2'
            self.on_notification_toast("selected temperature q2 layer")

        temperature_q1_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        temperature_q1_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        temperature_q1_toggle = arcade.gui.UIFlatButton(text="q1 temp", width=64, height=32)
        temperature_q1_buttons.add(temperature_q1_layer_select)
        temperature_q1_buttons.add(temperature_q1_toggle)
        @temperature_q1_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.q1_temperature_visibility = not self.q1_temperature_visibility
        @temperature_q1_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'temperature_layer_q1'
            self.on_notification_toast("selected temperature q1 layer")

        climate_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        climate_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        climate_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        climate_toggle.add(
            child=arcade.gui.UIImage(
                texture=climate_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        climate_buttons.add(climate_layer_select)
        climate_buttons.add(climate_toggle)
        @climate_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.climate_visibility = not self.climate_visibility
        @climate_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'climate_layer'
            self.on_notification_toast("selected climate_layer")

        biome_buttons = layer_toggle_buttons.add(
            arcade.gui.UIBoxLayout(vertical=False, space_between=1)
        )
        biome_layer_select = arcade.gui.UIFlatButton(text="sel", width=32, height=32)
        biome_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        biome_toggle.add(
            child=arcade.gui.UIImage(
                texture=geography_layer_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        biome_buttons.add(biome_layer_select)
        biome_buttons.add(biome_toggle)
        @biome_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.biome_visibility = not self.biome_visibility
        @biome_layer_select.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_layer = 'biome_layer'
            self.on_notification_toast("selected biome_layer")
        # ---
        palette_groups = {
            "biome": biome_palette_buttons,
            "country": country_palette_buttons,
            "climate": climate_palette_buttons,
            "temperature": temperature_palette_buttons
        }

        def show_only(selected_key):
            for key, group in palette_groups.items():
                group.visible = (key == selected_key and not group.visible)

        @biome_palette_choice.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            show_only("biome")

        @political_palette_choice.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            show_only("country")

        @climate_palette_choice.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            show_only("climate")

        @temperature_palette_choice.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            show_only("temperature")

        palette_toggle_buttons.add(temperature_palette_choice)
        palette_toggle_buttons.add(climate_palette_choice)
        palette_toggle_buttons.add(biome_palette_choice)
        palette_toggle_buttons.add(political_palette_choice)

    def on_notification_toast(self, message:str="", warn:bool=False, error:bool=False, success:bool=False):
        toast = na.Toast(message, duration=2)

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
        print(f"I[toast]- {message}")

    def on_clicked_load(self, filename: str):
        loaded_data = np.load(filename,allow_pickle=True)
        print(f"I- loading {filename}")
        try:
            loaded_a_data                   = loaded_data['a']
            self.upper_terrain_layer.grid[:]= np.reshape(loaded_a_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no a definition? skipping. ! THIS WILL CAUSE NORTH LOW DETAIL TO NOT LOAD")

        try:
            loaded_b_data                   = loaded_data['b']
            self.political_layer.grid[:]    = np.reshape(loaded_b_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no b definition? skipping. ! THIS WILL CAUSE NORTH POLITICAL TO NOT LOAD")

        try:
            loaded_c_data                   = loaded_data['c']
            self.lower_terrain_layer.grid[:]= np.reshape(loaded_c_data,(12000,6000))
            print("O- loaded ...")
        except:
            print("X- no c definition? skipping. ! THIS WILL CAUSE NORTH HIGH DETAIL TO NOT LOAD")

        # ---
        try:
            loaded_a_s_data                 = loaded_data['a_s']
            self.s_upper_terrain_layer.grid[:]=np.reshape(loaded_a_s_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no a_s definition? skipping. ! THIS WILL CAUSE SOUTH LOW DETAIL TO NOT LOAD")

        try:
            loaded_b_s_data                 = loaded_data['b_s']
            self.s_political_layer.grid[:]  = np.reshape(loaded_b_s_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no b_s definition? skipping. ! THIS WILL CAUSE NORTH POLITICAL TO NOT LOAD")

        try:
            loaded_c_s_data                 = loaded_data['c_s']
            self.s_lower_terrain_layer.grid[:]=np.reshape(loaded_c_s_data,(12000,6000))
            print("O- loaded ...")
        except:
            print("X- no c_s definition? skipping. ! THIS WILL CAUSE SOUTH HIGH DETAIL TO NOT LOAD")

        try:
            loaded_d_data                   = loaded_data['d']
            self.north_climate_layer.grid[:]=np.reshape(loaded_d_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no d definition? skipping. ! THIS WILL CAUSE NORTH CLIMATE TO NOT LOAD")

        try:
            loaded_d_s_data                 = loaded_data['d_s']
            self.south_climate_layer.grid[:]= np.reshape(loaded_d_s_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- no d_s definition? skipping. ! THIS WILL CAUSE SOUTH CLIMATE TO NOT LOAD")

        try:
            loaded_q1n_grid_data = loaded_data['q1n']
            self.north_temperature_layer_q1.grid[:] = np.reshape(loaded_q1n_grid_data,(600,300))
            loaded_q1s_grid_data = loaded_data['q1s']
            self.south_temperature_layer_q1.grid[:] = np.reshape(loaded_q1s_grid_data,(600,300))
            print("O- loaded ...")

            loaded_q2n_grid_data = loaded_data['q2n']
            self.north_temperature_layer_q2.grid[:] = np.reshape(loaded_q2n_grid_data,(600,300))
            loaded_q2s_grid_data = loaded_data['q2s']
            self.south_temperature_layer_q2.grid[:] = np.reshape(loaded_q2s_grid_data,(600,300))
            print("O- loaded ...")

            loaded_q3n_grid_data = loaded_data['q3n']
            self.north_temperature_layer_q3.grid[:] = np.reshape(loaded_q3n_grid_data,(600,300))
            loaded_q3s_grid_data = loaded_data['q3s']
            self.south_temperature_layer_q3.grid[:] = np.reshape(loaded_q3s_grid_data,(600,300))
            print("O- loaded ...")

            loaded_q4n_grid_data = loaded_data['q4n']
            self.north_temperature_layer_q4.grid[:] = np.reshape(loaded_q4n_grid_data,(600,300))
            loaded_q4s_grid_data = loaded_data['q4s']
            self.south_temperature_layer_q4.grid[:] = np.reshape(loaded_q4s_grid_data,(600,300))
            print("O- loaded ...")
        except:
            print("X- temperature layers failed to load. ! THIS WILL CAUSE TEMPERATURE MAPS TO NOT LOAD")

        try:
            civilian_icons_array            = loaded_data['icon_a']
            self.civilian_icons = civilian_icons_array.item()
            military_icons_array            = loaded_data['icon_b']
            self.military_icons = military_icons_array.item()
            print("O- loaded ...")

            civilian_lines_array = loaded_data['l_civ']
            self.civilian_lines = civilian_lines_array.item()
            military_lines_array = loaded_data['l_mil']
            self.military_lines = military_lines_array.item()
            misc_lines_1_array = loaded_data['l_1']
            self.misc_lines_1 = misc_lines_1_array.item()
            misc_lines_2_array = loaded_data['l_2']
            self.misc_lines_2 = misc_lines_2_array.item()
            misc_lines_3_array = loaded_data['l_3']
            self.misc_lines_3 = misc_lines_3_array.item()
            misc_lines_4_array = loaded_data['l_4']
            self.misc_lines_4 = misc_lines_4_array.item()
            print("O- loaded ...")
        except:
            print("X- icons and shapes have failed to load.")

        self.setup()

    def on_clicked_save(self):
        try:
            a_grid = np.frombuffer(self.north_upper_terrain_layer_texture.read(), dtype="u1")
            b_grid = np.frombuffer(self.north_political_layer_texture.read(), dtype="u1")
            c_grid = np.frombuffer(self.north_lower_terrain_layer_texture.read(), dtype="u1")

            a_s_grid = np.frombuffer(self.south_upper_terrain_layer_texture.read(), dtype="u1")
            b_s_grid = np.frombuffer(self.south_political_layer_texture.read(), dtype="u1")
            c_s_grid = np.frombuffer(self.south_lower_terrain_layer_texture.read(), dtype="u1")

            d_grid = np.frombuffer(self.north_climate_layer_texture.read(), dtype="u1")
            d_s_grid = np.frombuffer(self.south_climate_layer_texture.read(), dtype="u1")

            q1n_grid = np.frombuffer(self.north_temperature_layer_q1_texture.read(), dtype="u1")
            q1s_grid = np.frombuffer(self.north_temperature_layer_q1_texture.read(), dtype="u1")

            q2n_grid = np.frombuffer(self.north_temperature_layer_q2_texture.read(), dtype="u1")
            q2s_grid = np.frombuffer(self.north_temperature_layer_q2_texture.read(), dtype="u1")

            q3n_grid = np.frombuffer(self.north_temperature_layer_q3_texture.read(), dtype="u1")
            q3s_grid = np.frombuffer(self.north_temperature_layer_q3_texture.read(), dtype="u1")

            q4n_grid = np.frombuffer(self.north_temperature_layer_q4_texture.read(), dtype="u1")
            q4s_grid = np.frombuffer(self.north_temperature_layer_q4_texture.read(), dtype="u1")

            icon_layer = self.civilian_information_layer.get_sprite_list("0")
            for icon in icon_layer:
                icon_data = {
                    "x": icon.center_x,
                    "y": icon.center_y,
                    "id": icon.icon_id,
                    "unique_id": icon.unique_id
                }
                self.civilian_icons['locations'].append(icon_data)
            
            icon_layer = self.military_information_layer.get_sprite_list("0")
            for icon in icon_layer:
                icon_data = {
                    "x": icon.center_x,
                    "y": icon.center_y,
                    "id": icon.icon_id,
                    "unique_id": icon.unique_id,
                    "country_id": icon.country_id,
                    "angle_rot": icon.angle_rot,
                    "quality": icon.quality
                }
                self.military_icons['locations'].append(icon_data)

            print("?- trying np.savez_compressed ...")
            timer = time.time()
            np.savez_compressed(f"map_data/gpu-n_{time.localtime().tm_year}_{time.localtime().tm_mon}_{time.localtime().tm_mday}_{time.localtime().tm_hour}_{time.localtime().tm_min}_{time.localtime().tm_sec}.npz",
                                a=a_grid,
                                b=b_grid,
                                c=c_grid,
                                a_s=a_s_grid,
                                b_s=b_s_grid,
                                c_s=c_s_grid,
                                d=d_grid,
                                d_s=d_s_grid,
                                icon_a=np.array(self.civilian_icons),
                                icon_b=np.array(self.military_icons),
                                l_civ=np.array(self.civilian_lines),
                                l_mil=np.array(self.military_lines),
                                l_1=np.array(self.misc_lines_1),
                                l_2=np.array(self.misc_lines_2),
                                l_3=np.array(self.misc_lines_3),
                                l_4=np.array(self.misc_lines_4),
                                q1n=q1n_grid,
                                q1s=q1s_grid,
                                q2n=q2n_grid,
                                q2s=q2s_grid,
                                q3n=q3n_grid,
                                q3s=q3s_grid,
                                q4n=q4n_grid,
                                q4s=q4s_grid,
                                )
            time_taken = time.time()-timer
            self.on_notification_toast(f"O- map has been saved, took: {round(time_taken,3)} s")
        except Exception as e: 
            self.on_notification_toast("Failed to save map ... "+str(e),error=True)

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

    def setup(self):
        print("?- loading icons [1/3] ...")
        for icon in self.civilian_icons['locations']:
            icon_path = str(na.CIVILIAN_ICON_ID_MAP.get(icon['id'])) + ".png"
            icon_object = na.Icon.Civilian(
                icon_path,
                1,
                (icon['x'], icon['y']),
                0.0, 
                icon['id'],
                icon['unique_id']
            )
            self.civilian_information_layer.add_sprite("0", icon_object)
            self.information_icons_list.append(icon_object)

        for icon in self.military_icons['locations']:
            icon_path = str(na.MILITARY_ICON_ID_MAP.get(icon['id'])) + ".png"
            icon_object = na.Icon.Military(
                icon_path,
                1,
                (icon['x'], icon['y']),
                icon['angle_rot'], 
                icon['id'],
                icon['unique_id'],
                icon['country_id'],
                icon['angle_rot'],
                icon['quality']
            )
            self.military_information_layer.add_sprite("0", icon_object)
            self.information_icons_list.append(icon_object)

        timer = time.time()
        north_upper_terrain_layer_data = self.upper_terrain_layer.grid.astype(np.uint8).tobytes()
        north_lower_terrain_layer_data = self.lower_terrain_layer.grid.astype(np.uint8).tobytes()
        north_political_layer_data = self.political_layer.grid.astype(np.uint8).tobytes()

        south_upper_terrain_layer_data = self.s_upper_terrain_layer.grid.astype(np.uint8).tobytes()
        south_lower_terrain_layer_data = self.s_lower_terrain_layer.grid.astype(np.uint8).tobytes()
        south_political_layer_data = self.s_political_layer.grid.astype(np.uint8).tobytes()

        north_climate_layer_data    = self.north_climate_layer.grid.astype(np.uint8).tobytes()
        south_climate_layer_data    = self.south_climate_layer.grid.astype(np.uint8).tobytes()

        north_temperature_layer_q1_data = self.north_temperature_layer_q1.grid.astype(np.uint8).tobytes()
        south_temperature_layer_q1_data = self.south_temperature_layer_q1.grid.astype(np.uint8).tobytes()

        north_temperature_layer_q2_data = self.north_temperature_layer_q2.grid.astype(np.uint8).tobytes()
        south_temperature_layer_q2_data = self.south_temperature_layer_q2.grid.astype(np.uint8).tobytes()

        north_temperature_layer_q3_data = self.north_temperature_layer_q3.grid.astype(np.uint8).tobytes()
        south_temperature_layer_q3_data = self.south_temperature_layer_q3.grid.astype(np.uint8).tobytes()

        north_temperature_layer_q4_data = self.north_temperature_layer_q4.grid.astype(np.uint8).tobytes()
        south_temperature_layer_q4_data = self.south_temperature_layer_q4.grid.astype(np.uint8).tobytes()
        print(f"Data byte loader took {round(time.time()-timer,3)} s")

        terrain_palette_data = []
        political_palette_data=[]
        climate_palette_data = []
        temperature_palette_data = []
    
        political_water_overlay_palette = []

        for i in range(256):
            if i in na.TILE_ID_MAP:
                r, g, b = na.TILE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            a = 0 if i == 255 else 255
            terrain_palette_data.append([r, g, b, a])

        for i in range(256):
            if i in na.POLITICAL_ID_MAP:
                r, g, b = na.POLITICAL_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            political_palette_data.append([r, g, b, 255])

        for i in range(256):
            r, g, b = (0,0,0)
            a = 155 if i == 0 else 0
            political_water_overlay_palette.append([r, g, b, a])

        for i in range(256):
            if i in na.CLIMATE_ID_MAP:
                r, g, b = na.CLIMATE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            climate_palette_data.append([r, g, b, 155])

        for i in range(256):
            if i in na.TEMPERATURE_ID_MAP:
                r, g, b = na.TEMPERATURE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            temperature_palette_data.append([r, g, b, 155])

        terrain_palette_data = np.array(terrain_palette_data, dtype=np.uint8)
        terrain_palette_bytes = terrain_palette_data.tobytes()

        political_palette_data = np.array(political_palette_data, dtype=np.uint8)
        political_palette_bytes = political_palette_data.tobytes()

        political_water_overlay_palette_data = np.array(political_water_overlay_palette, dtype=np.uint8)
        political_water_overlay_palette_bytes= political_water_overlay_palette_data.tobytes()

        climate_palette_data = np.array(climate_palette_data, dtype=np.uint8)
        climate_palette_bytes = climate_palette_data.tobytes()

        temperature_palette_data = np.array(temperature_palette_data, dtype=np.uint8)
        temperature_palette_bytes = temperature_palette_data.tobytes()

        self.north_upper_terrain_layer_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=terrain_palette_bytes,         data=north_upper_terrain_layer_data
        )
        self.north_lower_terrain_layer_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(12000, 6000), colors=terrain_palette_bytes,  data=north_lower_terrain_layer_data
        )

        self.south_upper_terrain_layer_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=terrain_palette_bytes,         data=south_upper_terrain_layer_data
        )
        self.south_lower_terrain_layer_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(12000, 6000), colors=terrain_palette_bytes,  data=south_lower_terrain_layer_data
        )

        self.north_political_layer_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=political_palette_bytes,       data=north_political_layer_data
        )
        self.south_political_layer_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=political_palette_bytes,   data=south_political_layer_data
        )

        self.north_political_water_overlay_layer_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=political_water_overlay_palette_bytes,       data=north_upper_terrain_layer_data
        )
        self.south_political_water_overlay_layer_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=political_water_overlay_palette_bytes,       data=south_upper_terrain_layer_data
        )

        self.north_climate_layer_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=climate_palette_bytes,       data=north_climate_layer_data
        )
        self.south_climate_layer_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=climate_palette_bytes,       data=south_climate_layer_data
        )

        self.north_temperature_layer_q4_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=north_temperature_layer_q4_data
        )
        self.south_temperature_layer_q4_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=south_temperature_layer_q4_data
        )

        self.north_temperature_layer_q3_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=north_temperature_layer_q3_data
        )
        self.south_temperature_layer_q3_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=south_temperature_layer_q3_data
        )

        self.north_temperature_layer_q2_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=north_temperature_layer_q2_data
        )
        self.south_temperature_layer_q2_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=south_temperature_layer_q2_data
        )

        self.north_temperature_layer_q1_texture = cgpu.ColorChunk(
            pos=(0,0), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=north_temperature_layer_q1_data
        )
        self.south_temperature_layer_q1_texture = cgpu.ColorChunk(
            pos=(0,-6000), ctx=self.ctx, size=(600, 300), colors=temperature_palette_bytes,       data=south_temperature_layer_q1_data
        )

        try:
            del self.upper_terrain_layer
            del self.lower_terrain_layer
            del self.political_layer
            del self.s_upper_terrain_layer
            del self.s_lower_terrain_layer
            del self.s_political_layer
            del self.north_climate_layer
            del self.south_climate_layer
            del self.north_temperature_layer_q1
            del self.north_temperature_layer_q2
            del self.north_temperature_layer_q3
            del self.north_temperature_layer_q4
            del self.south_temperature_layer_q1
            del self.south_temperature_layer_q2
            del self.south_temperature_layer_q3
            del self.south_temperature_layer_q4
            print("O- freed up as much memory as possible")
        except:
            print("X- couldn't free up memory, good luck.")

        def _create_keybind_label(text):
            return arcade.gui.UITextArea(
                text=text,
                width=200,
                height=20,
                font_size=10
            ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(width=1,color=arcade.types.Color(30,30,30,255))
        if self.is_keybind_box_disabled == False:
            print("?- Loading keybind popup")

            self.keybinds_box.add(_create_keybind_label("[ O ] - Editing mode"))
            self.keybinds_box.add(_create_keybind_label("[ Scroll ] - Scrool zoom"))
            self.keybinds_box.add(_create_keybind_label("[ + ] - Zoom in"))
            self.keybinds_box.add(_create_keybind_label("[ - ] - Zoom out"))
            self.keybinds_box.add(_create_keybind_label("[ RMB ] - Pan camera"))
            self.keybinds_box.add(_create_keybind_label("[ LMB ] - Select/Place"))
            self.keybinds_box.add(_create_keybind_label("[ M ] - Toggle moving mode"))
            self.keybinds_box.add(_create_keybind_label("[ R ] - Toggle rotate mode"))
            self.keybinds_box.add(_create_keybind_label("[ E ] - Toggle icons menu"))
            self.keybinds_box.add(_create_keybind_label("[ G ] - Toggle grid"))

            close_keybinds_button = arcade.gui.UIFlatButton(width=200,height=20,text="Close").with_background(color=arcade.types.Color(25,25,25,255)).with_border(width=1,color=arcade.types.Color(30,30,30,255))
            self.keybinds_box.add(close_keybinds_button)

            @close_keybinds_button.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                self.keybinds_box.clear()
                self.keybinds_box.visible = False

            toggle_keybinds_attribute = arcade.gui.UIFlatButton(width=200,height=20,text="Don't show again").with_background(color=arcade.types.Color(25,25,25,255)).with_border(width=1,color=arcade.types.Color(30,30,30,255))
            self.keybinds_box.add(toggle_keybinds_attribute)

            @toggle_keybinds_attribute.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                na.set_attributes('keybinds_disable',True)
                self.keybinds_box.clear()
                self.keybinds_box.visible = False

            print("O- Loaded keybinds popup")
        
        self.has_map_been_loaded = True

    def on_resize(self, width, height):
        self.resized_size = width, height
        print(f"resized {width} and {height}")
        return super().on_resize(width, height)

    def on_update(self, dt):
        self.camera.position += (self.camera_speed[0]*self.zoomed_speed_mod, self.camera_speed[1]*self.zoomed_speed_mod)

        self.camera.zoom += self.zoom_speed*self.camera.zoom

        self.zoomed_speed_mod = max(self.zoomed_speed_mod+self.zoomed_speed_mod_adder, 0.01)
        self.zoomed_speed_mod = min(self.zoomed_speed_mod, 2.0)

        for icon in self.information_icons_list:
            icon.scale = max(1.0-(self.camera.zoom/3),0.05)
            # icon.color = na.QUALITY_COLOR_MAP.get(icon.quality, (255,0,0,255))

    def on_draw(self):
        self.camera.use() 
        self.clear()

        # drawing layers
        with self.ctx.enabled(self.ctx.BLEND):
            if self.has_map_been_loaded:
                if self.biome_visibility:
                    self.north_upper_terrain_layer_texture.draw(size=(12000,6000))
                    self.south_upper_terrain_layer_texture.draw(size=(12000,6000))
                    if self.camera.zoom >= 1.5:
                        self.north_lower_terrain_layer_texture.draw(size=(12000,6000))
                        self.south_lower_terrain_layer_texture.draw(size=(12000,6000))
            
                if self.climate_visibility:
                    self.north_climate_layer_texture.draw(size=(12000,6000))
                    self.south_climate_layer_texture.draw(size=(12000,6000))

                if self.q1_temperature_visibility:
                    self.north_temperature_layer_q1_texture.draw(size=(12000,6000))
                    self.south_temperature_layer_q1_texture.draw(size=(12000,6000))

                if self.q2_temperature_visibility:
                    self.north_temperature_layer_q2_texture.draw(size=(12000,6000))
                    self.south_temperature_layer_q2_texture.draw(size=(12000,6000))

                if self.q3_temperature_visibility:
                    self.north_temperature_layer_q3_texture.draw(size=(12000,6000))
                    self.south_temperature_layer_q3_texture.draw(size=(12000,6000))

                if self.q4_temperature_visibility:
                    self.north_temperature_layer_q4_texture.draw(size=(12000,6000))
                    self.south_temperature_layer_q4_texture.draw(size=(12000,6000))

            if self.political_background == True:
                if self.has_map_been_loaded:
                    if self.country_visibility:
                        self.north_political_layer_texture.draw(size=(12000,6000))
                        self.south_political_layer_texture.draw(size=(12000,6000))
                        self.north_political_water_overlay_layer_texture.draw(size=(12000,6000))
                        self.south_political_water_overlay_layer_texture.draw(size=(12000,6000))

        # grid assistance lines to show big tile borders
        if self.grid_assistance:
            for x__ in range(600):
                if x__*20 > self.camera.position[0]-100 and x__*20 < self.camera.position[0]+100:
                    arcade.draw_line(x__*20,0,x__*20,6000,color=(200,200,200,200),line_width=0.5)

            for y__ in range(300):
                if y__*20 > self.camera.position[1]-100 and y__*20 < self.camera.position[1]+100:
                    arcade.draw_line(0,y__*20,12000,y__*20,color=(200,200,200,200),line_width=0.5)

        # equator line
        arcade.draw_line(0,0,12000,0,(100,100,100),10)

        if self.current_position_world:
            if self.drawing_line_start and self.drawing_line_end is None:
                arcade.draw_line(self.drawing_line_start[0],self.drawing_line_start[1],self.current_position_world[0],self.current_position_world[1],(255,255,255,255),line_width=4)

        self.civilian_information_layer.draw(pixelated=True)
        self.military_information_layer.draw(pixelated=True)

        if self.misc_lines_1_visibility:
            for shape in self.misc_lines_1['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)
        if self.misc_lines_2_visibility:
            for shape in self.misc_lines_2['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)
        if self.misc_lines_3_visibility:
            for shape in self.misc_lines_3['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)
        if self.misc_lines_4_visibility:
            for shape in self.misc_lines_4['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)

        civilian_layer = self.civilian_information_layer.get_sprite_list("0")
        military_layer = self.military_information_layer.get_sprite_list("0")
        if civilian_layer.visible == True:
            for shape in self.civilian_lines['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)
        if military_layer.visible == True:
            for shape in self.military_lines['locations']:
                if shape:
                    arcade.draw_line_strip(shape,(255,255,255,255),1.5)

        if self.current_shape:
            arcade.draw_line_strip(self.current_shape,(255,0,255,155),2)

        if self.last_pressed_line_point:
            arcade.draw_line(self.last_pressed_line_point[0],self.last_pressed_line_point[1],self.current_position_world[0],self.current_position_world[1],(255,0,0,155),2)

        if self.selected_world_icon:
            arcade.draw_circle_outline(self.selected_world_icon.position[0],self.selected_world_icon.position[1],16,(255,255,255,155),1,0,6)

        if self.current_position_world:
            if self.editing_mode == True:
                if self.camera.zoom >= 2.5:
                    crosshair_size = (self.editing_mode_size/8)
                    crosshair_sprite = arcade.Sprite("icons/crosshair.png",(crosshair_size,crosshair_size),self.current_position_world[0],self.current_position_world[1],0)
                    arcade.draw_sprite(crosshair_sprite,pixelated=True)
                    arcade.draw_lrbt_rectangle_outline(round(self.current_position_world[0]-0.5),round(self.current_position_world[0]+0.5),round(self.current_position_world[1]-0.5),round(self.current_position_world[1]+0.5),color=(255,255,255,255),border_width=0.1)
                else:
                    arcade.draw_lbwh_rectangle_outline(round(self.current_position_world[0]/20-0.5)*20,round(self.current_position_world[1]/20-0.5)*20,20,20,(255,255,255,255),1)
            else:
                arcade.draw_circle_outline(self.current_position_world[0],self.current_position_world[1],2,(255,255,255,255),0.2,0,-1)
        
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

        # if symbol   == arcade.key.L:
        #     COLOR_TO_ID = {v: k for k, v in na.POLITICAL_ID_MAP.items()}

        #     image_path = 'cryaboutit.png'
        #     img = Image.open(image_path).convert('RGB')
        #     width, height = img.size

        #     for y in range(height):
        #         for x in range(width):
        #             current_color = img.getpixel((x, y))
        #             if current_color in COLOR_TO_ID:
        #                 color_id = COLOR_TO_ID[current_color]
        #                 self.north_political_layer_texture.write_tile((x,y),color_id)

        #             if current_color == (67, 134, 28) or current_color == (72, 119, 58) or current_color == (53, 134, 41) or current_color == (20, 42, 8):
        #                 self.north_political_layer_texture.write_tile((x,y),2)

        #             if current_color == (166, 29, 45) or current_color == (210, 37, 60) or current_color == (60, 3, 8):
        #                 self.north_political_layer_texture.write_tile((x,y),1)

        #             if current_color == (47, 10, 75):
        #                 self.north_political_layer_texture.write_tile((x,y),13)

        #             if current_color == (96, 18, 18):
        #                 self.north_political_layer_texture.write_tile((x,y),5)

        if symbol   == arcade.key.Q:
            self.editing_mode = not self.editing_mode
            self.on_notification_toast(f"editing mode toggled {self.editing_mode}")
        if symbol   == arcade.key.G:
            self.grid_assistance = not self.grid_assistance
        if symbol   == arcade.key.F:
            self.set_fullscreen(not self.fullscreen)
            self.on_notification_toast(f"fullscreen toggled")
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
            if self.icon_box.visible == False:
                brushes = na.get_all_files('local_data/brushes')
                print(f"I- found {brushes.__len__()} brush files")
                for idx, path in enumerate(brushes):
                    icon_texture = arcade.load_texture(path)
                    button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    button.add(
                        child=arcade.gui.UIImage(texture=icon_texture, width=48, height=48),
                        anchor_x="center",
                        anchor_y="center"
                    )
                    @button.event
                    def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, path=path):
                        self.selected_brush = path
                        self.on_notification_toast(f"Selected {path}")

                    self.custom_brushes.add(button, idx % 5, idx // 5)

            elif self.icon_box.visible == True:
                self.custom_brushes.clear()

            self.icon_box.visible = not self.icon_box.visible

        if symbol   == arcade.key.ESCAPE:
            self.escape_buttons.visible = not self.escape_buttons.visible
        
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

    def on_mouse_press(self, x, y, button, modifiers):
        if button is arcade.MOUSE_BUTTON_RIGHT:
            if self.selected_icon_id or self.selected_icon_id == 0:
                self.selected_icon_id = None
                self.on_notification_toast("Deselected icon id.", warn=True)
        
            if self.current_shape:
                self.last_pressed_line_point = None
                self.final_shape = self.current_shape[:]
                self.current_shape = []

                if self.selected_layer == 'civilian_information_layer':
                    self.civilian_lines['locations'].append(self.final_shape)
                elif self.selected_layer == 'military_information_layer':
                    self.military_lines['locations'].append(self.final_shape)
                elif self.selected_layer == 'misc_layer_4':
                    self.misc_lines_4['locations'].append(self.final_shape)
                elif self.selected_layer == 'misc_layer_3':
                    self.misc_lines_3['locations'].append(self.final_shape)
                elif self.selected_layer == 'misc_layer_2':
                    self.misc_lines_2['locations'].append(self.final_shape)
                elif self.selected_layer == 'misc_layer_1':
                    self.misc_lines_1['locations'].append(self.final_shape)
                else:
                    self.on_notification_toast("no layer received shape?",warn=True)
                
        if button is arcade.MOUSE_BUTTON_LEFT:
            self.last_pressed_screen = (x, y)
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2

            # Conversion from screen coordinates to world coordinates
            world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x) 
            world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
            # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset 
            self.last_pressed_world = (world_x, world_y)
            tile_x = round(world_x / 20 - 0.5)
            tile_y = round(world_y / 20 - 0.5)

            if self.editing_mode == True:
                pass
            else:
                if self.selected_line_tool:
                    self.last_pressed_line_point = (world_x,world_y)
                    clicked_point = (world_x,world_y)
                    self.current_shape.append(clicked_point)
                else:
                    if self.selected_icon_id or self.selected_icon_id == 0:
                        if self.selected_icon_type == 'civilian':
                            icon_path = str(na.CIVILIAN_ICON_ID_MAP.get(self.selected_icon_id))+".png"
                            generated_unique_id:int = random.randrange(1000,9999)
                            icon = na.Icon.Civilian(icon_path,1,(world_x,world_y),0.0,self.selected_icon_id,generated_unique_id)
                            self.civilian_information_layer.add_sprite("0",icon)
                            self.information_icons_list.append(icon)

                        if self.selected_icon_type == 'military':
                            icon_path = str(na.MILITARY_ICON_ID_MAP.get(self.selected_icon_id))+".png"
                            generated_unique_id:int = random.randrange(1000,9999)
                            icon = na.Icon.Military(icon_path,1,(world_x,world_y),0.0,self.selected_icon_id,generated_unique_id,0,0.0)
                            self.military_information_layer.add_sprite("0",icon)
                            self.information_icons_list.append(icon)

                    nearby_icon = self.find_element_near(world_x, world_y, elements=self.information_icons_list, radius=24)
                    if nearby_icon:
                        self.selected_world_icon = nearby_icon
                        self.selected_icon_edit_box.clear()
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
                                self.on_notification_toast("downgraded icon")
                            else:
                                self.on_notification_toast(f"icon is already at {nearby_icon.quality} !",error=True)

                        @upgrade_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            if nearby_icon.quality < 5:
                                nearby_icon.quality += 1
                                self.on_notification_toast("upgraded icon")
                            else:
                                self.on_notification_toast(f"icon is already at {nearby_icon.quality} !",error=True)

                        @rotate_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            self.rotating_the_icon = not self.rotating_the_icon

                        @rotate_reset_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            self.selected_world_icon.angle = 0.0

                        @move_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            self.moving_the_icon = not self.moving_the_icon

                        @remove_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            self.information_icons_list.remove(self.selected_world_icon)
                            if isinstance(self.selected_world_icon,na.Icon.Civilian):
                                icon_layer = self.civilian_information_layer.get_sprite_list("0")
                            if isinstance(self.selected_world_icon,na.Icon.Military):
                                icon_layer = self.military_information_layer.get_sprite_list("0")
                            icon_layer.remove(self.selected_world_icon)
                            self.selected_icon_edit_box.clear()
                            self.selected_world_icon = None
                            self.on_notification_toast("Successfully removed icon.", success=True)

                        self.selected_icon_edit_box.add(move_button)
                        self.selected_icon_edit_box.add(remove_button)
                        self.selected_icon_edit_box.add(rotate_button)
                        self.selected_icon_edit_box.add(rotate_reset_button)
                        if isinstance(self.selected_world_icon,na.Icon.Military):
                            self.selected_icon_edit_box.add(upgrade_button)
                            self.selected_icon_edit_box.add(downgrade_button)
                    else:
                        print("Found absolutely nothing in vicinity.") 
                        self.selected_world_icon = None
                        self.selected_icon_edit_box.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        camera = self.camera
        zoom = camera.zoom #
        if buttons is arcade.MOUSE_BUTTON_RIGHT:
            camera.position -= (dx / zoom, dy / zoom)
            
        if buttons is arcade.MOUSE_BUTTON_LEFT:
            self.current_position_screen = (x, y)
            camera_x, camera_y = camera.position
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
            # Conversion from screen coordinates to world coordinates
            world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + camera_x) 
            world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + camera_y)
            # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset
            tile_x = round(world_x / 20 - 0.5)
            tile_y = round(world_y / 20 - 0.5)

            self.current_position_world = (world_x, world_y)

            if self.editing_mode == True:
                
                if self.selected_layer == 'political_layer':
                    if not tile_y < 0:
                        political_tile_to_edit = tile_x,tile_y
                        self.north_political_layer_texture.write_tile(position=political_tile_to_edit,tile_id=self.selected_country_id)
                    else:
                        political_tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_political_layer_texture.write_tile(position=political_tile_to_edit,tile_id=self.selected_country_id)

                elif self.selected_layer == 'temperature_layer_q4':
                    if not tile_y < 0:
                        tile_to_edit = tile_x,tile_y
                        self.north_temperature_layer_q4_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)
                    else:
                        tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_temperature_layer_q4_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)

                elif self.selected_layer == 'temperature_layer_q3':
                    if not tile_y < 0:
                        tile_to_edit = tile_x,tile_y
                        self.north_temperature_layer_q3_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)
                    else:
                        tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_temperature_layer_q3_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)

                elif self.selected_layer == 'temperature_layer_q2':
                    if not tile_y < 0:
                        tile_to_edit = tile_x,tile_y
                        self.north_temperature_layer_q2_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)
                    else:
                        tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_temperature_layer_q2_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)

                elif self.selected_layer == 'temperature_layer_q1':
                    if not tile_y < 0:
                        tile_to_edit = tile_x,tile_y
                        self.north_temperature_layer_q1_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)
                    else:
                        tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_temperature_layer_q1_texture.write_tile(position=tile_to_edit,tile_id=self.selected_temperature_id)

                elif self.selected_layer == 'climate_layer':
                    if not tile_y < 0:
                        climate_tile_to_edit = tile_x,tile_y
                        self.north_climate_layer_texture.write_tile(position=climate_tile_to_edit,tile_id=self.selected_climate_id)
                    else:
                        political_tile_to_edit = tile_x,300-abs(tile_y)
                        self.south_climate_layer_texture.write_tile(position=climate_tile_to_edit,tile_id=self.selected_climate_id)

                elif self.selected_layer == 'biome_layer':
                    if self.camera.zoom >= 1.5:
                        if self.selected_brush:
                            if self.selected_brush == 1:
                                coordinates = na.generate_blob_coordinates(self.editing_mode_size,self.editing_mode_size)
                                if not coordinates:
                                    print("No coordinates provided.")
                                    return
                                    
                                min_x = min(x for x, y in coordinates)
                                min_y = min(y for x, y in coordinates)
                                max_x = max(x for x, y in coordinates)
                                max_y = max(y for x, y in coordinates)

                                center_x = (min_x + max_x) / 2
                                center_y = (min_y + max_y) / 2
                                
                                target_positions = []
                                for rel_x, rel_y in coordinates:
                                    x_pos = round(world_x-0.5 + (rel_x - center_x))
                                    y_pos = round(world_y-0.5 + (rel_y - center_y))
                                    target_positions.append((x_pos, y_pos))
                                
                                for pos in target_positions:
                                    x__, y__ = pos
                                    if not y__ < 0:
                                        self.north_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                                    else:
                                        y__ = 6000-abs(y__)
                                        self.south_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                            else:
                                coordinates = na.get_pixel_coordinates(self.selected_brush)
                                if not coordinates:
                                    print("No coordinates provided.")
                                    return
                                    
                                min_x = min(x for x, y in coordinates)
                                min_y = min(y for x, y in coordinates)
                                max_x = max(x for x, y in coordinates)
                                max_y = max(y for x, y in coordinates)

                                center_x = (min_x + max_x) / 2
                                center_y = (min_y + max_y) / 2
                                
                                target_positions = []
                                for rel_x, rel_y in coordinates:
                                    x_pos = round(world_x-0.5 + (rel_x - center_x))
                                    y_pos = round(world_y-0.5 + (rel_y - center_y))
                                    target_positions.append((x_pos, y_pos))
                                
                                for pos in target_positions:
                                    x__, y__ = pos
                                    if not y__ < 0:
                                        self.north_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                                    else:
                                        y__ = 6000-abs(y__)
                                        self.south_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                        else:
                            list_of_tile_positions = []

                            half_size = self.editing_mode_size // 2
                            radius = half_size

                            for x_offset in range(self.editing_mode_size):
                                for y_offset in range(self.editing_mode_size):
                                    x_ = world_x + (x_offset - half_size)
                                    y_ = world_y + (y_offset - half_size)

                                    distance = ((x_offset - half_size) + 0.5) ** 2 + ((y_offset - half_size) + 0.5) ** 2

                                    if not self.editing_mode_size == 1:
                                        if distance <= (radius + 0.5) ** 2:
                                            list_of_tile_positions.append((round(x_-0.5), round(y_-0.5)))
                                    else:
                                        list_of_tile_positions.append((round(x_-0.5), round(y_-0.5)))

                            if list_of_tile_positions:
                                for pos in list_of_tile_positions:
                                    x__, y__ = pos
                                    if not y__ < 0:
                                        self.north_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                                    else:
                                        y__ = 6000-abs(y__)
                                        self.south_lower_terrain_layer_texture.write_tile(position=(x__,y__),tile_id=self.selected_lower_id)
                            else:
                                print(f"no positions")

                    elif self.camera.zoom < 1.5:
                        if not tile_y < 0:
                            biome_tile_to_edit = tile_x,tile_y
                            self.north_upper_terrain_layer_texture.write_tile(position=biome_tile_to_edit,tile_id=self.selected_lower_id)
                        else:
                            biome_tile_to_edit = tile_x,300-abs(tile_y)
                            self.south_upper_terrain_layer_texture.write_tile(position=biome_tile_to_edit,tile_id=self.selected_lower_id)

            else:
                if self.rotating_the_icon:
                    try:
                        current_angle = math.atan2(world_x - self.selected_world_icon.position[0], world_y - self.selected_world_icon.position[1])
                        delta_angle = (((current_angle - self.previous_angle + math.pi) % (2 * math.pi)) - math.pi) * (180/math.pi)
                        self.selected_world_icon.angle += delta_angle
                        self.previous_angle = current_angle
                    except:
                        self.on_notification_toast("Couldn't rotate [cannot find icon] ...", warn=True)

                elif self.moving_the_icon == True:
                    self.selected_world_icon.position = (world_x,world_y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button is arcade.MOUSE_BUTTON_LEFT:
            self.last_pressed_world = None
            self.last_pressed_screen = None

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
        self.current_position_screen = (x, y)
        diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
        
        # Conversion from screen coordinates to world coordinates
        world_x = ((((x - self.width  / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x) 
        world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
        # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset 
        self.current_position_world = (world_x, world_y)

def main():
    print("I- GAME INITIALIZING ...")
    Game(WIDTH, HEIGHT, "NATIONWIDER")
    arcade.run()

if __name__ == "__main__":
    main()
    