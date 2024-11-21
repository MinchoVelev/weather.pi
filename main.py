from weather import fetchWeatherData
import machine
from time import sleep
import socket
import network
from machine import Pin, SPI
import framebuf
import utime
import micropython


EPD_WIDTH = 122
EPD_HEIGHT = 250

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_2in13_V4_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else:
            self.width = (EPD_WIDTH // 8) * 8 + 8

        self.height = EPD_HEIGHT

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while (self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)
        print('busy release')

    '''
    function : Turn On Display
    parameter:
    '''

    def TurnOnDisplay(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xf7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Turn On Display Fast
    parameter:
    '''

    def TurnOnDisplay_Fast(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Turn On Display Part
    parameter:
    '''

    def TurnOnDisplayPart(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xff)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Setting the display window
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
        Xend : End position of X-axis
        Yend : End position of Y-axis
    '''

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)

        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)

    '''
    function : Set Cursor
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
    '''

    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    '''
    function : Initialize the e-Paper register
    parameter:
    '''

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)

        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x07)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.ReadBusy()

    '''
    function : Initialize the e-Paper fast register
    parameter:
    '''

    def init_fast(self):
        print('init_fast')
        self.reset()
        self.delay_ms(100)

        self.send_command(0x12)  # SWRESET
        self.ReadBusy()

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_command(0x80)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x07)

        self.SetWindow(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x22)  # Load temperature value
        self.send_data(0xB1)
        self.send_command(0x20)
        self.ReadBusy()

        self.send_command(0x1A)  # Write to temperature register
        self.send_data(0x64)
        self.send_data(0x00)

        self.send_command(0x22)  # Load temperature value
        self.send_data(0x91)
        self.send_command(0x20)
        self.ReadBusy()

        return 0

    '''
    function : Clear screen
    parameter:
    '''

    def Clear(self):
        self.send_command(0x24)
        self.send_data1([0xff] * self.height * int(self.width / 8))

        self.TurnOnDisplay()

    '''
    function : Sends the image buffer in RAM to e-Paper and displays
    parameter:
        image : Image data
    '''

    def display(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay()

    def display_fast(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay_Fast()

    '''
    function : Refresh a base image
    parameter:
        image : Image data
    '''

    def Display_Base(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.send_command(0x26)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplay()

    '''
    function : Sends the image buffer in RAM to e-Paper and partial refresh
    parameter:
        image : Image data
    '''

    def displayPartial(self, image):
        self.reset()

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x01)  # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x07)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x24)  # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplayPart()

    '''
    function : Enter sleep mode
    parameter:
    '''

    def sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)


ssid = '<wifi id>'
password = '<wifi password>'


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)

    return wlan.ifconfig()[0]


def zero(offsetx, offsety, scale):
    startx = offsetx;
    starty = offsety;
    lengthx = scale;
    lengthy = 2 * scale;
    endx = startx + lengthx;
    endy = starty + lengthy;
    
    epd.hline(startx, starty, lengthx, 0x00)
    epd.hline(startx, endy, lengthx, 0x00)
    epd.vline(startx, starty, lengthy, 0x00)
    epd.vline(endx, starty, lengthy, 0x00)
    
def one(offsetx, offsety, scale):
    epd.vline(offsetx, offsety, 2 * scale, 0x00)

def two(offsetx, offsety, scale):
    epd.hline(offsetx, offsety, scale, 0x00)
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    epd.hline(offsetx, offsety + scale * 2, scale, 0x00)
    epd.vline(offsetx + scale, offsety, scale, 0x00)
    epd.vline(offsetx, offsety + scale, scale, 0x00)

def three(offsetx, offsety, scale):
    epd.hline(offsetx, offsety, scale, 0x00)
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    epd.hline(offsetx, offsety + scale * 2, scale, 0x00)
    epd.vline(offsetx + scale, offsety, 2 * scale, 0x00)
    
def four(offsetx, offsety, scale):
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    epd.vline(offsetx, offsety, scale, 0x00)
    epd.vline(offsetx + scale, offsety, 2 * scale, 0x00)
    
def five(offsetx, offsety, scale):
    epd.hline(offsetx, offsety, scale, 0x00)
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    epd.hline(offsetx, offsety + scale * 2, scale, 0x00)
    epd.vline(offsetx, offsety, scale, 0x00)
    epd.vline(offsetx + scale, offsety + scale, scale, 0x00)
    
def six(offsetx, offsety, scale):
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    epd.hline(offsetx, offsety + scale * 2, scale, 0x00)
    epd.vline(offsetx, offsety, scale * 2, 0x00)
    epd.vline(offsetx + scale, offsety + scale, scale, 0x00)

def seven(offsetx, offsety, scale):
    epd.vline(offsetx + scale, offsety, 2 * scale, 0x00)
    epd.hline(offsetx, offsety, scale, 0x00)

def eight(offsetx, offsety, scale):
    startx = offsetx;
    starty = offsety;
    lengthx = scale;
    lengthy = 2 * scale;
    endx = startx + lengthx;
    endy = starty + lengthy;
    
    epd.hline(startx, starty, lengthx, 0x00)
    epd.hline(startx, endy, lengthx, 0x00)
    epd.vline(startx, starty, lengthy, 0x00)
    epd.vline(endx, starty, lengthy, 0x00)
    epd.hline(offsetx, offsety + scale, scale, 0x00)
    
def nine(offsetx, offsety, scale):
    startx = offsetx;
    starty = offsety;
    lengthx = scale;
    lengthy = 2 * scale;
    endx = startx + lengthx;
    endy = starty + lengthy;
    
    epd.hline(startx, starty, lengthx, 0x00)
    epd.vline(startx, starty, scale, 0x00)
    epd.vline(endx, starty, lengthy, 0x00)
    epd.hline(offsetx, offsety + scale, scale, 0x00)

def minus(x, y, scale):
    epd.hline(x, y+scale, scale, 0x00)
    
def plus(x, y, scale):
    epd.hline(x, y+scale, scale, 0x00)
    epd.vline(x + int(scale/2), y + int(scale/2), scale, 0x00)
def dot(x,y,scale):
    zero(x,y + 2*scale - 2,1)
def t(x,y,scale):
    epd.hline(x + int(scale*0.33), y + int(scale*0.25), int(scale * 0.75), 0x00)
    epd.vline(x + int(scale*0.66), y + int(scale*0.25), int(scale * 1), 0x00)
def o(x,y,scale):
    zero(x + 1,y + 2,int(scale*0.5))
def rain(x,y,ascale):
    scale = int(ascale*0.8)
    epd.line(x + 1 * scale, y, x, y+2* scale, 0x00)
    epd.line(x + 3 * scale, y, x+int(2.175 * scale), y+2*int(scale*0.75), 0x00)
    epd.line(x + 5 * scale, y, x+4 * scale, y+2* scale, 0x00)
def snow(x,y,ascale):
    scale = int(ascale*1.1)
    epd.line(x + 1 * scale, y, x, y+2* scale, 0x00)
    epd.line(x, y, x + 1 * scale, y+2* scale, 0x00)
    epd.vline(x + int(scale*0.5), y, scale * 2, 0x00)
    epd.hline(x, y+scale + 1, scale, 0x00)
    epd.hline(x, y+scale, scale, 0x00)

x=5
y=10

def writeN(numberS, scale):
    global x,y
    for snumber in numberS:
        modifyscale = scale;
        if snumber == "-":
            minus(x,y,scale)
            modifyscale = int(modifyscale * 0.9)
        elif snumber == "+":
            plus(x,y,scale)
            modifyscale = int(modifyscale * 0.9)
        elif snumber == ".":
            dot(x,y,scale)
            modifyscale = int(modifyscale * 0.33)
        elif snumber == " ":
            print(" ")
        elif snumber == "t":
            t(x,y,scale)
            modifyscale = int(modifyscale * 0.9)
        elif snumber == "o":
            o(x,y,scale)
            modifyscale = int(modifyscale * 0.9)
        elif snumber == "/":
            rain(x,y,scale)
            modifyscale = int(modifyscale * 4)
        elif snumber == "*":
            snow(x,y,scale)
            modifyscale = int(modifyscale)
        
        else:
            number = int(snumber)
            if number == 0:
                zero(x, y, scale)
            if number == 1:
                one(x, y, scale)
                modifyscale = int(modifyscale * 0.75)
            if number == 2:
                two(x, y, scale)
            if number == 3:
                three(x, y, scale)
            if number == 4:
                four(x, y, scale)
            if number == 5:
                five(x, y, scale)
            if number == 6:
                six(x, y, scale)
            if number == 7:
                seven(x, y, scale)
            if number == 8:
                eight(x, y, scale)
            if number == 9:
                nine(x, y, scale)
            
        x = x + modifyscale + int(modifyscale/2)
        
        if x > 250 - scale:
            x = 5
            y = y + scale * 2 + int(scale/2)

if __name__ == '__main__':
    epd = EPD_2in13_V4_Landscape()  # 250x122. Text is with height of about 5?
    epd.Clear()
    epd.fill(0xff)
    epd.text("Starting...", 10, 10, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(1000)

    epd.text("Connecting to WiFi", 10, 20, 0x00)
    epd.display_fast(epd.buffer)
    try:
        ip = connect()
    except Exception:
        machine.reset()

    print(ip)
    epd.text("Got address " + ip, 10, 30, 0x00)
    epd.display_fast(epd.buffer)
    epd.sleep()
    
    while True:
        try:
            micropython.mem_info()
            epd.init()
            epd.fill(0xff)
            result = fetchWeatherData()
            epd.text(result["localTime"], 0, 10, 0x00)
            spaces = 20 - len(result["text"])
            headerLine = result["text"]
            for i in range(spaces):
                headerLine += " "
            headerLine += "Today"
            epd.text(headerLine, 0, 25, 0x00)
            epd.vline(120,40, 70, 0x00)
            
            x = 15
            y = 50
            today = result["currentTemp"]
            fToday = float(today)
            if fToday >= 10 or fToday <= -10:
                today = str(round(fToday))
            if not today.startswith("-"):
                today = "+" + today
            
            writeN(today, 20)
            
            # go to the right side
            x = 135
            y = 40
            
            writeN(str(round(float(result["currentMin"]))) + "to" + str(round(float(result["currentMax"]))), 10)
            
            
            epd.text("Tomorrow", 150, 70, 0x00)
            
            # go to next line
            x = 20
            y = 110
            
            if(result["currentRain"] == "yes"):
                writeN("/", 8) # rain
            if(result["currentSnow"] == "yes"):
                writeN("*", 8) # snow
            
            # go to right side
            x = 135
            y = 85
            writeN(str(round(float(result["tomorrowMin"]))) + "to" + str(round(float(result["tomorrowMax"]))), 10)
            
            
            x = 150
            y = 112
            if(result["tomorrowRain"] == "yes"):
                writeN("/", 7) # rain
            if(result["tomorrowSnow"] == "yes"):
                writeN("*", 7) # snow
            
            epd.display(epd.buffer)
            epd.sleep()
        except Exception as e:
            print(e)

        sleep(300)