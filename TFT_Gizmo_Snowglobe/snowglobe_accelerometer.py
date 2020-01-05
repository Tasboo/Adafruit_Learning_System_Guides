from random import randrange
from random import uniform
import board
import busio
import displayio
from adafruit_gizmo import tft_gizmo
import adafruit_imageload
import adafruit_lis3dh
import time

#---| User Config |---------------
BACKGROUND = "/fam.bmp"            # specify color or background BMP file
NUM_FLAKES = 75                    # total number of snowflakes
SNOW_COLOR = 0xFFFFFF              # snow color
SHAKE_THRESHOLD = 27               # shake sensitivity, lower=more sensitive
#---| User Config |---------------

# Accelerometer setup
accelo_i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
accelo = adafruit_lis3dh.LIS3DH_I2C(accelo_i2c, address=0x19)

# XYZ Accelerometer Sensor Setup

# Create the TFT Gizmo display
display = tft_gizmo.TFT_Gizmo()

# Load background image
try:
    bg_bitmap, bg_palette = adafruit_imageload.load(BACKGROUND,
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)
# Or just use solid color
except (OSError, TypeError):
    BACKGROUND = BACKGROUND if isinstance(BACKGROUND, int) else 0x000000
    bg_bitmap = displayio.Bitmap(display.width, display.height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = BACKGROUND
background = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)

# Shared palette for snow bitmaps
palette = displayio.Palette(2)
palette[0] = 0xADAF00   # transparent color
palette[1] = SNOW_COLOR # snow color
palette.make_transparent(0)

# Snowflake setup
FLAKES = (
    0, 0, 1, 0, 0,    0, 0, 1, 0, 0,    0, 1, 0, 1, 0,
    0, 0, 1, 0, 0,    0, 1, 0, 1, 0,    1, 1, 1, 1, 1,
    0, 1, 1, 1, 0,    1, 0, 1, 0, 1,    0, 1, 1, 1, 0,
    0, 0, 1, 0, 0,    0, 1, 0, 1, 0,    1, 1, 1, 1, 1,
    0, 0, 1, 0, 0,    0, 0, 1, 0, 0,    0, 1, 0, 1, 0,
)
flake_sheet = displayio.Bitmap(15, 5, len(palette))
for i, value in enumerate(FLAKES):
    flake_sheet[i] = value
flake_pos = [0.0] * NUM_FLAKES
flake_posx = [0.0] * NUM_FLAKES
flakes = displayio.Group(max_size=NUM_FLAKES)
for _ in range(NUM_FLAKES):
    flakes.append(displayio.TileGrid(flake_sheet, pixel_shader=palette,
                                     width = 1,
                                     height = 1,
                                     tile_width = 5,
                                     tile_height = 5 ) )

# Snowfield setup
snow_depth = [display.height] * display.width
snow_bmp = displayio.Bitmap(display.width, display.height, len(palette))
snow = displayio.TileGrid(snow_bmp, pixel_shader=palette)

# Add everything to display
splash = displayio.Group()
splash.append(background)
splash.append(flakes)
splash.append(snow)
display.show(splash)

def clear_the_snow():
    #pylint: disable=global-statement, redefined-outer-name
    global flakes, flake_pos, flake_posx, snow_depth
    display.auto_refresh = False
    for flake in flakes:
        # set to a random sprite
        flake[0] = randrange(0, 3)
        # set to a random x location
        flake.x = randrange(0, display.width)
        flake.y = randrange(0, display.height)
    # set random y and x locations, off screen to start
    flake_pos = [randrange(0, display.height) for _ in range(NUM_FLAKES)]
    flake_posx = [randrange(0, display.width) for _ in range(NUM_FLAKES)]
    # reset snow level
    snow_depth = [display.height] * display.width
    # and snow bitmap
    for i in range(display.width * display.height):
        snow_bmp[i] = 0
    display.auto_refresh = True

def add_snow(index, amount, steepness=2):
    location = []

    # local steepness check
    for x in range(index - amount, index + amount):
        add = False
        if x == 0:
            # check depth to right
            if snow_depth[x+1] - snow_depth[x] < steepness:
                add = True
        elif x == display.width - 1:
            # check depth to left
            if snow_depth[x-1] - snow_depth[x] < steepness:
                add = True
        elif 0 < x < display.width - 1:
            # check depth to left AND right
            if snow_depth[x-1] - snow_depth[x] < steepness and \
               snow_depth[x+1] - snow_depth[x] < steepness:
                add = True
        if add:
            location.append(x)
    # add where snow is not too steep
    for x in location:
        new_level = snow_depth[x] - 1
        if new_level >= 0:
            snow_depth[x] = new_level
            snow_bmp[x, new_level] = 1
            
clear_the_snow()
while True:
    for i, flake in enumerate(flakes):
        x, y, z = accelo.acceleration
        # speed based on accelerometer
        if(y > 0):
            flake_pos[i] += y - flake[0] / 3
        elif(y < 0):
            flake_pos[i] += y + flake[0] / 3
        if(x > 0):
            flake_posx[i] += x - flake[0] / 3
        elif(x < 0):
            flake_posx[i] += x + flake[0] / 3
        # check if snowflake has hit the ground
        if (int(flake_pos[i]) >= 240) and (y > 0):
            flake_pos[i] = 0
            flake_posx[i] = randrange(0, display.width)
        if (int(flake_pos[i]) < 0) and (y < 0):
            flake_pos[i] = 240
            flake_posx[i] = randrange(0, display.width)
        if (int(flake_posx[i]) >= 240) and (x > 0):
            flake_posx[i] = 0
            flake_pos[i] = randrange(0, display.height)
        if (int(flake_posx[i]) < 0) and (x < 0):
            flake_posx[i] = 240
            flake_pos[i] = randrange(0, display.height)
        flake.y = int(flake_pos[i])
        flake.x = int(flake_posx[i])
    display.refresh()