import random
import struct
from arcade.gl import geometry
import arcade
from PIL import Image
import numpy as np

"""
Chunk manager for the world, utilizing textures and shaders.
"""

class ColorChunk:
    """An RGBA color chunk."""
    def __init__(
        self,
        pos: tuple[int, int],
        ctx: arcade.ArcadeContext,
        size: tuple[int, int],
        data: bytes | None = None,
        colors: bytes | None = None,
    ) -> None:
        self.ctx = ctx
        self.pos = pos
        self.size = size
        self.width = size[0]
        self.height = size[1]
        self.tile_count = self.width * self.height

        # RGBA texture storing the color palette
        self._color_texture = ctx.texture((256, 1), components=4, dtype="f1")

        # ubyte texture storing the tile ids
        self._texture = ctx.texture(self.size, components=1, dtype="u1")
        self._texture.filter = ctx.NEAREST, ctx.NEAREST

        # Quad geometry for drawing the chunk to the screen
        self._quad = geometry.quad_2d(size=(1, 1), pos=(0.5, 0.5))
        # Framebuffer object just for getting the read/write pixel api
        self._fbo = ctx.framebuffer(color_attachments=[self._texture])
        # Shader program for rendering the chunk
        self._program = ctx.program(
            vertex_shader="""
            #version 330

            uniform WindowBlock {
                mat4 projection;
                mat4 view;
            } window;

            uniform vec2 size;
            uniform vec2 position;

            in vec2 in_vert;
            in vec2 in_uv;
            out vec2 uv;

            void main() {
                gl_Position = window.projection * window.view * vec4((in_vert * size) + position, 0.0, 1.0);
                uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330

            uniform sampler2D color_texture;
            uniform usampler2D chunk_texture;
            in vec2 uv;
            out vec4 fragColor;

            void main() {
                uint tile_id = texture(chunk_texture, uv).r;
                fragColor = texelFetch(color_texture, ivec2(tile_id, 0), 0);
            }
            """,
        )
        self._program["color_texture"] = 0  # channel 0
        self._program["chunk_texture"] = 1  # channel 1
        if data is not None:
            self.write(data)
        if colors:
            self.write_colors(colors)

    def read_tile(self, position: tuple[int, int]) -> tuple[int, int, int, int]:
        """Read a pixel."""
        data = self._fbo.read(components=1, dtype="u1", viewport=(position[0], position[1], 1, 1))
        return struct.unpack("B", data)

    def write_tile(self, position: tuple[int, int], tile_id: int):
        """Write a pixel"""
        self._texture.write(
            data=struct.pack("B", tile_id), viewport=(position[0], position[1], 1, 1)
        )

    def clear(self):
        """Clear the chunk"""
        self._fbo.clear()
        
    def read(self) -> bytes:
        """Read the entire chunk"""
        return self._fbo.read(components=1, dtype="u1")

    def write(self, data: bytes):
        """Write the entire chunk"""
        self._texture.write(data=data)

    def write_colors(self, colors: bytes):
        """Write the color palette"""
        self._color_texture.write(data=colors)

    def draw(self, size):
        """Render the chunk"""
        self._program["position"] = self.pos
        self._program["size"] = size
        self._color_texture.use(unit=0)
        self._texture.use(unit=1)
        self._quad.render(self._program)

    def update_shader(self, time:float = 1.0):
        """update variables in the chunk's shader"""
        self._program["time"] = time
        
    def get_image(self):
        """Export the chunk as an image file"""
        return data_to_image(self)


def data_to_image(chunk: ColorChunk) -> Image.Image:
    """
    Convert a ColorChunk to a PIL Image with proper coloring.
    
    Args:
        chunk: The ColorChunk object to convert
        
    Returns:
        PIL Image with the properly colored texture
    """
    # Get the raw tile ID data
    raw_data = chunk.read()
    
    # Convert bytes to numpy array of tile IDs
    tile_ids = np.frombuffer(raw_data, dtype=np.uint8).reshape(chunk.height, chunk.width)
    
    # Read color palette data
    color_palette_data = chunk._color_texture.read()
    
    # Convert color palette to usable format (256 RGBA colors)
    color_palette = np.frombuffer(color_palette_data, dtype=np.uint8).reshape(256, 4)
    
    # Create RGB image array (height, width, 3)
    img_array = np.zeros((chunk.height, chunk.width, 3), dtype=np.uint8)
    
    # Map each tile ID to its color
    for y in range(chunk.height):
        for x in range(chunk.width):
            tile_id = tile_ids[y, x]
            if tile_id < 256:  # Ensure valid index
                img_array[y, x, 0] = color_palette[tile_id][0]  # R
                img_array[y, x, 1] = color_palette[tile_id][1]  # G
                img_array[y, x, 2] = color_palette[tile_id][2]  # B

    # Flip image
    img_array = np.flipud(img_array)
    
    # Create PIL Image from array
    return Image.fromarray(img_array)