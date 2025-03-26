import itertools
import arcade
import arcade.gui
import arcade.gui.widgets
import math
import numpy as np
import threading
import queue
import random
import nation_utils as na
import time
import multiprocessing
# display settings; ts pmo fr rn
WIDTH, HEIGHT = 1920, 1080
SCREEN_SIZE = (WIDTH, HEIGHT)
RESIZED_SIZE = 1920, 1080

if __name__ == "__main__":
    print("?- checking for imagefiles ...")
    try:
        geographic_icon = arcade.load_texture("icons/geo_map_icon.png")
        political_icon = arcade.load_texture("icons/pol_map_icon.png")
        information_icon = arcade.load_texture("icons/inf_map_icon.png")
        geographic_palette_icon = arcade.load_texture("icons/geo_palette_icon.png")
        political_palette_icon = arcade.load_texture("icons/pol_palette_icon.png")
        print("O- imagefiles found and loaded")
    except:
        print(f"X- {Exception}: imagefiles not found")

    # precomputed_terrain_colors = np.array([
    #     na.TERRAIN_ID_MAP.get(i, (255, 255, 255)) for i in range(256)
    # ])
    # precomputed_political_colors = np.array([
    #     na.POLITICAL_ID_MAP.get(i, (53, 53, 53)) for i in range(256)
    # ])


# ---


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)
        print("?- initializing camera ...")
        self.camera = arcade.camera.Camera2D()
        self.camera.position = (0, 0)
        print("O- set up camera")
        print("?- initializing other variables ...")
        self.resized_size = 1920, 1080
        self.camera_speed = 0.0, 0.0
        self.zoomed_speed_mod_adder = 0.0
        self.zoomed_speed_mod = 1.0
        self.zoom_speed = 0.0
        self.terrain_scene = None
        self.last_pressed_screen = None
        self.last_pressed_world = None
        self.current_position_screen = None
        self.current_position_world = None
        self.selection_rectangle_size = 1
        self.last_interacted_tile = None
        self.political_background = True
        self.selected_lower_id = 0
        self.selected_country_id = 0
        self.editing_mode = False
        self.editing_mode_size = 4
        self.selected_brush = None

        self.previous_angle = 0

        self.selected_icon_id = None
        self.selected_world_icon = None
        self.moving_the_icon = False
        self.rotating_the_icon = False

        self.selected_line = None
        self.drawing_line_start = None
        self.drawing_line_end = None
        print("O- variables set up")

        print("?- setting up view layers ...")
        self.terrain_scene = arcade.Scene()
        print("[1/3]:self.terrain_scene")
        self.political_scene = arcade.Scene()
        print("[2/3]:self.political_scene")
        self.info_scene = arcade.Scene()
        print("[3/3]:self.info_scene")
        print("O- view layers set up")

        print("?- setting up loader queues ...")
        self.chunk_request_queue = queue.Queue()
        self.chunk_result_queue = queue.Queue()
        self.requested_chunks = set()
        print("O- request and result queues set up")

        print("?- setting up terrain spritelists ...")
        self.terrain_scene.add_sprite_list("0")
        print("[1/3]:self.terrain_scene 0")
        self.terrain_scene.add_sprite_list("1")
        print("[2/3]:self.terrain_scene 1")
        self.terrain_scene.add_sprite_list("2")
        print("[3/3]:self.terrain_scene 2")
        print("O- terrain spritelists set up")

        print("?- setting up info spritelists ...")
        self.info_scene.add_sprite_list("0")
        print("[1/1]:self.info_scene 0")
        self.info_scene_list = []
        print("O- info spritelists set up")

        print("?- setting up political spritelists ...")
        self.political_scene.add_sprite_list("0")
        print("[1/1]:self.political_scene 0")
        print("O- political spritelists set up")

        print("?- setting up UI manager ...")
        self.ui = arcade.gui.UIManager()
        self.ui.enable()
        print("O- UI manager successfully initialized")

        # < - DEFINING GRIDS FOR ALL LAYERS #GRIDS
        print("?- setting up grid layers ...")
        self.political_layer = na.GridLayer((600, 300), 20)
        print("[1/5]:self.political_layer")
        self.upper_terrain_layer = na.GridLayer((600, 300), 20)
        print("[2/5]:self.upper_terrain_layer")
        self.lower_terrain_layer = na.GridLayer((12000, 6000), 1)
        print("[3/5]:self.lower_terrain_layer")

        self.s_political_layer = na.GridLayer((600, 300), 20)
        print("[4/5]:self.s_political_layer")
        self.s_upper_terrain_layer = na.GridLayer((600, 300), 20)
        print("[5/5]:self.s_upper_terrain_layer")
        self.icons = {
            'locations': [],
            'lines': []
        }
        print("O- grids set up / icons dict initialized")

        keybinds_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.keybinds_box = keybinds_anchor.add(arcade.gui.UIBoxLayout(space_between=0), anchor_x="center", anchor_y="center")
        self.is_keybind_box_disabled = False

        load_menu_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.load_menu_buttons = load_menu_anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="center", anchor_y="center")
        savefiles = na.get_all_files('map_data')

        attributes_data = na.get_attributes()
        self.is_keybind_box_disabled = attributes_data['keybinds_disable']

        if savefiles:
            for i, savefile in enumerate(savefiles):
                save_file_button = arcade.gui.UIFlatButton(width=300, height=64, text=f"{savefile}")

                self.load_menu_buttons.add(save_file_button)

                @save_file_button.event
                def on_click(event: arcade.gui.UIOnClickEvent, savename=savefile, index=i):
                    self.on_clicked_load(savename)
                    self.load_menu_buttons.clear()
        else:
            print("I- NO MAPS WERE FOUND / LOADING DEFAULT ...")
            self.on_clicked_load('local_data/default_mapdata.npz')

        anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.toasts = anchor.add(arcade.gui.UIBoxLayout(space_between=2), anchor_x="left", anchor_y="top")
        self.toasts.with_padding(all=10)

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
            ).with_background(color=arcade.types.Color(10, 10, 10, 255)).with_border(color=arcade.types.Color(30, 30, 30, 255)),
            anchor_x="center",
            anchor_y="center"
        )

        self.mouse_brush_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.brush_menu_options = self.mouse_brush_anchor.add(
            arcade.gui.UIGridLayout(
                column_count=10,
                row_count=10,
                vertical_spacing=1,
                horizontal_spacing=1
            ).with_background(color=arcade.types.Color(10, 10, 10, 255)).with_border(color=arcade.types.Color(30, 30, 30, 255)),
            anchor_x="center",
            anchor_y="center"
        )

        icon_names = [
            "village", "town", "city", "metro", "outpost",
            "keep", "fortress", "bastion", "note", "line",
            "raft", "cog", "yawl", "brig", "corvette",
            "frigate", "cruiser", "battleship", "dreadnought", "carrier",
            "artillery", "cavarly", "heavy artillery", "heavy cavalry", "heavy infantry",
            "infantry", "ranged cavalry", "ranged infantry", "skirmishers"
        ]

        self.brush_buttons = []

        self.buttons = []
        for idx, name in enumerate(icon_names):
            icon_texture = arcade.load_texture(f"{na.ICON_ID_MAP.get(idx)}.png")
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

        layer_buttons = anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=4),
            anchor_x="right",
            anchor_y="top"
        )

        bottom_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        biome_palette_buttons = bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
            ).with_background(color=arcade.types.Color(30, 30, 30, 255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        country_palette_buttons = bottom_anchor.add(
            arcade.gui.UIBoxLayout(
                vertical=False
            ).with_background(color=arcade.types.Color(30, 30, 30, 255)),
            anchor_x="center",
            anchor_y="bottom"
        )
        biome_palette_buttons.visible = False
        country_palette_buttons.visible = False

        center_anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.popupmenu_buttons = center_anchor.add(
            arcade.gui.UIBoxLayout(vertical=True, space_between=4),
            anchor_x="center",
            anchor_y="center"
        )
        self.popupmenu_buttons.visible = False

        save_button = arcade.gui.UIFlatButton(width=200, height=64, text="Save map")

        @save_button.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            self.on_clicked_save()
        self.popupmenu_buttons.add(save_button)

        for i, (biome_name, biome_id) in enumerate(na.BIOME_PALETTE.items()):
            rgb = na.TERRAIN_ID_MAP.get(biome_id, 0)
            rgba = rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32, width=32, style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3])),
                "hover": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5, rgba[1]+5, rgba[2]+5, rgba[3])),
                "press": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3]-50))
            })
            biome_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=biome_id, name=biome_name):
                self.selected_lower_id = idx
                self.on_notification_toast(f"Selected {name}")

        for i, (country_owner, country_id) in enumerate(na.COUNTRY_PALETTE.items()):
            rgb = na.POLITICAL_ID_MAP.get(country_id, 0)
            rgba = rgb + (255,)
            button = arcade.gui.UIFlatButton(height=32, width=32, style={
                "normal": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3])),
                "hover": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0]+5, rgba[1]+5, rgba[2]+5, rgba[3])),
                "press": arcade.gui.UIFlatButton.UIStyle(bg=(rgba[0], rgba[1], rgba[2], rgba[3]-50))
            })
            country_palette_buttons.add(button)

            @button.event
            def on_click(event: arcade.gui.UIOnClickEvent, idx=country_id, name=country_owner):
                self.selected_country_id = idx
                self.on_notification_toast(f"Selected {name}")

        biome_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        biome_toggle.add(
            child=arcade.gui.UIImage(
                texture=geographic_icon,
                width=64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        political_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        political_toggle.add(
            child=arcade.gui.UIImage(
                texture=political_icon,
                width=64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        information_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        information_toggle.add(
            child=arcade.gui.UIImage(
                texture=information_icon,
                width=64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        biome_palette_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        biome_palette_toggle.add(
            child=arcade.gui.UIImage(
                texture=geographic_palette_icon,
                width=64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        political_palette_toggle = arcade.gui.UIFlatButton(text="", width=64, height=64)
        political_palette_toggle.add(
            child=arcade.gui.UIImage(
                texture=political_palette_icon,
                width=64,
                height=64,
            ),
            anchor_x="center",
            anchor_y="center"
        )

        @biome_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            print("Biome toggled")
            abc = self.terrain_scene.get_sprite_list("1")
            if abc.visible == True:
                abc.visible = False
            else:
                abc.visible = True

        @political_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            print("Political toggled")
            abc = self.political_scene.get_sprite_list("0")
            if abc.visible == True:
                abc.visible = False
                self.political_background = False
            else:
                abc.visible = True
                self.political_background = True

        @information_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            bcd = self.info_scene.get_sprite_list("0")
            if bcd.visible == True:
                bcd.visible = False
            else:
                bcd.visible = True

        @biome_palette_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            if country_palette_buttons.visible == True:
                country_palette_buttons.visible = False
                biome_palette_buttons.visible = True
            else:
                biome_palette_buttons.visible = not biome_palette_buttons.visible

        @political_palette_toggle.event
        def on_click(event: arcade.gui.UIOnClickEvent):
            if biome_palette_buttons.visible == True:
                biome_palette_buttons.visible = False
                country_palette_buttons.visible = True
            else:
                country_palette_buttons.visible = not country_palette_buttons.visible

        layer_buttons.add(information_toggle)
        layer_buttons.add(political_toggle)
        layer_buttons.add(biome_toggle)
        layer_buttons.add(biome_palette_toggle)
        layer_buttons.add(political_palette_toggle)

    def on_notification_toast(self, message: str = "", warn: bool = False, error: bool = False, success: bool = False):
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
        print(f"I- toast : {message}")

    def on_clicked_load(self, filename: str):
        loaded_data = np.load(filename, allow_pickle=True)
        print(f"I- loading {filename}")
        loaded_a_data = loaded_data['a']
        self.upper_terrain_layer.grid[:] = loaded_a_data

        loaded_b_data = loaded_data['b']
        self.political_layer.grid[:] = loaded_b_data

        loaded_c_data = loaded_data['c']
        self.lower_terrain_layer.grid[:] = loaded_c_data

        loaded_a_s_data = loaded_data['a_s']
        self.s_upper_terrain_layer.grid[:] = loaded_a_s_data

        loaded_b_s_data = loaded_data['b_s']
        self.s_political_layer.grid[:] = loaded_b_s_data

        icons_array = loaded_data['cc']
        self.icons = icons_array.item()

        self.setup()

    def on_clicked_save(self):
        try:
            self.on_notification_toast("Trying to save map ...")
            a_grid = np.empty((600, 300), dtype=np.uint8)
            a_grid = np.empty((600, 300), dtype=np.uint8)
            c_grid = np.empty((12000, 6000), dtype=np.uint8)

            def extract_id(cell):
                return cell.id_ if isinstance(cell, na.Tile) else cell

            def extract_country_id(cell):
                return cell.id_ if isinstance(cell, na.Tile) else cell

            extract_attribute_biome = np.vectorize(extract_id, otypes=[np.uint8])
            extract_attribute_country = np.vectorize(extract_country_id, otypes=[np.uint8])
            a_grid = extract_attribute_biome(self.upper_terrain_layer.grid)
            b_grid = extract_attribute_country(self.political_layer.grid)
            c_grid = extract_attribute_biome(self.lower_terrain_layer.grid)

            a_s_grid = extract_attribute_biome(self.s_upper_terrain_layer.grid)
            b_s_grid = extract_attribute_country(self.s_political_layer.grid)
            np.savez_compressed(f"map_data/{time.localtime().tm_year}_{time.localtime().tm_mon}_{time.localtime().tm_mday}_{time.localtime().tm_hour}_{time.localtime().tm_min}_{time.localtime().tm_sec}.npz",
                                a=a_grid,
                                b=b_grid,
                                c=c_grid,
                                a_s=a_s_grid,
                                b_s=b_s_grid,
                                cc=np.array(self.icons)
                                )
            self.on_notification_toast(f"{type(self.lower_terrain_layer.grid)}", warn=True)
            self.on_notification_toast(f"{type(self.upper_terrain_layer.grid)}", warn=True)
            self.on_notification_toast(f"{type(self.political_layer.grid)}", warn=True)
            self.on_notification_toast(f"{type(self.s_upper_terrain_layer.grid)}", warn=True)
            self.on_notification_toast(f"{type(self.s_political_layer.grid)}", warn=True)
            self.on_notification_toast("Saved map ...")
        except Exception as e:
            self.on_notification_toast("Failed to save map ... "+str(e), error=True)

    def background_loader(self, chunk_queue, result_queue, grid):
        while True:
            chunk_position = chunk_queue.get()
            if chunk_position is None:
                break

            tilex, tiley = chunk_position
            returned_spritelist = self.load_chunk(tilex, tiley, 20, grid)

            # Add to result queue
            result_queue.put((tilex, tiley, returned_spritelist))
            chunk_queue.task_done()

    def load_chunk(self, tilex: int, tiley: int, tiles_per_chunk: int, grid) -> list:
        chunk_spritelist = []
        chunk_data = np.zeros((tiles_per_chunk, tiles_per_chunk), dtype=np.uint8)
        for _x_ in range(tiles_per_chunk):
            for _y_ in range(tiles_per_chunk):
                chunk_data[_x_][_y_] = grid[_x_+tilex*tiles_per_chunk][_y_+tiley*tiles_per_chunk]

        for x in range(tiles_per_chunk):
            for y in range(tiles_per_chunk):
                try:
                    id_ = chunk_data[x][y]
                    world_x = x+tilex*20
                    world_y = y+tiley*20
                    if id_ == 255:
                        pixel_rgba = (0, 0, 0, 0)
                    else:
                        pixel_rgba = na.TERRAIN_ID_MAP.get(id_, (0, 0, 0)) + (255,)

                    tile = na.Tile(1, 1, world_x-9.5, world_y-9.5, pixel_rgba, id_)
                    chunk_spritelist.append(tile)

                    grid[world_x][world_y] = tile

                except IndexError:
                    print(f"Warning: Chunk ({tilex}, {tiley}) has missing data at ({x}, {y})")

        return chunk_spritelist

    def process_completed_chunks(self):
        try:
            for _ in range(1):
                if self.chunk_result_queue.empty():
                    break

                tilex, tiley, received_sprite_list = self.chunk_result_queue.get()

                for tile in received_sprite_list:
                    self.terrain_scene.add_sprite("2", tile)

                self.chunk_result_queue.task_done()

        except queue.Empty:
            pass

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

    def setup(self):
        print("?- loading icons [1/3] ...")
        for icon in self.icons['locations']:
            icon_path = str(na.ICON_ID_MAP.get(icon['id'])) + ".png"
            icon_object = na.Icon(
                icon_path, 1,
                icon['x'], icon['y'],
                0.0, icon['id'],
                icon['angle_rot'],
                icon['unique_id'],
                icon['country_id'],
                icon['quality']
            )
            icon_object.angle = icon['angle_rot']
            self.info_scene.add_sprite("0", icon_object)
            self.info_scene_list.append(icon_object)

        # --- generating the hemispheres

        x_start = 0
        x_end = 600
        y_start = 0
        y_end = 300

        # Begin numpy jiu jitsu

        terrain_alpha = np.where(self.upper_terrain_layer.grid == 0, 0, 255)
        political_alpha = np.where(self.upper_terrain_layer.grid == 0, 100, 255)

        y, x = np.meshgrid(np.arange(y_start, y_end), np.arange(x_start, x_end))
        world_x = x*20
        world_y = y*20

        # breakpoint()

        argument_stack = np.stack((x, y, world_x, world_y, self.upper_terrain_layer.grid, self.political_layer.grid, terrain_alpha, political_alpha), axis=-1)
        arguments = argument_stack.reshape(-1, argument_stack.shape[2])

        t1 = time.time()
        for arg in arguments:
            tile, political_tile, x, y = na.compute_tiles_2(*arg)
            self.terrain_scene.add_sprite("1", tile)
            self.political_scene.add_sprite("0", political_tile)
            self.lower_terrain_layer.grid[x][y] = tile
            self.political_layer.grid[x][y] = political_tile
        print(f"Singled threaded time:{(time.time()-t1):.2f}s")

        # t2 = time.time()
        # with multiprocessing.Pool(processes=4) as pool:

        #     data = pool.starmap(na.compute_tiles_2, arguments)

        # for datum in data:
        #     tile, political_tile, y, x = datum
        #     self.terrain_scene.add_sprite("1", tile)
        #     self.political_scene.add_sprite("0", political_tile)
        #     self.lower_terrain_layer.grid[x][y] = tile
        #     self.political_layer.grid[x][y] = political_tile

        # print(f"Multithreaded time:{(time.time()-t2):.2f}s")

        # adding south map loading later idfk

        def _create_keybind_label(text):
            return arcade.gui.UITextArea(
                text=text,
                width=200,
                height=20,
                font_size=10
            ).with_background(color=arcade.types.Color(10, 10, 10, 255)).with_border(width=1, color=arcade.types.Color(30, 30, 30, 255))
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
            self.keybinds_box.add(_create_keybind_label("[ P ] - Show brushes menu"))
            self.keybinds_box.add(_create_keybind_label("[ E ] - Toggle icons menu"))

            close_keybinds_button = arcade.gui.UIFlatButton(width=200, height=20, text="Close").with_background(color=arcade.types.Color(25, 25, 25, 255)).with_border(width=1, color=arcade.types.Color(30, 30, 30, 255))
            self.keybinds_box.add(close_keybinds_button)

            @close_keybinds_button.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                self.keybinds_box.clear()
                self.keybinds_box.visible = False

            toggle_keybinds_attribute = arcade.gui.UIFlatButton(width=200, height=20, text="Don't show again").with_background(color=arcade.types.Color(25, 25, 25, 255)).with_border(width=1, color=arcade.types.Color(30, 30, 30, 255))
            self.keybinds_box.add(toggle_keybinds_attribute)

            @toggle_keybinds_attribute.event
            def on_click(event: arcade.gui.UIOnClickEvent):
                na.set_attributes('keybinds_disable', True)
                self.keybinds_box.clear()
                self.keybinds_box.visible = False

            print("O- Loaded keybinds popup")

        loader_thread = threading.Thread(
            target=self.background_loader,
            args=(self.chunk_request_queue, self.chunk_result_queue, self.lower_terrain_layer.grid),
            daemon=True
        )
        print(f"?- Starting background thread : {loader_thread.name}")
        loader_thread.start()
        print(f"O- Started backgroun thread : {loader_thread.name}")

    def on_resize(self, width, height):
        self.resized_size = width, height
        print(f"resized {width} and {height}")
        return super().on_resize(width, height)

    def on_update(self, dt):
        self.camera.position += (self.camera_speed[0]*self.zoomed_speed_mod, self.camera_speed[1]*self.zoomed_speed_mod)

        self.camera.zoom += self.zoom_speed*self.camera.zoom

        self.zoomed_speed_mod = max(self.zoomed_speed_mod+self.zoomed_speed_mod_adder, 0.01)
        self.zoomed_speed_mod = min(self.zoomed_speed_mod, 2.0)

        abd = self.terrain_scene.get_sprite_list("1")

        if self.camera.zoom > 2.5:
            if abd.visible == True:
                low_terrain = self.terrain_scene.get_sprite_list("2")
                low_terrain.visible = True
            else:
                low_terrain = self.terrain_scene.get_sprite_list("2")
                low_terrain.visible = False

            list_of_chunks = []
            for a in range(6):
                for b in range(6):
                    camera_tile = (round(((self.camera.position.x/20)+a)-3), round(((self.camera.position.y/20)+b)-3))
                    if not (camera_tile[0], camera_tile[1]) in self.requested_chunks:
                        list_of_chunks.append((camera_tile[0], camera_tile[1]))
                        self.requested_chunks.add((camera_tile[0], camera_tile[1]))

            for chunk in list_of_chunks:
                self.chunk_request_queue.put(chunk)

            list_of_chunks.clear()
        else:
            low_terrain = self.terrain_scene.get_sprite_list("2")
            low_terrain.visible = False

        self.process_completed_chunks()

        for icon in self.info_scene_list:
            icon.scale = max(1.0-(self.camera.zoom/3), 0.05)
            icon.color = na.QUALITY_COLOR_MAP.get(icon.quality, (255, 0, 0, 255))

    def on_draw(self):
        self.camera.use()
        self.clear()
        arcade.draw_lbwh_rectangle_filled(-10, -10, 12000, 6000, (0, 0, 127, 255))
        arcade.draw_lbwh_rectangle_filled(-10, -10, 12000, -6000, (0, 0, 127, 255))
        self.terrain_scene.draw(pixelated=True)

        if self.political_background == True:
            arcade.draw_lbwh_rectangle_filled(-10, -10, 12000, 6000, (0, 0, 0, 255))
            arcade.draw_lbwh_rectangle_filled(-10, -10, 12000, -6000, (0, 0, 0, 255))

        arcade.draw_line(-10, -10, 12000, -10, (80, 80, 80), 2)

        self.political_scene.draw(pixelated=True)

        for start, end in self.icons['lines']:
            arcade.draw_line(start[0], start[1], end[0], end[1], (255, 0, 0, 255), line_width=0.1)

        if self.current_position_world:
            if self.drawing_line_start and self.drawing_line_end is None:
                arcade.draw_line(self.drawing_line_start[0], self.drawing_line_start[1], self.current_position_world[0], self.current_position_world[1], (255, 0, 0, 255), line_width=2)

        self.info_scene.draw(pixelated=True)

        if self.selected_world_icon:
            if self.rotating_the_icon:
                arcade.draw_circle_outline(self.selected_world_icon.position[0], self.selected_world_icon.position[1], max(32-(self.camera.zoom*3), 4), (255, 255, 255, 255), 1, 0, 12)
            elif self.moving_the_icon:
                arcade.draw_circle_outline(self.selected_world_icon.position[0], self.selected_world_icon.position[1], max(32-(self.camera.zoom*3), 4), (255, 255, 255, 255), 1, 0, 4)
            else:
                arcade.draw_circle_outline(self.selected_world_icon.position[0], self.selected_world_icon.position[1], max(32-(self.camera.zoom*3), 4), (255, 255, 255, 255), 1, 0, 6)

        if self.selected_line:
            arcade.draw_lbwh_rectangle_outline(self.selected_line[0]-2, self.selected_line[1]-2, 4, 4, (255, 255, 255, 255), 0.1)

        if self.current_position_world:
            if self.editing_mode == True:
                if self.camera.zoom >= 2.5:
                    crosshair_size = (self.editing_mode_size/8)
                    crosshair_sprite = arcade.Sprite("icons/crosshair.png", (crosshair_size, crosshair_size), self.current_position_world[0], self.current_position_world[1], 0)
                    arcade.draw_sprite(crosshair_sprite, pixelated=True)
                    arcade.draw_lrbt_rectangle_outline(round(self.current_position_world[0]-0.5), round(self.current_position_world[0]+0.5),
                                                       round(self.current_position_world[1]-0.5), round(self.current_position_world[1]+0.5), color=(255, 255, 255, 255), border_width=0.1)
                else:
                    arcade.draw_lbwh_rectangle_outline(round(self.current_position_world[0]/20)*20-10, round(self.current_position_world[1]/20)*20-10, 20, 20, (255, 255, 255, 255), 1)
            else:
                arcade.draw_circle_outline(self.current_position_world[0], self.current_position_world[1], 2, (255, 255, 255, 255), 0.2, 0, -1)

        self.ui.draw()

    def on_key_press(self, symbol, modifier):
        if symbol == arcade.key.W or symbol == arcade.key.UP:
            self.camera_speed = (self.camera_speed[0], 10.0)
        elif symbol == arcade.key.A or symbol == arcade.key.LEFT:
            self.camera_speed = (-10.0, self.camera_speed[1])
        elif symbol == arcade.key.S or symbol == arcade.key.DOWN:
            self.camera_speed = (self.camera_speed[0], -10.0)
        elif symbol == arcade.key.D or symbol == arcade.key.RIGHT:
            self.camera_speed = (10.0, self.camera_speed[1])

        if symbol == arcade.key.KEY_1:
            icons_spritelist = self.info_scene.get_sprite_list("0")
            icons_spritelist.visible = not icons_spritelist.visible
        if symbol == arcade.key.KEY_2:
            political_spritelist = self.political_scene.get_sprite_list("0")
            political_spritelist.visible = not political_spritelist.visible
            self.political_background = not self.political_background
        if symbol == arcade.key.KEY_3:
            biome_spritelist = self.terrain_scene.get_sprite_list("1")
            biome_spritelist_2 = self.terrain_scene.get_sprite_list("2")
            biome_spritelist.visible = not biome_spritelist.visible
            biome_spritelist_2.visible = not biome_spritelist_2.visible
        if symbol == arcade.key.KEY_0:
            self.zoomed_speed_mod_adder = 0.01
        if symbol == arcade.key.KEY_9:
            self.zoomed_speed_mod_adder = -0.01

        if symbol == arcade.key.O:
            self.editing_mode = not self.editing_mode
        if symbol == arcade.key.F:
            self.set_fullscreen(not self.fullscreen)
        if symbol == arcade.key.M:
            if self.rotating_the_icon == True:
                self.rotating_the_icon = False
                self.moving_the_icon = True
            else:
                self.moving_the_icon = not self.moving_the_icon
        if symbol == arcade.key.R:
            if self.moving_the_icon == True:
                self.moving_the_icon = False
                self.rotating_the_icon = True
            else:
                self.rotating_the_icon = not self.rotating_the_icon

        if symbol == arcade.key.E:
            self.mouse_click_anchor.visible = not self.mouse_click_anchor.visible
        if symbol == arcade.key.P:
            brushes = na.get_all_files('local_data/brushes')
            print(f"I- found {brushes.__len__()} brush files")
            for idx, path in enumerate(brushes):
                icon_texture = arcade.load_texture(path)
                button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                button.add(
                    child=arcade.gui.UIImage(texture=icon_texture, width=32, height=32),
                    anchor_x="center",
                    anchor_y="center"
                )
                self.brush_menu_options.add(button, idx % 10, idx // 10)
                self.brush_buttons.append(button)

                @button.event
                def on_click(event: arcade.gui.UIOnClickEvent, idx=idx, path=path):
                    if idx == 0:
                        self.selected_brush = None
                        self.brush_menu_options.clear()
                        self.on_notification_toast(f"Deselected brush")
                        self.brush_buttons.clear()
                    else:
                        self.selected_brush = path
                        self.brush_menu_options.clear()
                        self.on_notification_toast(f"Selected {path}")
                        self.brush_buttons.clear()
        if symbol == arcade.key.ESCAPE:
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
                self.on_notification_toast("Deselected icon id.", warn=True)
        if button is arcade.MOUSE_BUTTON_LEFT:
            self.last_pressed_screen = (x, y)
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2

            # Conversion from screen coordinates to world coordinates
            world_x = ((((x - self.width / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x)
            world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
            # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset
            self.last_pressed_world = (world_x, world_y)
            tile_x = round(world_x / 20)
            tile_y = round(world_y / 20)

            if self.editing_mode == True:
                if self.camera.zoom >= 2.5:
                    if self.selected_brush:
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

                        pixel_rgba = na.TERRAIN_ID_MAP.get(self.selected_lower_id, (0, 0, 0)) + (255,)

                        target_positions = []
                        for rel_x, rel_y in coordinates:
                            x_pos = round(world_x + (rel_x - center_x) + 9.5)
                            y_pos = round(world_y + (rel_y - center_y) + 9.5)
                            target_positions.append((x_pos, y_pos))

                        for pos in target_positions:
                            tile = self.lower_terrain_layer.__getitem__(pos)
                            if tile is not None:
                                tile.color = pixel_rgba
                                tile.id_ = self.selected_lower_id
                            else:
                                print(f"No tile at position {pos}")
                    else:
                        list_of_tiles = np.zeros((self.editing_mode_size, self.editing_mode_size), dtype=object)
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
                                        list_of_tiles[x_offset, y_offset] = self.lower_terrain_layer.__getitem__((round(x_ + 9.5), round(y_ + 9.5)))
                                        list_of_tile_positions.append((round(x_ + 9.5), round(y_ + 9.5)))
                                    else:
                                        list_of_tiles[x_offset, y_offset] = None
                                else:
                                    list_of_tiles[x_offset, y_offset] = self.lower_terrain_layer.__getitem__((round(x_ + 9.5), round(y_ + 9.5)))
                                    list_of_tile_positions.append((round(x_ + 9.5), round(y_ + 9.5)))

                        for x_ in range(self.editing_mode_size):
                            for y_ in range(self.editing_mode_size):
                                if not list_of_tiles[x_][y_] is None:
                                    pixel_rgba = na.TERRAIN_ID_MAP.get(self.selected_lower_id, (0, 0, 0)) + (255,)
                                    list_of_tiles[x_][y_].color = pixel_rgba
                                    list_of_tiles[x_][y_].id_ = self.selected_lower_id
                                else:
                                    print(f"no tiles returned to selection ...")

                elif self.camera.zoom < 2.5:
                    if not tile_y < 0:
                        political_tile_to_edit = self.political_layer.__getitem__((tile_x, tile_y))
                    else:
                        political_tile_to_edit = self.s_political_layer.__getitem__((tile_x, 300-abs(tile_y)))

                    if political_tile_to_edit:
                        political_tile_to_edit.color = na.POLITICAL_ID_MAP.get(self.selected_country_id, 0)
                        political_tile_to_edit.id_ = self.selected_country_id
                        print(f"set {tile_x,tile_y} to id {self.selected_country_id}, color {na.POLITICAL_ID_MAP.get(self.selected_country_id,0)}")

            else:
                if self.selected_icon_id or self.selected_icon_id == 0:
                    if self.selected_icon_id == 9:
                        if self.drawing_line_start == None:
                            self.drawing_line_start = (world_x, world_y)
                            self.on_notification_toast(f"starting line at {world_x,world_y}")
                        else:
                            self.drawing_line_end = (world_x, world_y)
                            self.icons['lines'].append((self.drawing_line_start, self.drawing_line_end))
                            self.on_notification_toast(f"made line at {self.drawing_line_start} . {self.drawing_line_end}")
                            self.drawing_line_start = None
                            self.drawing_line_end = None
                    else:
                        icon_path = str(na.ICON_ID_MAP.get(self.selected_icon_id))+".png"
                        generated_unique_id: int = random.randrange(1000, 9999)
                        icon = na.Icon(icon_path, 1, world_x, world_y, 0.0, self.selected_icon_id, 0, generated_unique_id, 0, 1)
                        self.info_scene.add_sprite("0", icon)
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
                nearby_line = self.find_line_near(world_x, world_y, radius=24)
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
                            nearby_icon_dict_index += 1
                    self.icon_description.clear()
                    move_button_icon = arcade.load_texture("icons/move_icon.png")
                    remove_button_icon = arcade.load_texture("icons/remove_icon.png")
                    rotate_button_icon = arcade.load_texture("icons/rotate_icon.png")
                    rotate_reset_button_icon = arcade.load_texture("icons/rotate_reset_icon.png")
                    up_button_icon = arcade.load_texture("icons/up_icon.png")
                    down_button_icon = arcade.load_texture("icons/down_icon.png")
                    move_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    move_button.add(
                        child=arcade.gui.UIImage(
                            texture=move_button_icon,
                            width=64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    remove_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    remove_button.add(
                        child=arcade.gui.UIImage(
                            texture=remove_button_icon,
                            width=64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    rotate_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    rotate_button.add(
                        child=arcade.gui.UIImage(
                            texture=rotate_button_icon,
                            width=64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    rotate_reset_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    rotate_reset_button.add(
                        child=arcade.gui.UIImage(
                            texture=rotate_reset_button_icon,
                            width=64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    upgrade_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    upgrade_button.add(
                        child=arcade.gui.UIImage(
                            texture=up_button_icon,
                            width=64,
                            height=64,
                        ),
                        anchor_x="center",
                        anchor_y="center"
                    )

                    downgrade_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                    downgrade_button.add(
                        child=arcade.gui.UIImage(
                            texture=down_button_icon,
                            width=64,
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
                            self.on_notification_toast(f"icon is already at {nearby_icon.quality} !", error=True)

                    @upgrade_button.event
                    def on_click(event: arcade.gui.UIOnClickEvent):
                        if nearby_icon.quality < 5:
                            nearby_icon.quality += 1
                            nearby_icon_dict['quality'] += 1
                            self.on_notification_toast("upgraded icon")
                        else:
                            self.on_notification_toast(f"icon is already at {nearby_icon.quality} !", error=True)

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
                    if nearby_line:
                        index = 0
                        for line in self.icons['lines']:
                            if line[0][0] == nearby_line[0][0] and line[0][1] == nearby_line[0][1]:
                                # self.icons['lines'].pop(index)
                                self.selected_line = (nearby_line[0][0], nearby_line[0][1])
                                self.on_notification_toast(f"Found line at {round(nearby_line[0][0])} and {round(nearby_line[0][1])}")
                                break
                            else:
                                index += 1

                        self.icon_description.clear()
                        label = arcade.gui.UITextArea(
                            text=f"Line {round(nearby_line[0][0])} {round(nearby_line[0][1])}",
                            multiline=True,
                            width=128,
                            height=64
                        ).with_background(color=arcade.types.Color(10, 10, 10, 255)).with_border(width=1, color=arcade.types.Color(30, 30, 30, 255))
                        remove_button_icon = arcade.load_texture("icons/remove_icon.png")
                        remove_button = arcade.gui.UIFlatButton(text="", width=64, height=64)
                        remove_button.add(
                            child=arcade.gui.UIImage(
                                texture=remove_button_icon,
                                width=64,
                                height=64,
                            ),
                            anchor_x="center",
                            anchor_y="center"
                        )

                        @remove_button.event
                        def on_click(event: arcade.gui.UIOnClickEvent):
                            self.icons['lines'].pop(index)
                            self.selected_line = None
                            self.icon_description.clear()
                            self.on_notification_toast("Successfully removed line.")

                        self.icon_description.add(label)
                        self.icon_description.add(remove_button)
                    else:
                        print("Found absolutely nothing in vicinity.")
                        self.selected_world_icon = None
                        self.selected_line = None
                        self.icon_description.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        camera = self.camera
        zoom = camera.zoom
        if buttons is arcade.MOUSE_BUTTON_RIGHT:
            camera.position -= (dx / zoom, dy / zoom)

        if buttons is arcade.MOUSE_BUTTON_LEFT:
            self.current_position_screen = (x, y)
            camera_x, camera_y = camera.position
            diff_fr_res = (SCREEN_SIZE[0]-self.resized_size[0])/2, (SCREEN_SIZE[1]-self.resized_size[1])/2
            # Conversion from screen coordinates to world coordinates
            world_x = ((((x - self.width / 2)-diff_fr_res[0]) / self.camera.zoom) + camera_x)
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
                            index += 1
                except:
                    self.on_notification_toast("Couldn't rotate [cannot find icon] ...", warn=True)

            if self.editing_mode == True:
                if self.camera.zoom >= 2.5:
                    if self.selected_brush:
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

                        pixel_rgba = na.TERRAIN_ID_MAP.get(self.selected_lower_id, (0, 0, 0)) + (255,)

                        target_positions = []
                        for rel_x, rel_y in coordinates:
                            x_pos = round(world_x + (rel_x - center_x) + 9.5)
                            y_pos = round(world_y + (rel_y - center_y) + 9.5)
                            target_positions.append((x_pos, y_pos))

                        for pos in target_positions:
                            tile = self.lower_terrain_layer.__getitem__(pos)
                            if tile is not None:
                                tile.color = pixel_rgba
                                tile.id_ = self.selected_lower_id
                            else:
                                print(f"No tile at position {pos}")
                    else:
                        list_of_tiles = np.zeros((self.editing_mode_size, self.editing_mode_size), dtype=object)
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
                                        list_of_tiles[x_offset, y_offset] = self.lower_terrain_layer.__getitem__((round(x_ + 9.5), round(y_ + 9.5)))
                                        list_of_tile_positions.append((round(x_ + 9.5), round(y_ + 9.5)))
                                    else:
                                        list_of_tiles[x_offset, y_offset] = None
                                else:
                                    list_of_tiles[x_offset, y_offset] = self.lower_terrain_layer.__getitem__((round(x_ + 9.5), round(y_ + 9.5)))
                                    list_of_tile_positions.append((round(x_ + 9.5), round(y_ + 9.5)))

                        for x_ in range(self.editing_mode_size):
                            for y_ in range(self.editing_mode_size):
                                if not list_of_tiles[x_][y_] is None:
                                    pixel_rgba = na.TERRAIN_ID_MAP.get(self.selected_lower_id, (0, 0, 0)) + (255,)
                                    list_of_tiles[x_][y_].color = pixel_rgba
                                    list_of_tiles[x_][y_].id_ = self.selected_lower_id
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
                            index += 1
                    self.selected_world_icon.position = (world_x, world_y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button is arcade.MOUSE_BUTTON_LEFT:
            self.last_pressed_world = None
            self.last_pressed_screen = None
            # self.moving_the_icon = False

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
        world_x = ((((x - self.width / 2)-diff_fr_res[0]) / self.camera.zoom) + self.camera.position.x)
        world_y = ((((y - self.height / 2)-diff_fr_res[1]) / self.camera.zoom) + self.camera.position.y)
        # x -> origin point changed to the center with '/2' -> zoom amount -> camera offset
        self.current_position_world = (world_x, world_y)

        tile_x = round(world_x / 20)
        tile_y = round(world_y / 20)
        self.last_interacted_tile = self.upper_terrain_layer.__getitem__((tile_x, tile_y))

    def cleanup(self):
        self.chunk_result_queue.shutdown()
        self.chunk_request_queue.shutdown()

# ---


def main():
    multiprocessing.freeze_support()
    print("I- GAME INITIALIZING ...")
    game = Game(WIDTH, HEIGHT, "NATIONWIDER")
    # game.setup()
    arcade.run()
    game.cleanup()


if __name__ == "__main__":
    main()
