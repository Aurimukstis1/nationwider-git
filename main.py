import itertools
import arcade
import arcade.gui
import arcade.gui.widgets
import math
import arcade.utils
import numpy as np
import random
import nation_utils as nutil
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



class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)
        self.uptime = 0.0
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

        self.selected_layer:str     = None

        self.has_map_been_loaded    = False

        self.political_layer        = nutil.GridLayer((600,300))
        self.upper_terrain_layer    = nutil.GridLayer((600,300))
        self.lower_terrain_layer    = nutil.GridLayer((12000,6000))

        self.s_political_layer      = nutil.GridLayer((600,300))
        self.s_upper_terrain_layer  = nutil.GridLayer((600,300))
        self.s_lower_terrain_layer  = nutil.GridLayer((12000,6000))

        self.north_climate_layer    = nutil.GridLayer((600,300))
        self.south_climate_layer    = nutil.GridLayer((600,300))

        self.north_temperature_layer_q1 = nutil.GridLayer((600,300))
        self.south_temperature_layer_q1 = nutil.GridLayer((600,300))

        self.north_temperature_layer_q2 = nutil.GridLayer((600,300))
        self.south_temperature_layer_q2 = nutil.GridLayer((600,300))

        self.north_temperature_layer_q3 = nutil.GridLayer((600,300))
        self.south_temperature_layer_q3 = nutil.GridLayer((600,300))

        self.north_temperature_layer_q4 = nutil.GridLayer((600,300))
        self.south_temperature_layer_q4 = nutil.GridLayer((600,300))
        self.selected_temperature_id= 0

        # icon tools
        self.selected_icon_type = None
        self.selected_icon_id = None
        self.selected_world_icon = None
        self.moving_the_icon = False
        self.rotating_the_icon = False

        # line tools
        self.selected_line_tool = False
        self.selected_remove_line_tool = False
        self.last_pressed_line_point = None
        self.current_shape = []
        self.final_shape = []

        self.export_flags = {
            "misc1_layer": True,
            "misc2_layer": True,
            "misc3_layer": True,
            "misc4_layer": True,
            "military_layer": True,
            "civilian_layer": True,
            "political_layer": True,
            "q4_temperature_layer": True,
            "q3_temperature_layer": True,
            "q2_temperature_layer": True,
            "q1_temperature_layer": True,
            "climate_layer": True,
            "biome_layer": True
        }
        
        self.misc1_information_layer = nutil.InformationLayer("misc1_layer")
        self.misc2_information_layer = nutil.InformationLayer("misc2_layer")
        self.misc3_information_layer = nutil.InformationLayer("misc3_layer")
        self.misc4_information_layer = nutil.InformationLayer("misc4_layer")
        self.military_information_layer = nutil.InformationLayer("military_layer")
        self.civilian_information_layer = nutil.InformationLayer("civilian_layer")

        # self.misc1_visibility = True
        # self.misc2_visibility = True
        # self.misc3_visibility = True
        # self.misc4_visibility = True
        # self.military_visibility = True
        # self.civilian_visibility = True
        # self.political_visibility = True
        # self.q1_temperature_visibility = False
        # self.q2_temperature_visibility = False
        # self.q3_temperature_visibility = False
        # self.q4_temperature_visibility = False
        # self.climate_visibility = False
        # self.biome_visibility = True

        self.visibility_flags = {
            "misc1_layer": True,
            "misc2_layer": True,
            "misc3_layer": True,
            "misc4_layer": True,
            "military_layer": True,
            "civilian_layer": True,
            "political_layer": True,
            "q1_temperature_layer": False,
            "q2_temperature_layer": False,
            "q3_temperature_layer": False,
            "q4_temperature_layer": False,
            "climate_layer": False,
            "biome_layer": True
        }

        self.information_layers = [
            self.military_information_layer,
            self.civilian_information_layer,
            self.misc1_information_layer,
            self.misc2_information_layer,
            self.misc3_information_layer,
            self.misc4_information_layer
        ]

        self.bottom_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.right_anchor = self.ui.add(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
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

        self.selected_icon_edit_box = self.bottom_anchor.add(arcade.gui.UIBoxLayout(space_between=1, vertical=True), anchor_x="center", anchor_y="bottom")

        self.keybinds_box = self.center_anchor.add(arcade.gui.UIBoxLayout(space_between=0), anchor_x="center", anchor_y="center")
        self.is_keybind_box_disabled = False

        savefiles = nutil.get_all_files('map_data')
        attributes_data = nutil.get_attributes()
        self.is_keybind_box_disabled = attributes_data['keybinds_disable']

        if savefiles:
            # menu for savefiles
            # each savefile is a rectangular button which could support the name, and thumbnail
            load_menu_box = self.center_anchor.add(
                arcade.gui.UIGridLayout(
                    column_count=5,
                    row_count=5,
                    vertical_spacing=1,
                    horizontal_spacing=1
                ).with_background(color=arcade.types.Color(10,10,10,255)).with_border(color=arcade.types.Color(20,20,20,255)),
                anchor_x="center",
                anchor_y="center"
            )
            for i, savefile in enumerate(savefiles):
                savefile_wrapper = arcade.gui.UIBoxLayout(vertical=True, space_between=1)
                savefile_button = arcade.gui.UIFlatButton(width=256,height=128,text=f"{savefile.split('\\')[-1]}")
                savefile_wrapper.add(arcade.gui.UILabel(text=f"{savefile.split('\\')[-1]}", font_size=10, align="center", height=8))
                savefile_wrapper.add(savefile_button)
                try:
                    thumbnail = np.load(savefile)['thumbnail']
                    thumbnail = Image.fromarray(thumbnail)
                    thumbnail = thumbnail.resize((248,120))
                    thumbnail = thumbnail.convert("RGBA")
                    savefile_button.add(
                        child=arcade.gui.UIImage(texture=arcade.Texture(image=thumbnail)),
                        anchor_x="center",
                        anchor_y="center"
                    )
                except Exception as e:
                    print(f"X- failed to load thumbnail for {savefile}: {e}")
                load_menu_box.add(savefile_wrapper, i % 5, i // 5)

                @savefile_button.event
                def on_click(event: arcade.gui.UIOnClickEvent, savename=savefile, index=i):
                    self.on_clicked_load(savename)
                    load_menu_box.visible = False
                    load_menu_box.clear()
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
            self.selected_remove_line_tool = False
            self.on_notification_toast("selected line tool")
        self.default_brushes.add(line_tool_select_button)

        line_tool_deselect_button = arcade.gui.UIFlatButton(text="no line", width=64, height=64)
        @line_tool_deselect_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_line_tool = False
            self.selected_remove_line_tool = False
            self.on_notification_toast("deselected line tool")
        self.default_brushes.add(line_tool_deselect_button)

        line_tool_remove_button = arcade.gui.UIFlatButton(text="rm line", width=64, height=64)
        @line_tool_remove_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.selected_remove_line_tool = True
            self.selected_line_tool = False
            self.on_notification_toast("selected line removal tool")
        self.default_brushes.add(line_tool_remove_button)

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
            label = arcade.gui.UILabel(text=name, font_size=10, align="center", height=8)
            button_wrapper = arcade.gui.UIBoxLayout(vertical=True, space_between=0)
            icon_texture = arcade.load_texture(f"{nutil.CIVILIAN_ICON_ID_MAP.get(idx)}.png")
            button = arcade.gui.UIFlatButton(text="", width=64, height=64)
            button.add(
                child=arcade.gui.UIImage(texture=icon_texture, width=48, height=48),
                anchor_x="center",
                anchor_y="center"
            )
            button_wrapper.add(button)
            button_wrapper.add(label)
            self.icon_civilian_grid.add(button_wrapper, idx % 5, idx // 5)
            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, name=name):
                self.selected_icon_id = idx
                self.selected_icon_type='civilian'
                self.on_notification_toast(f"Selected {idx} {name}")

        for idx, name in enumerate(military_icon_names):
            label = arcade.gui.UILabel(text=name, font_size=10, align="center", height=8)
            button_wrapper = arcade.gui.UIBoxLayout(vertical=True, space_between=0)
            icon_texture = arcade.load_texture(f"{nutil.MILITARY_ICON_ID_MAP.get(idx)}.png")
            button = arcade.gui.UIFlatButton(text="", width=64, height=64)
            button.add(
                child=arcade.gui.UIImage(texture=icon_texture, width=48, height=48),
                anchor_x="center",
                anchor_y="center"
            )
            button_wrapper.add(button)
            button_wrapper.add(label)
            self.icon_military_grid.add(button_wrapper, idx % 5, idx // 5)
            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, name=name):
                self.selected_icon_id = idx
                self.selected_icon_type='military'
                self.on_notification_toast(f"Selected {idx} {name}")

        layers_box = self.right_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=8, size_hint=(0, 1)),
            anchor_x="right",
            anchor_y="center"
        )
        layer_toggle_buttons = layers_box.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=2, size_hint=(0, 1))
        ).with_background(color=arcade.types.Color(0,0,0,100))
        palette_toggle_buttons = layers_box.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=2, size_hint=(0, 1))
        ).with_background(color=arcade.types.Color(0,0,0,100))

        self.hover_label = arcade.gui.UILabel(text="", font_size=12, align="center", width=32)

        biome_palette_wrapper = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1),
            anchor_x="center",
            anchor_y="bottom"
        )
        biome_palette_wrapper.add(self.hover_label)
        biome_palette_buttons = biome_palette_wrapper.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        biome_palette_buttons.visible = False

        country_palette_wrapper = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1),
            anchor_x="center",
            anchor_y="bottom"
        )
        country_palette_wrapper.add(self.hover_label)
        country_palette_buttons = country_palette_wrapper.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        country_palette_buttons.visible = False

        climate_palette_wrapper = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1),
            anchor_x="center",
            anchor_y="bottom"
        )
        climate_palette_wrapper.add(self.hover_label)
        climate_palette_buttons = climate_palette_wrapper.add(
            arcade.gui.UIBoxLayout(
                vertical=False
                ).with_background(color=arcade.types.Color(30,30,30,255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        climate_palette_buttons.visible = False

        temperature_palette_wrapper = self.bottom_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=1),
            anchor_x="center",
            anchor_y="bottom"
        )
        temperature_palette_wrapper.add(self.hover_label)
        temperature_palette_buttons = temperature_palette_wrapper.add(
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

        def _create_export_toggle(self, label: str, export_attr: str):
            layout = arcade.gui.UIBoxLayout(vertical=False, space_between=4)
            
            status_label = arcade.gui.UILabel(width=128, height=32, text=f"{self.export_flags[export_attr]}")
            toggle_button = arcade.gui.UIFlatButton(width=128, height=32, text=label)

            @toggle_button.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                current_value = self.export_flags[export_attr]
                self.export_flags[export_attr] = not current_value
                status_label.text = f"{self.export_flags[export_attr]}"

            layout.add(status_label)
            layout.add(toggle_button)

            return layout
        
        self.escape_buttons.add(_create_export_toggle(self, "Military Layer", "military_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Civilian Layer", "civilian_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Misc Layer 1", "misc1_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Misc Layer 2", "misc2_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Misc Layer 3", "misc3_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Misc Layer 4", "misc4_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Political", "political_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Q4 Temp", "q4_temperature_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Q3 Temp", "q3_temperature_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Q2 Temp", "q2_temperature_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Q1 Temp", "q1_temperature_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Climate", "climate_layer"))
        self.escape_buttons.add(_create_export_toggle(self, "Biome", "biome_layer"))

        save_button = arcade.gui.UIFlatButton(width=256,height=64,text=f"Save to File")
        @save_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.on_clicked_save()
        self.escape_buttons.add(save_button)

        def _create_palette_button(name, id, id_map, button_container, on_click_handler):
            rgb = id_map.get(id, 0)
            rgba = rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32, width=32, style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3])),
                "hover": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5, rgba[1]+5, rgba[2]+5, rgba[3])),
                "press": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3]-50))
            })
            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=id, n=name):
                on_click_handler(idx, n)
            
            def on_hover(button, is_hovered):
                if is_hovered:
                    self.hover_label.text = name
            arcade.gui.bind(button, "hovered", on_hover)

            button_container.add(button)

        for biome_name, biome_id in nutil.BIOME_PALETTE.items():
            def on_biome_click(idx, name):
                self.selected_lower_id = idx
                self.on_notification_toast(f"Selected {name}")
            _create_palette_button(
                biome_name, 
                biome_id,
                nutil.TILE_ID_MAP,
                biome_palette_buttons,
                on_biome_click
            )

        for country_owner, country_id in nutil.COUNTRY_PALETTE.items():
            def on_country_click(idx, name):
                self.selected_country_id = idx
                self.on_notification_toast(f"Selected {name}")
            _create_palette_button(
                country_owner,
                country_id,
                nutil.POLITICAL_ID_MAP,
                country_palette_buttons,
                on_country_click
            )

        for climate_name, climate_id in nutil.CLIMATE_PALETTE.items():
            def on_climate_click(idx, name):
                self.selected_climate_id = idx
                self.on_notification_toast(f"Selected {name}")
            _create_palette_button(
                climate_name,
                climate_id,
                nutil.CLIMATE_ID_MAP,
                climate_palette_buttons,
                on_climate_click
            )

        for temperature_name, temperature_id in nutil.TEMPERATURE_PALETTE.items():
            def on_temperature_click(idx, name):
                self.selected_temperature_id = idx
                self.on_notification_toast(f"Selected {name}")
            _create_palette_button(
                temperature_name,
                temperature_id,
                nutil.TEMPERATURE_ID_MAP,
                temperature_palette_buttons,
                on_temperature_click
            )

        biome_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64, size_hint=(None, 1))
        biome_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=geography_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        political_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64, size_hint=(None, 1))
        political_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=political_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        climate_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64, size_hint=(None, 1))
        climate_palette_choice.add(
            child=arcade.gui.UIImage(
                texture=climate_palette_button_icon,
                width =64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )
        
        temperature_palette_choice = arcade.gui.UIFlatButton(text="", width=64, height=64, size_hint=(None, 1))
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

        self.layer_select_buttons = {}
        selection_text = ">"
        deselection_text = ""

        selected_style = {
            "normal":   arcade.gui.UIFlatButton.UIStyle(bg=(40,150,80,255)),
            "hover":    arcade.gui.UIFlatButton.UIStyle(bg=(50,160,90,255)),
            "press":    arcade.gui.UIFlatButton.UIStyle(bg=(60,170,100,255))
        }
        deselected_style = {
            "normal":   arcade.gui.UIFlatButton.UIStyle(bg=(40,50,80,255)),
            "hover":    arcade.gui.UIFlatButton.UIStyle(bg=(50,60,90,255)),
            "press":    arcade.gui.UIFlatButton.UIStyle(bg=(60,70,100,255))
        }

        def _create_layer_toggle(layer_name, layer_toggle_buttons, texture, visibility_attr):
            wrapper = layer_toggle_buttons.add(
                arcade.gui.UIBoxLayout(vertical=True, space_between=2, size_hint=(0, 1))
            )
            buttons = wrapper.add(
                arcade.gui.UIBoxLayout(vertical=False, space_between=2)
            )
            select = arcade.gui.UIFlatButton(text=deselection_text, width=32, height=32)
            self.layer_select_buttons[layer_name] = select
            toggle = arcade.gui.UIFlatButton(text="", width=64, height=48)
            toggle.add(
                child=arcade.gui.UIImage(
                    texture=texture,
                    width=64,
                    height=64,
                ),
                anchor_x="center",
                anchor_y="center"
            )
            buttons.add(select)
            buttons.add(toggle)

            @toggle.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                self.visibility_flags[layer_name] = not self.visibility_flags[layer_name]

            @select.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                self.selected_layer = layer_name
                for key, btn in self.layer_select_buttons.items():
                    btn.text = deselection_text
                    btn.style = deselected_style
                select.text = selection_text
                select.style = selected_style
                self.on_notification_toast(f"selected {layer_name}")

            label = arcade.gui.UILabel(
                text=layer_name.replace('_', ' ').title(),
                font_size=10,
                align="center",
                height=12
            )
            wrapper.add(label)

        def _create_information_layer_toggle(layer_prefix, layer_toggle_buttons):
            wrapper = layer_toggle_buttons.add(
                arcade.gui.UIBoxLayout(vertical=True, space_between=2, size_hint=(0, 1))
            )
            buttons = wrapper.add(
                arcade.gui.UIBoxLayout(vertical=False, space_between=2)
            )
            select = arcade.gui.UIFlatButton(text=deselection_text, width=32, height=32)
            self.layer_select_buttons[f'{layer_prefix}_information'] = select
            toggle = arcade.gui.UIFlatButton(text="", width=64, height=48)
            toggle.add(
                child=arcade.gui.UIImage(
                    texture=information_layer_button_icon,
                    width=64,
                    height=64,
                ),
                anchor_x="center",
                anchor_y="center"
            )
            buttons.add(select)
            buttons.add(toggle)

            @toggle.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                layer__ = getattr(self, f'{layer_prefix}_information_layer').canvas
                layer__.visible = not layer__.visible
                self.visibility_flags[f'{layer_prefix}_visibility'] = not self.visibility_flags[f'{layer_prefix}_visibility']

            @select.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                layer_name = f'{layer_prefix}_information_layer'
                self.selected_layer = layer_name
                for key, btn in self.layer_select_buttons.items():
                    btn.text = deselection_text
                    btn.style = deselected_style
                select.text = selection_text
                select.style = selected_style
                self.on_notification_toast(f"selected {layer_name}")

            label = arcade.gui.UILabel(
                text=layer_prefix.replace('_', ' ').title(),
                font_size=10,
                align="center",
                height=12
            )
            wrapper.add(label)

        _create_information_layer_toggle('misc4', layer_toggle_buttons)
        _create_information_layer_toggle('misc3', layer_toggle_buttons)
        _create_information_layer_toggle('misc2', layer_toggle_buttons)
        _create_information_layer_toggle('misc1', layer_toggle_buttons)

        _create_information_layer_toggle('civilian', layer_toggle_buttons)
        _create_information_layer_toggle('military', layer_toggle_buttons)

        _create_layer_toggle('political_layer', layer_toggle_buttons, political_layer_button_icon, 'political_visibility')

        for q in range(4, 0, -1):
            temperature_buttons = layer_toggle_buttons.add(
                arcade.gui.UIBoxLayout(vertical=False, space_between=1, size_hint=(1, 1))
            )
            layer_select = arcade.gui.UIFlatButton(text=selection_text, width=32, height=32)
            self.layer_select_buttons[f'temperature_layer_q{q}'] = layer_select
            toggle = arcade.gui.UIFlatButton(text=f"q{q} temp", width=64, height=32)
            temperature_buttons.add(layer_select)
            temperature_buttons.add(toggle)

            @toggle.event
            def on_click(event: arcade.gui.UIOnClickEvent, q=q):
                self.visibility_flags[f'q{q}_temperature_layer'] = not self.visibility_flags[f'q{q}_temperature_layer']

            @layer_select.event
            def on_click(event: arcade.gui.UIOnClickEvent, q=q, select=layer_select):
                self.selected_layer = f'temperature_layer_q{q}'
                for key, btn in self.layer_select_buttons.items():
                    btn.text = deselection_text
                    btn.style = deselected_style
                select.text = selection_text
                select.style = selected_style
                self.on_notification_toast(f"selected temperature q{q} layer")

        # this ddoesnt work ^^^

        _create_layer_toggle('climate_layer', layer_toggle_buttons, climate_layer_button_icon, 'climate_visibility')
        _create_layer_toggle('biome_layer', layer_toggle_buttons, geography_layer_button_icon, 'biome_visibility')

        # --- palette groups
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
        # ---

    def on_notification_toast(self, message:str="", warn:bool=False, error:bool=False, success:bool=False) -> None:
        """
        Displays a toast notification with the given message.

        Args:
            message (str): The message to display in the toast.
            warn (bool): Whether to display a warning toast.
            error (bool): Whether to display an error toast.
            success (bool): Whether to display a success toast.
        """
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
        print(f"I[{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday},{time.localtime().tm_hour}h:{time.localtime().tm_min}m:{time.localtime().tm_sec}s/toast]- {message}")

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
            print("X- no b_s definition? skipping. ! THIS WILL CAUSE SOUTH POLITICAL TO NOT LOAD")

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
            print("O- loaded temperature q1 ...")

            loaded_q2n_grid_data = loaded_data['q2n']
            self.north_temperature_layer_q2.grid[:] = np.reshape(loaded_q2n_grid_data,(600,300))
            loaded_q2s_grid_data = loaded_data['q2s']
            self.south_temperature_layer_q2.grid[:] = np.reshape(loaded_q2s_grid_data,(600,300))
            print("O- loaded temperature q2 ...")

            loaded_q3n_grid_data = loaded_data['q3n']
            self.north_temperature_layer_q3.grid[:] = np.reshape(loaded_q3n_grid_data,(600,300))
            loaded_q3s_grid_data = loaded_data['q3s']
            self.south_temperature_layer_q3.grid[:] = np.reshape(loaded_q3s_grid_data,(600,300))
            print("O- loaded temperature q3 ...")

            loaded_q4n_grid_data = loaded_data['q4n']
            self.north_temperature_layer_q4.grid[:] = np.reshape(loaded_q4n_grid_data,(600,300))
            loaded_q4s_grid_data = loaded_data['q4s']
            self.south_temperature_layer_q4.grid[:] = np.reshape(loaded_q4s_grid_data,(600,300))
            print("O- loaded temperature q4 ...")
        except:
            print("X- temperature layers failed to load. ! THIS WILL CAUSE TEMPERATURE MAPS TO NOT LOAD")

        try:
            civilian_icons_array            = loaded_data['icon_a']
            self.civilian_icons = civilian_icons_array.item()
            military_icons_array            = loaded_data['icon_b']
            self.military_icons = military_icons_array.item()
            misc1_icons_array               = loaded_data['icon_c']
            self.misc1_icons = misc1_icons_array.item()
            misc2_icons_array               = loaded_data['icon_d']
            self.misc2_icons = misc2_icons_array.item()
            misc3_icons_array               = loaded_data['icon_e']
            self.misc3_icons = misc3_icons_array.item()
            misc4_icons_array               = loaded_data['icon_f']
            self.misc4_icons = misc4_icons_array.item()
            print("O- loaded ...")

            loaded_lines = loaded_data['l_civ']
            loaded_lines = loaded_lines.item()
            print(loaded_lines)
            for shape in loaded_lines['shapes']:
                self.civilian_information_layer.add_shape(nutil.Shape(input_shape=shape))
            loaded_lines = loaded_data['l_mil']
            loaded_lines = loaded_lines.item()
            for shape in loaded_lines['shapes']:
                self.military_information_layer.add_shape(nutil.Shape(input_shape=shape))

            loaded_lines = loaded_data['l_1']
            loaded_lines = loaded_lines.item()
            for shape in loaded_lines['shapes']:
                self.misc1_information_layer.add_shape(nutil.Shape(input_shape=shape))
            loaded_lines = loaded_data['l_2']
            loaded_lines = loaded_lines.item()
            for shape in loaded_lines['shapes']:
                self.misc2_information_layer.add_shape(nutil.Shape(input_shape=shape))
            loaded_lines = loaded_data['l_3']
            loaded_lines = loaded_lines.item()
            for shape in loaded_lines['shapes']:
                self.misc3_information_layer.add_shape(nutil.Shape(input_shape=shape))
            loaded_lines = loaded_data['l_4']
            loaded_lines = loaded_lines.item()
            for shape in loaded_lines['shapes']:
                self.misc4_information_layer.add_shape(nutil.Shape(input_shape=shape))

            print("O- loaded ...")
        except:
            print("X- icons and shapes have failed to load.")

        self.setup()

    def on_clicked_save(self):
        # try:
        a_grid = b_grid = c_grid = 0
        a_s_grid = b_s_grid = c_s_grid = 0
        d_grid = d_s_grid = 0
        q1n_grid = q1s_grid = 0
        q2n_grid = q2s_grid = 0 
        q3n_grid = q3s_grid = 0
        q4n_grid = q4s_grid = 0

        if self.export_flags["biome_layer"] == True:
            a_grid = np.frombuffer(self.north_upper_terrain_layer_texture.read(), dtype="u1")
            c_grid = np.frombuffer(self.north_lower_terrain_layer_texture.read(), dtype="u1")

            a_s_grid = np.frombuffer(self.south_upper_terrain_layer_texture.read(), dtype="u1")
            c_s_grid = np.frombuffer(self.south_lower_terrain_layer_texture.read(), dtype="u1")

        if self.export_flags["political_layer"] == True:
            b_grid = np.frombuffer(self.north_political_layer_texture.read(), dtype="u1")
            b_s_grid = np.frombuffer(self.south_political_layer_texture.read(), dtype="u1")

        if self.export_flags["climate_layer"] == True:
            d_grid = np.frombuffer(self.north_climate_layer_texture.read(), dtype="u1")
            d_s_grid = np.frombuffer(self.south_climate_layer_texture.read(), dtype="u1")

        if self.export_flags["q1_temperature_layer"]:
            q1n_grid = np.frombuffer(self.north_temperature_layer_q1_texture.read(), dtype="u1")
            q1s_grid = np.frombuffer(self.north_temperature_layer_q1_texture.read(), dtype="u1")

        if self.export_flags["q2_temperature_layer"]:
            q2n_grid = np.frombuffer(self.north_temperature_layer_q2_texture.read(), dtype="u1")
            q2s_grid = np.frombuffer(self.north_temperature_layer_q2_texture.read(), dtype="u1")

        if self.export_flags["q3_temperature_layer"]:
            q3n_grid = np.frombuffer(self.north_temperature_layer_q3_texture.read(), dtype="u1")
            q3s_grid = np.frombuffer(self.north_temperature_layer_q3_texture.read(), dtype="u1")

        if self.export_flags["q4_temperature_layer"]:
            q4n_grid = np.frombuffer(self.north_temperature_layer_q4_texture.read(), dtype="u1")
            q4s_grid = np.frombuffer(self.north_temperature_layer_q4_texture.read(), dtype="u1")

        def _create_shapes_dict(objects, use_shape_attr=True):
            shapes_dict = {'shapes': []}
            for obj in objects:
                shapes_dict['shapes'].append(obj.shape if use_shape_attr else obj)
            return shapes_dict

        civilian_lines_dict = _create_shapes_dict(self.civilian_information_layer.shapes) if self.export_flags["civilian_layer"] else None
        military_lines_dict = _create_shapes_dict(self.military_information_layer.shapes) if self.export_flags["military_layer"] else None
        misc_lines_1_dict = _create_shapes_dict(self.misc1_information_layer.shapes, False) if self.export_flags["misc1_layer"] else None
        misc_lines_2_dict = _create_shapes_dict(self.misc2_information_layer.shapes, False) if self.export_flags["misc2_layer"] else None
        misc_lines_3_dict = _create_shapes_dict(self.misc3_information_layer.shapes, False) if self.export_flags["misc3_layer"] else None 
        misc_lines_4_dict = _create_shapes_dict(self.misc4_information_layer.shapes, False) if self.export_flags["misc4_layer"] else None

        misc1_information_layer_icon_dict = {'locations': []}
        misc2_information_layer_icon_dict = {'locations': []}
        misc3_information_layer_icon_dict = {'locations': []}
        misc4_information_layer_icon_dict = {'locations': []}
        civilian_information_layer_icon_dict = {'locations': []}
        military_information_layer_icon_dict = {'locations': []}
        layers_to_save = {
            self.misc1_information_layer: misc1_information_layer_icon_dict,
            self.misc2_information_layer: misc2_information_layer_icon_dict,
            self.misc3_information_layer: misc3_information_layer_icon_dict,
            self.misc4_information_layer: misc4_information_layer_icon_dict,
            self.civilian_information_layer: civilian_information_layer_icon_dict,
            self.military_information_layer: military_information_layer_icon_dict
        }

        for layer, dict_ in layers_to_save.items():
            for icon in layer.canvas:
                if isinstance(icon, nutil.Icon.Civilian):
                    dict_['locations'].append({
                        'x': icon.center_x,
                        'y': icon.center_y,
                        'id': icon.icon_id,
                        'unique_id': icon.unique_id,
                        'type': 'civilian'
                    })
                elif isinstance(icon, nutil.Icon.Military):
                    dict_['locations'].append({
                        'x': icon.center_x,
                        'y': icon.center_y,
                        'id': icon.icon_id,
                        'unique_id': icon.unique_id,
                        'country_id': icon.country_id,
                        'angle_rot': icon.angle_rot,
                        'quality': icon.quality,
                        'type': 'military'
                    })

        thumbnail = self.north_political_layer_texture.get_image()
        thumbnail = np.array(thumbnail)

        print("?- trying np.savez_compressed ...")
        timer = time.time()
        np.savez_compressed(f"map_data/galaina_{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday}_{time.localtime().tm_hour}h_{time.localtime().tm_min}m_{time.localtime().tm_sec}s.npz",
                            a=a_grid,
                            b=b_grid,
                            c=c_grid,
                            a_s=a_s_grid,
                            b_s=b_s_grid,
                            c_s=c_s_grid,
                            d=d_grid,
                            d_s=d_s_grid,
                            icon_a=np.array(civilian_information_layer_icon_dict),
                            icon_b=np.array(military_information_layer_icon_dict),
                            icon_c=np.array(misc1_information_layer_icon_dict),
                            icon_d=np.array(misc2_information_layer_icon_dict),
                            icon_e=np.array(misc3_information_layer_icon_dict),
                            icon_f=np.array(misc4_information_layer_icon_dict),
                            l_civ=np.array(civilian_lines_dict),
                            l_mil=np.array(military_lines_dict),
                            l_1=np.array(misc_lines_1_dict),
                            l_2=np.array(misc_lines_2_dict),
                            l_3=np.array(misc_lines_3_dict),
                            l_4=np.array(misc_lines_4_dict),
                            q1n=q1n_grid,
                            q1s=q1s_grid,
                            q2n=q2n_grid,
                            q2s=q2s_grid,
                            q3n=q3n_grid,
                            q3s=q3s_grid,
                            q4n=q4n_grid,
                            q4s=q4s_grid,
                            thumbnail=thumbnail
                            )
        time_taken = time.time()-timer
        self.on_notification_toast(f"O- map has been saved, took: {round(time_taken,3)} s")
        # except Exception as e: 
        #     self.on_notification_toast("Failed to save map ... "+str(e),error=True)

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

    def distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def find_closest_icon(self, clicked_point, radius, icon_lists):
        closest_icon:nutil.Icon = None
        layer_name:arcade.SpriteList = None
        closest_icon_distance = float('inf')
        
        for icon_list in icon_lists:
            for icon in icon_list:
                dist = self.distance(clicked_point, (icon.center_x,icon.center_y))
                if dist < closest_icon_distance:
                    if dist <= radius:
                        closest_icon = icon
                        layer_name = icon_list

        return closest_icon, layer_name

    def find_closest_point(self, clicked_point, shape_lists):
        closest_point = None
        closest_shape = None
        closest_index = -1
        min_dist = float('inf')

        for shape_list in shape_lists:
            for shape in shape_list:
                for idx, point in enumerate(shape.shape):
                    dist = self.distance(clicked_point, point)
                    if dist < min_dist:
                        min_dist = dist
                        closest_point:tuple = point
                        closest_shape:object = shape
                        closest_index:int = idx

        return closest_point, closest_shape, closest_index, min_dist

    def setup(self):
        print("?- loading icons [1/3] ...")
        loaded_icon_layers = [
            (self.misc1_icons, self.misc1_information_layer),
            (self.misc2_icons, self.misc2_information_layer),
            (self.misc3_icons, self.misc3_information_layer),
            (self.misc4_icons, self.misc4_information_layer),
            (self.civilian_icons, self.civilian_information_layer),
            (self.military_icons, self.military_information_layer)
        ]
        for (loaded_data, corresponding_layer) in loaded_icon_layers:
            for icon in loaded_data['locations']:
                icon_type = icon['type']
                if icon_type == 'civilian':
                    icon_path = str(nutil.CIVILIAN_ICON_ID_MAP.get(icon['id'])) + ".png"
                    icon_object = nutil.Icon.Civilian(
                        icon_path, 
                        1, 
                        (icon['x'], icon['y']), 
                        0.0, 
                        icon['id'], 
                        icon['unique_id']
                    )
                elif icon_type == 'military':
                    icon_path = str(nutil.MILITARY_ICON_ID_MAP.get(icon['id'])) + ".png"
                    icon_object = nutil.Icon.Military(
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
                    country_id = int(icon['country_id'])
                    if not country_id == 0:
                        icon_object.color = nutil.POLITICAL_ID_MAP.get(country_id,(255,255,255,255))
                    else:
                        icon_object.color = (255,255,255,255)
                    
                corresponding_layer.add_icon(icon_object)

        timer = time.time()
        north_upper_terrain_layer_data = self.upper_terrain_layer.grid.astype(np.uint8).tobytes()
        north_lower_terrain_layer_data = self.lower_terrain_layer.grid.astype(np.uint8).tobytes()
        north_political_layer_data = self.political_layer.grid.astype(np.uint8).tobytes()

        south_upper_terrain_layer_data = self.s_upper_terrain_layer.grid.astype(np.uint8).tobytes()
        south_lower_terrain_layer_data = self.s_lower_terrain_layer.grid.astype(np.uint8).tobytes()
        south_political_layer_data = self.s_political_layer.grid.astype(np.uint8).tobytes()

        north_climate_layer_data = self.north_climate_layer.grid.astype(np.uint8).tobytes()
        south_climate_layer_data = self.south_climate_layer.grid.astype(np.uint8).tobytes()

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
            if i in nutil.TILE_ID_MAP:
                r, g, b = nutil.TILE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            a = 0 if i == 255 else 255
            terrain_palette_data.append([r, g, b, a])

        for i in range(256):
            if i in nutil.POLITICAL_ID_MAP:
                r, g, b = nutil.POLITICAL_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            political_palette_data.append([r, g, b, 255])

        for i in range(256):
            r, g, b = (0,0,0)
            a = 155 if i == 0 else 0
            political_water_overlay_palette.append([r, g, b, a])

        for i in range(256):
            if i in nutil.CLIMATE_ID_MAP:
                r, g, b = nutil.CLIMATE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            climate_palette_data.append([r, g, b, 155])

        for i in range(256):
            if i in nutil.TEMPERATURE_ID_MAP:
                r, g, b = nutil.TEMPERATURE_ID_MAP[i]
            else:
                r, g, b = (255, 255, 255)
            temperature_palette_data.append([r, g, b, 155])

        terrain_palette_data = np.array(terrain_palette_data, dtype=np.uint8)
        political_palette_data = np.array(political_palette_data, dtype=np.uint8)
        climate_palette_data = np.array(climate_palette_data, dtype=np.uint8)
        temperature_palette_data = np.array(temperature_palette_data, dtype=np.uint8)

        def _create_texture(pos, size, colors, data):
            return cgpu.ColorChunk(pos=pos, ctx=self.ctx, size=size, colors=colors, data=data)

        palette_bytes = {
            'terrain': np.array(terrain_palette_data, dtype=np.uint8).tobytes(),
            'political': np.array(political_palette_data, dtype=np.uint8).tobytes(),
            'political_water': np.array(political_water_overlay_palette, dtype=np.uint8).tobytes(),
            'climate': np.array(climate_palette_data, dtype=np.uint8).tobytes(),
            'temperature': np.array(temperature_palette_data, dtype=np.uint8).tobytes()
        }

        texture_configs = [
            # North
            ('north_upper_terrain_layer_texture', (0,0), (600,300), palette_bytes['terrain'], north_upper_terrain_layer_data),
            ('north_lower_terrain_layer_texture', (0,0), (12000,6000), palette_bytes['terrain'], north_lower_terrain_layer_data),
            ('north_political_layer_texture', (0,0), (600,300), palette_bytes['political'], north_political_layer_data),
            ('north_political_water_overlay_layer_texture', (0,0), (600,300), palette_bytes['political_water'], north_upper_terrain_layer_data),
            ('north_climate_layer_texture', (0,0), (600,300), palette_bytes['climate'], north_climate_layer_data),
            ('north_temperature_layer_q1_texture', (0,0), (600,300), palette_bytes['temperature'], north_temperature_layer_q1_data),
            ('north_temperature_layer_q2_texture', (0,0), (600,300), palette_bytes['temperature'], north_temperature_layer_q2_data),
            ('north_temperature_layer_q3_texture', (0,0), (600,300), palette_bytes['temperature'], north_temperature_layer_q3_data),
            ('north_temperature_layer_q4_texture', (0,0), (600,300), palette_bytes['temperature'], north_temperature_layer_q4_data),
            # South
            ('south_upper_terrain_layer_texture', (0,-6000), (600,300), palette_bytes['terrain'], south_upper_terrain_layer_data),
            ('south_lower_terrain_layer_texture', (0,-6000), (12000,6000), palette_bytes['terrain'], south_lower_terrain_layer_data),
            ('south_political_layer_texture', (0,-6000), (600,300), palette_bytes['political'], south_political_layer_data),
            ('south_political_water_overlay_layer_texture', (0,-6000), (600,300), palette_bytes['political_water'], south_upper_terrain_layer_data),
            ('south_climate_layer_texture', (0,-6000), (600,300), palette_bytes['climate'], south_climate_layer_data),
            ('south_temperature_layer_q1_texture', (0,-6000), (600,300), palette_bytes['temperature'], south_temperature_layer_q1_data),
            ('south_temperature_layer_q2_texture', (0,-6000), (600,300), palette_bytes['temperature'], south_temperature_layer_q2_data),
            ('south_temperature_layer_q3_texture', (0,-6000), (600,300), palette_bytes['temperature'], south_temperature_layer_q3_data),
            ('south_temperature_layer_q4_texture', (0,-6000), (600,300), palette_bytes['temperature'], south_temperature_layer_q4_data),
        ]

        self.created_textures = []

        for attr_name, pos, size, colors, data in texture_configs:
            setattr(self, attr_name, _create_texture(pos, size, colors, data))
            self.created_textures.append(attr_name)

        layers_to_delete = [
            'upper_terrain_layer',
            'lower_terrain_layer', 
            'political_layer',
            's_upper_terrain_layer',
            's_lower_terrain_layer',
            's_political_layer',
            'north_climate_layer',
            'south_climate_layer',
            'north_temperature_layer_q1',
            'north_temperature_layer_q2', 
            'north_temperature_layer_q3',
            'north_temperature_layer_q4',
            'south_temperature_layer_q1',
            'south_temperature_layer_q2',
            'south_temperature_layer_q3',
            'south_temperature_layer_q4'
        ]

        try:
            for layer in layers_to_delete:
                if hasattr(self, layer):
                    delattr(self, layer)
            print("O- freed up as much memory as possible")
        except Exception as e:
            print(f"X- couldn't free up memory: {str(e)}")

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
                nutil.set_attributes('keybinds_disable',True)
                self.keybinds_box.clear()
                self.keybinds_box.visible = False

            print("O- Loaded keybinds popup")
        
        self.has_map_been_loaded = True

    def on_resize(self, width, height):
        self.resized_size = width, height
        self.camera.match_window()
        return super().on_resize(width, height)

    def on_update(self, dt):
        self.uptime += dt
        
        self.camera.position += (self.camera_speed[0]*self.zoomed_speed_mod, self.camera_speed[1]*self.zoomed_speed_mod)
        self.camera.zoom += self.zoom_speed*self.camera.zoom

        self.zoomed_speed_mod = max(self.zoomed_speed_mod+self.zoomed_speed_mod_adder, 0.01)
        self.zoomed_speed_mod = min(self.zoomed_speed_mod, 2.0)

        for layer in self.information_layers:
            for icon in layer.canvas:
                icon.scale = max(1.0-(self.camera.zoom/3),0.05)

    def on_draw(self):
        self.camera.use() 
        self.clear()

        # drawing layers
        with self.ctx.enabled(self.ctx.BLEND):
            if self.has_map_been_loaded:
                if self.visibility_flags['biome_layer'] == True:
                    self.north_upper_terrain_layer_texture.draw(size=(12000,6000))
                    self.south_upper_terrain_layer_texture.draw(size=(12000,6000))
                    if self.camera.zoom >= 1.5:
                        self.north_lower_terrain_layer_texture.draw(size=(12000,6000))
                        self.south_lower_terrain_layer_texture.draw(size=(12000,6000))
            
                if self.visibility_flags['climate_layer'] == True:
                    self.north_climate_layer_texture.draw(size=(12000,6000))
                    self.south_climate_layer_texture.draw(size=(12000,6000))

                for quarter in range(1, 5):
                    if self.visibility_flags[f'q{quarter}_temperature_layer'] == True:
                        getattr(self, f'north_temperature_layer_q{quarter}_texture').draw(size=(12000,6000))
                        getattr(self, f'south_temperature_layer_q{quarter}_texture').draw(size=(12000,6000))

            if self.political_background == True:
                if self.has_map_been_loaded:
                    if self.visibility_flags['political_layer'] == True:
                        self.north_political_layer_texture.draw(size=(12000,6000))
                        self.south_political_layer_texture.draw(size=(12000,6000))
                        self.north_political_water_overlay_layer_texture.draw(size=(12000,6000))
                        self.south_political_water_overlay_layer_texture.draw(size=(12000,6000))

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

        lines_config = {
            'misc1_layer': (self.visibility_flags['misc1_layer'], self.misc1_information_layer.shapes, (255,255,255,255)),
            'misc2_layer': (self.visibility_flags['misc2_layer'], self.misc2_information_layer.shapes, (255,255,255,255)),
            'misc3_layer': (self.visibility_flags['misc3_layer'], self.misc3_information_layer.shapes, (255,255,255,255)),
            'misc4_layer': (self.visibility_flags['misc4_layer'], self.misc4_information_layer.shapes, (255,255,255,255)),
            'civilian_layer': (self.visibility_flags['civilian_layer'], self.civilian_information_layer.shapes, (100,100,255,255)),
            'military_layer': (self.visibility_flags['military_layer'], self.military_information_layer.shapes, (255,100,100,255))
        }

        for layer_name, (visibility, shapes, color) in lines_config.items():
            if visibility:
                for shape_object in shapes:
                    if shape_object.shape:
                        arcade.draw_line_strip(shape_object.shape, color, 1.25)

        self.misc1_information_layer.canvas.draw(pixelated=True)
        self.misc2_information_layer.canvas.draw(pixelated=True)
        self.misc3_information_layer.canvas.draw(pixelated=True)
        self.misc4_information_layer.canvas.draw(pixelated=True)
        self.civilian_information_layer.canvas.draw(pixelated=True)
        self.military_information_layer.canvas.draw(pixelated=True)

        if self.current_shape:
            arcade.draw_line_strip(self.current_shape,(255,0,255,100),2)

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
                brushes = nutil.get_all_files('local_data/brushes')
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

        # dev tools
        if symbol == arcade.key.NUM_7:
            for layer in self.information_layers:
                layer.canvas.clear()
            self.on_notification_toast("all icons have been removed", warn=True)
        if symbol == arcade.key.NUM_8:
            try:
                start_time = time.time()
                # loop through all icons and check if there's duplicates, delete if so
                for layer in self.information_layers:
                    for icon in layer.canvas:
                        # find duplicate ids
                        for icon2 in layer.canvas:
                            if icon.unique_id == icon2.unique_id:
                                if icon != icon2:
                                    layer.canvas.remove(icon2)
                                    self.on_notification_toast(f"Removed duplicate icon with unique_id {icon.unique_id} ...", success=True)
                        icon.unique_id = icon.unique_id+1
                end_time = time.time()
                print(f"O- found {self.information_layers.__len__()} layers, {self.information_layers[0].canvas.__len__()} icons in {round(end_time-start_time,3)} seconds")
            except Exception as e:
                self.on_notification_toast(f"Error: {e}", error=True)
        if symbol == arcade.key.NUM_9:
            # wiping the data from the selected layer's fbo
            for attr_name in self.created_textures:
                getattr(self, attr_name).clear()

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
        layer_map = {
            'civilian_information_layer': self.civilian_information_layer,
            'military_information_layer': self.military_information_layer,
            'misc4_information_layer': self.misc4_information_layer,
            'misc3_information_layer': self.misc3_information_layer, 
            'misc2_information_layer': self.misc2_information_layer,
            'misc1_information_layer': self.misc1_information_layer
        }
        if button is arcade.MOUSE_BUTTON_RIGHT:
            if self.selected_icon_id or self.selected_icon_id == 0:
                self.selected_icon_id = None
                self.on_notification_toast("Deselected icon id.", warn=True)
        
            if self.current_shape:
                self.last_pressed_line_point = None
                self.final_shape = self.current_shape[:]
                self.current_shape = []

                if self.selected_layer in layer_map:
                    layer_map[self.selected_layer].shapes.append(nutil.Shape(self.final_shape))
                    self.on_notification_toast(f"Added shape to {self.selected_layer}")
                else:
                    self.on_notification_toast("No layer selected for shape", warn=True)
                
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

            try:
                all_shape_lists = [
                    self.misc1_information_layer.shapes,
                    self.misc2_information_layer.shapes,
                    self.misc3_information_layer.shapes,
                    self.misc4_information_layer.shapes,
                    self.civilian_information_layer.shapes,
                    self.military_information_layer.shapes
                ]
                closest_point, closest_shape, index, dist = self.find_closest_point((self.last_pressed_world[0],self.last_pressed_world[1]), all_shape_lists)
            except:
                pass
                # if it didn't find anything, just fuhgeddaboudit

            if self.editing_mode == True:
                pass
            else:
                if self.selected_line_tool:
                    self.last_pressed_line_point = (world_x,world_y)
                    clicked_point = (world_x,world_y)
                    self.current_shape.append(clicked_point)
                elif self.selected_remove_line_tool:
                    if closest_shape:
                        if dist <= 16.0:
                            print(f"{closest_shape}\nclosest_point {closest_point} at index {index}, with a distance of={dist}")
                            if len(closest_shape.shape) <= 2:
                                closest_shape.shape.clear()
                                del closest_shape
                                print(f"I- removed full shape since there were less than 2 points")
                            else:
                                closest_shape.shape.pop(index)
                                print(f"O- popped point in shape")
                else:
                    if self.selected_icon_id or self.selected_icon_id == 0:
                        if self.selected_icon_type == 'civilian':
                            icon_path = str(nutil.CIVILIAN_ICON_ID_MAP.get(self.selected_icon_id))+".png"
                            generated_unique_id:int = random.randrange(1000,9999)
                            icon = nutil.Icon.Civilian(icon_path,1,(world_x,world_y),0.0,self.selected_icon_id,generated_unique_id)
                            layer_map[self.selected_layer].add_icon(icon)
                        if self.selected_icon_type == 'military':
                            icon_path = str(nutil.MILITARY_ICON_ID_MAP.get(self.selected_icon_id))+".png"
                            generated_unique_id:int = random.randrange(1000,9999)
                            icon = nutil.Icon.Military(icon_path,1,(world_x,world_y),0.0,self.selected_icon_id,generated_unique_id,0,0.0)
                            layer_map[self.selected_layer].add_icon(icon)

                    layers_to_check = [
                        self.civilian_information_layer.canvas,
                        self.military_information_layer.canvas,
                        self.misc4_information_layer.canvas,
                        self.misc3_information_layer.canvas,
                        self.misc2_information_layer.canvas,
                        self.misc1_information_layer.canvas
                    ]
                    nearby_icon, icon_layer = self.find_closest_icon((world_x,world_y),24,layers_to_check)
                    if nearby_icon:
                        self.selected_world_icon = nearby_icon
                        self.selected_icon_edit_box.clear()
                        move_button_icon            = arcade.load_texture("icons/move_icon.png")
                        remove_button_icon          = arcade.load_texture("icons/remove_icon.png")
                        rotate_button_icon          = arcade.load_texture("icons/rotate_icon.png")
                        rotate_reset_button_icon    = arcade.load_texture("icons/rotate_reset_icon.png")
                        up_button_icon              = arcade.load_texture("icons/up_icon.png")
                        down_button_icon            = arcade.load_texture("icons/down_icon.png")
                        change_nation_icon          = arcade.load_texture("icons/pol_palette_icon.png")
                        remove_nation_icon          = arcade.load_texture("icons/pol_remove_icon.png")

                        if isinstance(nearby_icon,nutil.Icon.Military):
                            self.selected_icon_edit_box_label = self.selected_icon_edit_box.add(
                                child=arcade.gui.UILabel(
                                    text=f"quality: {self.selected_world_icon.quality}; unique_id: {self.selected_world_icon.unique_id};",
                                    font_size=12,
                                )
                            )

                        def update_label():
                            self.selected_icon_edit_box_label.text = f"quality: {self.selected_world_icon.quality}; unique_id: {self.selected_world_icon.unique_id};"

                        self.selected_icon_edit_box_buttons = self.selected_icon_edit_box.add(
                            child=arcade.gui.UIBoxLayout(
                                vertical=False,
                                space=1
                            )
                        )

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

                        nation_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                        nation_button.add(
                            child=arcade.gui.UIImage(
                                texture=change_nation_icon,
                                width =64,
                                height=64,
                            ),
                            anchor_x="center",
                            anchor_y="center"
                        )

                        reset_nation_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                        reset_nation_button.add(
                            child=arcade.gui.UIImage(
                                texture=remove_nation_icon,
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
                                update_label()
                            else:
                                self.on_notification_toast(f"icon is already at {nearby_icon.quality} !",error=True)

                        @upgrade_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            if nearby_icon.quality < 5:
                                nearby_icon.quality += 1
                                self.on_notification_toast("upgraded icon")
                                update_label()
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
                            icon_layer.remove(nearby_icon)
                            self.selected_icon_edit_box.clear()
                            self.selected_world_icon = None
                            self.on_notification_toast("Successfully removed icon.", success=True)

                        @nation_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            nearby_icon.color = nutil.POLITICAL_ID_MAP.get(self.selected_country_id,(255,255,255,255))
                            nearby_icon.country_id = self.selected_country_id
                            self.on_notification_toast(f"Successfully changed icon to {self.selected_country_id}")

                        @reset_nation_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            nearby_icon.color = (255,255,255,255)
                            nearby_icon.country_id = 0
                            self.on_notification_toast(f"Successfully removed country color")

                        self.selected_icon_edit_box_buttons.add(move_button)
                        self.selected_icon_edit_box_buttons.add(remove_button)
                        self.selected_icon_edit_box_buttons.add(rotate_button)
                        self.selected_icon_edit_box_buttons.add(rotate_reset_button)
                        if isinstance(self.selected_world_icon,nutil.Icon.Military):
                            self.selected_icon_edit_box_buttons.add(upgrade_button)
                            self.selected_icon_edit_box_buttons.add(downgrade_button)
                            self.selected_icon_edit_box_buttons.add(nation_button)
                            self.selected_icon_edit_box_buttons.add(reset_nation_button)
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
                                coordinates = nutil.generate_blob_coordinates(self.editing_mode_size,self.editing_mode_size)
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
                                coordinates = nutil.get_pixel_coordinates(self.selected_brush)
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
                    if self.selected_world_icon:
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
    