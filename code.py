import board
import displayio
import terminalio
import busio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import time
import digitalio
import struct
import usb_hid


displayio.release_displays()

# Use for I2C
i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)

WIDTH = 128
HEIGHT = 32
BORDER = 4

display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

# Draw a label
text = " PiKeyPro v1.0"
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=18, y=HEIGHT // 2 - 1
)
splash.append(text_area)
display.refresh()

green = digitalio.DigitalInOut(board.GP5)
red = digitalio.DigitalInOut(board.GP4)
green.direction = digitalio.Direction.OUTPUT
red.direction = digitalio.Direction.OUTPUT
green.value = False
red.value = True


#from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Create and init keyboard USB HID device.
keeb = None
for dev in list(usb_hid.devices):
    if ((dev.usage == 0x06) and
        (dev.usage_page == 0x01) and
        hasattr(dev, "send_report")):
        keeb = dev
if keeb == None:
    raise Exception("Device cannot be found")

# 2D list to convert keyboard matrix to keycode (Row Wise)
matrix = [
    [
        Keycode.ESCAPE, Keycode.ONE, Keycode.TWO, Keycode.THREE, Keycode.FOUR,
        Keycode.FIVE, Keycode.SIX, Keycode.SEVEN, Keycode.EIGHT, Keycode.NINE,
        Keycode.ZERO, Keycode.MINUS, Keycode.EQUALS, Keycode.BACKSPACE
    ],
    [
        Keycode.TAB, Keycode.Q, Keycode.W, Keycode.E, Keycode.R, Keycode.T,
        Keycode.Y, Keycode.U, Keycode.I, Keycode.O, Keycode.P,
        Keycode.LEFT_BRACKET, Keycode.RIGHT_BRACKET, Keycode.BACKSLASH
    ],
    [
        Keycode.CAPS_LOCK, Keycode.A, Keycode.S, Keycode.D, Keycode.F,
        Keycode.G, Keycode.H, Keycode.J, Keycode.K, Keycode.L,
        Keycode.SEMICOLON, Keycode.QUOTE, Keycode.RETURN, Keycode.ENTER
    ],
    [
        Keycode.LEFT_SHIFT, Keycode.Z, Keycode.X, Keycode.C,
        Keycode.V, Keycode.B, Keycode.N, Keycode.M, Keycode.COMMA,
        Keycode.PERIOD, Keycode.FORWARD_SLASH, Keycode.RIGHT_SHIFT,
        Keycode.PAGE_UP,Keycode.GRAVE_ACCENT
    ],
    [
        Keycode.LEFT_CONTROL, Keycode.LEFT_GUI, Keycode.LEFT_ALT, Keycode.SPACE,Keycode.SPACEBAR,
        Keycode.RIGHT_ALT, Keycode.RIGHT_GUI,
        Keycode.RIGHT_CONTROL, Keycode.LEFT_ARROW, Keycode.UP_ARROW,
        Keycode.DOWN_ARROW, Keycode.RIGHT_ARROW, Keycode.PAGE_DOWN, Keycode.DELETE
    ],
] # matrix[row][col]
input_pins = (board.GP6, board.GP7, board.GP8, board.GP9,board.GP10) # 5 input rows

input_pin_array = [] # DigitalIO array for inputs.

output_pins = (
    board.GP11, board.GP12, board.GP13, board.GP14, board.GP15,
    board.GP16, board.GP17, board.GP18, board.GP19, board.GP20,
    board.GP21, board.GP22, board.GP26, board.GP27
) # 14 output columns

output_pin_array = [] # DigitalIO array for outputs.

# Initialise DigitalIO pins.
for pin in input_pins:
    key_pin = digitalio.DigitalInOut(pin)
    key_pin.direction = digitalio.Direction.INPUT
    key_pin.pull = digitalio.Pull.DOWN
    input_pin_array.append(key_pin)

for pin in output_pins:
    key_pin = digitalio.DigitalInOut(pin)
    key_pin.direction = digitalio.Direction.OUTPUT
    key_pin.drive_mode = digitalio.DriveMode.PUSH_PULL
    output_pin_array.append(key_pin)
           
keys_pressed = [] # list for possible n-key rollover upgrade in the future.
report_array = [0x00] * 8

while True:
    for col in range(len(output_pin_array)):
        output_pin_array[col].value = True # Turn on column pin.
        for row in range(len(input_pin_array)):
            if (matrix[row][col] >= 0xE0) and (input_pin_array[row].value): # Check if modifier is pressed
                report_array[0] |= Keycode.modifier_bit(matrix[row][col]) # Add modifier bit to report.
            elif input_pin_array[row].value: # Check if key is pressed.
                keys_pressed.append(matrix[row][col])
        output_pin_array[col].value = False # Turn off column pin.
    if len(keys_pressed) > 6: # Check for Rollover Error
        for i in range(2,8):
            report_array[i] = 0x01 # Add Rollover Error keycode*6 to report.
    else:
        for i in range(6):
            report_array[i+2] = keys_pressed[i] if i < len(keys_pressed) else 0 # Add keycode to report.
    keeb.send_report(struct.pack("8B", *report_array))
    report_array = [0x00] * 8
    keys_pressed = []




