#!/usr/bin/env python
import os
import pygame, sys
import datetime
import time
import math
from pygame.locals import *
import pygame.camera
import shutil
import random
import numpy
import subprocess, glob
import signal
from decimal import *
getcontext().prec = 8


#Pi Autoguider r8y7

#ONLY WORKS WITH PYTHON 2.7

# If your Pi doesn't start with the GUI then START BY TYPING 'startx' at the prompt
# THEN ON THE GUI OPEN LXTerminal AND ENTER 'sudo idle'
# then open the file, choose 'run', and 'run module'

# If you want to run at boot using Jessie: Assuming you've saved it as /home/pi/PiAG.py
# Add @sudo /usr/bin/python /home/pi/PiAG.py to the end of ~/.config/lxsession/LXDE-pi/autostart
# Make the file executable with sudo chmod +x PiAG.py

#==================================================================================================
use_config =          0 # set pre-stored config to load at startup, 1, 2 or 3.

#==================================================================================================
# CONNECTION SETTINGS

#FOR TESTING / simulation ONLY, 1 for normal use
# setting camera_connected = 0 will run in demo / simulation mode
camera_connected =    1

# set serial_connected = 0 if you don't have the Arduino Uno etc connected.
# ensure you install pyserial (sudo apt-get install python-serial) if not already installed.
serial_connected =    0

# if using the RPi camera set use_Pi_Cam = 1 , if set to 0 the program will use a USB camera.
use_Pi_Cam =          1

# Pi camera version, 1 or 2
Pi_Cam = 2#

# if using the RPi.GPIO on the Pi set use_RPiGPIO = 1, not required if only using the DSLR GPIO O/P (photoon = 1).
use_RPiGPIO =         1

# to enable GPIO control of DSLR function set photoon = 1
photoon =             1

# if using the Seeed Raspberry PI relay v1.0 card set use_Seeed = 1
# ensure you install smbus (sudo apt-get install python-smbus')
# and enable i2c on your Pi
use_Seeed =           0

# if using the PiFace Relay Plus card set use_PiFaceRP = 1
# ensure you install pifacerelayplus (sudo apt-get install python-pifacerelayplus')
# and enable SPI on your Pi
use_PiFaceRP =        0


#==================================================================================================
# DISPLAY SETTINGS

# Display - Set this dependent on your display. 0 = Pi Screen (800x480) or LCD (840x480), 1 = PAL Composite (640x480),
# 2 = other as set by parameters below
# if using 1 for PAL composite then adjust /boot/config.txt to suit
# if using 0 and a 840x480 HDMI LCD then change /boot/config.txt for hmdi group = 2 and hdmi mode = 14
Display =             0

Disp_Width =        608 #Disp_Width - sets image width when using Display = 0, set 608 for Pi Display (800x480), set 640 for 840x480 display

Night =               0 # Night Colours, 1 = ON

# Image_window - sets image window size, either 0 = 320x240, 1 = 352x288,2 = 640x480, 3 = 800x600, 4 = 960x720, 5 = 1280x960,
# Any for HDMI but recommend 0 for Composite (PAL)
Image_window =        5

# usb_max_res - webcam max available resolution, depends on your webcam
# 0 = 320x240, 1 = 352x288, 2 = 640x480, 3 = 800x600, 4 = 960x720, 5 = 1280x960,
# 6 = 1920x1440, 7 = 2592x1944
# eg. Logitech C270 won't work above 4, Philips NC900 won't work above 2
# (Pi camera uses a max of 7 automatically)
usb_max_res =         4

bits =               24 # bits - bits to display in pygame

Frame =               0 # Frame - frame displayed or not, 0 = no, 1 = yes

bh =                 32 # button height
bw =                 32 # button width

#SETUP GPIO and Seeed
#===================================================================================
#Telescope control GPIO pins
N_OP =               22
S_OP =               18
E_OP =               24
W_OP =               16
# External camera control GPIO pin, eg DSLR
C_OP =               26
# Alternative camera control GPIO pin if C_OP = 26 and using SPI
AC_OP =              13

#==================================================================================================
# SET DEFAULT VALUES
#==================================================================================================
auto_g =              0 # auto_g - autoguide on = 1, off = 0
nscale =            150 # n/sscale - North/South scaling in milliSecs/pixel
sscale =            150
escale =            150 # e/wscale - East / West scaling in milliSecs/pixel
wscale =            150
ewi =                 0 # ewi - Invert East <> West invert = 1, non-invert = 0
nsi =                 0 # nsi - Invert North<>South invert = 1, non-invert = 0
crop =               30 # crop - Tracking Window size in pixels.
minwin =             20 # minwin - set minimum Tracking window size
maxwin =            200 # maxwin - set maximum Tracking window size
offset3 =             0 # offset3/4 - Tracking Window offset from centre of screen
offset4 =             0
Intervals =           5 # Intervals - Guiding Interval in frames
log =                 0 # log - Log commands to /run/shm/YYMMDDHHMMSS.txt file, on = 1, off = 0
rgbw =                5 # rgbw - R,G,B,W1,W2 = 1,2,3,4,5
threshold =          20 # threshold value
thres =               0 # threshold - on = 1,off = 0. Displays detected star pixels
graph =               0 # graph - on = 1, off = 0. shows brightness of star, and threshold value
plot =                0 # plot - plot movements, on = 1, off = 0
auto_win =            0 # auto_win - auto size tracking window, on = 1, off = 0
auto_wlos =           1 # auto_wlos - auto window increase on loss of guide star, when using auto_win, on = 1, off = 0
auto_t =              0 # auto_t - auto threshold, on = 1, off = 0
zoom =                0 # zoom - set to give cropped image, higher magnification, pi camera max = 7.
auto_i =              0 # auto_i - auto-interval, on = 1, off = 0
decN =                1 # disable N/S DEC commands, 0 = OFF/DISABLED
decS =                1 
binn =                0 # binning 2x2, 0 = OFF, 1 = ON
nr =                  0 # noise reduction, 0 = off, 1,2 or 3 - averaged over a number of frames
minc =                1 # minimum correction in pixels

# Settings for external camera eg DSLR photos (set camera to B (BULB))
#===================================================================================
pwait =              10 # pwait - wait in seconds between multiple photos
ptime =              60 # ptime - exposure time in seconds
pcount =              1 # pcount - number of photos to take
# pmlock - if using mirrorlock on the DSLR set = 1, set pwait to a suitable value to settle.
# tested only on a Canon DSLR, triggers shutter to lock mirror and then triggers exposure.
pmlock =              0

# RPi camera presets
#===================================================================================
rpico =              90 # contrast
rpibr =              76 # brightness
rpiexno =             3 # exposure mode
rpiISO =              0 # ISO
rpiev =               0 # eV correction
rpisa =               0 # saturation
rpiss =          200000 # shutter speed
rpit =                0 # timer
rpired =            100 # red gain
rpiblue =           130 # blue gain
rpineg =              0 # negative image

rpimodes =  ['off',  'auto', 'night', 'night', 'sports', 'sports', 'verylong', 'verylong', 'fireworks', 'fireworks']
rpimodesa = [' off', 'auto', 'night', 'nigh2', 'sport',  'spor2',  'vlong',    'vlon2',    'fwork',     'fwor2']
rpiwidth =  [320, 352, 640, 800, 960, 1280, 1920, 2592, 3280]#
rpiheight = [240, 288, 480, 600, 720,  960, 1440, 1944, 2464]#
rpiscalex = [1, 1.1, 1.818, 1.25, 1.2, 1.333, 1.5, 1.35, 1.265]#
rpiscaley = [1, 1.2, 1.666, 1.25, 1.2, 1.333, 1.5, 1.35, 1.267]#

# Load pre-stored config at startup

if use_config > 0 and use_config < 4:
   deffile = "config" + str(use_config)
   if os.path.exists(deffile + ".txt"):
      with open(deffile + ".txt", "r") as file:
         inputx = file.readline()
      auto_g =              int(inputx[  0:  1])
      nscale =              int(inputx[  1:  5])
      sscale =              int(inputx[  5:  9])
      escale =              int(inputx[  9: 13])
      wscale =              int(inputx[ 13: 17])
      ewi =                 int(inputx[ 17: 18])
      nsi =                 int(inputx[ 18: 19])
      crop =                int(inputx[ 19: 23])
      offset3 =             int(inputx[ 23: 27])
      offset5 =             int(inputx[ 27: 31])
      offset6 =             int(inputx[ 31: 35])
      offset4 =             int(inputx[ 35: 39])
      if offset3 > 9000:
         offset3 = 9000 - offset3
      if offset4 > 9000:
         offset4 = 9000 - offset4
      if offset5 > 9000:
         offset5 = 9000 - offset5
      if offset6 > 9000:
         offset6 = 9000 - offset6
      Intervals =           int(inputx[ 39: 43])
      log2 =      log
      log =                 int(inputx[ 43: 44])
      if log and not log2:
         now = datetime.datetime.now()
         timestamp = now.strftime("%y%m%d%H%M%S")
         logfile = "/tmp/" + str(timestamp) + ".txt"
      rgbw =                int(inputx[ 44: 45])
      threshold =           int(inputx[ 45: 49])
      thres =               int(inputx[ 49: 50])
      graph =               int(inputx[ 50: 51])
      auto_i =              int(inputx[ 51: 52])
      plot =                int(inputx[ 52: 53])
      auto_win =            int(inputx[ 53: 54])
      auto_t =              int(inputx[ 54: 55])
      if camera_connected :
         zoom =             int(inputx[ 55: 56])
      zoom = max(Image_window, zoom)
      if not zoom:
         w = width
         h = height
      if zoom > 0:
         w = rpiwidth[zoom]
         h = rpiheight[zoom]
      if not use_Pi_Cam:
         cam.stop()
         pygame.camera.init()
         if not zoom:
            cam = pygame.camera.Camera("/dev/video0", (320, 240))
         elif zoom == 1 and usb_max_res >= 1:
            cam = pygame.camera.Camera("/dev/video0", (352, 288))
         elif zoom == 2 and usb_max_res >= 2:
            cam = pygame.camera.Camera("/dev/video0", (640, 480))
         elif zoom == 3 and usb_max_res >= 3:
            cam = pygame.camera.Camera("/dev/video0", (800, 600))
         elif zoom == 4 and usb_max_res >= 4:
            cam = pygame.camera.Camera("/dev/video0", (960, 720))
         elif zoom == 5 and usb_max_res >= 5:
            cam = pygame.camera.Camera("/dev/video0", (1280, 960))
         elif zoom == 6 and usb_max_res >= 6:
            cam = pygame.camera.Camera("/dev/video0", (1920, 1440))
         elif zoom == 7 and usb_max_res >= 7:
            cam = pygame.camera.Camera("/dev/video0", (2592, 1944))
         cam.start()
      if not camera_connected:
         zoom =             int(inputx[ 55: 56])
         wd = 20 + zoom*4
         hd = wd
      rpibr =               int(inputx[ 56: 60])
      rpico =               int(inputx[ 60: 64])
      if rpico > 9000:
         rpico = 9000 - rpico
      rpiev =               int(inputx[ 64: 68])
      if rpiev > 9000:
         rpiev = 9000 - rpiev
      rpiss =               int(inputx[ 68: 72])*1000
      rpiISO =              int(inputx[ 72: 76])
      rpiexno =             int(inputx[ 76: 77])
      rpiex =   rpimodes[rpiexno]
      rpiexa = rpimodesa[rpiexno]
      if len(inputx) > 77:
         binn =             int(inputx[ 77: 78])
         nr =               int(inputx[ 78: 79])
         decN =             int(inputx[ 79: 80])
         decS =             int(inputx[ 80: 81])
         rpired =           int(inputx[ 81: 84])
         rpiblue =          int(inputx[ 84: 87])
         rpiredx =   Decimal(rpired)/Decimal(100)
         rpibluex = Decimal(rpiblue)/Decimal(100)
         pcount =           int(inputx[ 87: 90])
         ptime =            int(inputx[ 90: 93])
      if len(inputx) > 93:
         camera_connected = int(inputx[ 93: 94])
         serial_connected = int(inputx[ 94: 95])
         use_Pi_Cam =       int(inputx[ 95: 96])
         use_RPiGPIO =      int(inputx[ 96: 97])
         photoon =          int(inputx[ 97: 98])
         use_Seeed =        int(inputx[ 98: 99])
         use_PiFaceRP =     int(inputx[ 99:100])
         Display =          int(inputx[101:102])
         Disp_Width =       int(inputx[102:106])
         Night =            int(inputx[106:107])
         Image_window =     int(inputx[107:108])
         usb_max_res =      int(inputx[108:109])
         Frame =            int(inputx[109:110])
         bh =               int(inputx[110:112])
         bw =               int(inputx[112:114])
         N_OP =             int(inputx[114:118])
         S_OP =             int(inputx[118:122])
         E_OP =             int(inputx[122:126])
         W_OP =             int(inputx[126:130])
         C_OP =             int(inputx[130:134])
         AC_OP =            int(inputx[134:138])
         rpineg =           int(inputx[138:139])
         bits =             int(inputx[139:143])
      if len(inputx) > 143:
         minc =    Decimal(int(inputx[144:148]))/Decimal(10)

#===================================================================================
# Seeed i2c address etc.
DEVICE_ADDRESS =   0x20
DEVICE_REG_MODE1 = 0x06
DEVICE_REG_DATA =  0xff

if use_Seeed:
   use_PiFaceRP = 0
   import smbus
   bus = smbus.SMBus(1) # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
   bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
#===================================================================================
# PiFace Relay Plus Board
if use_PiFaceRP:
   # switch OFF GPIO outputs as conflicts with SPI connections
   use_RPiGPIO = 0
   # Change to alternative DSLR camrea control pin O/P as pin 26 conflicts with SPI connections
   if C_OP == 26:
      C_OP = AC_OP
   import pifacerelayplus
   pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
#===================================================================================
if use_RPiGPIO:
   import RPi.GPIO as GPIO
   GPIO.setwarnings(False)
   GPIO.setmode(GPIO.BOARD)
   GPIO.setup(N_OP, GPIO.OUT)
   GPIO.setup(S_OP, GPIO.OUT)
   GPIO.setup(E_OP, GPIO.OUT)
   GPIO.setup(W_OP, GPIO.OUT)
if photoon:
   if not use_RPiGPIO:
      import RPi.GPIO as GPIO
      GPIO.setwarnings(False)
      GPIO.setmode(GPIO.BOARD)
   GPIO.setup(C_OP, GPIO.OUT)
   GPIO.output(C_OP, GPIO.LOW)

#==============================================================================
#a_thr_scale - sets scaling factor for auto_t
global a_thr_scale
a_thr_scale =         3
#a_thr_limit - sets lower limit for auto threshold to work
a_thr_limit =         5
#==============================================================================
if serial_connected:
   import serial

vtime =  0
htime =  0
ptime2 = 0
rpiex = rpimodes[rpiexno]
rpiexa = rpimodesa[rpiexno]

pygame.init()
imu =                    ""
limg =                    0
Interval =        Intervals
pimg =                   ""
scalex =                  1
scaley =                  1
rpiredx =  Decimal(rpired)/Decimal(100)
rpibluex = Decimal(rpiblue)/Decimal(100)
cls =                     0
avemax =                 10
photo =                   0
pcount2 =                 0
ptime2 =                  0
ptime4 =                  0
camera =                  0
ymax =                    0
z =                       0
con_cap =                 0
change =                  0
restart =                 0
fc =                      0
mxo =                     []
mxp =                     []
mxq =                     []
auto_c =                  0
fc =                      0
vt =                      0
ht =                      0
h_corr =                  1
w_corr =                  1
rgb = ['X', 'R', 'G', 'B', 'W1', 'W2']
fontObj = pygame.font.Font(None, 16)
global greyColor, redColor, greenColor, blueColor, dgryColor, lgryColor, blackColor, whiteColor, purpleColor, yellowColor
bredColor =   pygame.Color(200,   0,   0)
lgryColor =   pygame.Color(192, 192, 192)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color( 50,  20,  20) if Night else pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128,  70,  70) if Night else pygame.Color(128, 128, 128)
dgryColor =   pygame.Color(  0,   0,   0) if Night else pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 128,   0) if Night else pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(128,   0, 128) if Night else pygame.Color(255,   0, 255)
yellowColor = pygame.Color(128, 128,   0) if Night else pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 150) if Night else pygame.Color(  0,   0, 255)
redColor =    pygame.Color( 50,   0,   0) if Night else pygame.Color(200,   0,   0)
red =  chr(255) + chr(0)   + chr(0)
blu =  chr(0)   + chr(0)   + chr(255)
grn =  chr(0)   + chr(255) + chr(0)
yel =  chr(255) + chr(255) + chr(0)
dred = chr(128) + chr(70)  + chr(70)
dblu = chr(0)   + chr(0)   + chr(255)
dgrn = chr(0)   + chr(128) + chr(0)
dyel = chr(255) + chr(255) + chr(0)
fs = min(bh, bw)/2 - 3

zoom = max(Image_window, zoom)
if not use_Pi_Cam and zoom > usb_max_res:
   zoom = Image_window = usb_max_res

if Display == 0:
   width = Disp_Width
   b1x = b2x = b3x = width
   b1y = -bh
   b2y = bh*4
   b3y = bh*9
   Image_window = 2
   height = 480
   if bh <= 32:
      hplus = 0
   else:
      hplus = bh*15 - 480
   if use_config == 0:
      zoom = 2

if Display == 1:
   bh = bw = 32
   width = 352
   height = 288
   b1x = 0
   b1y = b2y = b3y = height
   b2x = 192
   b3x = 385
   hplus = 192
   Image_window = 1
   modewidth = 640
   if use_config == 0:
      zoom = 1
   hplus = 192

if Display > 1:
   width =   rpiwidth[Image_window]
   height = rpiheight[Image_window]
   b1x = b2x = b3x = width
   b1y = -bh
   b2y = bh*4 + 1
   b3y = bh*9 + 1
   hplus = 0
   Disp_Width = width

min_res = Image_window

while z <= zoom:
   scalex *= rpiscalex[z]
   scaley *= rpiscaley[z]
   z += 1

if zoom > 0 and use_config == 0:
   nscale = int(nscale/scaley)
   escale = int(escale/scalex)
   sscale = int(sscale/scaley)
   wscale = int(wscale/scalex)
   offset5 = offset6 = 0
mincor = int(Decimal(minc)*Decimal((nscale + sscale + wscale + escale)/4))

w =  rpiwidth[zoom]
h = rpiheight[zoom]
if width <= 352:
   modewidth = 640
else:
   modewidth = width + bw*6

if not Frame:
   windowSurfaceObj = pygame.display.set_mode((modewidth, height + hplus), pygame.NOFRAME, bits)
else:
   windowSurfaceObj = pygame.display.set_mode((modewidth, height + hplus), 1,              bits)
pygame.display.set_caption('Pi-AutoGuider')

if camera_connected and not use_Pi_Cam:
   pygame.camera.init()
   if not zoom:
      cam = pygame.camera.Camera("/dev/video0", (320, 240))
   elif zoom == 1 and usb_max_res >= 1:
      cam = pygame.camera.Camera("/dev/video0", (352, 288))
   elif zoom == 2 and usb_max_res >= 2:
      cam = pygame.camera.Camera("/dev/video0", (640, 480))
   elif zoom == 3 and usb_max_res >= 3:
      cam = pygame.camera.Camera("/dev/video0", (800, 600))
   elif zoom == 4 and usb_max_res >= 4:
      cam = pygame.camera.Camera("/dev/video0", (960, 720))
   elif zoom == 5 and usb_max_res >= 5:
      cam = pygame.camera.Camera("/dev/video0", (1280, 960))
   elif zoom == 6 and usb_max_res >= 6:
      cam = pygame.camera.Camera("/dev/video0", (1920, 1440))
   elif zoom == 7 and usb_max_res >= 7:
      cam = pygame.camera.Camera("/dev/video0", (2592, 1944))
   cam.start()
   cam.set_controls(0, 0, rpibr)

if use_Pi_Cam and camera_connected:
   if os.path.exists('/run/shm/test.jpg'):
      os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')

   rpistr = "raspistill -o /run/shm/test.jpg -co " + str(rpico) + " -br " + str(rpibr)
   if rpiexa != ' off' and rpiexa != 'nigh2' and rpiexa != 'fwor2' and rpiexa != 'vlon2' and rpiexa != 'spor2':
      rpistr += " -t " + str(rpit) + " -tl 0 -ex " + rpiex + " -bm -fp -awb off -awbg " + str(rpiredx) + "," + str(rpibluex)
   elif rpiexa == ' off':
      rpistr += " -t " + str(rpit) + " -tl 0 -ss " + str(rpiss) + " -fp -bm -awb off -awbg " + str(rpiredx) + "," + str(rpibluex)
   else:
      rpistr += " -t " + str(rpit) + " -tl 0 -ex " + rpiex + " -ss " + str(rpiss) + " -fp -bm -awb off -awbg " + str(rpiredx) + "," + str(rpibluex)
   if rpiISO > 0:
      rpistr += " -ISO " + str(rpiISO)
   if rpiev != 0:
      rpistr += " -ev " + str(rpiev)
   off5 = (Decimal(0.5) - (Decimal(width)/Decimal(2))/Decimal(w)) + (Decimal(offset5)/Decimal(w))
   off6 = (Decimal(0.5) - (Decimal(height)/Decimal(2))/Decimal(h)) + (Decimal(offset6)/Decimal(h))
   widx =  Decimal(width)/Decimal(w)
   heiy = Decimal(height)/Decimal(h)
   rpistr += " -q 100 -n -sa " + str(rpisa) + " -w " + str(width) + " -h " + str(height) + " -roi " + str(off5) + "," + str(off6) + ","+str(widx) + "," + str(heiy)
   if rpineg:
      rpistr += " -ifx negative "
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

def R_ON(RD, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA):
   if use_RPiGPIO:
      RE = [N_OP, S_OP, E_OP, W_OP][RD]
      GPIO.output(RE, GPIO.HIGH)
   if use_Seeed:
      DEVICE_REG_DATA &= ~(0x1<<RD)
      bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
   if use_PiFaceRP:
      pfr.relays[RD].turn.on()
   return(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)

def R_OFF(RD, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA):
   if use_RPiGPIO:
      RE = [N_OP, S_OP, E_OP, W_OP][RD]
      GPIO.output(RE, GPIO.LOW)
   if use_Seeed:
      DEVICE_REG_DATA |= (0x1<<RD)
      bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
   if use_PiFaceRP:
      pfr.relays[RD].turn.off()
   return(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)

def button2(bx1, x, by1, y, bw, z, by2, bColor):
   colors = [greyColor, dgryColor, dgryColor, dgryColor]
   Color = colors[bColor]
   bx1 += 1 + (x - 1)*bw
   by1 += 1 + (y - 1)*bh - 1
   bx2 = z*bw - 1
   pygame.draw.rect(windowSurfaceObj, Color,      Rect(bx1, by1, bx2, by2))
   pygame.draw.line(windowSurfaceObj, whiteColor, (bx1,   by1),   (bx1+bx2-1, by1   ))
   pygame.draw.line(windowSurfaceObj, whiteColor, (bx1+1, by1+1), (bx1+bx2-2, by1+1 ))
   pygame.draw.line(windowSurfaceObj, whiteColor, (bx1,   by1),   (bx1,       by1+bh))
   return

button2(b1x, 1, b1y, 2, bw, 2, bh, auto_g)
button2(b1x, 3, b1y, 2, bw, 1, bh, binn)
button2(b1x, 4, b1y, 2, bw, 1, bh, nr)
button2(b1x, 1, b1y, 3, bw, 1, bh, plot)
button2(b1x, 1, b1y, 4, bw, 1, bh, log)
button2(b1x, 2, b1y, 3, bw, 1, bh, graph)
button2(b1x, 2, b1y, 4, bw, 1, bh, thres)
button2(b1x, 4, b1y, 3, bw, 1, bh, auto_win)
button2(b1x, 4, b1y, 4, bw, 1, bh, auto_t)
button2(b1x, 4, b1y, 5, bw, 1, bh, auto_i)
button2(b1x, 3, b1y, 3, bw, 1, bh, nsi)
button2(b1x, 3, b1y, 4, bw, 1, bh, ewi)
button2(b1x, 3, b1y, 6, bw, 2, bh, 0)
button2(b1x, 3, b1y, 5, bw, 1, bh, 0)
cy = 2
while cy <= 6:
   button2(b1x, 5, b1y, cy, bw, 2, bh, 0)
   button2(b2x, 3, b2y, cy, bw, 2, bh, 0)
   cy += 1
if use_Pi_Cam and camera_connected:
   cy = 3
   while cy <= 6:
      button2(b2x, 1, b2y, cy, bw, 2, bh, 0)
      cy += 1
   button2(b1x, 1, b1y, 5, bw, 2, bh, 0)
   button2(b1x, 1, b1y, 6, bw, 2, bh, 0)
button2(b2x, 1, b2y, 2, bw, 2, bh, 0)
if photoon:
   button2(b2x, 5, b2y, 2, bw, 2, bh, 0)
   button2(b2x, 5, b2y, 3, bw, 2, bh, 0)
   button2(b2x, 5, b2y, 4, bw, 2, bh, 0)
if use_Pi_Cam:
   button2(b2x, 5, b2y, 5, bw, 1, bh, 0)
button2(b2x, 6, b2y, 5, bw, 1, bh, 0)
button2(b2x, 6, b2y, 6, bw, 1, bh, con_cap)
button2(b3x, 1, b3y, 3, bw, 1, bh, 0)
button2(b3x, 1, b3y, 2, bw, 1, bh, decN)
button2(b3x, 1, b3y, 4, bw, 1, bh, decS)
if decN:
   button2(b3x, 2, b3y, 2, bw, 1, bh, 0)
else:
   button2(b3x, 2, b3y, 2, bw, 1, bh, 1)
if decS:
   button2(b3x, 2, b3y, 4, bw, 1, bh, 0)
else:
   button2(b3x, 2, b3y, 4, bw, 1, bh, 1)
button2(b3x, 3, b3y, 3, bw, 1, bh, 0)
button2(b3x, 5, b3y, 2, bw, 1, bh, 0)
button2(b3x, 5, b3y, 4, bw, 1, bh, 0)
button2(b3x, 4, b3y, 3, bw, 1, bh, 0)
button2(b3x, 6, b3y, 3, bw, 1, bh, 0)
button2(b3x, 1, b3y, 6, bw, 1, bh, 0)
button2(b3x, 2, b3y, 6, bw, 1, bh, 0)
button2(b3x, 3, b3y, 6, bw, 1, bh, 0)
if use_config > 0:
   button2(b3x, use_config, b3y, 6, bw, 1, bh, 3)
button2(b3x, 4, b3y, 6, bw, 1, bh, 0)
button2(b3x, 5, b3y, 6, bw, 1, bh, 0)
button2(b3x, 6, b3y, 6, bw, 1, bh, 0)

def keys2(msg, fsize, fcolor, fx, bw, hp, fy, bh, vp, vo, upd):
   fy += 2 + (vp - 1)*bh + vo*(bh/6)
   fx += 2 + hp*bw
   if msg == "Exp Time" or msg == "     eV":
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(fx,        fy+1, bw*2 - 3, bh/2.4))
   if vo == 3:
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(fx-2-bw/2, fy,   bw+4,     bh/2.2))
      fx -= 2 + (len(msg)*fsize)/4
   elif vo == 4:
      fy -= 2
   colors =        [dgryColor, greenColor, yellowColor, redColor, greenColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   color =         colors[fcolor]
   fontObj =       pygame.font.Font('freesansbold.ttf', fsize)
   msgSurfaceObj = fontObj.render(msg, False, color)
   msgRectobj =    msgSurfaceObj.get_rect()
   msgRectobj.topleft = (fx, fy)
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd:
      pygame.display.update(pygame.Rect(int(fx/bw)*bw, int(fy/bh)*bh, bw*3, bh))
   return

keys2(str(int(nscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 2, 3, 0)
keys2(str(int(sscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 3, 3, 0)
keys2(str(int(escale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 4, 3, 0)
keys2(str(int(wscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 5, 3, 0)
keys2(str(threshold),             fs,       3,        b1x,         bw,   5,     b1y, bh, 4, 3, 0)
keys2(str(Interval),              fs,       3,        b1x,         bw,   5,     b1y, bh, 5, 3, 0)
keys2(str(zoom),                  fs,       3,        b1x,         bw,   5,     b1y, bh, 6, 3, 0)
keys2(str(rpibr),                 fs,       3,        b2x,         bw,   1,     b2y, bh, 2, 3, 0)
keys2(str(minc),                  fs,       3,        b1x,         bw,   3,     b1y, bh, 6, 3, 0)

msg = rgb[rgbw]
if rgbw < 5:
   keys2(msg,                     fs,  rgbw+2,        b1x,         bw,   5,     b1y, bh, 2, 3, 0)
else:
   keys2(msg,                     fs,  rgbw+1,        b1x,         bw,   5,     b1y, bh, 2, 3, 0)
if crop != maxwin:
   keys2(str(crop),               fs,       3,        b1x,         bw,   5,     b1y, bh, 3, 3, 0)
else:
   keys2("max",                   fs,       3,        b1x,         bw,   5,     b1y, bh, 3, 3, 0)
keys2("AWin",                     fs-1,       auto_win, b1x,         bw,   3,     b1y, bh, 3, 1, 0)
keys2("W",                        fs-1,       5,        b1x+fs/1.5,      bw,   3,     b1y, bh, 3, 1, 0)
keys2("AThr",                     fs-1,       auto_t,   b1x,         bw,   3,     b1y, bh, 4, 1, 0)
keys2("T",                        fs-1,       5,        b1x+fs/1.5,      bw,   3,     b1y, bh, 4, 1, 0)
keys2("AutoG",                    fs,       auto_g,   b1x,         bw,   0,     b1y, bh, 2, 1, 0)
keys2("A",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 2, 1, 0)
keys2("2x2",                      fs,       binn,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
keys2("x",                        fs,       5,        b1x+fs/2,    bw,   2,     b1y, bh, 2, 1, 0)
keys2("Log",                      fs,       log,      b1x,         bw,   0,     b1y, bh, 4, 1, 0)
keys2("L",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 4, 1, 0)
keys2("Gph",                      fs,       graph,    b1x,         bw,   1,     b1y, bh, 3, 1, 0)
keys2("G",                        fs,       5,        b1x,         bw,   1,     b1y, bh, 3, 1, 0)
keys2("Plot",                     fs,       plot,     b1x,         bw,   0,     b1y, bh, 3, 1, 0)
keys2("P",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 3, 1, 0)
keys2("Thr",                      fs,       thres,    b1x,         bw,   1,     b1y, bh, 4, 1, 0)
keys2("h",                        fs,       5,        b1x+fs/1.5,  bw,   1,     b1y, bh, 4, 1, 0)
keys2("NSi",                      fs,       nsi,      b1x,         bw,   2,     b1y, bh, 3, 1, 0)
keys2("N",                        fs,       5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
keys2("EWi",                      fs,       ewi,      b1x,         bw,   2,     b1y, bh, 4, 1, 0)
keys2("E",                        fs,       5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)
keys2("AInt",                     fs-1,     auto_i,   b1x,         bw,   3,     b1y, bh, 5, 1, 0)
keys2("I",                        fs-1,     5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 5, 1, 0)
keys2("rgbw",                     fs,       6,        b1x,         bw,   4,     b1y, bh, 2, 0, 0)
keys2("b",                        fs,       5,        b1x+fs,      bw,   4,     b1y, bh, 2, 0, 0)
keys2(" <",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 2, 4, 0)
keys2(">",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 2, 4, 0)
keys2("window",                   fs,       6,        b1x,         bw,   4,     b1y, bh, 3, 0, 0)
keys2(" -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 3, 4, 0)
keys2("+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 3, 4, 0)
keys2("threshold",                fs-1,     6,        b1x,         bw,   4,     b1y, bh, 4, 0, 0)
keys2(" -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 4, 4, 0)
keys2("+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 4, 4, 0)
keys2("interval",                 fs,       6,        b1x,         bw,   4,     b1y, bh, 5, 0, 0)
keys2(" -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 5, 4, 0)
keys2("+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 5, 4, 0)
keys2("Zoom",                     fs,       6,        b1x,         bw,   4,     b1y, bh, 6, 0, 0)
keys2(" -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 6, 4, 0)
keys2("+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 6, 4, 0)
keys2("Min Corr",                 fs,       6,        b1x,         bw,   2,     b1y, bh, 6, 0, 0)
keys2(" -",                       fs,       6,        b1x,         bw,   2,     b1y, bh, 6, 4, 0)
keys2("+",                        fs,       6,        b1x+bw-fs,   bw,   3,     b1y, bh, 6, 4, 0)
keys2("scale N",                  fs,       6,        b2x,         bw,   2,     b2y, bh, 2, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 2, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 2, 4, 0)
keys2("scale S",                  fs,       6,        b2x,         bw,   2,     b2y, bh, 3, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 3, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 3, 4, 0)
keys2("scale E",                  fs,       6,        b2x,         bw,   2,     b2y, bh, 4, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 4, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 4, 4, 0)
keys2("scale W",                  fs,       6,        b2x,         bw,   2,     b2y, bh, 5, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 5, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 5, 4, 0)
keys2("scale all",                fs,       6,        b2x,         bw,   2,     b2y, bh, 6, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 6, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 6, 4, 0)
keys2("Brightness",               fs-2,     6,        b2x,         bw,   0,     b2y, bh, 2, 0, 0)
keys2(" -",                       fs,       6,        b2x,         bw,   0,     b2y, bh, 2, 4, 0)
keys2("+",                        fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 2, 4, 0)

if use_Pi_Cam and camera_connected:
   keys2(str(rpico),              fs,       3,        b2x,         bw,   1,     b2y, bh, 3, 3, 0)
   rpiexa = rpimodesa[rpiexno]
   if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
      keys2(str(int(rpiss/1000)), fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
   else:
      keys2(str(int(rpiev)),      fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
   keys2((rpimodesa[rpiexno]),    fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
   keys2(str(rpiISO),             fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
   if not rpiISO:
      keys2('auto',               fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
   keys2("Contrast",              fs,       6,        b2x,         bw,   0,     b2y, bh, 3, 0, 0)
   keys2(" -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 3, 4, 0)
   keys2("+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 3, 4, 0)
   if rpiex == 'off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
      keys2("Exp Time",           fs-1,     6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
   else:
      keys2("     eV",            fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
   keys2(" -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
   keys2("+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
   keys2("ISO",                   fs,       6,        b2x,         bw*2, 0,     b2y, bh, 6, 0, 0)
   keys2(" -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
   keys2("+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
   keys2("Exp Mode",              fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
   keys2(" <",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
   keys2(">",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
   keys2("Adj Red",               fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
   keys2(" -",                    fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
   keys2("+",                     fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
   keys2("Adj Blue",              fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
   keys2(" -",                    fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
   keys2("+",                     fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
   rpiredx =   Decimal(rpired)/Decimal(100)
   rpibluex = Decimal(rpiblue)/Decimal(100)
   keys2(str(rpiredx),            fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
   keys2(str(rpibluex),           fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)

hor = 0
while hor < 4:
   keys2("N",                     fs,       6,        b3x,         bw,   1+hor, b3y, bh, 2, 2, 0)
   keys2("E",                     fs,       6,        b3x,         bw,   2+hor, b3y, bh, 3, 2, 0)
   keys2("S",                     fs,       6,        b3x,         bw,   1+hor, b3y, bh, 4, 2, 0)
   keys2("W",                     fs,       6,        b3x,         bw,   hor,   b3y, bh, 3, 2, 0)
   hor += 3
keys2("Esc",                      fs,       5,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
keys2("DEC",                      fs-1,     decN,     b3x,         bw,   0,     b3y, bh, 2, 0, decN)
keys2("  N",                      fs-1,     decN,     b3x,         bw,   0,     b3y, bh, 2, 2, decN)
keys2("nr",                       fs,       nr,       b1x,         bw,   3,     b1y, bh, 2, 1, nr)
keys2("DEC",                      fs-1,     decS,     b3x,         bw,   0,     b3y, bh, 4, 0, decS)
keys2("  S",                      fs-1,     decS,     b3x,         bw,   0,     b3y, bh, 4, 2, decS)
keys2(" R1",                      fs,       6,        b3x,         bw,   0,     b3y, bh, 6, 1, 0)
keys2("1",                        fs,       5,        b3x+fs,      bw,   0,     b3y, bh, 6, 1, 1)
keys2(" R2",                      fs,       6,        b3x,         bw,   1,     b3y, bh, 6, 1, 0)
keys2("2",                        fs,       5,        b3x+fs,      bw,   1,     b3y, bh, 6, 1, 0)
keys2(" R3",                      fs,       6,        b3x,         bw,   2,     b3y, bh, 6, 1, 0)
keys2("3",                        fs,       5,        b3x+fs,      bw,   2,     b3y, bh, 6, 1, 0)
keys2(" S1",                      fs,       6,        b3x,         bw,   3,     b3y, bh, 6, 1, 0)
keys2(" S2",                      fs,       6,        b3x,         bw,   4,     b3y, bh, 6, 1, 0)
keys2(" S3",                      fs,       6,        b3x,         bw,   5,     b3y, bh, 6, 1, 0)
keys2("RELOAD cfg",               fs-2,     7,        b3x+bw/6,    bw,   0,     b3y, bh, 5, 4, 0)
keys2("SAVE cfg",                 fs-2,     7,        b3x+bw/2,    bw,   3,     b3y, bh, 5, 4, 0)
if Night:
   keys2("Day",                   fs-1,     6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
else:
   keys2("Night",                 fs-1,     6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
   
keys2("TELESCOPE",                fs,       1,        b3x+bw/5,    bw,   0,     b3y, bh, 5, 0, 0)
keys2("WINDOW",                   fs,       1,        b3x+bw/2,    bw,   3,     b3y, bh, 5, 0, 0)
keys2("Stop",                     fs,       7,        b3x,         bw,   2,     b3y, bh, 4, 1, 0)
keys2("cen",                      fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
keys2(" tre",                     fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
keys2("cen",                      fs,       7,        b3x,         bw,   4,     b3y, bh, 3, 0, 0)
keys2(" tre",                     fs,       7,        b3x,         bw,   4,     b3y, bh, 3, 2, 0)
keys2("con",                      fs,       con_cap,  b2x,         bw,   5,     b2y, bh, 6, 0, 0)
keys2("cap",                      fs,       con_cap,  b2x,         bw,   5,     b2y, bh, 6, 2, 0)

if use_Pi_Cam:
   keys2("pic",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 5, 0, 0)
   keys2("cap",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 5, 2, 0)
keys2("scr",                      fs,       6,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
keys2("s",                        fs,       5,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
keys2("cap",                      fs,       6,        b2x,         bw,   5,     b2y, bh, 5, 2, 0)
if photoon:
    keys2("PHOTO",                fs,       photo,    b2x,         bw,   4,     b2y, bh, 2, 0, 0)
    keys2("O",                    fs,       5,        b2x+fs*1.5,  bw,   4,     b2y, bh, 2, 0, 0)
    keys2("P-Time",               fs,       6,        b2x,         bw,   4,     b2y, bh, 3, 0, 0)
    keys2(" -",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 3, 4, 0)
    keys2("+",                    fs,       6,        b2x+bw-fs,   bw,   5,     b2y, bh, 3, 4, 0)
    keys2(str(ptime),             fs,       3,        b2x,         bw,   5,     b2y, bh, 3, 3, 0)
    keys2("P-Count",              fs,       6,        b2x,         bw,   4,     b2y, bh, 4, 0, 0)
    keys2(" -",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 4, 4, 0)
    keys2("+",                    fs,       6,        b2x+bw-fs,   bw,   5,     b2y, bh, 4, 4, 0)
    keys2(str(pcount),            fs,       3,        b2x,         bw,   5,     b2y, bh, 4, 3, 0)


button2(b2x, 5, b2y, 6, bw, 1, bh, cls)
keys2("CLS",                      fs,       cls,      b2x,         bw,   4,     b2y, bh, 6, 1, 0)
keys2("C",                        fs,       5,        b2x,         bw,   4,     b2y, bh, 6, 1, 0)
use_config = 0
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 15, bh*10 + bh/3 + 10), 2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 5,  bh*10 + bh/3 + 5),  2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 10, bh*10 + bh/3),      2)

pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 5,  bh*10 + bh/3 + 10), 2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 15, bh*10 + bh/3 + 5),  2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 10, bh*10 + bh/3),      2)

pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 5,  bh*12 + bh/3),      (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), 2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 5),  2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (width + bw*5 + bw/4 + 10, bh*12 + bh/3 + 10), 2)

pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 15, bh*12 + bh/3),      (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), 2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 5),  2)
pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (width + bw*3 + bw/4 + 10, bh*12 + bh/3 + 10) ,2)

pygame.display.update()

def demo(width, height, posx, posy, blankline, wd, hd):
   time.sleep(0.5)
   ad = width
   bd = height
   imu = ""
   height = 1
   line = ""
   while height < posy:
      line += blankline
      height += 1
   imu += line
   height = posy
   while height < posy + hd:
      byte = blankline[0:((posx-1)*3)]
      imu += byte
      width = posx
      while width < posx + wd:
         cd = width - posx
         if cd <= wd/2:
             fd = cd + 2
         else:
             fd = wd - cd + 2
         dd = height - posy
         if dd<= hd/2:
             l = dd + 2
         else:
             l = hd - dd + 2
         fe = fd * l
         fe = min(fe, 255)
         byte = chr(fe) + chr(fe) + chr(fe)
         imu += byte
         width += 1
      byte = blankline[0:(ad+1-width)*3]
      imu += byte
      height += 1
   height = posy + hd
   line = ""
   while height < bd + 1:
      line += blankline
      height += 1
   imu += line
   return(imu)


def commands(nscale, escale, sscale, wscale, ewi, nsi, acorrect, bcorrect, mincor):
   dirn = 'n'
   nsscale = int(nscale)
   lcorrect = int((acorrect * nsscale)/100)
   if nsi != 0:
      dirn = 's'
      nsscale = int(sscale)
      lcorrect = int((acorrect * nsscale)/100)
   if lcorrect <= 0:
      dirn = 's'
      nsscale = int(sscale)
      lcorrect = int((acorrect * nsscale)/100)
      if nsi != 0:
         dirn = 'n'
         nsscale = int(nscale)
         lcorrect = int((acorrect * nsscale)/100)
      lcorrect = -lcorrect
   lcorrect = min(lcorrect, 9999)
   if lcorrect < mincor:
      lcorrect = 0
   Vcorrect = lcorrect
   Vcorlen = len(str(Vcorrect))
   ime = 1
   Vcorr = ""
   while ime <= (4-Vcorlen):
      Vcorr += '0'
      ime += 1
   Vcorrt = ':Mg' + dirn + Vcorr + str(Vcorrect)

   dirn = 'e'
   ewscale = int(wscale)
   ccorrect = int((bcorrect * ewscale)/100)
   if ewi != 0:
      dirn = 'w'
      ewscale = int(escale)
      ccorrect = int((bcorrect * ewscale)/100)
   if ccorrect <= 0:
      dirn = 'w'
      ewscale = int(escale)
      ccorrect = int((bcorrect * ewscale)/100)
      if ewi != 0:
         dirn = 'e'
         ewscale = int(wscale)
         ccorrect = int((bcorrect * ewscale)/100)
      ccorrect = -ccorrect
   ccorrect = min(ccorrect, 9999)
   if ccorrect < mincor:
      ccorrect = 0
   Hcorrect = ccorrect
   Hcorlen = len(str(Hcorrect))
   ime = 1
   Hcorr= ""
   while ime <= (4-Hcorlen):
      Hcorr += '0'
      ime += 1
   Hcorrt = ':Mg' + dirn + Hcorr + str(Hcorrect)
   return Vcorrt, Hcorrt, ewi, nsi

def lx200(Vcorrt, Hcorrt, decN, decS):
   if serial_connected:
      ser.write(bytes(Vcorrt.encode('ascii')))
      time.sleep(0.5)
      ser.write(bytes(Hcorrt.encode('ascii')))
   return

oldminc,oldnscale, oldescale, oldsscale, oldwscale, oldcrop, oldauto_g, oldInterval, oldlog, oldrgbw, oldthreshold, oldgraph, oldthres, oldauto_i, oldplot, oldauto_win, oldauto_t, oldzoom, oldrpibr, oldrpico, oldrpiss, oldrpiexno, oldrpiISO, oldrpiev, oldcls, oldcon_cap, oldphoto, oldptime, oldpcount, oldrpired, oldrpiblue, oldbinn, oldnr, olddecN, olddecS, oldnsi, oldewi = minc,nscale, escale, sscale, wscale, crop, auto_g, Interval, log, rgbw, threshold, graph, thres, auto_i, plot, auto_win, auto_t, zoom, rpibr, rpico, rpiss, rpiexno, rpiISO, rpiev, cls, con_cap, photo, ptime, pcount, rpired, rpiblue, binn, nr, decN, decS, nsi, ewi

arv =        {}
arh =        {}
arp =        {}
count =       0
crop  =    crop
posx =  width/2
posy = height/2
posxi =      -1
posxj =       1
posyi =      -1
posyj =       1
poss =        3
cycle =       0
wd =         20
hd =         20
pct =         1
pcu =         1

wz = 1
blankline =     chr(  3) + chr(  3) + chr(  3)
while wz < width:
   blankline += chr(  3) + chr(  3) + chr(  3)
   wz += 1
wz = 1
redline =       chr(128) + chr(  0) + chr(  0)
bluline =       chr(  0) + chr(  0) + chr(128)
greline =       chr(  0) + chr( 64) + chr(  0)
gryline =       chr(128) + chr(128) + chr(128)
dgryline =      chr(128) + chr( 70) + chr( 70)
while wz < 50:
   redline +=   chr(128) + chr(  0) + chr(  0)
   bluline +=   chr(  0) + chr(  0) + chr(128)
   greline +=   chr(  0) + chr( 64) + chr(  0)
   gryline +=   chr(128) + chr(128) + chr(128)
   dgryline +=  chr(128) + chr( 70) + chr( 70)
   wz += 1
if serial_connected:
   ser = serial.Serial('/dev/ttyACM0', 9600)
start = time.time()
start2 =   start
esc1 =         0
totvcor =      0
tothcor =      0
avevcor =      0
avehcor =      0
xcount =       0
xycle =        0
xvcor =       {}
xhcor =       {}
count =        1
ycount =       0
xvcor =   [0]*11
xhcor =   [0]*11
filno =        1
pmlock2 =      0
pmlock3 =      0

while True:
   xycle += 1

# demo(set camera_connected = 0 to use)
   if not camera_connected:
      posxa = random.randrange(posxi, posxj)
      posya = random.randrange(posyi, posyj)
      posx = int(posx + posxa)
      if posx > (width-50):
          posxi = -2
          posxj =  0
      if posx < 50:
          posxi =  0
          posxj =  2
      posy = int(posy + posya)
      if posy > (height-50):
          posyi = -2
          posyj =  0
      if posy < 50:
          posyj =  2
          posyi =  0
      if (time.time() - start) >= Interval - 0.2 and not serial_connected:
         if auto_g and (bcorrect/100 * escale) > mincor:
            posx = int(posx - bcorrect/100)
            start = time.time()
         if auto_g and (acorrect/100 * nscale) > mincor:
            posy = int(posy - acorrect/100)
            start = time.time()
         if auto_g and -(bcorrect/100 * escale) > mincor:
            posx = int(posx - bcorrect/100)
            start = time.time()
         if auto_g and -(acorrect/100 * nscale) > mincor:
            posy = int(posy - acorrect/100)
            start = time.time()
      imu = demo(width, height, posx, posy, blankline, wd, hd)

# take picture
  # webcam
   if camera_connected and not use_Pi_Cam:
      image = cam.get_image()
      if not zoom:
         offset5 = offset3
         offset6 = offset4
         if offset5 > 0 and offset5 >= w/2 - width/2:
            offset5 = w/2 - width/2
         if offset5 < 0 and offset5 <= width/2 - w/2:
            offset5 = width/2 - w/2
         if offset6 > 0 and offset6 >= h/2 - height/2:
            offset6 = h/2 - height/2
         if offset6 < 0 and offset6 <= height/2 - h/2:
            offset6 = height/2 - h/2
      if zoom > 0 and zoom != Image_window:
         strim1 = pygame.image.tostring(image, "RGB", 1)
         x = (h/2-height/2) - offset6
         strt = w * 3 * x
         imb = ""
         c = 0
         stas = (w/2 - width/2 + offset5) * 3
         while c < height:
            ima = strim1[strt:strt+(w*3)]
            imd = ima[stas : stas + width*3]
            imb += imd
            strt += (w*3)
            c += 1
         image = pygame.image.fromstring(imb, (width, height), "RGB", 1)

      try:
         if con_cap:
            filno += 1
            now = datetime.datetime.now()
            timestamp = now.strftime("%y%m%d%H%M%S")
            fname = '/home/pi/pic' + str(timestamp) + "_" + str(filno) + '.jpg'
            pygame.image.save(image, fname)
      except OSError:
         pass

      if not fc:
         # crop webcam picture to suit Display Width
         cropped = pygame.Surface((Disp_Width, height))
         cropped.blit(image, (0, 0), (0, 0, Disp_Width, height))
         catSurfaceObj = cropped
         windowSurfaceObj.blit(catSurfaceObj, (0, 0))
      strim = pygame.image.tostring(image, "RGB", 1)
      t3 = time.time()
      if vtime < t3:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("N",                          fs, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys2("S",                          fs, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
      if htime < t3:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("W",                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys2("E",                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
      if photo:
         ptime3 = int(ptime2 - t3) + 1
         if pmlock == 1 and pmlock2 == 1 and ptime3 == pwait - 3 and not camera:
            GPIO.output(C_OP, GPIO.HIGH)
            pmlock2 = 0
            pmlock3 = 1
         if pmlock == 1 and pmlock3 == 1 and ptime3 == pwait - 4 and not camera:
            GPIO.output(C_OP, GPIO.LOW)
            pmlock3 = 0
         if ptime3 != ptime4:
            keys2(str(ptime3),               fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            ptime4 = ptime3
      if ptime2 < t3 and photo and camera:
         pcount2 -= 1
         keys2(str((pcount + 1) - pcount2),  fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
         if not pcount2:
            photo = 0
            camera = 0
            keys2("PHOTO",                   fs, photo, b2x,        bw, 4, b2y, bh, 2, 0, 1)
            keys2("O",                       fs, 5,     b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)
            keys2("",                        fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
            keys2("",                        fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            if use_RPiGPIO or photoon:
               GPIO.output(C_OP, GPIO.LOW)
         else:
            camera = 0
            ptime2 = time.time() + pwait
            GPIO.output(C_OP, GPIO.LOW)
      if ptime2 < t3 and photo and not camera:
         camera = 1
         ptime2 = time.time() + ptime
         keys2(str(pcount + 1 - pcount2),    fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
         if use_RPiGPIO or photoon:
            GPIO.output(C_OP, GPIO.HIGH)

   # load Pi Camera picture
   if camera_connected and use_Pi_Cam:
      rpistopNS = 0
      rpistopEW = 0
      mkey =      0
      while not os.path.exists('/run/shm/test.jpg') and not mkey:
         t2 = time.time()
         if vtime < t2 and not rpistopNS:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("N",                       fs, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
            keys2("S",                       fs, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
            rpistopNS = 1
         if htime < t2 and not rpistopEW:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("W",                       fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
            keys2("E",                       fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
            rpistopEW = 1

         for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP:
               mkey = 1
      if not mkey:
         imagefile = '/run/shm/test.jpg'
      else:
         imagefile = '/run/shm/oldtest.jpg'
         pygame.event.post(event)

      # load picture
      try:
         image = pygame.image.load(imagefile)
      except pygame.error:
         imagefile = '/run/shm/oldtest.jpg'
         image = pygame.image.load(imagefile)
      windowSurfaceObj.blit(image, (0, 0))

      t3 = time.time()
      if vtime < t3 and not rpistopNS:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("N",                          fs, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys2("S",                          fs, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
         rpistopNS = 1
      if htime < t3 and not rpistopEW:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("W",                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys2("E",                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
         rpistopEW = 1

      if photo:
         ptime3 = int(ptime2 - t3) + 1
         if pmlock == 1 and pmlock2 == 1 and ptime3 == pwait - 3 and not camera:
            GPIO.output(C_OP, GPIO.HIGH)
            pmlock2 = 0
            pmlock3 = 1
         if pmlock == 1 and pmlock3 == 1 and ptime3 == pwait - 4 and not camera:
            GPIO.output(C_OP, GPIO.LOW)
            pmlock3 = 0
         if ptime3 != ptime4:
            keys2(str(ptime3),               fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            ptime4 = ptime3
         if ptime2 < t3 and camera:
            pcount2 -= 1
            keys2(str(pcount + 1 - pcount2), fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
            if not pcount2:
               photo = 0
               camera = 0
               keys2("PHOTO",                fs, photo, b2x,        bw, 4, b2y, bh, 2, 0, 1)
               keys2("O",                    fs, 5,     b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)
               keys2("",                     fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
               keys2("",                     fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
               if use_RPiGPIO or photoon:
                  GPIO.output(C_OP, GPIO.LOW)
            else:
               camera = 0
               pmlock2 = 1
               ptime2 = time.time() + pwait
               GPIO.output(C_OP, GPIO.LOW)
              
         if ptime2 < t3 and photo and not camera:
            camera = 1
            ptime2 = time.time() + ptime
            keys2(str(pcount + 1 - pcount2), fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
            if use_RPiGPIO or photoon:
               GPIO.output(C_OP, GPIO.HIGH)

      try:
         # constant capture
         if con_cap:
            filno += 1
            now = datetime.datetime.now()
            timestamp = now.strftime("%y%m%d%H%M%S")
            fname = '/home/pi/con' + str(timestamp)+ "_" + str(filno) + '.jpg'
            if os.path.exists('/run/shm/test.jpg'):
               shutil.copy('/run/shm/test.jpg', fname)
         if os.path.exists('/run/shm/test.jpg'):
            os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
      except OSError:
         pass

# simulation demo
   if not camera_connected:
      image = pygame.image.fromstring(imu, (width, height), "RGB", 1)
      catSurfaceObj = image
      windowSurfaceObj.blit(catSurfaceObj, (0, 0))
      imb = imu
      t2 = time.time()
      if vtime < t2:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("N",                          fs, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys2("S",                          fs, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
      if htime < t2:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys2("W",                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys2("E",                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)

# crop picture
   if crop == maxwin:
      cropped = pygame.transform.scale(image, [crop, crop])
      w_corr =  Decimal(width)/Decimal(crop)
      h_corr = Decimal(height)/Decimal(crop)
      offset3 = 0
      offset4 = 0
   else:
      cropped = pygame.Surface((crop, crop))
      cropped.blit(image, (0, 0), (width/2 - crop/2 + offset3, height/2 - crop/2 + offset4, crop, crop))
   if bits < 24:
      pygame.image.save(cropped, '/run/shm/cropped.jpg')
      cropped = pygame.image.load('/run/shm/cropped.jpg')
   imb = pygame.image.tostring(cropped, "RGB", 1)

# initialise arrays
   ars =      {}
   art =      {}
   arp =      {}
   mx =       []
   arp = [0]*260

   if rgbw < 4:
      imc = imb[rgbw - 1:crop*crop*3:3]
      mx = [ord(i) for i in imc]
   else:
      xcounter = 0
      while xcounter < (crop*crop*3):
         imrc = ord(imb[xcounter    :xcounter + 1])
         imgc = ord(imb[xcounter + 1:xcounter + 2])
         imbc = ord(imb[xcounter + 2:xcounter + 3])
         if rgbw == 4:
            ima = (imrc + imgc + imbc)/3
         else:
            ima = max(imrc, imgc, imbc)
         mx.append(ima)
         xcounter += 3

# 2x2 binning
   if binn:
      cy = 0
      while cy < crop-1:
         cx = 0
         while cx < crop-1:
            tot = sum(mx[cy*crop + cx:cy*crop + cx + 2]) + sum(mx[crop + cy*crop + cx:cy*crop + cx + 2 + crop])
            if tot > 255:
               tot = 255
            mx[cy*crop + cx] =            tot
            mx[cy*crop + cx + 1] =        tot
            mx[cy*crop + cx + crop] =     tot
            mx[cy*crop + cx + crop + 1] = tot
            cx += 2
         cy += 2

# noise reduction(average frames)
   if nr > 0 and len(mx) == len(mxo):
      mx = (numpy.add(mxo, mx))/2 
   if nr > 1 and len(mxo) == len(mxp) and len(mx) == len(mxo):
      mx = (numpy.add(mxp, mx))/2 
   if nr > 2 and len(mxo) == len(mxp) and len(mx) == len(mxo) and len(mxp) == len(mxq):
      mx = (numpy.add(mxq, mx))/2
   if nr > 2:
      mxq[:] = mxp[:]
   if nr > 1:
      mxp[:] = mxo[:]
   if nr > 0:
      mxo[:] = mx[:]

# calculate min and max values
   ct = 0
   ste = int(crop/50) + 1
   while ct < crop * crop:
      arp[mx[ct] + 1] += 1
      ct += ste

   count =  1
   mintot = 0
   maxtot = 0
   totm =   0
   while count <= 255:
      val = arp[count]
      totm += val
      if totm < (crop*crop)/ste*0.02:
         mintot = count
      if totm < (crop*crop)/ste - 11:
         maxtot = count
      count += 1
   if not auto_t:
      pcont = maxtot - threshold

   else:
      threshold = (maxtot-mintot)/a_thr_scale
      pcont = maxtot - threshold
      keys2(str(threshold), fs, 3, b1x, bw, 5, b1y, bh, 4, 3, 1)
      if threshold <= a_thr_limit:
         threshold = maxtot - mintot + 1
         pcont = maxtot - threshold

# compare array to threshold value

   mz = numpy.array(mx)
   if pcont < mintot:
      pcont = maxtot + 5
   mz[mz <  pcont] = 0
   mz[mz >= pcont] = 1
   ttot = numpy.sum(mz)
   if ttot < 1:
      ttot = 1

# display Threshold if enabled
   pic = ""
   counter = 0

   if thres:
      while counter < crop*crop:
         ima = mz[counter]
         if ima < 1:
            pic += imb[counter*3:counter*3 + 3]
         else:
            if rgbw == 1:
               pic += red
            elif rgbw == 2:
               pic += grn
            elif rgbw == 3:
               pic += blu
            else:
               pic += yel
         counter += 1
      imagep = pygame.image.fromstring(pic, (crop, crop), "RGB", 1)
      if crop != maxwin:
         catSurfaceObj = imagep
         windowSurfaceObj.blit(catSurfaceObj, (width/2 - crop/2 + offset3, height/2 - crop/2 + offset4))
      else:
         imagep = pygame.transform.scale(imagep, [width, height])
         catSurfaceObj = imagep
         windowSurfaceObj.blit(catSurfaceObj, (0, 0))


# calculate corrections
   if auto_win:
      lcounter = 0
      while lcounter < crop:
         loc = lcounter * crop
         ars[lcounter]= sum(mz[loc:loc + crop])
         art[lcounter]= sum(mz[lcounter:crop*crop:crop])
         lcounter += 1

   if ttot > 1:
      acorrect = 0
      ltot = 0
      while ltot < ttot/2:
         loc = acorrect * crop
         line = sum(mz[loc:loc+crop])
         ltot += line
         acorrect += 1
      acorrect -= (Decimal(ltot) - Decimal(ttot)/Decimal(2))/Decimal(line)

      bcorrect = 0
      ctot = 0
      while ctot < ttot/2:
         col = sum(mz[bcorrect:crop*crop:crop])
         ctot += col
         bcorrect += 1
      bcorrect -= (Decimal(ctot) - Decimal(ttot)/Decimal(2))/Decimal(col)

      acorrect = 100 * (acorrect - crop/2)
      bcorrect = 100 * (bcorrect - crop/2)

   if not pcont or ttot == 1:
      acorrect = 1
      bcorrect = 1

# auto_c autocentre telescope
   if auto_c == 1:
      if ttot > 1:
         if offset3 > 0:
            offset3 -= 1
         elif offset3 < 0:
            offset3 += 1
         if offset4 > 0:
            offset4 -= 1
         elif offset4 < 0:
            offset4 += 1
         if offset3 == 0 and offset4 == 0:
            auto_c = 0
            auto_win = 0
            crop = ocrop
            change = 1
            keys2("cen",  fs, 7, b3x, bw, 1, b3y, bh, 3, 0, 1)
            keys2(" tre", fs, 7, b3x, bw, 1, b3y, bh, 3, 2, 1)

      else:
         auto_c = 0
         auto_win = 0
         crop = ocrop
         change = 1
         keys2("cen",     fs, 7, b3x, bw, 1, b3y, bh, 3, 0, 1)
         keys2(" tre",    fs, 7, b3x, bw, 1, b3y, bh, 3, 2, 1)

# set auto window
   if auto_win:
      if ttot > 1 and ars[3]< 2 and ars[crop-2] < 2 and art[3] < 2 and art[crop-2] < 2:
         crop -= 1
         crop = max(crop, minwin)
      if ttot > 1 and (ars[2] > 1 or ars[crop-2] > 1 or art[2] > 1 or art[crop-2] > 1):
         crop += 1
         crop = min(crop, maxwin - 1)
         if (width/2 + crop/2 + offset3 > width) or (width/2 + offset3 - crop/2) <= 1 or (height/2 + offset4 - crop/2) >= height or (height/2 - offset4 - crop/2) <= 1:
            crop -= 2
      if ttot == 1 and auto_wlos:
         crop += 1
         crop = min(crop, maxwin - 1)
         if (width/2 + offset3 + crop/2) >= width:
            crop -= 1
         elif (width/2 + offset3 - crop/2) <= 1:
            crop -= 1
         if (height/2 + offset4 + crop/2) >= height:
            crop -= 1
         elif (height/2 + offset4 - crop/2) <= 1:
            crop -= 1
      keys2(str(crop), fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)

   if crop == maxwin:
      acorrect = Decimal(acorrect) * Decimal(h_corr)
      bcorrect = Decimal(bcorrect) * Decimal(w_corr)

   if auto_g and ttot < 5 and cls and ymax == avemax:
      acorrect = avevcor
      bcorrect = avehcor
      auto_win = 1
      change = 1

   if auto_g and ttot < 5 and cls:
      keys2("CLS", fs, 2, b2x, bw, 4, b2y, bh, 6, 1, 1)
      keys2("C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
   elif auto_g and ttot > 4 and cls:
      keys2("CLS", fs, 1, b2x, bw, 4, b2y, bh, 6, 1, 1)
      keys2("C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)


   Vcorrt, Hcorrt, ewi, nsi = commands(nscale, escale, sscale, wscale, ewi, nsi, acorrect, bcorrect, mincor)

   if xycle >= Interval:
      xycle = 0

      if auto_g:
         xcount += 1
         ycount += 1
         zcount = ycount
         if ycount > avemax:
            ymax = avemax
         if ymax == avemax:
            zcount = avemax
         if cls and zcount > avemax-1:
            keys2("CLS", fs, 1, b2x, bw, 4, b2y, bh, 6, 1, 1)
            keys2("C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
         elif cls and zcount < avemax:
            keys2("CLS", fs, 2, b2x, bw, 4, b2y, bh, 6, 1, 1)
            keys2("C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
         if ycount > avemax:
            ycount = 1
         if ttot > 1:
            xvcor[ycount] = acorrect
            xhcor[ycount] = bcorrect
            totvcor = 0
            tothcor = 0
            count = 1
            while count <= zcount:
               totvcor += xvcor[count]
               tothcor += xhcor[count]
               count += 1
            avevcor = int(totvcor/zcount)
            avehcor = int(tothcor/zcount)

            Vcorrt, Hcorrt, ewi, nsi = commands(nscale, escale, sscale, wscale, ewi, nsi, acorrect, bcorrect, mincor)

         vdir = Vcorrt[3:4]
         hdir = Hcorrt[3:4]
         vcor = int(Vcorrt[4:8])
         hcor = int(Hcorrt[4:8])
         time1 = time.time()
         vtime = (time1 * 1000 + vcor)/1000
         htime = (time1 * 1000 + hcor)/1000
         vt = 1
         ht = 1
         start = time.time()
         if vdir == "n" and vcor > 0 and decN:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("N", fs, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
         if hdir == "e" and hcor > 0:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
            keys2("E", fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
         if vdir == "s" and vcor > 0 and decS == 1:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
            keys2("S", fs, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
         if hdir == "w" and hcor > 0:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys2("W", fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
         if serial_connected:
            if decN and vdir == "n":
               ser.write(bytes(Vcorrt.encode('ascii')))
            if decS and vdir == "s":
               ser.write(bytes(Vcorrt.encode('ascii')))
            time.sleep(0.2)
            ser.write(bytes(Hcorrt.encode('ascii')))
            time.sleep(0.2)
         if log:
            now = datetime.datetime.now()
            timestamp = now.strftime("%y/%m/%d-%H:%M:%S")
            timp = str(timestamp) + "," + Vcorrt + "," + Hcorrt + "," + str(acorrect) + "," + str(bcorrect) + "\n"
            with open(logfile, "a") as file:
               file.write(timp)
         if not camera_connected:
            posx -= bcorrect/100
            posy -= acorrect/100

      if auto_i:
         acor = int(Vcorrt[4:8])
         bcor = int(Hcorrt[4:8])
         if acor >= bcor and acor > 0:
            Interval = acor/300 + 2
            rpiexa = rpimodesa[rpiexno]
            if use_Pi_Cam and (rpiexa == " off" or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
               Interval += (rpiss/1000000)*4
         if bcor > acor and bcor > 0:
            Interval = bcor/300 + 2
            rpiexa = rpimodesa[rpiexno]
            if use_Pi_Cam and (rpiexa == " off" or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
               Interval += (rpiss/1000000)*4
         if not use_Pi_Cam and camera_connected:
            Interval *= 3
         keys2(str(Interval), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
      else:
         Interval = Intervals

# Display
   if plot > 0:
      if Display == 0 or Display > 1:
         pox = width - 110
      else:
         pox = width + 10
      poy = 20
      pov = 50
      pol = 256
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(pox-1, poy-1, 52, 258), 1)
      limg += 1
      val2 = pov/2
      val3 = pov/2
      if acorrect >= 0:
         val2 = pov/2 + int(math.sqrt(acorrect))/4
      else:
         val2 = pov/2 - int(math.sqrt(-acorrect))/4
      if bcorrect >= 0:
         val3 = pov/2 + int(math.sqrt(bcorrect))/4
      else:
         val3 = pov/2 - int(math.sqrt(-bcorrect))/4
      if val2 < val3:
         rimg = blankline[0:(val2)*3]
         rimg += dred if Night else red
         rimg += blankline[val2*3:val3*3]
         rimg += dgrn if Night else grn
         rimg += blankline
         pimg += rimg[0:pov*3]
      else:
         rimg = blankline[0:(val3)*3]
         rimg += dgrn if Night else grn
         rimg += blankline[val3*3:val2*3]
         rimg += dred if Night else red
         rimg += blankline
         pimg += rimg[0:pov*3]
      if limg > pol:
         yt = (limg - pol)*pov*3
         yu = limg*pov*3
         pimg = pimg[yt:yu]
         limg = pol
      imageg = pygame.image.fromstring(pimg, (pov, limg), "RGB", 1)
      if plot == 1:
         imageg.set_alpha(127)
      windowSurfaceObj.blit(imageg, (pox, poy))

   w2 =  width/2 + offset3
   h2 = height/2 + offset4
   c1 = crop/2
   c2 = crop/2

#display graph if enabled
   if graph > 0:
      if Display == 0 or Display > 1:
         pox = width - 55
      else:
         pox = width + 65
      poy = 20
      pov = 50
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(pox-1, poy-1, 52, 258), 1)
      count = 0
      img = ""
      while count < 256:
         if count != maxtot and count != mintot and count != pcont:
            val = arp[count+1]
            val2 = int(30*math.log10(val + 10) - 29)
            val2 = min(val2, 49)
            val2 = max(val2, 1)
            if val2 <= 1:
               byte = blankline[0:pov*3]
            if val2 > 1:
               if rgbw == 1 and not Night:
                  byte = redline[0:val2*3]
               elif rgbw == 2 and not Night:
                  byte = greline[0:val2*3]
               elif rgbw == 3 and not Night:
                  byte = bluline[0:val2*3]
               elif rgbw > 3 and not Night:
                  byte = gryline[0:val2*3]
               elif Night:
                  byte = dgryline[0:val2*3]
               byte += blankline[0:(pov-val2)*3]
            img += byte
         if count == maxtot or count == mintot:
            mcount = 0
            while mcount < pov:
               img += " zz"
               mcount += 1
         if count == pcont:
            mcount = 0
            while mcount < pov:
               img += "zz "
               mcount += 1
         count += 1
      if len(img) > (pov*256*3):
         img = img[0:pov*256*3]
      imageg = pygame.image.fromstring(img, (pov, 256), "RGB", 1)
      if graph == 1:
         imageg.set_alpha(127)
      windowSurfaceObj.blit(imageg, (pox, poy))

   if not auto_g:
      pygame.draw.line(   windowSurfaceObj, purpleColor, (w2 + bcorrect/100 - 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 + 5, h2 - acorrect/100 + 5))
      pygame.draw.line(   windowSurfaceObj, purpleColor, (w2 + bcorrect/100 + 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 - 5, h2 - acorrect/100 + 5))
   else:
      if ttot > 1:
         pygame.draw.line(windowSurfaceObj, greenColor,  (w2 + bcorrect/100 - 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 + 5, h2 - acorrect/100 + 5))
         pygame.draw.line(windowSurfaceObj, greenColor,  (w2 + bcorrect/100 + 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 - 5, h2 - acorrect/100 + 5))
      else:
         pygame.draw.line(windowSurfaceObj, yellowColor, (w2 + bcorrect/100 - 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 + 5, h2 - acorrect/100 + 5))
         pygame.draw.line(windowSurfaceObj, yellowColor, (w2 + bcorrect/100 + 5, h2 - acorrect/100 - 5), (w2 + bcorrect/100 - 5, h2 - acorrect/100 + 5))

   if not fc or use_Pi_Cam or not camera_connected or thres:
      if maxwin != crop:
         pygame.draw.rect(windowSurfaceObj, bredColor, Rect(w2 - c1, h2 - c2, crop, crop), 1)
      pygame.draw.line(windowSurfaceObj,    bredColor, (w2 - 4, h2),     (w2 + 4, h2))
      pygame.draw.line(windowSurfaceObj,    bredColor, (w2,     h2 - 4), (w2,     h2 + 4))
      if not auto_g:
         keys2(Vcorrt,    16, 9,          0, 0, 0, 0, 0, 0, 0, 0)
         keys2(Hcorrt,    16, 9, width - 80, 0, 0, 0, 0, 0, 0, 0)
      else:
         if ttot > 1:
            keys2(Vcorrt, 16, 1,          0, 0, 0, 0, 0, 0, 0, 0)
            keys2(Hcorrt, 16, 1, width - 80, 0, 0, 0, 0, 0, 0, 0)
         else:
            keys2(Vcorrt, 16, 2,          0, 0, 0, 0, 0, 0, 0, 0)
            keys2(Hcorrt, 16, 2, width - 80, 0, 0, 0, 0, 0, 0, 0)

   if Display == 1:
      pygame.display.update(0, 0, width + 150, height)
   else:
      pygame.display.update(0, 0, width,       height)

# read mouse or keyboard

   for event in pygame.event.get():
       if event.type == QUIT:
          if use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
          pygame.quit()
          sys.exit()

       elif event.type == MOUSEBUTTONUP or event.type == KEYDOWN:
          start = time.time()
          xcount =     0
          ycount =     0
          ymax =       0
          totvcor =    0
          tothcor =    0
          count =      1
          xvcor = [0]*11
          xhcor = [0]*11
          keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
          keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
          if use_RPiGPIO or use_Seeed or use_PiFaceRP:
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
          keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
          keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
          if use_RPiGPIO or use_Seeed or use_PiFaceRP:
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
          restart = 0
          z =  0
          kz = 0
          if event.type == KEYDOWN:
             kz = event.key

          if event.type == MOUSEBUTTONUP:
             mousex, mousey = event.pos
             if Display == 1:
                x = mousex/bw
                if mousey > height:
                   y = (mousey-height)/bh
                   z = 10*x + y
             else:
                if mousex > width:
                   if mousey < bh * 5:
                      x = int((mousex - width)/bw)
                      y = int(mousey/bh) + 1
                      z = 10*x + y
                   if mousey > bh*5 and mousey < bh*10:
                      x = int((mousex - width)/bw) + 6
                      y = int((mousey - 5*bh)/bh) + 1
                      z = 10*x + y
                   if mousey > bh*10:
                      x = int((mousex - width)/bw) + 12
                      y = int((mousey - 10*bh)/bh) + 1
                      z = 10*x + y
             if ((Display != 1 and mousex > (width - 55)) or (Display == 1 and mousex > width + 60)) and ((Display != 1 and mousex < (width - 5)) or (Display == 1 and mousex < width +110)) and mousey > 20 and mousey < 276 and graph > 0:
                if ((Display != 1 and mousex > (width - 55)) or (Display == 1 and mousex > width + 60)) and ((Display != 1 and mousex < (width - 5)) or (Display == 1 and mousex < width +110)) and mousey > (256 - maxtot) and mousey < 276:
                   level = 276 - mousey
                   threshold = maxtot - level
                   threshold = max(threshold, 1)
             else:
                if mousex < width and mousey < height:
                   start = time.time()
                   xcount =  0
                   ycount =  0
                   totvcor = 0
                   tothcor = 0
                   count =   1
                   while count <= 10:
                      xvcor[count] = 0
                      xhcor[count] = 0
                      count += 1
                   offset3o = offset3
                   offset4o = offset4
                   offset3 = mousex - width/2
                   offset4 = mousey - height/2
                   if (width/2 + offset3 + crop/2) >= width or (width/2 + offset3 - crop/2) <= 1:
                      offset3 = offset3o
                      offset4 = offset4o
                   if (height/2 + offset4 + crop/2) >= height or (height/2 + offset4 - crop/2) <= 1:
                      offset3 = offset3o
                      offset4 = offset4o
          if ((z > 60 and z < 76) or z == 5 or z == 4 or z == 15 or z == 14 or z == 154) and use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
          if esc1 > 0 and z != 141 and kz != K_ESCAPE:
             esc1 = 0
             keys2("Esc",                      fs,       5,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
          if z == 115 or kz == 304 or kz == 303:
             con_cap += 1
             if con_cap > 1:
                con_cap = 0
             change = 1
          elif z == 141 or kz == K_ESCAPE:
             if esc1 == 0:
                keys2("Esc",                      fs,       2,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
             if esc1 > 0:
                if use_Pi_Cam and camera_connected:
                   os.killpg(p.pid, signal.SIGTERM)
                if serial_connected:
                   lx200(':Q#', ':Q#', decN, decS)
                if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
                keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
                keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
                keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
                pygame.quit()
                sys.exit()
             esc1 += 1
          elif z == 114 or kz == K_s:
             keys2("scr", fs, 1, b2x, bw, 5, b2y, bh, 5, 0, 1)
             keys2("cap", fs, 1, b2x, bw, 5, b2y, bh, 5, 2, 1)
             now = datetime.datetime.now()
             timestamp = now.strftime("%y%m%d%H%M%S")
             pygame.image.save(windowSurfaceObj, '/home/pi/scr' + str(timestamp) + "_"  + str(pct) + '.bmp')
             keys2("scr", fs, 6, b2x, bw, 5, b2y, bh, 5, 0, 1)
             keys2("s",   fs, 5, b2x, bw, 5, b2y, bh, 5, 0, 0)
             keys2("cap", fs, 6, b2x, bw, 5, b2y, bh, 5, 2, 1)
             pct += 1
          elif z == 104 and use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
             keys2("pic", fs, 1, b2x, bw, 4, b2y, bh, 5, 0, 1)
             keys2("cap", fs, 1, b2x, bw, 4, b2y, bh, 5, 2, 1)
             now = datetime.datetime.now()
             timestamp = now.strftime("%y%m%d%H%M%S")
             fname = '/home/pi/pic' + str(timestamp) + "_" + str(pcu) + '.jpg'
             rpistr = "raspistill -o " + str(fname) + " -co " + str(rpico) + " -br " + str(rpibr)
             if rpiex != 'off':
                rpistr += " -t 800 -ex " + rpiex
             else:
                rpistr += " -t 500 -ss " + str(rpiss)
             if rpiISO > 0:
                rpistr += " -ISO " + str(rpiISO)
             if rpiev != 0:
                rpistr += " -ev " + str(rpiev)
             rpistr += " -n -sa " + str(rpisa)
             path = rpistr + ' -w 2592 -h 1944'
             os.system(path)
             keys2("pic", fs, 6, b2x, bw, 4, b2y, bh, 5, 0, 1)
             keys2("cap", fs, 6, b2x, bw, 4, b2y, bh, 5, 2, 1)
             pcu += 1
             restart = 1
          elif (z == 151 or z == 161 or z == 171 or kz == K_0) and zoom == Image_window:
             offset4 -= 5
             if ((height/2 + offset4 + crop/2) >= height) or ((height/2 + offset4 - crop/2) <= 1):
                offset4 += 5
             if z == 151:
                offset3 -= 5
                if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                   offset3 += 5
             if z == 171:
                offset3 += 5
                if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                   offset3 -= 5
          elif (z == 153 or z == 163 or z == 173 or kz == K_9) and zoom == Image_window:
             offset4 += 5
             if ((height/2 + offset4 + crop/2) >= height) or ((height/2 + offset4 - crop/2) <= 1):
                offset4 -= 5
             if z == 153:
                offset3 -= 5
                if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                   offset3 += 5
             if z == 173:
                offset3 += 5
                if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                   offset3 -= 5
          elif (z == 172 or kz == K_8) and zoom == Image_window:
             offset3 += 5
             if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                offset3 -= 5
          elif (z == 152 or kz == K_7) and zoom == Image_window:
             offset3 -= 5
             if ((width/2 + offset3 + crop/2) >= width) or ((width/2 + offset3 - crop/2) <= 1):
                offset3 += 5

          elif (z == 151 or z == 161 or z == 171) and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 -= 5
             if offset6 > 0 and offset6 >= h/2 - height/2:
                offset6 += 5
             if offset6 < 0 and offset6 <= height/2 - h/2:
                offset6 += 5
             if z == 151:
                offset5 -= 5
                if offset5 > 0 and offset5 >= w/2 - width/2:
                   offset5 += 5
                if offset5 < 0 and offset5 <= width/2 - w/2:
                   offset5 += 5
             if z == 171:
                offset5 += 5
                if offset5 > 0 and offset5 >= w/2 - width/2:
                   offset5 -= 5
                if offset5 < 0 and offset5 <= width/2 - w/2:
                   offset5 -= 5
          elif (z == 153 or z == 163 or z == 173) and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 += 5
             if offset6 > 0 and offset6 >= h/2 - height/2:
                offset6 -= 5
             if offset6 < 0 and offset6 <= height/2 - h/2:
                offset6 -= 5
             if z == 173:
                offset5 += 5
                if offset5 > 0 and offset5 >= w/2 - width/2:
                   offset5 -= 5
                if offset5 < 0 and offset5 <= width/2 - w/2:
                   offset5 -= 5
             if z == 153:
                offset5 -= 5
                if offset5 > 0 and offset5 >= w/2 - width/2:
                   offset5 += 5
                if offset5 < 0 and offset5 <= width/2 - w/2:
                   offset5 += 5
          elif z == 172 and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset5 += 5
             if offset5 > 0 and offset5 >= w/2 - width/2:
                offset5 -= 5
             if offset5 < 0 and offset5 <= width/2 - w/2:
                offset5 -= 5
          elif z == 152 and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset5 -= 5
             if offset5 > 0 and offset5 >= w/2 - width/2:
                offset5 += 5
             if offset5 < 0 and offset5 <= width/2 - w/2:
                offset5 += 5
          elif z == 162 and zoom > Image_window:
             offset6a = offset6
             offtry = 0
             while offtry < 10 and (offset6a == offset6):
                offset4a = int(offset4 * (1 - offtry/10))
                offset6a = offset6 + offset4a
                if (offset6a > 0 and offset6a >= h/2 - height/2) or (offset6a < 0 and offset6a <= height/2 - h/2):
                   offset6a -= offset4a
                offtry += 1
             if offtry < 10:
                offset6 = offset6a
                offset4 -= offset4a
             offset5a = offset5
             offtry = 1
             while offtry < 10 and (offset5a == offset5):
                offset3a = int(offset3/offtry)
                offset5a = offset5 + offset3a
                if (offset5a > 0 and offset5a >= w/2 - width/2) or (offset5a < 0 and offset5a <= width/2 - w/2):
                   offset5a -= offset3a
                offtry += 1
             if offtry < 10:
                offset5 = offset5a
                offset3 -= offset3a
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
          elif z == 162 and zoom == Image_window:
             offset3 = 0
             offset4 = 0
          elif z == 54:
             Interval = Intervals
             Interval += 1
             Intervals = Interval
             change = 1
          elif z == 44:
             Interval = Intervals
             Interval -= 1
             Intervals = Interval
             if Interval < 1:
                Interval = 1
                Intervals = Interval
             change = 1

          elif z == 71:
             rpibr += 2
             rpibr = min(rpibr, 100)
             if camera_connected and not use_Pi_Cam:
                cam.set_controls(0, 0, rpibr)
             restart = 1
             change = 1
          elif z == 61:
             rpibr -= 2
             rpibr = max(rpibr, 0)
             if camera_connected and not use_Pi_Cam:
                cam.set_controls(0, 0, rpibr)
             restart = 1
             change = 1
          elif z == 62 and use_Pi_Cam:
             rpico -= 5
             rpico = max(rpico, -100)
             restart = 1
             change = 1
          elif z == 72 and use_Pi_Cam:
             rpico += 5
             rpico = min(rpico, 100)
             restart = 1
             change = 1
          elif z == 63 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
             if rpiss < 20000:
                rpiss -= 1000
             if rpiss >= 20000 and rpiss <= 490000:
                rpiss -= 10000
             if rpiss > 490000:
                rpiss -= 100000
             if rpiss <= 1000:
                rpiss = 1000
             restart = 1
             change = 1
          elif z == 73 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
             if rpiss < 20000:
                rpiss += 1000
             if rpiss >= 20000 and rpiss <= 490000:
                rpiss += 10000
             if rpiss > 490000:
                rpiss += 100000
             if rpiss >= 6000000:
                rpiss = 6000000
             restart = 1
             change = 1

          elif z == 63 and use_Pi_Cam and rpiexa != ' off' and rpiexa != 'nigh2' and rpiexa != 'fwor2' and rpiexa != 'vlon2' and rpiexa != 'spor2':
             if rpiev >= -9:
                rpiev -= 1
             restart = 1
             change = 1
          elif z == 73 and use_Pi_Cam and rpiexa != ' off' and rpiexa != 'nigh2' and rpiexa != 'fwor2' and rpiexa != 'vlon2' and rpiexa != 'spor2':
             if rpiev <= 9:
                rpiev += 1
             restart = 1
             change = 1

          elif z == 65 and use_Pi_Cam:
             if rpiISO > 0:
                rpiISO -= 100
             restart = 1
             change = 1
          elif z == 75 and use_Pi_Cam:
             if rpiISO < 800:
                rpiISO += 100
             restart = 1
             change = 1
          elif z == 132:
             auto_c += 1
             auto_g =   1
             auto_win = 1
             ocrop = crop
             if auto_c > 1:
                auto_c =   0
                auto_win = 0
                crop = ocrop
             keys2("cen",  fs, auto_c, b3x, bw, 1, b3y, bh, 3, 0, 1)
             keys2(" tre", fs, auto_c, b3x, bw, 1, b3y, bh, 3, 2, 1)

          elif z == 121:
             decN = not decN
             change = 1
          elif z == 123:
             decS = not decS
             change = 1
          elif z == 31 or kz == K_r:
             nr +=1
             if nr > 3:
                nr = 0
             change = 1
          elif (z == 105 or kz == K_c) and auto_g:
             cls = not cls
             change = 1

          elif z == 52 or kz == K_f:
             auto_win = 0
             crop += 5
             crop = min(crop, maxwin)
             if (width/2 + offset3 + crop/2) >= width:
                crop -= 5
             if (width/2 + offset3 - crop/2) <= 1:
                crop -= 5
             if (height/2 + offset4 + crop/2) >= height:
                crop -= 5
             if (height/2 + offset4 - crop/2) <= 1:
                crop -= 5
             change = 1

          elif z == 42 or kz == K_d:
             auto_win = 0
             crop -= 5
             crop = max(crop, minwin)
             change = 1

          elif (z == 101 or z == 111 or kz == K_o) and photoon:
             photo = not photo
             if not photo:
                camera = 0
                keys2("",  fs, photo, b2x+18, bw, 4, b2y, bh, 2, 3, 1)
                keys2("",  fs, photo, b2x+14, bw, 5, b2y, bh, 2, 3, 1)
                if use_RPiGPIO or photoon:
                   GPIO.output(C_OP, GPIO.LOW)
             if photo:
                pcount2 = pcount
                keys2("1", fs, photo, b2x+18, bw, 4, b2y, bh, 2, 3, 1)
                ptime2 = time.time() + ptime
                camera = 1
                if use_RPiGPIO or photoon:
                   if pmlock == 1:
                      GPIO.output(C_OP, GPIO.HIGH)
                      time.sleep(0.5)
                      GPIO.output(C_OP, GPIO.LOW)
                      time.sleep(0.5)
                   GPIO.output(C_OP, GPIO.HIGH)
             change = 1
          elif z == 112 and photoon and not photo:
             ptime += 10
             ptime = min(ptime, 990)
             change = 1
          elif z == 102 and photoon and not photo:
             ptime -= 10
             ptime = max(ptime, 10)
             change = 1
          elif z == 113 and photoon and not photo:
             pcount += 1
             pcount = min(pcount, 90)
             change = 1
          elif z == 103 and photoon and not photo:
             pcount -= 1
             pcount = max(pcount, 0)
             change = 1
          elif z == 91:
             nscale += 10
             nscale = min(nscale, 800)
             change = 1
          elif z == 81:
             nscale -= 10
             nscale = max(nscale, 10)
             change = 1
          elif z == 35:
             mind = minc * 10
             mind += 1
             minc = Decimal(mind)/Decimal(10)
             minc = min(minc, 50)
             change = 1
          elif z == 25:
             mind = minc * 10
             mind -= 1
             minc = Decimal(mind)/Decimal(10)
             minc = max(minc, 0.1)
             change = 1
          elif z == 93:
             escale += 10
             escale = min(escale, 800)
             change = 1
          elif z == 83:
             escale -= 10
             escale = max(escale, 10)
             change = 1
          elif z == 92:
             sscale += 10
             sscale = min(sscale, 800)
             change = 1
          elif z == 82:
             sscale -= 10
             sscale = max(sscale, 10)
             change = 1
          elif z == 94:
             wscale += 10
             wscale = min(wscale, 800)
             change = 1
          elif z == 84:
             wscale -= 10
             wscale = max(wscale, 10)
             change = 1
          elif z == 95:
             nscale += 10
             nscale = min(nscale, 800)
             wscale += 10
             wscale = min(wscale, 800)
             sscale += 10
             sscale = min(sscale, 800)
             escale += 10
             escale = min(escale, 800)
             change = 1
          elif z == 85:
             wscale -= 10
             wscale = max(wscale, 10)
             escale -= 10
             escale = max(escale, 10)
             sscale -= 10
             sscale = max(sscale, 10)
             nscale -= 10
             nscale = max(nscale, 10)
             change = 1
          elif z == 51 or kz == K_b:
             rgbw += 1
             if rgbw > 5:
                rgbw = 1
             change = 1
          elif z == 41 or kz == K_v:
             rgbw -= 1
             if rgbw < 1:
                rgbw = 5
             change = 1
          elif z == 43:
             threshold -= 1
             threshold = max(threshold, 1)
             auto_t = 0
             change = 1
          elif z == 53:
             threshold += 1
             threshold = min(threshold, 100)
             auto_t = 0
             change = 1
          elif z == 133 or kz == K_DOWN:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mgs' + blan[(len(blan))-4:len(blan)]
                keys2("S", fs, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
                lx200(move, ':Mgw0000', decN, decS)
                keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                keys2("S", fs, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
                time.sleep(mincor/100)
                keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif z == 131 or kz == K_UP:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mgn' + blan[(len(blan))-4:len(blan)]
                keys2("N", fs, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
                lx200(move, ':Mgw0000', decN, decS)
                keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                keys2("N", fs, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
                time.sleep(mincor/100)
                keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif z == 122 or kz == K_LEFT:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mgw' + blan[(len(blan))-4:len(blan)]
                keys2("W", fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
                lx200(move, ':Mgs0000', decN, decS)
                keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                keys2("W", fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
                time.sleep(mincor/100)
                keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif z == 142 or kz == K_RIGHT:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mge' + blan[(len(blan))-4:len(blan)]
                keys2("E", fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
                lx200(move, ':Mgs0000', decN, decS)
                keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                keys2("E", fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
                time.sleep(mincor/100)
                keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif z == 143 or kz == K_END:
             auto_g = 0
             if serial_connected:
                lx200(':Q#', ':Q#', decN, decS)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP:
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             keys2("N", fs, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
             keys2("S", fs, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
             keys2("W", fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
             keys2("E", fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
             change = 1

          elif z == 34 or kz == K_i:
                auto_i = not auto_i
                change = 1

          elif z == 21 or kz == K_x:
                binn = not binn
                change = 1

          elif z == 1 or z == 11 or kz == K_a:
             auto_g = not auto_g
             if auto_g:
                start = time.time()
                xcount = 0
                ycount = 0
                totvcor = 0
                tothcor = 0
                count = 1
                while count <= avemax:
                   xvcor[count] = 0
                   xhcor[count] = 0
                   count += 1
             else:
                log = 0
                cls = 0
             change = 1

          elif z == 4:
             if rpired > 50:
                rpired -= 1
                rpiredx = Decimal(rpired)/Decimal(100)
             restart = 1
             change = 1
          elif z == 14:
             if rpired < 200:
                rpired += 1
                rpiredx = Decimal(rpired)/Decimal(100)
             restart = 1
             change = 1
          elif z == 5:
             if rpiblue > 50:
                rpiblue -= 1
                rpibluex = Decimal(rpiblue)/Decimal(100)
             restart = 1
             change = 1
          elif z == 15:
             if rpiblue < 200:
                rpiblue += 1
                rpibluex = Decimal(rpiblue)/Decimal(100)
             restart = 1
             change = 1
          elif z == 13 or kz == K_h:
             thres = not thres
             change = 1
          elif z == 12 or kz == K_g:
             graph += 1
             if graph > 2:
                graph = 0
             change = 1
          elif z == 2 or kz == K_p:
             plot += 1
             if plot > 2:
                plot = 0
             change = 1
          elif z == 32 or kz == K_w:
             auto_win = not auto_win
             change = 1
          elif z == 33 or kz == K_t:
             auto_t = not auto_t
             change = 1
          elif z == 74 and use_Pi_Cam:
             if rpiexno < 9:
                rpiexno += 1
                rpiex =   rpimodes[rpiexno]
                rpiexa = rpimodesa[rpiexno]
             restart = 1
             change = 1
          elif kz == K_m and use_Pi_Cam:
             rpiexno += 1
             if rpiexno > 9:
                rpiexno = 0
             rpiex = rpimodes[rpiexno]
             restart = 1
             change = 1
          elif z == 64 and use_Pi_Cam:
             if rpiexno > 0:
                rpiexno -= 1
                rpiex = rpimodes[rpiexno]
                rpiexa = rpimodesa[rpiexno]
             restart = 1
             change = 1
          elif (z == 3 or kz == K_l) and auto_g:
             log = not log
             if log:
                now = datetime.datetime.now()
                timestamp = now.strftime("%y%m%d%H%M%S")
                logfile = "/run/shm/" + str(timestamp) + ".txt"
             change = 1
          elif z == 55 or kz == K_z:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if (not use_Pi_Cam and zoom < usb_max_res) or (use_Pi_Cam and Pi_Cam == 1 and zoom < 7) or (use_Pi_Cam and Pi_Cam == 2 and zoom < 8):#
                zoom += 1
                if camera_connected:
                   w = rpiwidth[zoom]
                   h = rpiheight[zoom]
                   scalex = rpiscalex[zoom]
                   scaley = rpiscaley[zoom]
                   nscale /= scaley
                   escale /= scalex
                   sscale /= scaley
                   wscale /= scalex
                   offset5 = int((offset5 + offset3)*scalex)
                   offset6 = int((offset6 + offset4)*scaley)
                   if offset5 > 0 and offset5 >= w/2 - width/2:
                      offset5 = w/2 - width/2
                   if offset5 < 0 and offset5 <= width/2 - w/2:
                      offset5 = width/2 - w/2
                   if offset6 > 0 and offset6 >= h/2 - height/2:
                      offset6 = h/2 - height/2
                   if offset6 < 0 and offset6 <= height/2 - h/2:
                      offset6 = height/2 - h/2
                   offset3 = 0
                   offset4 = 0
                   if not use_Pi_Cam and camera_connected:
                      cam.stop()
                      pygame.camera.init()
                      if not zoom:
                         cam = pygame.camera.Camera("/dev/video0", (320, 240))
                      elif zoom == 1 and usb_max_res >= 1:
                         cam = pygame.camera.Camera("/dev/video0", (352, 288))
                      elif zoom == 2 and usb_max_res >= 2:
                         cam = pygame.camera.Camera("/dev/video0", (640, 480))
                      elif zoom == 3 and usb_max_res >= 3:
                         cam = pygame.camera.Camera("/dev/video0", (800, 600))
                      elif zoom == 4 and usb_max_res >= 4:
                         cam = pygame.camera.Camera("/dev/video0", (960, 720))
                      elif zoom == 5 and usb_max_res >= 5:
                         cam = pygame.camera.Camera("/dev/video0", (1280, 960))
                      elif zoom == 6 and usb_max_res >= 6:
                         cam = pygame.camera.Camera("/dev/video0", (1920, 1440))
                      elif zoom == 7 and usb_max_res >= 7:
                         cam = pygame.camera.Camera("/dev/video0", (2592, 1944))
                      cam.start()
                   if not zoom:
                      offset3 /= 2
                      offset4 /= 2
                if not camera_connected:
                   wd = 20 + zoom*4
                   hd = wd
             restart = 1
             change = 1
          elif z == 45 or kz == K_q:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if zoom > min_res:
                zoom -= 1
                if camera_connected:
                   w = rpiwidth[zoom]
                   h = rpiheight[zoom]
                   scalex = rpiscalex[zoom +1]
                   scaley = rpiscalex[zoom +1]
                   nscale *= scaley
                   escale *= scalex
                   sscale *= scaley
                   wscale *= scalex
                   offset5 = int((offset5 + offset3)/scalex)
                   offset6 = int((offset6 + offset4)/scaley)
                   if offset5 > 0 and offset5 >= w/2 - width/2:
                      offset5 = w/2 - width/2
                   if offset5 < 0 and offset5 <= width/2 - w/2:
                      offset5 = width/2 - w/2
                   if offset6 > 0 and offset6 >= h/2 - height/2:
                      offset6 = h/2 - height/2
                   if offset6 < 0 and offset6 <= height/2 - h/2:
                      offset6 = height/2 - h/2
                   offset3 = 0
                   offset4 = 0
                   if not use_Pi_Cam:
                      cam.stop()
                      pygame.camera.init()
                      if not zoom:
                         cam = pygame.camera.Camera("/dev/video0", (320, 240))
                      elif zoom == 1 and usb_max_res >= 1:
                         cam = pygame.camera.Camera("/dev/video0", (352, 288))
                      elif zoom == 2 and usb_max_res >= 2:
                         cam = pygame.camera.Camera("/dev/video0", (640, 480))
                      elif zoom == 3 and usb_max_res >= 3:
                         cam = pygame.camera.Camera("/dev/video0", (800, 600))
                      elif zoom == 4 and usb_max_res >= 4:
                         cam = pygame.camera.Camera("/dev/video0", (960, 720))
                      elif zoom == 5 and usb_max_res >= 5:
                         cam = pygame.camera.Camera("/dev/video0", (1280, 960))
                      elif zoom == 6 and usb_max_res >= 6:
                         cam = pygame.camera.Camera("/dev/video0", (1920, 1440))
                      elif zoom == 7 and usb_max_res >= 7:
                         cam = pygame.camera.Camera("/dev/video0", (2592, 1944))
                      cam.start()
                   if not zoom:
                      offset3 /= 2
                      offset4 /= 2
                if not camera_connected:
                   wd = 20 + zoom*4
                   hd = wd
             restart = 1
             change = 1
          elif z == 22 or kz == K_n:
             nsi = not nsi
             change = 1
          elif z == 24:
             Night = not Night
             if not Night:
                redColor =    pygame.Color(255,   0,   0)
                greenColor =  pygame.Color(  0, 255,   0)
                blueColor =   pygame.Color(  0,   0, 255)
                greyColor =   pygame.Color(128, 128, 128)
                dgryColor =   pygame.Color( 64,  64,  64)
                lgryColor =   pygame.Color(192, 192, 192)
                blackColor =  pygame.Color(  0,   0,   0)
                whiteColor =  pygame.Color(200, 200, 200)
                purpleColor = pygame.Color(255,   0, 255)
                yellowColor = pygame.Color(255, 255,   0)
             else:
                whiteColor =  pygame.Color( 50,  20,  20)
                greyColor =   pygame.Color(128,  70,  70)
                dgryColor =   pygame.Color(  0,   0,   0)
                greenColor =  pygame.Color(  0, 128,   0)
                purpleColor = pygame.Color(128,   0, 128)
                yellowColor = pygame.Color(128, 128,   0)
                blueColor =   pygame.Color(  0,   0, 150)
                redColor =    pygame.Color(  0,   0,   0)
             button2(      b1x, 1,          b1y, 2,  bw, 2, bh, auto_g)
             button2(      b1x, 3,          b1y, 2,  bw, 1, bh, binn)
             button2(      b1x, 4,          b1y, 2,  bw, 1, bh, nr)
             button2(      b1x, 1,          b1y, 3,  bw, 1, bh, plot)
             button2(      b1x, 1,          b1y, 4,  bw, 1, bh, log)
             button2(      b1x, 2,          b1y, 3,  bw, 1, bh, graph)
             button2(      b1x, 2,          b1y, 4,  bw, 1, bh, thres)
             button2(      b1x, 4,          b1y, 3,  bw, 1, bh, auto_win)
             button2(      b1x, 4,          b1y, 4,  bw, 1, bh, auto_t)
             button2(      b1x, 4,          b1y, 5,  bw, 1, bh, auto_i)
             button2(      b1x, 3,          b1y, 3,  bw, 1, bh, nsi)
             button2(      b1x, 3,          b1y, 4,  bw, 1, bh, ewi)
             button2(      b1x, 3,          b1y, 6,  bw, 2, bh, 0)
             button2(      b1x, 3,          b1y, 5,  bw, 1, bh, 0)
             cy = 2
             while cy <= 6:
                button2(   b1x, 5,          b1y, cy, bw, 2, bh, 0)
                button2(   b2x, 3,          b2y, cy, bw, 2, bh, 0)
                cy += 1
             if use_Pi_Cam and camera_connected:
                cy = 3
                while cy <= 6:
                   button2(b2x, 1,          b2y, cy, bw, 2, bh, 0)
                   cy += 1
                button2(   b1x, 1,          b1y, 5,  bw, 2, bh, 0)
                button2(   b1x, 1,          b1y, 6,  bw, 2, bh, 0)
             button2(      b2x, 1,          b2y, 2,  bw, 2, bh, 0)
             if photoon:
                button2(   b2x, 5,          b2y, 2,  bw, 2, bh, 0)
                button2(   b2x, 5,          b2y, 3,  bw, 2, bh, 0)
                button2(   b2x, 5,          b2y, 4,  bw, 2, bh, 0)
             if use_Pi_Cam:
                button2(   b2x, 5,          b2y, 5,  bw, 1, bh, 0)
             button2(      b2x, 6,          b2y, 5,  bw, 1, bh, 0)
             button2(      b2x, 6,          b2y, 6,  bw, 1, bh, con_cap)
             button2(      b3x, 1,          b3y, 3,  bw, 1, bh, 0)
             button2(      b3x, 1,          b3y, 2,  bw, 1, bh, decN)
             button2(      b3x, 1,          b3y, 4,  bw, 1, bh, decS)
             if decN:
                button2(   b3x, 2,          b3y, 2,  bw, 1, bh, 0)
             else:
                button2(   b3x, 2,          b3y, 2,  bw, 1, bh, 1)
             if decS:
                button2(   b3x, 2,          b3y, 4,  bw, 1, bh, 0)
             else:
                button2(   b3x, 2,          b3y, 4,  bw, 1, bh, 1)
             button2(      b3x, 3,          b3y, 3,  bw, 1, bh, 0)
             button2(      b3x, 5,          b3y, 2,  bw, 1, bh, 0)
             button2(      b3x, 5,          b3y, 4,  bw, 1, bh, 0)
             button2(      b3x, 4,          b3y, 3,  bw, 1, bh, 0)
             button2(      b3x, 6,          b3y, 3,  bw, 1, bh, 0)
             button2(      b3x, 1,          b3y, 6,  bw, 1, bh, 0)
             button2(      b3x, 2,          b3y, 6,  bw, 1, bh, 0)
             button2(      b3x, 3,          b3y, 6,  bw, 1, bh, 0)
             if use_config > 0:
                button2(   b3x, use_config, b3y, 6,  bw, 1, bh, 3)
             button2(      b3x, 4,          b3y, 6,  bw, 1, bh, 0)
             button2(      b3x, 5,          b3y, 6,  bw, 1, bh, 0)
             button2(      b3x, 6,          b3y, 6,  bw, 1, bh, 0)
             keys2(str(int(nscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 2, 3, 0)
             keys2(str(int(sscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 3, 3, 0)
             keys2(str(int(escale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 4, 3, 0)
             keys2(str(int(wscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 5, 3, 0)
             keys2(str(threshold),             fs,   3,        b1x,         bw,   5,     b1y, bh, 4, 3, 0)
             keys2(str(Interval),              fs,   3,        b1x,         bw,   5,     b1y, bh, 5, 3, 0)
             keys2(str(zoom),                  fs,   3,        b1x,         bw,   5,     b1y, bh, 6, 3, 0)
             keys2(str(rpibr),                 fs,   3,        b2x,         bw,   1,     b2y, bh, 2, 3, 0)
             keys2(str(int(minc)),                fs,       3,        b1x,         bw,   3,     b1y, bh, 6, 3, 0)

             msg = rgb[rgbw]
             if rgbw < 5:
                keys2(msg,                     fs,   rgbw+2,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
             else:
                keys2(msg,                     fs,   rgbw+1,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
             keys2(str(crop),                  fs,   3,        b1x,         bw,   5,     b1y, bh, 3, 3, 0)
             keys2("AWin",                     fs-1, auto_win, b1x,         bw,   3,     b1y, bh, 3, 1, 0)
             keys2("W",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 3, 1, 0)
             keys2("AThr",                     fs-1, auto_t,   b1x,         bw,   3,     b1y, bh, 4, 1, 0)
             keys2("T",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 4, 1, 0)
             keys2("AutoG",                    fs,   auto_g,   b1x,         bw,   0,     b1y, bh, 2, 1, 0)
             keys2("A",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 2, 1, 0)
             keys2("2x2",                      fs,   binn,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
             keys2("x",                        fs,   5,        b1x+fs/2,    bw,   2,     b1y, bh, 2, 1, 0)
             keys2("Log",                      fs,   log,      b1x,         bw,   0,     b1y, bh, 4, 1, 0)
             keys2("L",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 4, 1, 0)
             keys2("Gph",                      fs,   graph,    b1x,         bw,   1,     b1y, bh, 3, 1, 0)
             keys2("G",                        fs,   5,        b1x,         bw,   1,     b1y, bh, 3, 1, 0)
             keys2("Plot",                     fs,   plot,     b1x,         bw,   0,     b1y, bh, 3, 1, 0)
             keys2("P",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 3, 1, 0)
             keys2("Thr",                      fs,   thres,    b1x,         bw,   1,     b1y, bh, 4, 1, 0)
             keys2("h",                        fs,   5,        b1x+fs/1.5,  bw,   1,     b1y, bh, 4, 1, 0)
             keys2("NSi",                      fs,   nsi,      b1x,         bw,   2,     b1y, bh, 3, 1, 0)
             keys2("N",                        fs,   5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
             keys2("EWi",                      fs,   ewi,      b1x,         bw,   2,     b1y, bh, 4, 1, 0)
             keys2("E",                        fs,   5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)  
             keys2("AInt",                     fs-1, auto_i,   b1x,         bw,   3,     b1y, bh, 5, 1, 0)
             keys2("I",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 5, 1, 0)
             keys2("rgbw",                     fs,   6,        b1x,         bw,   4,     b1y, bh, 2, 0, 0)
             keys2("b",                        fs,   5,        b1x+fs,      bw,   4,     b1y, bh, 2, 0, 0)
             keys2(" <",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 2, 4, 0)
             keys2(">",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 2, 4, 0)
             keys2("window",                   fs,   6,        b1x,         bw,   4,     b1y, bh, 3, 0, 0)
             keys2(" -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 3, 4, 0)
             keys2("+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 3, 4, 0)
             keys2("threshold",                fs-1, 6,        b1x,         bw,   4,     b1y, bh, 4, 0, 0)
             keys2(" -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 4, 4, 0)
             keys2("+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 4, 4, 0)
             keys2("interval",                 fs,   6,        b1x,         bw,   4,     b1y, bh, 5, 0, 0)
             keys2(" -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 5, 4, 0)
             keys2("+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 5, 4, 0)
             keys2("Zoom",                     fs,   6,        b1x,         bw,   4,     b1y, bh, 6, 0, 0)
             keys2(" -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 6, 4, 0)
             keys2("+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 6, 4, 0)
             keys2("Min Corr",                 fs,   6,        b1x,         bw,   2,     b1y, bh, 6, 0, 0)
             keys2(" -",                       fs,   6,        b1x,         bw,   2,     b1y, bh, 6, 4, 0)
             keys2("+",                        fs,   6,        b1x+bw-fs,   bw,   3,     b1y, bh, 6, 4, 0)
             keys2("scale N",                  fs,   6,        b2x,         bw,   2,     b2y, bh, 2, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 2, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 2, 4, 0)
             keys2("scale S",                  fs,   6,        b2x,         bw,   2,     b2y, bh, 3, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 3, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 3, 4, 0)
             keys2("scale E",                  fs,   6,        b2x,         bw,   2,     b2y, bh, 4, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 4, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 4, 4, 0)
             keys2("scale W",                  fs,   6,        b2x,         bw,   2,     b2y, bh, 5, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 5, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 5, 4, 0)
             keys2("scale all",                fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 6, 4, 0)
             keys2("Brightness",               fs-2, 6,        b2x,         bw,   0,     b2y, bh, 2, 0, 0)
             keys2(" -",                       fs,   6,        b2x,         bw,   0,     b2y, bh, 2, 4, 0)
             keys2("+",                        fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 2, 4, 0)

             if use_Pi_Cam and camera_connected:
                keys2(str(rpico),              fs,   3,        b2x,         bw,   1,     b2y, bh, 3, 3, 0)
                rpiexa = rpimodesa[rpiexno]
                if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
                   keys2(str(int(rpiss/1000)), fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
                else:
                   keys2(str(int(rpiev)),      fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
                keys2((rpimodesa[rpiexno]),    fs,   3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                keys2(str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                if not rpiISO:
                   keys2('auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                keys2("Contrast",              fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 0, 0)
                keys2(" -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 4, 0)
                keys2("+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 3, 4, 0)
                if rpiex == 'off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
                   keys2("Exp Time",           fs-1, 6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
                else:
                   keys2("     eV",            fs,   6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
                keys2(" -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
                keys2("+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
                keys2("ISO",                   fs,   6,        b2x,         bw*2, 0,     b2y, bh, 6, 0, 0)
                keys2(" -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
                keys2("+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
                keys2("Exp Mode",              fs-1, 6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
                keys2(" <",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
                keys2(">",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
                keys2("Adj Red",               fs,   6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
                keys2(" -",                    fs,   6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
                keys2("+",                     fs,   6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
                keys2("Adj Blue",              fs,   6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
                keys2(" -",                    fs,   6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
                keys2("+",                     fs,   6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
                rpiredx = Decimal(rpired)/Decimal(100)
                rpibluex = Decimal(rpiblue)/Decimal(100)
                keys2(str(rpiredx),            fs,   3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
                keys2(str(rpibluex),           fs,   3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
             hor = 0
             while hor < 4:
                keys2("N",                     fs,   6,        b3x,         bw,   1+hor, b3y, bh, 2, 2, 0)
                keys2("E",                     fs,   6,        b3x,         bw,   2+hor, b3y, bh, 3, 2, 0)
                keys2("S",                     fs,   6,        b3x,         bw,   1+hor, b3y, bh, 4, 2, 0)
                keys2("W",                     fs,   6,        b3x,         bw,   hor,   b3y, bh, 3, 2, 0)
                hor += 3
             keys2("Esc",                      fs,   5,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
             keys2("DEC",                      fs-1, decN,     b3x,         bw,   0,     b3y, bh, 2, 0, decN)
             keys2("  N",                      fs-1, decN,     b3x,         bw,   0,     b3y, bh, 2, 2, decN)
             keys2("nr",                       fs,   nr,       b1x,         bw,   3,     b1y, bh, 2, 1, nr)
             keys2("DEC",                      fs-1, decS,     b3x,         bw,   0,     b3y, bh, 4, 0, decS)
             keys2("  S",                      fs-1, decS,     b3x,         bw,   0,     b3y, bh, 4, 2, decS)
             keys2(" R1",                      fs,   6,        b3x,         bw,   0,     b3y, bh, 6, 1, 0)
             keys2("1",                        fs,   5,        b3x+fs,      bw,   0,     b3y, bh, 6, 1, 1)
             keys2(" R2",                      fs,   6,        b3x,         bw,   1,     b3y, bh, 6, 1, 0)
             keys2("2",                        fs,   5,        b3x+fs,      bw,   1,     b3y, bh, 6, 1, 0)
             keys2(" R3",                      fs,   6,        b3x,         bw,   2,     b3y, bh, 6, 1, 0)
             keys2("3",                        fs,   5,        b3x+fs,      bw,   2,     b3y, bh, 6, 1, 0)
             keys2(" S1",                      fs,   6,        b3x,         bw,   3,     b3y, bh, 6, 1, 0)
             keys2(" S2",                      fs,   6,        b3x,         bw,   4,     b3y, bh, 6, 1, 0)
             keys2(" S3",                      fs,   6,        b3x,         bw,   5,     b3y, bh, 6, 1, 0)
             keys2("RELOAD cfg",               fs-2, 7,        b3x+bw/6,    bw,   0,     b3y, bh, 5, 4, 0)
             keys2("SAVE cfg",                 fs-2, 7,        b3x+bw/2,    bw,   3,     b3y, bh, 5, 4, 0)
             if Night:
                keys2("Day",                   fs-1, 6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
             else:
                keys2("Night",                 fs-1, 6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
             keys2("TELESCOPE",                fs,   1,        b3x+bw/5,    bw,   0,     b3y, bh, 5, 0, 0)
             keys2("WINDOW",                   fs,   1,        b3x+bw/2,    bw,   3,     b3y, bh, 5, 0, 0)
             keys2("Stop",                     fs,   7,        b3x,         bw,   2,     b3y, bh, 4, 1, 0)
             keys2("cen",                      fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
             keys2(" tre",                     fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
             keys2("cen",                      fs,   7,        b3x,         bw,   4,     b3y, bh, 3, 0, 0)
             keys2(" tre",                     fs,   7,        b3x,         bw,   4,     b3y, bh, 3, 2, 0)
             keys2("con",                      fs,   con_cap,  b2x,         bw,   5,     b2y, bh, 6, 0, 0)
             keys2("cap",                      fs,   con_cap,  b2x,         bw,   5,     b2y, bh, 6, 2, 0)
             if use_Pi_Cam:
                keys2("pic",                   fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 0, 0)
                keys2("cap",                   fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 2, 0)
             keys2("scr",                      fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
             keys2("s",                        fs,   5,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
             keys2("cap",                      fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 2, 0)
             if photoon:
                 keys2("PHOTO",                fs,   photo,    b2x,         bw,   4,     b2y, bh, 2, 0, 0)
                 keys2("O",                    fs,   5,        b2x+fs*1.5,  bw,   4,     b2y, bh, 2, 0, 0)
                 keys2("P-Time",               fs,   6,        b2x,         bw,   4,     b2y, bh, 3, 0, 0)
                 keys2(" -",                   fs,   6,        b2x,         bw,   4,     b2y, bh, 3, 4, 0)
                 keys2("+",                    fs,   6,        b2x+bw-fs,   bw,   5,     b2y, bh, 3, 4, 0)
                 keys2(str(ptime),             fs,   3,        b2x,         bw,   5,     b2y, bh, 3, 3, 0)
                 keys2("P-Count",              fs,   6,        b2x,         bw,   4,     b2y, bh, 4, 0, 0)
                 keys2(" -",                   fs,   6,        b2x,         bw,   4,     b2y, bh, 4, 4, 0)
                 keys2("+",                    fs,   6,        b2x+bw-fs,   bw,   5,     b2y, bh, 4, 4, 0)
                 keys2(str(pcount),            fs,   3,        b2x,         bw,   5,     b2y, bh, 4, 3, 0)
             button2(b2x, 5, b2y, 6, bw, 1, bh, cls)
             keys2("CLS",                      fs,   cls,      b2x,         bw,   4,     b2y, bh, 6, 1, 0)
             keys2("C",                        fs,   5,        b2x,         bw,   4,     b2y, bh, 6, 1, 0)
             if photo == 1:
                keys2(str(pcount + 1 - pcount2),    fs, photo, b2x+18,     bw, 4, b2y, bh, 2, 3, 1)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 15, bh*10 + bh/3 + 10), 2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 5,  bh*10 + bh/3 + 5),  2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (width + bw*3 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                                                                                 
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 5,  bh*10 + bh/3 + 10), 2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 15, bh*10 + bh/3 + 5),  2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (width + bw*5 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                                                                                 
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 5,  bh*12 + bh/3),      (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), 2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 5),  2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (width + bw*5 + bw/4 + 10, bh*12 + bh/3 + 10), 2)
                                                                                                                                                    
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 15, bh*12 + bh/3),      (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), 2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 5),  2)
             pygame.draw.line(windowSurfaceObj, greyColor, (width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (width + bw*3 + bw/4 + 10, bh*12 + bh/3 + 10), 2)
             pygame.display.update()
             change = 1
          elif z == 23 or kz == K_e:
             ewi = not ewi
             change = 1
          elif (z == 155 or z == 165 or z == 175 or kz == K_4 or kz == K_5 or kz == K_6):
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if kz == K_4 or z == 154:
                z = 155
             elif kz == K_5 or z == 164:
                z = 165
             elif kz == K_6 or z == 174:
                z = 175
             deffile = "config" + str((z-145)/10)
             if z == 155:
                keys2(" S1",                   fs,   1,        b3x,         bw,   3,     b3y, bh, 6, 1, 1)
             elif z == 165:
                keys2(" S2",                   fs,   1,        b3x,         bw,   4,     b3y, bh, 6, 1, 1)
             elif z == 175:
                keys2(" S3",                   fs,   1,        b3x,         bw,   5,     b3y, bh, 6, 1, 1)
             fil = "0000"
             timp = str(int(auto_g))
             timp += fil[len(str(int(nscale)))    :len(str(int(nscale)))+4    ] + str(int(nscale))
             timp += fil[len(str(int(sscale)))    :len(str(int(sscale)))+4    ] + str(int(sscale))
             timp += fil[len(str(int(escale)))    :len(str(int(escale)))+4    ] + str(int(escale))
             timp += fil[len(str(int(wscale)))    :len(str(int(wscale)))+4    ] + str(int(wscale))
             timp += str(int(ewi)) + str(int(nsi))
             timp += fil[len(str(crop))           :len(str(crop))+4           ] + str(crop)
             if offset3 < 0:
                offset3a = -int(offset3)
                timp += "9"
             else:
                offset3a = int(offset3)
                timp += "0"
             timp += fil[len(str(offset3a))+1     :len(str(offset3a))+4       ] + str(offset3a)
             if offset5 < 0:
                offset5a = -int(offset5)
                timp += "9"
             else:
                offset5a = int(offset5)
                timp += "0"
             timp += fil[len(str(offset5a))+1     :len(str(offset5a))+4       ] + str(offset5a)
             if offset6 < 0:
                offset6a = -int(offset6)
                timp += "9"
             else:
                offset6a = int(offset6)
                timp += "0"
             timp += fil[len(str(offset6a))+1     :len(str(offset6a))+4       ] + str(offset6a)
             if offset4 < 0:
                offset4a = -int(offset4)
                timp += "9"
             else:
                offset4a = int(offset4)
                timp += "0"
             timp += fil[len(str(offset4a))+1     :len(str(offset4a))+4       ] + str(offset4a)
             timp += fil[len(str(Intervals))      :len(str(Intervals))+4      ] + str(Intervals)
             timp += str(int(log)) + str(rgbw)
             timp += fil[len(str(threshold))      :len(str(threshold))+4  ] + str(threshold)
             timp += str(int(thres)) + str(graph) + str(int(auto_i)) + str(plot)
             timp += str(int(auto_win)) + str(int(auto_t)) + str(zoom)
             timp += fil[len(str(rpibr))          :len(str(rpibr))+4          ] + str(rpibr)
             if rpico < 0:
                rpicoa = -rpico
                timp += "9"
             else:
                rpicoa = rpico
                timp += "0"
             timp += fil[len(str(rpicoa))+1       :len(str(rpicoa))+4         ] + str(rpicoa)
             if rpiev < 0:
                rpieva = -rpiev
                timp += "9"
             else:
                rpieva = rpiev
                timp += "0"
             timp += fil[len(str(rpieva))+1       :len(str(rpieva))+4         ] + str(rpieva)
             timp += fil[len(str(int(rpiss/1000))):len(str(int(rpiss/1000)))+4] + str(int(rpiss/1000))
             timp += fil[len(str(rpiISO))         :len(str(rpiISO))+4         ] + str(rpiISO)
             timp += str(rpiexno) + str(int(binn)) + str(int(nr)) + str(int(decN)) + str(int(decS))
             timp += fil[len(str(rpired))+1       :len(str(rpired))+4         ] + str(rpired)
             timp += fil[len(str(rpiblue))+1      :len(str(rpiblue))+4        ] + str(rpiblue)
             timp += fil[len(str(pcount))+1       :len(str(pcount))+4         ] + str(pcount)
             timp += fil[len(str(ptime))+1        :len(str(ptime))+4          ] + str(ptime)
             timp += str(camera_connected) + str(serial_connected) + str(use_Pi_Cam)
             timp += str(use_RPiGPIO) + str(photoon) + str(use_Seeed) + str(use_PiFaceRP) + str(use_config) + str(Display) 
             timp += fil[len(str(Disp_Width)):len(str(Disp_Width))+4] + str(Disp_Width) + str(Night)
             timp += str(Image_window) + str(usb_max_res) + str(Frame) + str(bh) + str(bw)
             timp += fil[len(str(N_OP)):len(str(N_OP))+4] + str(N_OP) + fil[len(str(E_OP)):len(str(E_OP))+4] + str(E_OP)
             timp += fil[len(str(S_OP)):len(str(S_OP))+4] + str(S_OP) + fil[len(str(W_OP)):len(str(W_OP))+4] + str(W_OP)
             timp += fil[len(str(C_OP)):len(str(C_OP))+4] + str(C_OP)
             timp += fil[len(str(AC_OP)):len(str(AC_OP))+4] + str(AC_OP) + str(rpineg) + fil[len(str(bits)):len(str(bits))+4] + str(bits)
             timp += fil[len(str(int(minc*10))) :len(str(int(minc*10)))+4   ] + str(int(minc*10))

             with open(deffile + ".txt", "w") as file:
                file.write(timp)

             if z == 155:
                keys2(" S1", fs, 6, b3x, bw, 3, b3y, bh, 6, 1, 1)
             elif z == 165:
                keys2(" S2", fs, 6, b3x, bw, 4, b3y, bh, 6, 1, 1)
             elif z == 175:
                keys2(" S3", fs, 6, b3x, bw, 5, b3y, bh, 6, 1, 1)

             restart = 1
             change = 1

          elif (z == 125 or z == 135 or z == 145 or kz == K_1 or kz == K_2 or kz == K_3):
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if use_config > 0:
                z = use_config*10 + 115
             if kz == K_1 or z == 124:
                z = 125
             elif kz == K_2 or z == 134:
                z = 135
             elif kz == K_3 or z == 144:
                z = 145
             deffile = "config" + str((z - 115)/10)
             if z == 125:
                keys2(" R1", fs, 1, b3x, bw, 0, b3y, bh, 6, 1, 1)
             elif z == 135:
                keys2(" R2", fs, 1, b3x, bw, 1, b3y, bh, 6, 1, 1)
             elif z == 145:
                keys2(" R3", fs, 1, b3x, bw, 2, b3y, bh, 6, 1, 1)
             if os.path.exists(deffile + ".txt"):
                with open(deffile + ".txt", "r") as file:
                   inputx = file.readline()
                auto_g =     int(inputx[ 0: 1])
                nscale =     int(inputx[ 1: 5])
                sscale =     int(inputx[ 5: 9])
                escale =     int(inputx[ 9:13])
                wscale =     int(inputx[13:17])
                ewi =        int(inputx[17:18])
                nsi =        int(inputx[18:19])
                crop =       int(inputx[19:23])
                offset3 =    int(inputx[23:27])
                if offset3 > 9000:
                   offset3 = 9000 - offset3
                offset5 =    int(inputx[27:31])
                if offset5 > 9000:
                   offset5 = 9000 - offset5
                offset6 =    int(inputx[31:35])
                if offset6 > 9000:
                   offset6 = 9000 - offset6
                offset4 =    int(inputx[35:39])
                if offset4 > 9000:
                   offset4 = 9000 - offset4
                Intervals =  int(inputx[39:43])
                log2 =       log
                log =        int(inputx[43:44])
                if log and not log2:
                   now = datetime.datetime.now()
                   timestamp = now.strftime("%y%m%d%H%M%S")
                   logfile = "/tmp/" + str(timestamp) + ".txt"
                rgbw =       int(inputx[44:45])
                threshold =  int(inputx[45:49])
                thres =      int(inputx[49:50])
                graph =      int(inputx[50:51])
                auto_i =     int(inputx[51:52])
                plot =       int(inputx[52:53])
                auto_win =   int(inputx[53:54])
                auto_t =     int(inputx[54:55])
                if camera_connected:
                   zoom =    int(inputx[55:56])
                zoom = max(Image_window, zoom)
                if not zoom:
                   w = width
                   h = height
                if zoom > 0:
                   w = rpiwidth[zoom]
                   h = rpiheight[zoom]

                if not use_Pi_Cam:
                   cam.stop()
                   pygame.camera.init()
                   if not zoom:
                      cam = pygame.camera.Camera("/dev/video0", (320, 240))
                   elif zoom == 1 and usb_max_res >= 1:
                      cam = pygame.camera.Camera("/dev/video0", (352, 288))
                   elif zoom == 2 and usb_max_res >= 2:
                      cam = pygame.camera.Camera("/dev/video0", (640, 480))
                   elif zoom == 3 and usb_max_res >= 3:
                      cam = pygame.camera.Camera("/dev/video0", (800, 600))
                   elif zoom == 4 and usb_max_res >= 4:
                      cam = pygame.camera.Camera("/dev/video0", (960, 720))
                   elif zoom == 5 and usb_max_res >= 5:
                      cam = pygame.camera.Camera("/dev/video0", (1280, 960))
                   elif zoom == 6 and usb_max_res >= 6:
                      cam = pygame.camera.Camera("/dev/video0", (1920, 1440))
                   elif zoom == 7 and usb_max_res >= 7:
                      cam = pygame.camera.Camera("/dev/video0", (2592, 1944))
                   cam.start()
                if not camera_connected:
                   zoom =    int(inputx[55:56])
                   wd = 20 + zoom*4
                   hd = wd
                rpibr =      int(inputx[56:60])
                rpico =      int(inputx[60:64])
                if rpico > 9000:
                   rpico = 9000 - rpico
                rpiev =      int(inputx[64:68])
                if rpiev > 9000:
                   rpiev = 9000 - rpiev
                rpiss =      int(inputx[68:72])*1000
                rpiISO =     int(inputx[72:76])
                rpiexno =    int(inputx[76:77])
                rpiex =   rpimodes[rpiexno]
                rpiexa = rpimodesa[rpiexno]
                if len(inputx) > 77:
                   binn =    int(inputx[77:78])
                   nr =      int(inputx[78:79])
                   decN =    int(inputx[79:80])
                   decS =    int(inputx[80:81])
                   rpired =  int(inputx[81:84])
                   rpiblue = int(inputx[84:87])
                   rpiredx =   Decimal(rpired)/Decimal(100)
                   rpibluex = Decimal(rpiblue)/Decimal(100)
                   pcount =  int(inputx[87:90])
                   ptime =   int(inputx[90:93])
                if len(inputx) > 143:
                   minc =    Decimal(int(inputx[144:148]))/Decimal(10)

             if z == 125:
                keys2(" R1", fs, 6, b3x,    bw, 0, b3y, bh, 6, 1, 1)
                keys2("1",   fs, 5, b3x+fs, bw, 0, b3y, bh, 6, 1, 1)
             elif z == 135:
                keys2(" R2", fs, 6, b3x,    bw, 1, b3y, bh, 6, 1, 1)
                keys2("2",   fs, 5, b3x+fs, bw, 1, b3y, bh, 6, 1, 1)
             elif z == 145:
                keys2(" R3", fs, 6, b3x,    bw, 2, b3y, bh, 6, 1, 1)
                keys2("3",   fs, 5, b3x+fs, bw, 2, b3y, bh, 6, 1, 1)

             restart = 1
             change = 1

   if change:
      change = 0
      if oldthreshold != threshold:
         pygame.draw.rect(windowSurfaceObj, greyColor, Rect(b1x+148, b1y+111, 26, 16))
         keys2(str(threshold), fs, 3, b1x, bw, 5, b1y, bh, 4, 3, 1)
      if oldInterval != Interval:
         pygame.draw.rect(windowSurfaceObj, greyColor, Rect(b1x+148, b1y+143, 26, 16))
         keys2(str(Interval), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
         oldInterval = Interval
      if oldphoto != photo and photoon:
         keys2("PHOTO", fs, photo, b2x, bw, 4, b2y, bh, 2, 0, 1)
         keys2("O", fs, 5, b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)
         oldphoto = photo
      if oldcon_cap != con_cap:
         button2(b2x, 6, b2y, 6, bw, 1, bh, con_cap)
         keys2("con", fs, con_cap, b2x, bw, 5, b2y, bh, 6, 0, 1)
         keys2("cap", fs, con_cap, b2x, bw, 5, b2y, bh, 6, 2, 1)
         oldcon_cap = con_cap
      if oldauto_win != auto_win:
         button2(b1x, 4, b1y, 3, bw, 1, bh, auto_win)
         keys2("AWin", fs-1, auto_win, b1x, bw, 3, b1y, bh, 3, 1, 1)
         keys2("W", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 3, 1, 1)
         oldauto_win = auto_win
      if oldauto_i != auto_i:
         button2(b1x, 4, b1y, 5, bw, 1, bh, auto_i)
         keys2("AInt", fs-1, auto_i, b1x, bw, 3, b1y, bh, 5, 1, 1)
         keys2("I", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 5, 1, 1)
         oldauto_i = auto_i
      if oldnsi != nsi:
         button2(b1x, 3, b1y, 3, bw, 1, bh, nsi)
         keys2("NSi", fs, nsi, b1x, bw, 2, b1y, bh, 3, 1, 1)
         keys2("N", fs, 5, b1x, bw, 2, b1y, bh, 3, 1, 1)
         oldnsi = nsi
      if oldewi != ewi:
         button2(b1x, 3, b1y, 4, bw, 1, bh, ewi)
         keys2("EWi", fs, ewi, b1x, bw, 2, b1y, bh, 4, 1, 1)
         keys2("E", fs, 5, b1x, bw, 2, b1y, bh, 4, 1, 1)
         oldewi = ewi
      if oldauto_t != auto_t:
         button2(b1x, 4, b1y, 4, bw, 1, bh, auto_t)
         keys2("AThr", fs-1, auto_t, b1x, bw, 3, b1y, bh, 4, 1, 1)
         keys2("T", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 4, 1, 1)
         oldauto_t = auto_t
      if oldauto_g != auto_g:
         button2(b1x, 1, b1y, 2, bw, 2, bh, auto_g)
         keys2("AutoG", fs, auto_g, b1x, bw, 0, b1y, bh, 2, 1, 1)
         keys2("A", fs, 5, b1x, bw, 0, b1y, bh, 2, 1, 1)
         oldauto_g = auto_g
      if oldlog != log:
         button2(b1x, 1, b1y, 4, bw, 1, bh, log)
         keys2("Log", fs, log, b1x, bw, 0, b1y, bh, 4, 1, 1)
         keys2("L", fs, 5, b1x, bw, 0, b1y, bh, 4, 1, 1)
         oldlog = log
      if oldgraph != graph:
         button2(b1x, 2, b1y, 3, bw, 1, bh, graph)
         keys2("Gph", fs, graph, b1x, bw, 1, b1y, bh, 3, 1, 1)
         keys2("G", fs, 5, b1x, bw, 1, b1y, bh, 3, 1, 1)
         oldgraph = graph
      if oldplot != plot:
         button2(b1x, 1, b1y, 3, bw, 1, bh, plot)
         keys2("Plot", fs, plot, b1x, bw, 0, b1y, bh, 3, 1, 1)
         keys2("P", fs, 5, b1x, bw, 0, b1y, bh, 3, 1, 1)
         oldplot = plot
      if oldthres != thres:
         button2(b1x, 2, b1y, 4, bw, 1, bh, thres)
         keys2("Thr", fs, thres, b1x, bw, 1, b1y, bh, 4, 1, 1)
         keys2("h", fs, 5, b1x+fs/1.5, bw, 1, b1y, bh, 4, 1, 1)
         oldthres = thres
      if oldptime != ptime and photoon:
         keys2(str(ptime), fs, 3, b2x, bw, 5, b2y, bh, 3, 3, 1)
         oldptime = ptime
      if oldpcount != pcount and photoon:
         keys2(str(pcount), fs, 3, b2x, bw, 5, b2y, bh, 4, 3, 1)
         oldpcount = pcount
      if oldnscale != nscale:
         keys2(str(int(nscale)), fs, 3, b2x, bw, 3, b2y, bh, 2, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldnscale = nscale
      if oldsscale != sscale:
         keys2(str(int(sscale)), fs, 3, b2x, bw, 3, b2y, bh, 3, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldsscale = sscale
      if oldescale != escale:
         keys2(str(int(escale)), fs, 3, b2x, bw, 3, b2y, bh, 4, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldescale = escale
      if oldwscale != wscale:
         keys2(str(int(wscale)), fs, 3, b2x, bw, 3, b2y, bh, 5, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldwscale = wscale
      if oldthreshold != threshold:
         keys2(str(threshold), fs, 3, b1x, bw, 5, b1y, bh, 4, 3, 1)
         oldthreshold = threshold
      if oldInterval != Interval:
         keys2(str(Interval), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
      if oldrpired != rpired and camera_connected and use_Pi_Cam:
         keys2(str(rpiredx), fs, 3, b1x, bw, 1, b1y, bh, 5, 3, 1)
         oldrpired = rpired
      if oldrpiblue != rpiblue and camera_connected and use_Pi_Cam:
         keys2(str(rpibluex), fs, 3, b1x, bw, 1, b1y, bh, 6, 3, 1)
         oldrpiblue = rpiblue
      if oldzoom != zoom:
         keys2(str(zoom), fs, 3, b1x, bw, 5, b1y, bh, 6, 3, 1)
         oldzoom = zoom
      if oldrgbw != rgbw:
         msg = rgb[rgbw]
         if rgbw < 5:
            keys2(msg, fs, rgbw + 2, b1x, bw, 5, b1y, bh, 2, 3, 1)
         else:
            keys2(msg, fs, rgbw + 1, b1x, bw, 5, b1y, bh, 2, 3, 1)
         oldrgbw = rgbw
      if oldcrop != crop:
         if crop != maxwin:
            keys2(str(crop), fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)
         else:
            keys2("max", fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)
         oldcrop = crop
      if oldrpibr != rpibr:
         keys2(str(rpibr), fs, 3, b2x, bw, 1, b2y, bh, 2, 3, 1)
         oldrpibr = rpibr
      if oldrpico != rpico and camera_connected and use_Pi_Cam:
         keys2(str(rpico), fs, 3, b2x, bw, 1, b2y, bh, 3, 3, 1)
         oldrpico = rpico
      if oldrpiss != rpiss and camera_connected and use_Pi_Cam:
         keys2(str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         oldrpiss = rpiss
      if oldrpiexno != rpiexno:
         rpiexa = rpimodesa[rpiexno]
         keys2((rpimodesa[rpiexno]), fs, 3, b2x, bw, 1, b2y, bh, 5, 3, 1)
         if rpimodes[rpiexno] != "off":
            keys2(str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         else:
            keys2(str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa== 'vlon2' or rpiexa == 'spor2':
            keys2("Exp Time", fs-1, 6, b2x, bw, 0, b2y, bh, 4, 0, 1)
         else:
            keys2("     eV", fs, 6, b2x, bw, 0, b2y, bh, 4, 0, 1)
         if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
            keys2(str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         else:
            keys2(str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         keys2((rpimodesa[rpiexno]), fs, 3, b2x, bw, 1, b2y, bh, 5, 3, 1)
         oldrpiexno = rpiexno
      if oldrpiISO != rpiISO and camera_connected and use_Pi_Cam:
         keys2(str(rpiISO), fs, 3, b2x, bw, 1, b2y, bh, 6, 3, 1)
         if not rpiISO:
            keys2('auto', fs, 3, b2x, bw, 1, b2y, bh, 6, 3, 1)
         oldrpiISO = rpiISO
      if oldrpiev != rpiev and camera_connected and use_Pi_Cam:
         keys2(str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         oldrpiev = rpiev
      if oldbinn != binn:
         button2(b1x, 3, b1y, 2, bw, 1, bh, binn)
         keys2("2x2", fs, binn, b1x, bw, 2, b1y, bh, 2, 1, 1)
         oldbinn = binn
      if oldnr != nr:
         button2(b1x, 4, b1y, 2, bw, 1, bh, nr)
         keys2("nr", fs, nr, b1x, bw, 3, b1y, bh, 2, 1, 1)
         oldnr = nr
      if olddecN != decN:
         button2(b3x, 1, b3y, 2, bw, 1, bh, decN)
         keys2("DEC", fs-1, decN, b3x, bw, 0, b3y, bh, 2, 0, 1)
         keys2("  N", fs-1, decN, b3x, bw, 0, b3y, bh, 2, 2, 1)
         olddecN = decN
      if olddecS != decS:
         button2(b3x, 1, b3y, 4, bw, 1, bh, decS)
         keys2("DEC", fs-1, decS, b3x, bw, 0, b3y, bh, 4, 0, 1)
         keys2("  S", fs-1, decS, b3x, bw, 0, b3y, bh, 4, 2, 1)
         olddecS = decS
      if oldcls != cls:
         button2(b2x, 5, b2y, 6, bw, 1, bh, cls)
         keys2("CLS", fs, cls, b2x, bw, 4, b2y, bh, 6, 1, 1)
         keys2("C",   fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
         oldcls = cls
      if oldminc != minc:
         keys2(str(minc),                fs,       3,        b1x,         bw,   3,     b1y, bh, 6, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldminc = minc

   if use_Pi_Cam and restart and camera_connected:
      if os.path.exists('/run/shm/test.jpg'):
         os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
      try:
         os.remove('/run/shm/test.jpg')
      except OSError:
         pass

      rpistr = "raspistill -o /run/shm/test.jpg -co " + str(rpico) + " -br " + str(rpibr)
      if rpiexa != ' off' and rpiexa != 'nigh2' and rpiexa != 'fwor2' and rpiexa != 'vlon2' and rpiexa != 'spor2':
         rpistr += " -t " + str(rpit) + " -tl 0 -ex " + rpiex + " -fp -bm -awb off -awbg " + str(rpiredx)+","+str(rpibluex)
      elif rpiexa == ' off':
         rpistr += " -t " + str(rpit) + " -tl 0 -ss " + str(rpiss) + " -fp -bm -awb off -awbg " + str(rpiredx)+","+str(rpibluex)
      else:
         rpistr += " -t " + str(rpit) + " -tl 0 -ex " + rpiex + " -ss " + str(rpiss) + " -fp -bm -awb off -awbg " + str(rpiredx)+","+str(rpibluex)
      if rpiISO > 0:
         rpistr += " -ISO " + str(rpiISO)
      if rpiev != 0:
         rpistr += " -ev " + str(rpiev)
      rpistr += " -q 100 -n -sa " + str(rpisa)
      off5 = (Decimal(0.5) - (Decimal(width)/Decimal(2))/Decimal(w)) + (Decimal(offset5)/Decimal(w))
      off6 = (Decimal(0.5) - (Decimal(height)/Decimal(2))/Decimal(h)) + (Decimal(offset6)/Decimal(h))
      widx = Decimal(width)/Decimal(w)
      heiy = Decimal(height)/Decimal(h)
      rpistr += " -w " + str(width) + " -h " + str(height) + " -roi " + str(off5) + "," + str(off6) + ","+str(widx) + "," + str(heiy)
      if rpineg:
         rpistr += " -ifx negative "
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      restart = 0

