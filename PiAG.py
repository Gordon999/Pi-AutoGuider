#!/usr/bin/env python3
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

#Pi Autoguider r12e

#WORKS WITH PYTHON 2 or 3 

# If you want to run at boot using Buster: Assuming you've saved it as /home/pi/PiAG.py
# Add @sudo /usr/bin/python3 /home/pi/PiAG.py to the end of /etc/xdg/lxsession/LXDE-pi/autostart
# Make the file executable with sudo chmod +x PiAG.py

#=============================================================================================================
use_config  =         0 # set pre-stored config to load at startup, 1, 2 or 3. 
                        # !!! to use a pre-stored config ensure you saved it when use_config was set = 0
#=============================================================================================================
power_down  =         0 # set = 1 to power down the Pi when you exit the script, clicking Esc twice.
                        # To stop the script without exiting when set, click 'Esc' then 'Stop'.
#=============================================================================================================
# CONNECTION SETTINGS

camera_connected =    1 # FOR TESTING / simulation ONLY, 1 for normal use
                        # setting camera_connected = 0 will run in demo / simulation mode
serial_connected =    0 # set serial_connected = 0 if you don't have the Arduino Uno etc connected.
use_Pi_Cam =          1 # if using the RPi camera set use_Pi_Cam = 1 , if set to 0 the program will use a USB camera.
Webcam =              3 # 0 = Philips, 1 = Logitech, 2 = Pi Camera using v4l2 and imutils,3 = Pi Camera using v4l2,picamera and opencv
                        # if using Webcam = 2 then install imutils 
                        # if using Webcam = 3 then install opencv
usb_max_res =         1 # usb_max_res - Webcam max available resolution, depends on your Webcam
                        # all USB camera images will be taken using this resolution
                        # 0 = 320x240, 1 = 640x480, 2 = 800x600, 3 = 960x720, 4 = 1280x960,
                        # 5 = 1620X1215, 6 = 1920x1440, 7 = 2592x1944, 8 = 3280x2464, 9 = 5184x3688
                        # eg. Philips NC900 and Toucam Pro 740 won't work above 1, Logitech C270 max 4.
                        # (Pi camera uses a max of 7 (v1) or 9 (v2) automatically)
use_RPiGPIO =         1 # if using the RPi.GPIO on the Pi set use_RPiGPIO = 1, not required if only using the DSLR GPIO O/P (photoon = 1).
photoon =             1 # to enable GPIO control of DSLR function set photoon = 1
use_Seeed =           0 # if using the Seeed Raspberry PI relay v1.0 card set use_Seeed = 1
                        # ensure you install smbus (sudo apt-get install python-smbus)
                        # and enable i2c on your Pi
use_PiFaceRP =        0 # if using the PiFace Relay Plus card set use_PiFaceRP = 1
                        # ensure you install pifacerelayplus (sudo apt-get install python-pifacerelayplus)
                        # and enable SPI on your Pi
use_crelay =          0 # if using the Sainsmart USB 4 relay card set use_crelay = 1
                        # ensure you install crelay (http://ondrej1024.github.io/crelay/)
                        
#==================================================================================================
# DISPLAY SETTINGS

Display =             0 # Display - Set this dependent on your display. 0 = Pi Screen (800x480) or LCD (840x480), 1 = PAL Composite (640x480),
                        # 2 = other as set by parameters below
                        # if using 1 for PAL composite then adjust /boot/config.txt to suit
                        # if using 0 and a 840x480 HDMI LCD then change /boot/config.txt for hmdi group = 2 and hdmi mode = 14
Disp_Width =        608 # Disp_Width - sets image width when using Display = 0, set 608 for Pi Display (800x480), set 640 for 840x480 display
Night =               0 # Night Colours, 1 = ON. (can be changed whilst running by clicking on Day / Night)
Cwindow =             1 # Enable circular window (can be changed whilst running by clicking on WIN in WINDOW)
Image_window =        2 # Image_window - sets image window size, either 0 = 320x240, 1 = 640x480, 2 = 800x600, 3 = 960x720, 4 = 1280x960 etc,
                        # Any for HDMI but recommend 0 for Composite (PAL)
bits =               24 # bits - bits to display in pygame
Frame =               0 # Frame - frame displayed or not, 0 = no, 1 = yes
bh =                 32 # button height
bw =                 32 # button width
DKeys =               0 # Choose direction keys setting, 0 = Dec and RA, 1 = N,E,S,W
show_time =           1 # show time on display
mouse_button =        0 # set mouse button for setting window, 0/1/2 = left/centre/right
calibrate_time =     16 # sets time , in seconds, telescope moved for calibrate when zoom = 1, will be varied dependent
                        # on zoom level set, can be changed from the screen 
auto_rotate  =        0 # set to automatically rotate image after calibration

#SETUP GPIO 
#===================================================================================
#Telescope control GPIO 'physical/BOARD' pins
N_OP         =       22 # 22
S_OP         =       18 # 18
E_OP         =       24 # 24
W_OP         =       16 # 16
# External camera control GPIO pin, eg DSLR
C_OP         =       26 # 26
# Alternative camera control GPIO pin if C_OP = 26 and using SPI for PiFace
AC_OP        =       13 # 13

#==================================================================================================
# SET DEFAULT VALUES
#==================================================================================================
auto_g       =        0 # auto_g - autoguide on = 1, off = 0
nscale       =      150 # nscale - North scaling in milliSecs/pixel
sscale       =      150 # sscale - South scaling in milliSecs/pixel
escale       =      150 # escale - East  scaling in milliSecs/pixel
wscale       =      150 # wscale - West  scaling in milliSecs/pixel
ewi          =        0 # ewi - Invert East <> West invert = 1, non-invert = 0
nsi          =        0 # nsi - Invert North<>South invert = 1, non-invert = 0
crop         =       30 # crop - Tracking Window size in pixels.
minwin       =       30 # minwin - set minimum Tracking window size
maxwin       =      200 # maxwin - set maximum Tracking window size (FULLSCREEN above this)
offset3      =        0 # offset3 - Tracking Window x offset from centre of screen
offset4      =        0 # offset4 - Tracking Window y offset from centre of screen
offset5      =        0 # offset5/6 - Tracking Window offset from centre of screen
offset6      =        0
Intervals    =        5 # Intervals - Guiding Interval in frames
log          =        0 # log - Log commands to /run/shm/YYMMDDHHMMSS.txt file, on = 1, off = 0
rgbw         =        5 # rgbw - R,G,B,W1,W2 = 1,2,3,4,5
threshold    =       20 # threshold value
thres        =        0 # threshold - on = 1,off = 0. Displays detected star pixels
graph        =        0 # graph - on = 1, off = 0. shows brightness of star, and threshold value
plot         =        0 # plot - plot movements, on = 1, off = 0
auto_win     =        0 # auto_win - auto size tracking window, on = 1, off = 0
auto_wlos    =        0 # auto_wlos - auto window increase on loss of guide star, when using auto_win, on = 1, off = 0
auto_t       =        0 # auto_t - auto threshold, on = 1, off = 0
zoom         =        0 # zoom - set to give cropped image, higher magnification, pi camera max = 7 (v1) or 9 (v2).
auto_i       =        0 # auto_i - auto-interval, on = 1, off = 0
decN         =        1 # disable N DEC commands, 0 = OFF/DISABLED
decS         =        1 # disable S DEC commands, 0 = OFF/DISABLED
hist         =        0 # equalise / 2x2 binning , 0 = OFF, 1 = stretch histogram, 2 = stretch histogram improved noise, 3 = 2x2 binning
nr           =        0 # noise reduction, 0 = off, 1,2 or 3 - averaged over a number of frames, and single pixels removed.
minc         =      0.5 # minimum correction in pixels
move_limit   =      100 # minimum movement for calibration

# Settings for external camera eg DSLR photos (set camera to B (BULB))
#===================================================================================
pwait        =       10 # pwait - wait in seconds between multiple photos
ptime        =       60 # ptime - exposure time in seconds
pcount       =       10 # pcount - number of photos to take
pmlock       =        0 # pmlock - if using mirrorlock on the DSLR set = 1, set pwait to a suitable value to settle.
                        # tested only on a Canon DSLR, triggers shutter to lock mirror and then triggers exposure.

# RPi camera presets
#===================================================================================
rpico        =       90 # contrast
rpibr        =       76 # brightness
rpiexno      =        3 # exposure mode
rpiISO       =        0 # ISO, 0 = auto
rpiev        =        0 # eV correction
rpisa        =        0 # saturation
rpiss        =   200000 # shutter speed
rpit         =        0 # timer
rpired       =      100 # red gain
rpiblue      =      130 # blue gain
rpineg       =        0 # negative image

# USB common Webcam presets
#===================================================================================
Auto_Gain    =        0 # Switch Automatic Gain , 1 = ON, 0 = OFF
brightness   =      128 # sets USB camera initial brightness
contrast     =       63 # sets USB camera initial contrast
exposure     =      255 # USB camera initial exposure
gain         =       35 # sets USB camera initial gain

# USB Webcam presets only for Philips...
#============================================

gamma        =       31 # sets USB camera initial gamma
red_balance  =       66 # sets USB camera initial red balance
blue_balance =       48 # sets USB camera initial blue balance
auto_contour =        0 # 0 switches it to manual, range 0-1
contour      =        0 # sets to min, range 0-63
dnr          =        0 # sets to min, range 0-3
backlight    =        0 # sets it OFF 0-1

# USB Webcam presets only for Logitech...
#============================================

sharpness    =       63 # sets USB camera initial sharpness
saturation   =       63 # sets USB camera initial saturation
color_temp   =     4000 # sets USB camera initial Colour Temperature

# USB Webcam presets only for Pi Camera using v4l2...
#============================================
scene_mode      =      0 # sets scene_mode 0 = None, 8 = night
if Webcam > 1:
   brightness    =       50 # sets USB camera initial brightness
   contrast      =       50 # sets USB camera initial contrast
   sharpness     =       50 # sets USB camera initial sharpness
   saturation    =       10 # sets USB camera initial saturation
   red_balance   =     1200 # sets USB camera initial red balance
   blue_balance  =     1300 # sets USB camera initial blue balance
   Auto_Gain     =        1 # sets USB camera Automatic Exposure , 0 = ON, 1 = OFF
   exposure      =     1000 # sets USB camera initial exposure
   iso_sensitivity =      4 # sets USB ISO
   rpiev           =      6 # sets eV correction


# Philips Webcam limits
#--------------------------------------------
if Webcam == 0:
   usb_min_br   =     0
   usb_max_br   =   127 # Philips brightness limits
   usb_min_co   =     0
   usb_max_co   =    63 # Philips contrast limits
   usb_min_ex   =     0
   usb_max_ex   =   255 # Philips exposure limits
   usb_min_gn   =     0
   usb_max_gn   =    63 # Philips gain limits
   usb_min_rx   =     0      
   usb_max_rx   =   255 # Philips red_balance limits
   usb_min_bx   =     0      
   usb_max_bx   =   255 # Philips blue_balance limits
usb_min_ga   =        0      
usb_max_ga   =       31 # Philips gamma limits

# Logitech Webcam limits
#--------------------------------------------
if Webcam == 1:
   usb_min_br   =     0
   usb_max_br   =   255 # Logitech brightness limits
   usb_min_co   =     0
   usb_max_co   =   255 # Logitech contrast limits
   usb_min_ex   =     0
   usb_max_ex   =  1000 # Logitech exposure limits 
   usb_min_gn   =     0
   usb_max_gn   =   255 # Logitech gain limits 
   usb_min_sh   =     0
   usb_max_sh   =   255 # Logitech sharpness limits
   usb_min_sa   =     0
   usb_max_sa   =   255 # Logitech saturation limits
usb_min_ct   =        0
usb_max_ct   =     9999 # Logitech Colour Temp limits

# Pi Camera using v4l2 Webcam limits
#--------------------------------------------
if Webcam > 1:
   usb_min_br   =     0
   usb_max_br   =   100 # Pi Cam v4l2 brightness limits
   usb_min_co   =  -100
   usb_max_co   =   100 # Pi Cam v4l2  contrast limits
   usb_min_ex   =     1
   usb_max_ex   = 10000 # Pi Cam v4l2  exposure limits 
   usb_min_sh   =  -100
   usb_max_sh   =   100 # Pi Cam v4l2  sharpness limits
   usb_min_sa   =  -100
   usb_max_sa   =   100 # Pi Cam v4l2  saturation limits
   usb_min_rx   =     1      
   usb_max_rx   =  7999 # Pi Cam v4l2 red_balance limits
   usb_min_bx   =     1      
   usb_max_bx   =  7999 # Pi Cam v4l2 blue_balance limits
   usb_min_is   =     0      
   usb_max_is   =     4 # Pi Cam v4l2 ISO limits
   usb_min_ev   =   -12      
   usb_max_ev   =    12 # Pi Cam v4l2 eV limits
   
# Arrays
#===================================================================================
rpimodes =  ['off',  'auto', 'night', 'night', 'sports', 'sports', 'verylong', 'verylong', 'fireworks', 'fireworks']
rpimodesa = [' off', 'auto', 'night', 'nigh2', 'sport',  'spor2',  'vlong',    'vlon2',    'fwork',     'fwor2']
rpiwidth =  [320, 640, 800, 960, 1280, 1620, 1920, 2592, 3280, 5184]
rpiheight = [240, 480, 600, 720,  960, 1215, 1440, 1944, 2464, 3688]
rpiscalex = [1, 2, 1.25, 1.2, 1.333, 1.265, 1.185, 1.35, 1.266, 1.538]
rpiscaley = [1, 2, 1.25, 1.2, 1.333, 1.265, 1.185, 1.35, 1.266, 1.538]

#===================================================================================
# Set USB parameters
if not use_Pi_Cam and camera_connected:
   rpibr    = brightness
   rpico    = contrast
   rpired   = red_balance
   rpiblue  = blue_balance
   rpiredx  = red_balance
   rpibluex = blue_balance
   
# Check for Pi Camera version
if use_Pi_Cam and camera_connected:
   if os.path.exists('test.jpg'):
      os.rename('test.jpg', 'oldtest.jpg')
   rpistr = "raspistill -n -o test.jpg -t 100"
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   time.sleep(2)
   if os.path.exists('test.jpg'):
      imagefile = 'test.jpg'
      image = pygame.image.load(imagefile)
      if image.get_width() == 2592:
         Pi_Cam = 1
      else:
         Pi_Cam = 2
   else:
      Pi_Cam = 2
      
# use Pi Camera as webcam      
if use_Pi_Cam == 0 and Webcam == 2 and camera_connected:
   from imutils.video import VideoStream
if use_Pi_Cam == 0 and Webcam == 3 and camera_connected:
   import picamera
   import cv2
   
# restart USB for Logitech Webcam
if not use_Pi_Cam and camera_connected and Webcam == 1:
   rpistr = "echo '1-1' > /sys/bus/usb/drivers/usb/unbind"
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   time.sleep(2)
   rpistr = "echo '1-1' > /sys/bus/usb/drivers/usb/bind"
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

if not use_Pi_Cam and camera_connected and Webcam > 1:
   if not os.path.exists('/dev/video0'):
      rpistr = "sudo modprobe bcm2835-v4l2"
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   dve = 0

#===================================================================================
# Generate mask if required for Circular window
#===================================================================================
if Cwindow and not os.path.exists('/run/shm/CMask.bmp'):
   pygame.init()
   bredColor =   pygame.Color(100,100,100)
   mwidth =200
   mheight = 200
   mcrop = 200
   windowSurfaceObj = pygame.display.set_mode((mwidth, mheight), pygame.NOFRAME, 24)
   pygame.draw.circle(windowSurfaceObj, bredColor, (int(mcrop/2),int(mcrop/2)), int(mcrop/2),0)
   pygame.display.update()
   pygame.image.save(windowSurfaceObj, '/run/shm/CMask.bmp')
   pygame.display.quit()
   
def MaskChange(): # used for circular window
   mask = pygame.image.load('/run/shm/CMask.bmp')
   smask = pygame.transform.scale(mask, [crop, crop])
   imm = pygame.image.tostring(smask, "RGB", 1)
   if sys.version_info[0] == 3:
      mm = numpy.array(list(imm),dtype='int')
      mmq = mm[0:crop*crop*3:3]
   if sys.version_info[0] == 2:
      mm = []
      for mcounter in range (0, crop*crop*3, 3):
         ima = ord(imm[mcounter  :mcounter + 1])
         mm.append(ima)
      mmq = (numpy.add(mm, 0))
   mmq[mmq > 50] = 1
   change = 1
   return (mmq, mask, change)

# Load pre-stored config at startup
if use_config > 0 and use_config < 4:
   deffile = "config" + str(use_config)
   if os.path.exists(deffile + ".txt"):
       configs = []
       with open(deffile + ".txt", "r") as file:
           line = file.readline()
           while line:
               configs.append(line.strip())
               line = file.readline()
       configs = list(map(int,configs))
       auto_g = configs[0]
       nscale = configs[1]
       sscale = configs[2]
       escale = configs[3]
       wscale = configs[4]
       ewi = configs[5]
       nsi = configs[6]
       crop = configs[7]
       offset3 = configs[8]
       offset5 = configs[9]
       offset6 = configs[10]
       offset4 = configs[11]
       Intervals = configs[12]
       log = configs[13]
       rgbw = configs[14]
       threshold = configs[15]
       thres = configs[16]
       graph = configs[17]
       auto_i = configs[18]
       plot = configs[19]
       auto_win = configs[20]
       auto_t = configs[21]
       zoom = configs[22]
       rpibr = configs[23]
       rpico = configs[24]
       rpiev = configs[25]
       rpiss = configs[26] * 1000
       rpiISO = configs[27]
       rpiexno = configs[28]
       hist = configs[29]
       nr = configs[30]
       decN = configs[31]
       decS = configs[32]
       rpired = configs[33]
       rpiblue = configs[34]
       pcount = configs[35]
       ptime = configs[36]
       camera_connected = configs[37]
       serial_connected = configs[38]
       use_Pi_Cam = configs[39]
       use_RPiGPIO = configs[40]
       photoon = configs[41]
       use_Seeed = configs[42]
       use_PiFaceRP = configs[43]
       use_config = configs[44]
       Display = configs[45]
       Disp_Width = configs[46]
       Night = configs[47]
       Image_window = configs[48]
       usb_max_res = configs[49]
       Frame = configs[50]
       bho = configs[51]
       bwo = configs[52]
       N_OP = configs[53]
       E_OP = configs[54]
       S_OP = configs[55]
       W_OP = configs[56]
       C_OP = configs[57]
       AC_OP = configs[58]
       rpineg = configs[59]
       bits = configs[60]
       minc = configs[61]/10
       a_thr_limit = configs[62]
       m_thr_limit = configs[63]
       calibrate_time = configs[64]
       Cang = configs[65]
       exposure = configs[66]
       gain = configs[67]
       gamma = configs[68]
       Auto_Gain = configs[69]
       sharpness = configs[70]
       saturation = configs[71]
       color_temp  = configs[72] * 10
       if Cwindow:
           mmq, mask, change = MaskChange()
   #else:
   #   print ("No config file found")
#===================================================================================
# Seeed i2c address etc.
#===================================================================================
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
#===================================================================================
if use_PiFaceRP:
   # switch OFF GPIO outputs as conflicts with SPI connections
   use_RPiGPIO = 0
   # Change to alternative DSLR camera control pin O/P as pin 26 conflicts with SPI connections
   if C_OP == 26:
      C_OP = AC_OP
   import pifacerelayplus
   pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
#===================================================================================
# GPIO
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
   po = 0
#==============================================================================
#a_thr_scale - sets scaling factor for auto_t
global a_thr_scale
a_thr_scale =         3
#a_thr_limit - sets lower limit for auto threshold to detect loss of star
a_thr_limit =         5
#m_thr_limit - sets lower limit for manual threshold to detect loss of star
m_thr_limit =         5
#==============================================================================
if serial_connected:
   import serial

pygame.init()
vtime =  0
htime =  0
ptime2 = 0
rpiex = rpimodes[rpiexno]
rpiexa = rpimodesa[rpiexno]
menu =                    0
switch =                  0
imu =                    ""
limg =                    0
Interval =        Intervals
pimg =                   ""
scalex =                  1
scaley =                  1
if use_Pi_Cam:
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
mxo =                     []
mxp =                     []
mxq =                     []
mmx =                     []
mnr =                     0
mousepress =              0
press =                   0
rad =                minwin
xouse  =                  0
youse =                   0
mousexx =                 0  
mouseyy =                 0
store =                   0
auto_c =                  0
fc =                      0
vt =                      0
ht =                      0
h_corr =                  1
w_corr =                  1
esctimer =                0     
oldsec =                 ""
bho =                    bh
bwo =                    bw
calibrate =               0
cal_count =               0
no_star =                 0
no_move =                 0
ang =                  0.01
Dang =                    0
Rang =                    0
Aang =                    0
Cang =                    0
ocrop =                crop
oCwindow =          Cwindow
mintot =                  0
maxtot =                255
nycle =                   0
nstart =                  1

rgb = ['X', 'R', 'G', 'B', 'W1', 'W2']

if DKeys == 0:
   Dkey = ["Dec+","RA-","RA+","Dec-","Up","Left","Right","Down","scale Dec+","scale Dec-","scale RA+","scale RA-","Deci","RAi"]
else:
   Dkey = ["N","W","E","S","N","W","E","S","scale N","scale S","scale E","scale W","NSi","EWi"]

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
red =  chr(127) + chr(0)   + chr(0)
bla =  chr(0)   + chr(0)   + chr(0)
blu =  chr(0)   + chr(0)   + chr(127)
grn =  chr(0)   + chr(127) + chr(0)
yel =  chr(127) + chr(127) + chr(0)
dred = chr(127) + chr(70)  + chr(70)
dblu = chr(0)   + chr(0)   + chr(127)
dgrn = chr(0)   + chr(127) + chr(0)
dyel = chr(127) + chr(127) + chr(0)
fs = min(bh, bw)/2 - 3

zoom = max(Image_window, zoom)
if not use_Pi_Cam and zoom > usb_max_res:
   zoom = Image_window = usb_max_res

#===================================================================================
# DISPLAY MODE SETTINGS
#===================================================================================

if Display == 0: # Pi 7" LCD or 840x480 HDMI
   width = 800
   b1x = b2x = b3x = Disp_Width
   b1y = -bh
   b2y = bh*4
   b3y = bh*9
   if use_Pi_Cam:
      Image_window = 2
   else:
      Image_window = 1
   height = 600
   Disp_Height = 480
   if bh <= 32:
      hplus = 0
   else:
      hplus = bh*15 - 480
   if use_config == 0:
      if use_Pi_Cam:
         zoom = 2
      elif not use_Pi_Cam and Webcam < 2:
         zoom = 1
      else:
         zoom = 0

if Display == 1: # PAL Display
   bh = bw = 32
   width = 320
   height = 240
   b1x = 0
   b1y = b2y = b3y = height
   b2x = 192
   b3x = 385
   hplus = 192
   Image_window = 0
   modewidth = 640
   if use_config == 0:
      zoom = 0
   hplus = 192
   Disp_Width = width
   Disp_Height = height

if Display == 2: # User Defined
   width =  rpiwidth[Image_window]
   height = rpiheight[Image_window]
   b1x = b2x = b3x = width
   b1y = -bh
   b2y = bh*4 + 1
   b3y = bh*9 + 1
   hplus = 0
   Disp_Width = width
   Disp_Height = height

   
min_res = Image_window
z = 0
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
if width <= 352 and Display == 1:
   modewidth = 640
else:
   modewidth = Disp_Width + bw*6

zt = 0
scale_t = 1
while zt <= zoom:
   scale_t *= rpiscalex[zt]
   zt += 1
cal_time = int((calibrate_time * 1000) / scale_t)

# setup Frame
if not Frame:
   windowSurfaceObj = pygame.display.set_mode((modewidth, Disp_Height + hplus), pygame.NOFRAME, bits)
else:
   windowSurfaceObj = pygame.display.set_mode((modewidth, Disp_Height + hplus), 1,              bits)
pygame.display.set_caption('Pi-AutoGuider')

# start Pi Camera subprocess 
if use_Pi_Cam and camera_connected:
   #rename old test.jpg if exists
   if os.path.exists('/run/shm/test.jpg'):
      os.rename('/run/shm/test.jpg', '/run/shm/oldtest.jpg')
   # start subprocess to capture pictures using Pi camera
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

# start Webcam
elif camera_connected and not use_Pi_Cam and Webcam < 2:
   pygame.camera.init()
   if os.path.exists('/dev/video0') == True:
      cam = pygame.camera.Camera("/dev/video0", (rpiwidth[usb_max_res],rpiheight[usb_max_res]))
      dve= 0
   elif os.path.exists('/dev/video1') == True:
      cam = pygame.camera.Camera("/dev/video1", (rpiwidth[usb_max_res],rpiheight[usb_max_res]))
      dve= 1
   cam.start()

elif camera_connected and not use_Pi_Cam and Webcam == 2:
   vs = VideoStream(src=0,resolution=(960,720)).start() 
   time.sleep(1.0)
elif camera_connected and not use_Pi_Cam and Webcam == 3:
   vs = cv2.VideoCapture(0)
   time.sleep(1.0)
   
# switch required relay ON
def R_ON(RD, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA):
   if use_RPiGPIO:
      RE = [N_OP, S_OP, E_OP, W_OP][RD]
      GPIO.output(RE, GPIO.HIGH)
   if use_Seeed:
      DEVICE_REG_DATA &= ~(0x1<<RD)
      bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
   if use_PiFaceRP:
      pfr.relays[RD].turn.on()
   if use_crelay:
      rpistr = "crelay " + str(RD+1) +  " on"
      q = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      
   return(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)

# switch required relay OFF
def R_OFF(RD, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA):
   if use_RPiGPIO:
      RE = [N_OP, S_OP, E_OP, W_OP][RD]
      GPIO.output(RE, GPIO.LOW)
   if use_Seeed:
      DEVICE_REG_DATA |= (0x1<<RD)
      bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
   if use_PiFaceRP:
      pfr.relays[RD].turn.off()
   if use_crelay:
      rpistr = "crelay " + str(RD+1) +  " off"
      q = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   return(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)

# draw a button
def button(bx1, x, by1, y, bw, z, by2, bColor,upd):
   colors = [greyColor, dgryColor, dgryColor, dgryColor, yellowColor]
   Color = colors[bColor]
   bx1 += 1 + (x - 1)*bw
   by1 += 1 + (y - 1)*bh - 1
   bx2 = z*bw - 1
   pygame.draw.rect(windowSurfaceObj, Color,      Rect(bx1, by1, bx2, by2))
   if bColor == 0:
      pygame.draw.line(windowSurfaceObj, blackColor, (bx1,   by1),   (bx1+bx2-1, by1   ))
      pygame.draw.line(windowSurfaceObj, whiteColor, (bx1+1, by1+1), (bx1+bx2-2, by1+1 ))
      pygame.draw.line(windowSurfaceObj, whiteColor, (bx1,   by1),   (bx1,       by1+bh))
   else:
      pygame.draw.line(windowSurfaceObj, whiteColor, (bx1,   by1),   (bx1+bx2-1, by1   ))
      pygame.draw.line(windowSurfaceObj, blackColor, (bx1+1, by1+1), (bx1+bx2-2, by1+1 ))
      pygame.draw.line(windowSurfaceObj, whiteColor, (bx1,   by1),   (bx1,       by1+bh))
   if upd == 1:
      pygame.display.update(bx1, by1, bx2, by2)
   return

button(b1x, 1, b1y, 2, bw, 2, bh, auto_g,0)
button(b1x, 3, b1y, 2, bw, 1, bh, hist,0)
button(b1x, 4, b1y, 2, bw, 1, bh, nr,0)
button(b1x, 1, b1y, 3, bw, 1, bh, plot,0)
button(b1x, 1, b1y, 4, bw, 1, bh, log,0)
button(b1x, 2, b1y, 3, bw, 1, bh, graph,0)
button(b1x, 2, b1y, 4, bw, 1, bh, thres,0)
button(b1x, 4, b1y, 3, bw, 1, bh, auto_win,0)
button(b1x, 4, b1y, 4, bw, 1, bh, auto_t,0)
button(b1x, 4, b1y, 5, bw, 1, bh, auto_i,0)
button(b1x, 3, b1y, 3, bw, 1, bh, nsi,0)
button(b1x, 3, b1y, 4, bw, 1, bh, ewi,0)
button(b1x, 3, b1y, 6, bw, 2, bh, 0,0)
button(b1x, 3, b1y, 5, bw, 1, bh, 0,0)
button(b2x, 5, b2y, 6, bw, 1, bh, cls,1)
for cy in range (2, 7):
   button(b1x, 5, b1y, cy, bw, 2, bh, 0,0)
   button(b2x, 3, b2y, cy, bw, 2, bh, 0,0)
for cy in range (3, 7):
   button(b2x, 1, b2y, cy, bw, 2, bh, 0,0)
button(b1x, 1, b1y, 5, bw, 2, bh, 0,0)
button(b1x, 1, b1y, 6, bw, 2, bh, 0,0)
button(b2x, 1, b2y, 2, bw, 2, bh, 0,0)
if photoon:
   button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
   button(b2x, 5, b2y, 3, bw, 2, bh, 0,0)
   button(b2x, 5, b2y, 4, bw, 2, bh, 0,0)
if use_Pi_Cam:
   button(b2x, 5, b2y, 5, bw, 1, bh, 0,0)
else:
   button(b2x, 5, b2y, 5, bw, 1, bh, Auto_Gain,0)
button(b2x, 6, b2y, 5, bw, 1, bh, 0,0)
button(b2x, 6, b2y, 6, bw, 1, bh, con_cap,0)
button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
button(b3x, 1, b3y, 2, bw, 1, bh, decN,0)
button(b3x, 1, b3y, 4, bw, 1, bh, decS,0)
button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
button(b3x, 5, b3y, 2, bw, 1, bh, 0,0)
button(b3x, 5, b3y, 4, bw, 1, bh, 0,0)
button(b3x, 4, b3y, 3, bw, 1, bh, 0,0)
button(b3x, 6, b3y, 3, bw, 1, bh, 0,0)
button(b3x, 1, b3y, 6, bw, 1, bh, 0,0)
button(b3x, 2, b3y, 6, bw, 1, bh, 0,0)
button(b3x, 3, b3y, 6, bw, 1, bh, 0,0)
if use_config > 0:
   button(b3x, use_config, b3y, 6, bw, 1, bh, 3,0)
button(b3x, 4, b3y, 6, bw, 1, bh, 0,0)
button(b3x, 5, b3y, 6, bw, 1, bh, 0,0)
button(b3x, 6, b3y, 6, bw, 1, bh, 0,0)
if Display == 0:
   button(b3x, 6, b3y, 5, bw, 1, bh, 0,0)

# put text on a button
def keys(bcolor,msg, fsize, fcolor, fx, bw, hp, fy, bh, vp, vo, upd):
   fy += 2 + (vp - 1)*bh + vo*(bh/6)
   fx += 2 + hp*bw
   if msg == "Exp Time" or msg == "     eV" or msg == "Cam Angle" or msg == "scale all" or msg == "CAL Time" or msg == "ISO" :
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(fx,        fy+1, bw*2 - 3, bh/2.4))
   if msg == " CALIB DEC" or msg == " CALIB  RA" or msg == "TELESCOPE":
      pygame.draw.rect(windowSurfaceObj, blackColor, Rect(fx,        fy+1, bw*3 - 3, bh/2.4))
   if msg == "CAL" or msg == " ......" or msg == "cen" or msg == " tre":
      pygame.draw.rect(windowSurfaceObj, blackColor, Rect(fx,        fy+1, bw*1 - 3, bh/2.4))
   if vo == 3:
      if bcolor  == 0:
         pygame.draw.rect(windowSurfaceObj, greyColor, Rect(fx-3-bw/2, fy,   bw+4,     bh/2.2))
      else:
         pygame.draw.rect(windowSurfaceObj, dgryColor, Rect(fx-2-bw/2, fy,   bw+4,     bh/2.2))
      fx -= 2 + (len(msg)*fsize)/4
   elif vo == 4:
      fy -= 2
   colors =        [dgryColor, greenColor, yellowColor, redColor, greenColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   color =         colors[fcolor]
   fontObj =       pygame.font.Font('freesansbold.ttf', int(fsize))
   msgSurfaceObj = fontObj.render(msg, False, color)
   msgRectobj =    msgSurfaceObj.get_rect()
   msgRectobj.topleft = (fx, fy)
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd > 0 :
      if Display == 1:
         pygame.display.update(0,height,modewidth,hplus)
      else:
         pygame.display.update(pygame.Rect(int(fx/bw)*bw, int(fy/bh)*bh, bw*3, bh))
   return

keys(0,str(int(nscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 2, 3, 0)
keys(0,str(int(sscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 3, 3, 0)
keys(0,str(int(escale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 4, 3, 0)
keys(0,str(int(wscale)),           fs,       3,        b2x,         bw,   3,     b2y, bh, 5, 3, 0)
keys(0,str(int(threshold)),        fs,       3,        b1x,         bw,   5,     b1y, bh, 4, 3, 0)
keys(0,str(int(Interval)),         fs,       3,        b1x,         bw,   5,     b1y, bh, 5, 3, 0)
keys(0,str(minc),                  fs,       3,        b1x,         bw,   3,     b1y, bh, 6, 3, 0)
msg = rgb[rgbw]
if rgbw < 5:
   keys(0,msg,                     fs,       rgbw+2,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
else:
   keys(0,msg,                     fs,       rgbw+1,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
if crop != maxwin:
   keys(0,str(crop),               fs,       3,        b1x,         bw,   5,     b1y, bh, 3, 3, 0)
else:
   keys(0,"max",                   fs,       3,        b1x,         bw,   5,     b1y, bh, 3, 3, 0)
keys(0,"AWin",                     fs-1,     auto_win, b1x,         bw,   3,     b1y, bh, 3, 1, 0)
keys(0,"W",                        fs-1,     5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 3, 1, 0)
keys(0,"AThr",                     fs-1,     auto_t,   b1x,         bw,   3,     b1y, bh, 4, 1, 0)
keys(0,"T",                        fs-1,     5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 4, 1, 0)
keys(0,"AutoG",                    fs,       auto_g,   b1x,         bw,   0,     b1y, bh, 2, 1, 0)
keys(0,"A",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 2, 1, 0)
if hist <= 2:
   keys(0,"Hist",                  fs,       hist,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
else:
   keys(0,"2x2",                   fs,       hist,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
keys(0,"Log",                      fs,       log,      b1x,         bw,   0,     b1y, bh, 4, 1, 0)
keys(0,"L",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 4, 1, 0)
keys(0,"Gph",                      fs,       graph,    b1x,         bw,   1,     b1y, bh, 3, 1, 0)
keys(0,"G",                        fs,       5,        b1x,         bw,   1,     b1y, bh, 3, 1, 0)
keys(0,"Plot",                     fs,       plot,     b1x,         bw,   0,     b1y, bh, 3, 1, 0)
keys(0,"P",                        fs,       5,        b1x,         bw,   0,     b1y, bh, 3, 1, 0)
keys(0,"Thr",                      fs,       thres,    b1x,         bw,   1,     b1y, bh, 4, 1, 0)
keys(0,"h",                        fs,       5,        b1x+fs/1.5,  bw,   1,     b1y, bh, 4, 1, 0)
keys(0,Dkey[12],                   fs,       nsi,      b1x,         bw,   2,     b1y, bh, 3, 1, 0)
keys(0,Dkey[13],                   fs,       ewi,      b1x,         bw,   2,     b1y, bh, 4, 1, 0)
if DKeys == 1:
   keys(0,"N",                     fs,       5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
   keys(0,"E",                     fs,       5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)
else:
   keys(0,"D",                     fs,       5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
   keys(0,"R",                     fs,       5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)
keys(0,"AInt",                     fs-1,     auto_i,   b1x,         bw,   3,     b1y, bh, 5, 1, 0)
keys(0,"I",                        fs-1,     5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 5, 1, 0)
keys(0,"rgbw",                     fs,       6,        b1x,         bw,   4,     b1y, bh, 2, 0, 0)
keys(0,"b",                        fs,       5,        b1x+fs,      bw,   4,     b1y, bh, 2, 0, 0)
keys(0," <",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 2, 4, 0)
keys(0,">",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 2, 4, 0)
keys(0,"window",                   fs,       6,        b1x,         bw,   4,     b1y, bh, 3, 0, 0)
keys(0," -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 3, 4, 0)
keys(0,"+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 3, 4, 0)
keys(0,"threshold",                fs-1,     6,        b1x,         bw,   4,     b1y, bh, 4, 0, 0)
keys(0," -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 4, 4, 0)
keys(0,"+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 4, 4, 0)
keys(0,"interval",                 fs,       6,        b1x,         bw,   4,     b1y, bh, 5, 0, 0)
keys(0," -",                       fs,       6,        b1x,         bw,   4,     b1y, bh, 5, 4, 0)
keys(0,"+",                        fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 5, 4, 0)
if use_Pi_Cam == 1 or (use_Pi_Cam == 0 and Webcam <2):
    keys(0,"Zoom",                 fs,       6,        b1x,         bw,   4,     b1y, bh, 6, 0, 0)
    keys(0," -",                   fs,       6,        b1x,         bw,   4,     b1y, bh, 6, 4, 0)
    keys(0,"+",                    fs,       6,        b1x+bw-fs,   bw,   5,     b1y, bh, 6, 4, 0)
    keys(0,str(zoom),              fs,       3,        b1x,         bw,   5,     b1y, bh, 6, 3, 0)
    
keys(0,"Min Corr",                 fs,       6,        b1x,         bw,   2,     b1y, bh, 6, 0, 0)
keys(0," -",                       fs,       6,        b1x,         bw,   2,     b1y, bh, 6, 4, 0)
keys(0,"+",                        fs,       6,        b1x+bw-fs,   bw,   3,     b1y, bh, 6, 4, 0)
keys(0,Dkey[8],                    fs-1,     6,        b2x,         bw,   2,     b2y, bh, 2, 0, 0)
keys(0," -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 2, 4, 0)
keys(0,"+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 2, 4, 0)
keys(0,Dkey[9],                    fs-1,     6,        b2x,         bw,   2,     b2y, bh, 3, 0, 0)
keys(0," -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 3, 4, 0)
keys(0,"+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 3, 4, 0)
keys(0,Dkey[11],                   fs,       6,        b2x,         bw,   2,     b2y, bh, 4, 0, 0)
keys(0," -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 4, 4, 0)
keys(0,"+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 4, 4, 0)
keys(0,Dkey[10],                   fs,       6,        b2x,         bw,   2,     b2y, bh, 5, 0, 0)
keys(0," -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 5, 4, 0)
keys(0,"+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 5, 4, 0)
keys(0,"scale all",                fs,       6,        b2x,         bw,   2,     b2y, bh, 6, 0, 0)
keys(0," -",                       fs,       6,        b2x,         bw,   2,     b2y, bh, 6, 4, 0)
keys(0,"+",                        fs,       6,        b2x+bw-fs,   bw,   3,     b2y, bh, 6, 4, 0)
if (use_Pi_Cam and camera_connected) or (not use_Pi_Cam and camera_connected):
   keys(0,"Brightness",            fs-2,     6,        b2x,         bw,   0,     b2y, bh, 2, 0, 0)
   keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 2, 4, 0)
   keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 2, 4, 0)
   keys(0,str(rpibr),              fs,       3,        b2x,         bw,   1,     b2y, bh, 2, 3, 0)
   keys(0,str(rpico),              fs,       3,        b2x,         bw,   1,     b2y, bh, 3, 3, 0)
   keys(0,"Contrast",              fs,       6,        b2x,         bw,   0,     b2y, bh, 3, 0, 0)
   keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 3, 4, 0)
   keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 3, 4, 0)
if not use_Pi_Cam and camera_connected:
   keys(0,"Exposure",              fs-1,     6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
   keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
   keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
   keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
   if Webcam == 0 :
      keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
      keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
      keys(0,"Adj Red",            fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
      keys(0,"Adj Blue",           fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
      keys(0,str(rpiredx),         fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
      keys(0,str(rpibluex),        fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
      keys(0,"Gain",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
      keys(0,str(gain),            fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
   elif Webcam == 1:
      keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
      keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
      keys(0,"Saturation",         fs-1,     6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
      keys(0,"Color Temp",         fs-2,     6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
      keys(0,str(saturation),      fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
      keys(0,str(color_temp),      fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
      keys(0,"Gain",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
      keys(0,str(gain),            fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
   elif Webcam > 1:
      keys(0,"  eV",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
      keys(0,str(rpiev),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
      keys(0,"Adj Red",            fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
      keys(0,"Adj Blue",           fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
      keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
      keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
      keys(0,str(rpiredx),         fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
      keys(0,str(rpibluex),        fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
      keys(0,"Exp Mode",           fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
      if scene_mode == 0:
          keys(0,"None ",          fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
      else:
          keys(0,"Night",          fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)

if use_Pi_Cam and camera_connected:
   rpiexa = rpimodesa[rpiexno]
   if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
      keys(0,str(int(rpiss/1000)), fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
   else:
      keys(0,str(int(rpiev)),      fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
   keys(0,(rpimodesa[rpiexno]),    fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
   keys(0,str(rpiISO),             fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
   if not rpiISO:
      keys(0,'auto',               fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
   if rpiex == 'off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
      keys(0,"Exp Time",           fs-1,     6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
   else:
      keys(0,"     eV",            fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
   keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
   keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
   keys(0,"ISO",                   fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
   keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
   keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
   keys(0,"Exp Mode",              fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
   keys(0," <",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
   keys(0,">",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
   keys(0,"Adj Red",               fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
   keys(0," -",                    fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
   keys(0,"+",                     fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
   keys(0,"Adj Blue",              fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
   keys(0," -",                    fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
   keys(0,"+",                     fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
   rpiredx =   Decimal(rpired)/Decimal(100)
   rpibluex = Decimal(rpiblue)/Decimal(100)
   keys(0,str(rpiredx),            fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
   keys(0,str(rpibluex),           fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
keys(0,Dkey[4],                    fs-1,     6,        b3x,         bw,   4,     b3y, bh, 2, 2, 0)
keys(0,Dkey[6],                    fs-2,     6,        b3x,         bw,   5,     b3y, bh, 3, 2, 0)
keys(0,Dkey[7],                    fs-2,     6,        b3x,         bw,   4,     b3y, bh, 4, 2, 0)
keys(0,Dkey[5],                    fs-2,     6,        b3x,         bw,   3,     b3y, bh, 3, 2, 0)
keys(0,"Esc",                      fs,       5,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
keys(0,"DEC",                      fs-1,     decN,     b3x,         bw,   0,     b3y, bh, 2, 0, decN)
keys(0,"  N",                      fs-1,     decN,     b3x,         bw,   0,     b3y, bh, 2, 2, decN)
keys(0,"nr",                       fs,       nr,       b1x,         bw,   3,     b1y, bh, 2, 1, nr)
keys(0,"DEC",                      fs-1,     decS,     b3x,         bw,   0,     b3y, bh, 4, 0, decS)
keys(0,"  S",                      fs-1,     decS,     b3x,         bw,   0,     b3y, bh, 4, 2, decS)
keys(0," R1",                      fs,       6,        b3x,         bw,   0,     b3y, bh, 6, 1, 0)
keys(0,"1",                        fs,       5,        b3x+fs,      bw,   0,     b3y, bh, 6, 1, 1)
keys(0," R2",                      fs,       6,        b3x,         bw,   1,     b3y, bh, 6, 1, 0)
keys(0,"2",                        fs,       5,        b3x+fs,      bw,   1,     b3y, bh, 6, 1, 0)
keys(0," R3",                      fs,       6,        b3x,         bw,   2,     b3y, bh, 6, 1, 0)
keys(0,"3",                        fs,       5,        b3x+fs,      bw,   2,     b3y, bh, 6, 1, 0)
keys(0," S1",                      fs,       6,        b3x,         bw,   3,     b3y, bh, 6, 1, 0)
keys(0," S2",                      fs,       6,        b3x,         bw,   4,     b3y, bh, 6, 1, 0)
keys(0," S3",                      fs,       6,        b3x,         bw,   5,     b3y, bh, 6, 1, 0)
if Display == 0:
   keys(0,"Menu",                  fs-2,     6,        b3x,         bw,   5,     b3y, bh, 5, 1, 0)
keys(0,"RELOAD cfg",               fs-2,     7,        b3x+bw/10,    bw,   0,     b3y, bh, 5, 4, 0)
keys(0,"SAVE cfg",                 fs-2,     7,        b3x+bw/10,    bw,   3,     b3y, bh, 5, 4, 0)
if Night:
   keys(0,"Day",                   fs-1,     6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
else:
   keys(0,"Night",                 fs-1,     6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
keys(0,"TELESCOPE",                fs,       1,        b3x+bw/5,    bw,   0,     b3y-2, bh, 5, 0, 0)
keys(0,"WINDOW",                   fs,       1,        b3x+bw/6,    bw,   3,     b3y-2, bh, 5, 0, 0)
keys(0,"Stop",                     fs,       7,        b3x,         bw,   2,     b3y, bh, 4, 1, 0)
keys(0,"cen",                      fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
keys(0," tre",                     fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
keys(0,"cen",                      fs,       7,        b3x,         bw,   4,     b3y, bh, 3, 0, 0)
keys(0," tre",                     fs,       7,        b3x,         bw,   4,     b3y, bh, 3, 2, 0)
keys(0,"con",                      fs,       con_cap,  b2x,         bw,   5,     b2y, bh, 6, 0, 0)
keys(0,"cap",                      fs,       con_cap,  b2x,         bw,   5,     b2y, bh, 6, 2, 0)
if use_Pi_Cam:
   keys(0,"pic",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 5, 0, 0)
   keys(0,"cap",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 5, 2, 0)
if not use_Pi_Cam and camera_connected:
   keys(0,"Auto",                  fs,       Auto_Gain,b2x,         bw,   4,     b2y, bh, 5, 0, 0)
   keys(0,"Gain",                  fs,       Auto_Gain,b2x,         bw,   4,     b2y, bh, 5, 2, 0)
keys(0,"Scr",                      fs,       6,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
keys(0,"cap",                      fs,       6,        b2x,         bw,   5,     b2y, bh, 5, 2, 0)
keys(0,"S",                        fs,       5,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
if photoon:
    keys(0,"PHOTO",                fs,       photo,    b2x,         bw,   4,     b2y, bh, 2, 0, 0)
    keys(0,"O",                    fs,       5,        b2x+fs*1.5,  bw,   4,     b2y, bh, 2, 0, 0)
    keys(0,"P-Time",               fs,       6,        b2x,         bw,   4,     b2y, bh, 3, 0, 0)
    keys(0," -",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 3, 4, 0)
    keys(0,"+",                    fs,       6,        b2x+bw-fs,   bw,   5,     b2y, bh, 3, 4, 0)
    keys(0,str(ptime),             fs,       3,        b2x,         bw,   5,     b2y, bh, 3, 3, 0)
    keys(0,"P-Count",              fs,       6,        b2x,         bw,   4,     b2y, bh, 4, 0, 0)
    keys(0," -",                   fs,       6,        b2x,         bw,   4,     b2y, bh, 4, 4, 0)
    keys(0,"+",                    fs,       6,        b2x+bw-fs,   bw,   5,     b2y, bh, 4, 4, 0)
    keys(0,str(pcount),            fs,       3,        b2x,         bw,   5,     b2y, bh, 4, 3, 0)
keys(0,"CLS",                      fs,       cls,      b2x,         bw,   4,     b2y, bh, 6, 1, 0)
keys(0,"C",                        fs,       5,        b2x,         bw,   4,     b2y, bh, 6, 1, 0)
use_config = 0

# draw the direction arrows
if Display != 1:
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 15, bh*10 + bh/3 + 10), 2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3 + 5),  2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                              
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 5,  bh*10 + bh/3 + 10), 2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3 + 5),  2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                                                                              
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 5,  bh*12 + bh/3),      (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), 2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 5),  2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (Disp_Width + bw*5 + bw/4 + 10, bh*12 + bh/3 + 10), 2)
                                                                                                                                                   
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 15, bh*12 + bh/3),      (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), 2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 5),  2)
   pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (Disp_Width + bw*3 + bw/4 + 10, bh*12 + bh/3 + 10), 2)

pygame.display.update()

def demo(width, height, posx, posy, blanklinr, wd, hd):
   time.sleep(0.25)
   zz = 1000
   ad = width
   bd = height
   imu = ""
   line = ""
   for height in range (1, posy):
      tt = random.randrange(0,zz,1)
      line += blanklinr[0+tt:(width*3)+tt]
   imu += line
   for height in range (posy, posy + hd):
      tt = random.randrange(0,zz,1)
      byte = blanklinr[0 +tt:((posx-1)*3)+tt]
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
         fe = min(fe, 127)
         byte = chr(fe) + chr(fe) + chr(fe)
         imu += byte
         width += 1
         
      tt = random.randrange(0,zz,1)
      byte = blanklinr[0+tt:((ad+1-width)*3)+tt]
      imu += byte
   line = ""
   for height in range (posy + hd, bd + 1):
      tt = random.randrange(0,zz,1)
      line += blanklinr[0+tt:(ad*3)+tt]
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

oldscene_mode,oldsaturation,oldcolor_temp,oldsharpness,oldAuto_Gain,oldgamma,oldexposure,oldgain,oldminc,oldnscale, oldescale, oldsscale, oldwscale, oldcrop, oldauto_g, oldInterval, oldlog, oldrgbw, oldthreshold, oldgraph, oldthres, oldauto_i, oldplot, oldauto_win, oldauto_t, oldzoom, oldrpibr, oldrpico, oldrpiss, oldrpiexno, oldrpiISO, oldrpiev, oldcls, oldcon_cap, oldphoto, oldptime, oldpcount, oldrpired, oldrpiblue, oldhist, oldnr, olddecN, olddecS, oldnsi, oldewi = scene_mode,saturation,color_temp,sharpness,Auto_Gain,gamma,exposure, gain,minc,nscale, escale, sscale, wscale, crop, auto_g, Interval, log, rgbw, threshold, graph, thres, auto_i, plot, auto_win, auto_t, zoom, rpibr, rpico, rpiss, rpiexno, rpiISO, rpiev, cls, con_cap, photo, ptime, pcount, rpired, rpiblue, hist, nr, decN, decS, nsi, ewi

arv =        {}
arh =        {}
arp =        {}
count =       0
crop  =    crop
posx =  Disp_Width/2
posy = Disp_Height/2
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
oldmn2 =      0

blankline =     chr(  3) + chr(  3) + chr(  3)
blanklinr =     chr(  3) + chr(  3) + chr(  3)
for wz in range (1, width):
   blankline += chr(  3) + chr(  3) + chr(  3)
if not camera_connected:
   for wz in range (1, width * 10):
      tx = random.randrange(0,30,1)
      blanklinr += chr(tx) + chr(tx) + chr(tx)
redline =       chr(127) + chr(  0) + chr(  0)
bluline =       chr(  0) + chr(  0) + chr(127)
greline =       chr(  0) + chr(127) + chr(  0)
gryline =       chr(127) + chr(127) + chr(127)
dgryline =      chr(127) + chr( 70) + chr( 70)
yelline =       chr(127) + chr(127) + chr(  0)
cynline =       chr(  0) + chr(127) + chr(127)
purline =       chr(127) + chr(  0) + chr(127)
for wz in range (1, 50):
   redline +=   chr(127) + chr(  0) + chr(  0)
   bluline +=   chr(  0) + chr(  0) + chr(127)
   greline +=   chr(  0) + chr(127) + chr(  0)
   gryline +=   chr(127) + chr(127) + chr(127)
   dgryline +=  chr(127) + chr( 70) + chr( 70)
   yelline +=   chr(127) + chr(127) + chr(  0)
   cynline +=   chr(  0) + chr(127) + chr(127)
   purline +=   chr(127) + chr(  0) + chr(127)

if serial_connected:
   if os.path.exists('/dev/ttyACM0') == True:
      ser = serial.Serial('/dev/ttyACM0', 9600)
   elif os.path.exists('/dev/ttyACM1') == True:
      ser = serial.Serial('/dev/ttyACM1', 9600)
      
start = time.time()
start2 =   start
esc1 =         0
esc2 =         0
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
navscale =     3
samples =      nr * navscale 
nav =         {}
nav =     [0]* navscale * 3
nav2 =        {}
nav2 =    [0]* navscale * 3
nav3 =        {}
nav3 =    [0]* navscale * 3
nav4 =        {}
nav4 =    [0]* navscale * 3
nycle2 =       0
   
if sys.version_info[0] == 3:
   mr = numpy.ones((crop*crop,1),dtype = 'int')
if Cwindow:
   mmq, mask, change = MaskChange()
if not use_Pi_Cam and camera_connected:
   rpistr = "v4l2-ctl -c brightness=" + str(rpibr) + " -d " + str(dve)
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   rpistr = "v4l2-ctl -c contrast=" + str(rpico) + " -d " + str(dve)
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   if Webcam == 0 : # Philips Webcam initialisation
      rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c gamma=" + str(gamma) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c white_balance_automatic=3" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c red_balance=" + str(rpired) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c blue_balance=" + str(rpiblue) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c auto_contour=" + str(auto_contour) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c contour=" + str(contour) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c dynamic_noise_reduction=" + str(dnr) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c backlight_compensation=" + str(backlight) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   elif Webcam == 1: # Logitech Webcam  initialisation
      rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c sharpness=" + str(sharpness) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c white_balance_temperature_auto=0" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   elif Webcam > 1 : # Pi Cam as Webcam initialisation
      path = 'v4l2-ctl -p 10' # 10 fps
      os.system (path)
      rpistr = "v4l2-ctl -c white_balance_auto_preset=0" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c red_balance=" + str(rpired) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c blue_balance=" + str(rpiblue) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c sharpness=" + str(sharpness) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c iso_sensitivity_auto=1" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c iso_sensitivity=1" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c scene_mode=8" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c auto_exposure_bias=" + str(rpiev + 12) + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c compression_quality=30" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      rpistr = "v4l2-ctl -c horizontal_flip=1" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

   if Auto_Gain:
      keys(0,str(exposure),           fs,   0,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
      if Webcam != 2:
         keys(0,str(gain),            fs,   0,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
      if Webcam == 0:   
         rpistr = "v4l2-ctl -c gain_automatic=1" + " -d " + str(dve)
      elif Webcam == 1:
         rpistr = "v4l2-ctl -c exposure_auto=3" + " -d " + str(dve)
      elif Webcam > 1:
         rpistr = "v4l2-ctl -c auto_exposure=0" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
   else:
      keys(0,str(exposure),           fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
      if Webcam != 2:
         keys(0,str(gain),            fs,   3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
      if Webcam == 0:   
         rpistr = "v4l2-ctl -c gain_automatic=0" + " -d " + str(dve)
      elif Webcam == 1:
         rpistr = "v4l2-ctl -c exposure_auto=1" + " -d " + str(dve)
      elif Webcam > 1:
         rpistr = "v4l2-ctl -c auto_exposure=1" + " -d " + str(dve)
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      
   if Webcam == 0:
      rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
   elif Webcam == 1:
      rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
   elif Webcam > 1:
      rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
   p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)

# MAIN loop starts here...
#============================================================================================
#============================================================================================
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
      imu = demo(width, height, posx, posy, blanklinr, wd, hd)

# take picture
  # Webcam
   if camera_connected and not use_Pi_Cam:
      if Webcam == 2: # pi camera videostream
         img = vs.read()
         img = img[..., [2, 1, 0]]
         image = pygame.surfarray.make_surface(img)
         image = pygame.transform.rotate(image,-90)
      elif Webcam == 3: # pi camera videostream
         ok, img = vs.read()
         img = img[..., [2, 1, 0]]
         image = pygame.surfarray.make_surface(img)
         image = pygame.transform.rotate(image,-90)
      else:  
         image = cam.get_image()
      if calibrate:
         for zcounter in range (1,10):
            if Webcam == 2: # pi camera videostream
                img = vs.read()
                img = img[..., [2, 1, 0]]
                image = pygame.surfarray.make_surface(img)
                image = pygame.transform.rotate(image,-90)
            elif Webcam == 3: # pi camera videostream
                ok, img = vs.read()
                img = img[..., [2, 1, 0]]
                image = pygame.surfarray.make_surface(img)
                image = pygame.transform.rotate(image,-90)
            else:  
                image = cam.get_image()
      if not zoom:
         offset5 = offset3
         offset6 = offset4
         if offset5 > 0 and offset5 >= w/2 - Disp_Width/2:
            offset5 = int(w/2) - int(Disp_Width/2)
         if offset5 < 0 and offset5 <= Disp_Width/2 - w/2:
            offset5 = int(Disp_Width/2) - int(w/2)
         if offset6 > 0 and offset6 >= h/2 - Disp_Height/2:
            offset6 = int(h/2) - int(Disp_Height/2)
         if offset6 < 0 and offset6 <= Disp_Height/2 - h/2:
            offset6 = int(Disp_Height/2) - int(h/2)

      if Webcam == 0 and zoom > 1 : # Philips
         wq = rpiwidth[usb_max_res - 1]
         hq = rpiheight[usb_max_res - 1]
         cropped = pygame.Surface((wq,hq ))
         cropped.blit(image, (0, 0), (int(rpiwidth[usb_max_res]/2)-int(rpiwidth[usb_max_res - 1]/2) + offset5,int(rpiheight[usb_max_res]/2)-int(rpiheight[usb_max_res - 1]/2) + offset6, wq, hq))
         if zoom == 2:
            image = pygame.transform.scale(cropped,(Disp_Width,Disp_Height))
         if zoom == 3:
            image = pygame.transform.scale(cropped,(width,height))
            
      if Webcam == 1: # Logitech
         wq = rpiwidth[usb_max_res - zoom + 1]
         hq = rpiheight[usb_max_res - zoom + 1]
         cropped = pygame.Surface((wq,hq ))
         cropped.blit(image, (0, 0), (int(rpiwidth[usb_max_res]/2)-int(rpiwidth[usb_max_res - zoom  + 1]/2) + offset5,int(rpiheight[usb_max_res]/2)-int(rpiheight[usb_max_res - zoom + 1]/2) + offset6, wq, hq))
         image = pygame.transform.scale(cropped,(Disp_Width,Disp_Height))
         
      catSurfaceObj = image
      
      try:
         if con_cap:
            filno += 1
            now = datetime.datetime.now()
            timestamp = now.strftime("%y%m%d%H%M%S")
            fname = '/home/pi/pic' + str(timestamp) + "_" + str(filno) + '.jpg'
            pygame.image.save(image, fname)
      except OSError:
         pass

      if show_time == 1 and menu == 1:
         now = datetime.datetime.now()
         sec = now.strftime("%S")
         if sec != oldsec:
            timestamp = now.strftime("%H:%M:%S")
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(630, 400, 70, 20), 0)
            keys(0,timestamp, 16, 7, 630, 0, 0, 400, 0, 0, 0, 0)
            pygame.display.update(630, 400, 70, 20)
            oldsec = sec

      if not fc :
         if width != Disp_Width or Display > 0:
            if auto_rotate == 1 :
               Cang = Aang
               image = pygame.transform.rotate(image,Cang)
            else:
               image = pygame.transform.rotate(image,Cang)
            cropped = pygame.Surface((Disp_Width, Disp_Height))
            cropped.blit(image, (0,0), ((image.get_width()/2)-Disp_Width/2,(image.get_height()/2)-Disp_Height/2, Disp_Width, Disp_Height))
            catSurfaceObj = cropped
            image = cropped
         if menu != 1:
            windowSurfaceObj.blit(catSurfaceObj, (0, 0))
         if menu == 1:
            catSurfacesmall = pygame.transform.scale(catSurfaceObj, (int(Disp_Width/2),240))
            windowSurfaceObj.blit(catSurfacesmall, (318, 238))

      t3 = time.time()
      # check if DEC ouput timer complete, if so switch output relay OFF
      if vtime < t3:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[0],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys(0,Dkey[3],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
      # check if RA ouput timer complete, if so switch output relay OFF
      if htime < t3:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[1],                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys(0,Dkey[2],                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
      # use if camera has mirror lockup (tested on CANON only)
      if photo:
         ptime3 = int(ptime2 - t3) + 1
         if pmlock == 1 and pmlock2 == 1 and ptime3 == pwait - 3 and not camera:
            GPIO.output(C_OP, GPIO.HIGH)
            po = 1
            pmlock2 = 0
            pmlock3 = 1
         if pmlock == 1 and pmlock3 == 1 and ptime3 == pwait - 4 and not camera:
            GPIO.output(C_OP, GPIO.LOW)
            po = 0
            pmlock3 = 0
         if ptime3 != ptime4:
            keys(0,str(ptime3),               fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)##
            ptime4 = ptime3
      # take next PHOTO with DSLR
      if ptime2 < t3 and photo and camera:
         pcount2 -= 1
         keys(1,str((pcount + 1) - pcount2),  fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
         # check if PHOTO with DSLR are complete, if so stop taking photos with DSLR
         if not pcount2:
            photo = 0
            camera = 0
            button(b2x, 5, b2y, 2, bw, 2, bh, photo,1)
            keys(0,"PHOTO",                   fs, photo, b2x,        bw, 4, b2y, bh, 2, 0, 1)
            keys(0,"O",                       fs, 5,     b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)
            keys(0,"",                        fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
            keys(0,"",                        fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            if use_RPiGPIO or photoon:
               GPIO.output(C_OP, GPIO.LOW)
               po = 0
         else:
            camera = 0
            ptime2 = time.time() + pwait
            GPIO.output(C_OP, GPIO.LOW)
            po = 0
      # take next PHOTO with DSLR
      if ptime2 < t3 and photo and not camera:
         camera = 1
         ptime2 = time.time() + ptime
         keys(1,str(pcount + 1 - pcount2),    fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
         if use_RPiGPIO or photoon:
            GPIO.output(C_OP, GPIO.HIGH)
            po = 1

   # load Pi Camera picture
   elif camera_connected and use_Pi_Cam:
      rpistopNS = 0
      rpistopEW = 0
      mkey =      0
      # check next camera image is ready, and wait if not, checking for mousekey press and relay time out.
      while not os.path.exists('/run/shm/test.jpg') and not mkey:
         if auto_g :
            t2 = time.time()
            # check if DEC ouput timer complete, if so switch output relay OFF
            if vtime < t2 and not rpistopNS:
               if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                  DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                  DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               keys(0,Dkey[0],                       fs-1, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
               keys(0,Dkey[3],                       fs-1, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
               rpistopNS = 1
            # check if RA ouput timer complete, if so switch output relay OFF
            if htime < t2 and not rpistopEW:
               if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                  DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                  DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               keys(0,Dkey[1],                       fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
               keys(0,Dkey[2],                       fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
               rpistopEW = 1
         # check for mouse press whilst wating for new camera image
         for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP:
               mkey = 1
      # display clock if enabled
      if show_time == 1 and menu == 1:
         now = datetime.datetime.now()
         sec = now.strftime("%S")
         if sec != oldsec:
            timestamp = now.strftime("%H:%M:%S")
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(630, 400, 70, 20), 0)
            keys(0,timestamp, 16, 7, 630, 0, 0, 400, 0, 0, 0, 0)
            pygame.display.update(630, 400, 70, 20)
            oldsec = sec
            
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
      catSurfaceObj = image

      buttonx = pygame.mouse.get_pressed()
      if buttonx[0] != 0 :
         mousepress = 1
      
      # crop picam picture to suit Display Width
      if width != Disp_Width or Display > 0:
         if auto_rotate == 1 :
            Cang = Aang
            image = pygame.transform.rotate(image,Cang)
         else:
            image = pygame.transform.rotate(image,Cang)
         cropped = pygame.Surface((Disp_Width, Disp_Height))
         cropped.blit(image, (0,0), ((image.get_width()/2)-Disp_Width/2,(image.get_height()/2)-Disp_Height/2, Disp_Width, Disp_Height))
         catSurfaceObj = cropped
         image = cropped
      if menu != 1:
         windowSurfaceObj.blit(catSurfaceObj, (0, 0))
      else:
         catSurfacesmall = pygame.transform.scale(catSurfaceObj, (int(int(Disp_Width)/int(2)),240))
         windowSurfaceObj.blit(catSurfacesmall, (318, 238))
        
      t3 = time.time()
      # check if DEC ouput timer complete, if so switch output relay OFF
      if vtime < t3 and not rpistopNS:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[0],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys(0,Dkey[3],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
         rpistopNS = 1
      # check if RA ouput timer complete, if so switch output relay OFF
      if htime < t3 and not rpistopEW:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[1],                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys(0,Dkey[2],                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)
         rpistopEW = 1
      # take photo with DSLR if enabled
      if photo:
         ptime3 = int(ptime2 - t3) + 1
         # use if camera has mirror lockup (tested on CANON only)
         if pmlock == 1 and pmlock2 == 1 and ptime3 == pwait - 3 and not camera:
            GPIO.output(C_OP, GPIO.HIGH)
            po = 1
            pmlock2 = 0
            pmlock3 = 1
         if pmlock == 1 and pmlock3 == 1 and ptime3 == pwait - 4 and not camera:
            GPIO.output(C_OP, GPIO.LOW)
            po = 0
            pmlock3 = 0
         if ptime3 != ptime4:
            if po == 1:
               keys(1,str(ptime3),               fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            if po == 0:
               keys(1,str(ptime3),               fs, 2, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
            ptime4 = ptime3
         if ptime2 < t3 and camera:
            pcount2 -= 1
            keys(1,str(pcount + 1 - pcount2), fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
            # check if PHOTO with DSLR are complete, if so stop taking photos with DSLR
            if not pcount2:
               photo = 0
               camera = 0
               button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
               keys(0,"PHOTO",                fs, photo, b2x,        bw, 4, b2y, bh, 2, 0, 1)
               keys(0,"O",                    fs, 5,     b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)##
               keys(0,"",                     fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
               keys(0,"",                     fs, photo, b2x+14,     bw, 5, b2y, bh, 2, 3, 1)
               if use_RPiGPIO or photoon:
                  GPIO.output(C_OP, GPIO.LOW)
                  po = 0
            else:
               camera = 0
               pmlock2 = 1
               ptime2 = time.time() + pwait
               GPIO.output(C_OP, GPIO.LOW)
               po = 0
         # take next PHOTO with DSLR    
         if ptime2 < t3 and photo and not camera:
            camera = 1
            ptime2 = time.time() + ptime
            keys(1,str(pcount + 1 - pcount2), fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
            if use_RPiGPIO or photoon:
               GPIO.output(C_OP, GPIO.HIGH)
               po = 1

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
   elif not camera_connected:
      if sys.version_info[0] == 3:
         imu = bytes(imu,'ascii')
      image = pygame.image.fromstring(imu, (width, height), "RGB", 1)
      if auto_rotate == 1 :
         Cang = Aang
         image = pygame.transform.rotate(image,Cang)
      else:
         image = pygame.transform.rotate(image,Cang)
      cropped = pygame.Surface((Disp_Width, height))
      cropped.blit(image, (0,0), ((image.get_width()/2)-Disp_Width/2,(image.get_height()/2)-Disp_Height/2, Disp_Width, Disp_Height))
      catSurfaceObj = cropped
      image = cropped
      if menu != 1:
         windowSurfaceObj.blit(catSurfaceObj, (0, 0))
      if menu == 1:
         catSurfacesmall = pygame.transform.scale(catSurfaceObj, (int(Disp_Width/2),240))
         windowSurfaceObj.blit(catSurfacesmall, (318, 238))
      
      imb = imu
      t2 = time.time()
      if vtime < t2:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[0],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 2, 2, 1)
         keys(0,Dkey[3],                          fs-1, 6,     b3x,        bw, 1, b3y, bh, 4, 2, 1)
      if htime < t2:
         if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         keys(0,Dkey[1],                          fs, 6,     b3x,        bw, 0, b3y, bh, 3, 2, 1)
         keys(0,Dkey[2],                          fs, 6,     b3x,        bw, 2, b3y, bh, 3, 2, 1)

# crop picture
   if crop == maxwin:
      cropped = pygame.transform.scale(image, [crop, crop])
      w_corr =  Decimal(Disp_Width)/Decimal(crop)
      h_corr =  Decimal(Disp_Height)/Decimal(crop)
      offset3 = 0
      offset4 = 0
   else:
      cropped = pygame.Surface((crop, crop))
      cropped.blit(image, (0, 0), (Disp_Width/2 - crop/2 + offset3, Disp_Height/2 - crop/2 + offset4, crop, crop))
   if bits < 24:
      pygame.image.save(cropped, '/run/shm/cropped.jpg')
      cropped = pygame.image.load('/run/shm/cropped.jpg')
   imb = pygame.image.tostring(cropped, "RGB", 1)

# initialise arrays
   ars =      {}
   art =      {}
   arp =      {}
   mx =       []
   arp = [0]*300
   
   if rgbw < 4:
      if sys.version_info[0] == 3 :
         mq = numpy.array(list(imb),dtype='int')
         mq = mq[rgbw-1:crop*crop*3:3]
         if Cwindow == 1 and maxwin != crop:
            mq = mq * mmq
         mx = mq.tolist()

      else:
         for xcounter in range (0, crop*crop*3, 3):
            if rgbw == 1:
               ima = ord(imb[xcounter    :xcounter + 1])
            elif rgbw == 2:
               ima = ord(imb[xcounter + 1:xcounter + 2])
            elif rgbw == 3:
               ima = ord(imb[xcounter + 2:xcounter + 3])
            mx.append(ima)
         if Cwindow == 1 and maxwin != crop:
            mx = mx * mmq
   else:
      if sys.version_info[0] == 3:
         mq = numpy.array(list(imb),dtype='int')
         mqr = mq[0:crop*crop*3:3]
         mqg = mq[1:crop*crop*3:3]
         mqb = mq[2:crop*crop*3:3]
         if rgbw == 4:
            mq = numpy.maximum(mqr,mqg,mqb)
         else:
            mq = (mqr + mqg + mqb)/3
         if Cwindow == 1 and maxwin != crop:
            mq = mq * mmq
         mx = mq.tolist()

      else:
         for xcounter in range (0, crop*crop*3, 3):
            imrc = ord(imb[xcounter    :xcounter + 1])
            imgc = ord(imb[xcounter + 1:xcounter + 2])
            imbc = ord(imb[xcounter + 2:xcounter + 3])
            if rgbw == 4:
               ima = int(((imrc + imgc + imbc)/3))
               if ima > 255:
                  ima = 255
            else:
               ima = max(imrc, imgc, imbc)
            mx.append(ima)
         if Cwindow and maxwin != crop:
            mx = mx * mmq

         
# stretch histogram
   if hist == 1 or hist == 2:
      ct = 0
      ste = int((crop*crop)/3000)+1
      if crop == maxwin:
         ste = int((crop*crop)/((crop*crop)/zoom))+1
      while ct < (crop * crop):
         arp[int(mx[int(ct)]) + 1] += 1
         ct += ste
      count =  2
      mintot = 0
      tval = 0
      while tval < 3 and count < 299:
         tval += arp[count]
         count +=1
         mintot = count
      count =  255
      maxtot = 0
      tval = 0
      limit = 0.001
      if crop == maxwin:
         limit = 0.00001
      while tval < sum(arp) * limit and count < 299:
         tval += arp[count]
         count -=1
         maxtot = count
      
      mo = maxtot - mintot
      if nr > 0:
         nav[nycle] = mo
         if nstart == 1:
            for count2 in range (0,samples):
               nav[count2] = mo
         mo = int(sum(nav) / samples)
         nycle += 1
         if nycle > (samples - 1):
            nycle = 0
      if mo == 0:
         mo = 1
      cy = 0
      if hist == 1 or hist == 2:
         while cy < crop-1:
            cx = 0
            while cx < crop-1:
               if mx[cy*crop + cx] > 10:
                  tot = (mx[cy*crop + cx] - mintot) * (250 / mo) 
                  if tot > 250:
                     tot = 250
                  elif tot < 0:
                     tot = 0
                  mx[cy*crop + cx] = tot
               cx += 1
            cy += 1
         
# 2x2 binning
   if hist == 3:
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
   if nr > 0 and thres == 2 and crop != maxwin and menu == 0:
      me = numpy.c_[mx,mx,mx]
      me = numpy.reshape(me,(crop,crop,3))
      imagez = pygame.surfarray.make_surface(me)
      imagez = pygame.transform.rotate(imagez,90)
      imagez.set_colorkey(0, pygame.RLEACCEL)
      catSurfaceObj = imagez
      windowSurfaceObj.blit(catSurfaceObj, (int(Disp_Width/2) - int(crop/2) + offset3, int(Disp_Height/2) - int(crop/2) + offset4))

# calculate min and max values
   arp = [0]*300
   ct = 0
   ste = int((crop*crop)/3000)+1
   if crop == maxwin:
      ste = int((crop*crop)/((crop*crop)/zoom))+1
   while ct < (crop * crop):
      arp[int(mx[int(ct)]) + 1] += 1
      ct += ste
   count =  2
   mintot = 0
   tval = 0
   while tval < 3 and count < 299:
      tval += arp[count]
      count +=1
      mintot = count
   count =  2
   noitot = 0
   tval = 0
   while tval < sum(arp) * 0.25 and count < 299:
      tval += arp[count]
      count +=1
      noitot = count
   count =  255
   maxtot = 0
   tval = 0
   limit = 0.001
   if crop == maxwin:
      limit = 0.00001
   while tval < sum(arp) * limit and count < 299 :
      tval += arp[count]
      count -=1
      maxtot = count
   if noitot > (maxtot - mintot)/1.5:
      noitot = (maxtot - mintot)/2
   if nr > 0:
      if nstart == 1:
         nav2 = [0]* navscale * 3
         nav3 = [0]* navscale * 3
         nav4 = [0]* navscale * 3
         for count2 in range (0,samples):
            nav2[count2] = mintot
            nav3[count2] = maxtot
            nav4[count2] = noitot
         nstart = 0
      nav2[nycle2] = mintot
      nav3[nycle2] = maxtot
      nav4[nycle2] = noitot
      mintot = int(sum(nav2) / samples)
      maxtot = int(sum(nav3) / samples)
      noitot = int(sum(nav4) / samples)
   upnoi = noitot + (noitot-mintot)
   mn2 = maxtot - mintot
   nycle2 += 1
   if nycle2 > (samples - 1):
      nycle2 = 0
      
# calculate threshold value
   if not auto_t:
      pcont = maxtot - threshold
      if hist == 2:
         if maxtot - upnoi < m_thr_limit :
            pcont = 255
      else:
         if maxtot - noitot < m_thr_limit :
            pcont = 255
   else:
      if hist == 2:
         threshold = (maxtot - upnoi)/2
      else:
         threshold = (maxtot - noitot)/3
      pcont = maxtot - threshold
      if esc1 == 0:
         keys(0,str(int(threshold)), fs, 3, b1x, bw, 5, b1y, bh, 4, 3, 1)
      if hist == 2:
         if maxtot - upnoi < a_thr_limit :
            pcont = 255
      else:
         if maxtot - noitot < a_thr_limit :
            pcont = 255
      
# compare array to threshold value
   mz = numpy.array(mx,dtype = 'int')
   mz[mz <  pcont] = 0
   mz[mz >= pcont] = 1
   ttot = numpy.sum(mz)
   if ttot < 6 or (not Cwindow and ttot == crop*crop) or (Cwindow and ttot > (int(int(crop/2)*int(crop/2)) * 3)):
      ttot = 1
      
# more noise reduction by removing single pixels
   if nr > 0 and hist != 3:
      pz = numpy.reshape(mz,(crop,crop))
      pr = numpy.diff(numpy.diff(pz))
      pr[pr !=  -2 ] = 0
      pr[pr ==  -2 ] = -1
      mt = numpy.zeros((crop,1),dtype = 'int')
      pr = numpy.c_[mt,pr,mt]
      
      qc = numpy.swapaxes(pz,0,1)
      qr = numpy.diff(numpy.diff(qc))
      qr[qr !=  -2 ] = 0
      qr[qr ==  -2 ] = -1
      qr = numpy.c_[mt,qr,mt]
      
      qr = numpy.swapaxes(qr,0,1) 
      qt = pr + qr
      qt[qt !=  -2 ] = 0
      qt[qt ==  -2 ] = -1
      qu = numpy.reshape(qt,(crop*crop))
      mz = mz + qu
      ttot = numpy.sum(mz)
      if ttot < 6 or (not Cwindow and ttot == crop*crop) or (Cwindow and ttot > (int(int(crop/2)*int(crop/2)) * 3)):
         ttot = 1
     
# display Threshold if enabled
   if thres and ttot > 1:
      mr = numpy.zeros((crop*crop,1),dtype = 'int')
      ma = mz * 255
      if rgbw == 1:
         ms = numpy.c_[ma,mr,mr]
      elif rgbw == 2:
         ms = numpy.c_[mr,ma,mr]
      elif rgbw == 3:
         ms = numpy.c_[mr,mr,ma]
      else:
         ms = numpy.c_[ma,ma,mr]

      md = numpy.reshape(ms,(crop,crop,3))
      imagep = pygame.surfarray.make_surface(md)
      imagep = pygame.transform.rotate(imagep,90)

      if crop != maxwin:
         if menu != 1:
            if thres == 1:
               imagep.set_alpha(127)
            imagep.set_colorkey(0, pygame.RLEACCEL)
            catSurfaceObj = imagep
            windowSurfaceObj.blit(catSurfaceObj, (int(Disp_Width/2) - int(crop/2) + offset3, int(Disp_Height/2) - int(crop/2) + offset4))
         else:
            imagep = pygame.transform.scale(imagep, [int(crop/2), int(crop/2)])
            if thres == 1:
               imagep.set_alpha(127)
            imagep.set_colorkey(0, pygame.RLEACCEL)
            catSurfaceObj = imagep
            windowSurfaceObj.blit(catSurfaceObj, (318 + Disp_Width/4 - int(crop/4) + int(offset3/2), 238 + Disp_Height/4 - int(crop/4) + int(offset4/2)))
            
      else:
         if menu == 0:
            imagep = pygame.transform.scale(imagep, [Disp_Width, Disp_Height])
            crimage = pygame.Surface((Disp_Width, Disp_Height))
            crimage.blit(imagep, (0, 0), (0, 0, Disp_Width, Disp_Height))
            if thres == 1:
               crimage.set_alpha(127)
            catSurfaceObj = crimage
            windowSurfaceObj.blit(catSurfaceObj, (0, 0))
         else:
            imagep = pygame.transform.scale(imagep, [int(Disp_Width/2), int(Disp_Height/2)])
            if thres == 1:
               imagep.set_alpha(127)
            catSurfaceObj = imagep
            windowSurfaceObj.blit(catSurfaceObj, (318, 238))

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
      while ltot < int(ttot/2):
         loc = int(acorrect * crop)
         line = sum(mz[loc:loc+crop])
         ltot += line
         acorrect += 1
      acorrect -= (Decimal(int(ltot)) - Decimal(int(ttot))/Decimal(2))/Decimal(int(line))

      bcorrect = 0
      ctot = 0
      while ctot < int(ttot/2):
         col = sum(mz[bcorrect:crop*crop:crop])
         ctot += col
         bcorrect += 1
      bcorrect -= (Decimal(int(ctot)) - Decimal(int(ttot))/Decimal(2))/Decimal(int(col))

      acorrect = 100 * (Decimal(acorrect) - Decimal(crop)/Decimal(2))
      bcorrect = 100 * (Decimal(bcorrect) - Decimal(crop)/Decimal(2))

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
            Cwindow = oCwindow
            if Cwindow:
               mmq, mask, change = MaskChange()
            keys(0,"cen",  fs, 7, b3x, bw, 1, b3y, bh, 3, 0, 1)
            keys(0," tre", fs, 7, b3x, bw, 1, b3y, bh, 3, 2, 1)

      else:
         auto_c = 0
         auto_win = 0
         crop = ocrop
         Cwindow = oCwindow
         if Cwindow:
            mmq, mask, change = MaskChange()
         keys(0,"cen",     fs, 7, b3x, bw, 1, b3y, bh, 3, 0, 1)
         keys(0," tre",    fs, 7, b3x, bw, 1, b3y, bh, 3, 2, 1)

# set auto window
   if auto_win:
      if ttot > 1 and ars[3]< 2 and ars[crop-2] < 2 and art[3] < 2 and art[crop-2] < 2:
         crop -= 2
         crop = max(crop, minwin)
      if ttot > 1 and (ars[2] > 1 or ars[crop-2] > 1 or art[2] > 1 or art[crop-2] > 1):
         crop += 2
         crop = min(crop, maxwin - 2)
         if (Disp_Width/2 + crop/2 + offset3 > Disp_Width) or (Disp_Width/2 + offset3 - crop/2) <= 1 or (Disp_Height/2 + offset4 - crop/2) >= Disp_Height or (Disp_Height/2 - offset4 - crop/2) <= 1:
            crop -= 2
      if ttot == 1 and auto_wlos:
         crop += 2
         crop = min(crop, maxwin - 2)
         if (Disp_Width/2 + offset3 + crop/2) >= Disp_Width:
            crop -= 2
         elif (Disp_Width/2 + offset3 - crop/2) <= 1:
            crop -= 2
         if (Disp_Height/2 + offset4 + crop/2) >= Disp_Height:
            crop -= 2
         elif (Disp_Height/2 + offset4 - crop/2) <= 1:
            crop -= 2
      keys(0,str(crop), fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)
      if Cwindow:
         mmq, mask, change = MaskChange()

   if crop == maxwin:
      acorrect = Decimal(acorrect) * Decimal(h_corr)
      bcorrect = Decimal(bcorrect) * Decimal(w_corr)

   if auto_g and ttot < 6 and cls and ymax == avemax:
      acorrect = avevcor
      bcorrect = avehcor
      auto_win = 1
      change = 1

   if auto_g and ttot < 6 and cls:
      keys(0,"CLS", fs, 2, b2x, bw, 4, b2y, bh, 6, 1, 1)
      keys(0,"C",   fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
   elif auto_g and ttot > 4 and cls:
      keys(0,"CLS", fs, 1, b2x, bw, 4, b2y, bh, 6, 1, 1)
      keys(0,"C",   fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)

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
            keys(0,"CLS", fs, 1, b2x, bw, 4, b2y, bh, 6, 1, 1)
            keys(0,"C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
         elif cls and zcount < avemax:
            keys(0,"CLS", fs, 2, b2x, bw, 4, b2y, bh, 6, 1, 1)
            keys(0,"C", fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
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
         # switch ON / OFF appropriate output relays
         if vdir == "n" and vcor > 0 and decN:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
         if hdir == "e" and hcor > 0:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
            keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
         if vdir == "s" and vcor > 0 and decS == 1:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
            keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
         if hdir == "w" and hcor > 0:
            if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
               DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
         # send serial output to Arduino if enabled
         if serial_connected:
            if decN and vdir == "n":
               ser.write(bytes(Vcorrt.encode('ascii')))
            if decS and vdir == "s":
               ser.write(bytes(Vcorrt.encode('ascii')))
            time.sleep(0.2)
            ser.write(bytes(Hcorrt.encode('ascii')))
            time.sleep(0.2)
         # add to log if enabled
         if log:
            now = datetime.datetime.now()
            timestamp = now.strftime("%y/%m/%d-%H:%M:%S")
            timp = str(timestamp) + "," + Vcorrt + "," + Hcorrt + "," + str(acorrect) + "," + str(bcorrect) + "," + str(ttot)
            if ttot == 1:
               timp = timp + ", No Star "
            timp = timp + "\n"
            with open(logfile, "a") as file:
               file.write(timp)
         if not camera_connected:
            posx -= bcorrect/100
            posy -= acorrect/100
      # auto_interval
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
         keys(0,str(int(Interval)), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
      else:
         Interval = Intervals

# Display
   #display plot if enabled
   if plot > 0:
      if (Display == 0 and menu ==0) or Display > 1:
         poxd = Disp_Width - 105
         poyd = 20
      else:
         poxd = Disp_Width + 18
         poyd = 10
      povd = 50
      pold = 256
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(poxd-1, poyd-1, 52, 258), 1)
      limg += 1
      if limg == 1:
         rimg = blankline[0:3]
      val2 = int(povd/2)
      val3 = int(povd/2)
      if acorrect >= 0:
         val2 = int(povd/2) + int((math.sqrt(acorrect))/6)
      else:
         val2 = int(povd/2) - int((math.sqrt(-acorrect))/6)
      if val2 > povd-1:
         val2 = povd-1
      if val2 < 0:
         val2 = 0
      if bcorrect >= 0:
         val3 = int(povd/2) + int((math.sqrt(bcorrect))/6)
      else:
         val3 = int(povd/2) - int((math.sqrt(-bcorrect))/6)
      if val3 > povd-1:
         val3 = povd-1
      if val3 < 0 :
         val3 = 0
      if val2 < val3:
         if limg == 1:
            rimg += blankline[3:int((val2)*3)]
         else:
            if ttot > 1:
               rimg += blankline[0:int((val2)*3)]
            else:
               rimg += purline[0:9]
               rimg += blankline[9:int((val2)*3)]
         rimg += red 
         rimg += blankline[int(val2*3):int(val3*3)-3]
         rimg += grn 
         rimg += blankline[int(val3*3):int(povd*3)-3]
      elif val3 < val2:
         if limg == 1:
            rimg += blankline[3:int((val3)*3)]
         else:
            if ttot > 1:
               rimg += blankline[0:int((val3)*3)]
            else:
               rimg += purline[0:9]
               rimg += blankline[9:int((val3)*3)]
         rimg += grn 
         rimg += blankline[int(val3*3):int(val2*3)-3]
         rimg += red 
         rimg += blankline[int(val2*3):int(povd*3)-3]
      else:
         if limg == 1:
            rimg += blankline[3:int((val3)*3)]
         else:
            if ttot > 1:
               rimg += blankline[0:int((val3)*3)]
            else:
               rimg += purline[0:9]
               rimg += blankline[9:int((val3)*3)]
         rimg += yel 
         rimg += blankline[int(val3*3):int(povd*3)-3]
         
      if limg > pold:
         yt = int((limg - pold)*povd*3)
         yu = int(limg*povd*3)
         rimg = rimg[yt:yu]
         limg = pold
      
      if sys.version_info[0] == 3:
         pimg = bytes(rimg,'ascii')
      else:
         pimg = rimg
      if len(pimg) > (povd*limg*3):
         pimg = pimg[0:povd*limg*3]
      imageg = pygame.image.fromstring(pimg, (povd, limg), "RGB", 1)
      if plot == 1:
         imageg.set_alpha(127)
      windowSurfaceObj.blit(imageg, (poxd, poyd))
      if graph == 0  and menu == 1 :
         pygame.display.update(bw*12, 9, 800-(bw*12),461)

   w2 = Disp_Width/2 + offset3
   h2 = Disp_Height/2 + offset4
   c1 = crop/2
   c2 = crop/2

   #display graph if enabled
   if graph > 0:
      if (Display == 0 and menu == 0) or Display > 1:
         pox = Disp_Width - 52
         poy = 20
      else:
         pox = Disp_Width + 70
         poy = 10
      pov = 50
      pygame.draw.rect(windowSurfaceObj, greyColor, Rect(pox-1, poy-1, 52, 258), 1)
      img = ""
      for count in range (0, 256):
         if hist == 2 and count != maxtot and count != mintot and count != upnoi and count != pcont:
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
         if hist != 2 and count != maxtot and count != noitot and count != pcont:
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
         if count == maxtot:
            img += greline[0:pov*3]
         if hist == 2:
            if count == mintot:
               img += purline[0:pov*3]
         else:
            if count == noitot:
               img += cynline[0:pov*3]
         if hist == 2:
            if count == upnoi:
               img += purline[0:pov*3]
         if count == int(pcont):
            img += redline[0:pov*3]
         elif count == int(noitot + a_thr_limit) and esc1 > 0 and auto_t == 1 and hist != 2:
            img += yelline[0:pov*3]
         elif count == int(noitot + m_thr_limit) and esc1 > 0 and auto_t == 0 and hist != 2:
            img += yelline[0:pov*3]
         elif count == int(upnoi + a_thr_limit) and esc1 > 0 and auto_t == 1 and hist == 2:
            img += yelline[0:pov*3]
         elif count == int(upnoi + m_thr_limit) and esc1 > 0 and auto_t == 0 and hist == 2:
            img += yelline[0:pov*3]

      if len(img) > (pov*256*3):
         img = img[0:pov*256*3]
      if sys.version_info[0] == 3:
         img = bytes(img,'ascii')
      imageg = pygame.image.fromstring(img, (pov, 256), "RGB", 1)
      if graph == 1:
         imageg.set_alpha(127)
      windowSurfaceObj.blit(imageg, (pox, poy))
      if menu == 1:
         pygame.display.update(bw*12, 9, 800-(bw*12),470)
         
   if not auto_g:
      if menu == 0:
         pygame.draw.line(windowSurfaceObj, purpleColor, (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) + 5)))
         pygame.draw.line(windowSurfaceObj, purpleColor, (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) + 5)))
      else:
         pygame.draw.line(windowSurfaceObj, purpleColor, (int(318+(int(w2) + int(bcorrect)/int(100) - 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) + 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))
         pygame.draw.line(windowSurfaceObj, purpleColor, (int(318+(int(w2) + int(bcorrect)/int(100) + 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) - 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))
   else:
      if ttot > 1:
         if menu == 0:
            pygame.draw.line(windowSurfaceObj, greenColor, (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) + 5)))
            pygame.draw.line(windowSurfaceObj, greenColor, (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) + 5)))
         else:
            pygame.draw.line(windowSurfaceObj, greenColor, (int(318+(int(w2) + int(bcorrect)/int(100) - 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) + 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))
            pygame.draw.line(windowSurfaceObj, greenColor, (int(318+(int(w2) + int(bcorrect)/int(100) + 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) - 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))
      else:
         if menu == 0:
            pygame.draw.line(windowSurfaceObj, yellowColor, (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) + 5)))
            pygame.draw.line(windowSurfaceObj, yellowColor, (int(int(w2) + int(bcorrect)/int(100) + 5), int(int(h2) - int(acorrect)/int(100) - 5)), (int(int(w2) + int(bcorrect)/int(100) - 5), int(int(h2) - int(acorrect)/int(100) + 5)))
         else:
            pygame.draw.line(windowSurfaceObj, yellowColor, (int(318+(int(w2) + int(bcorrect)/int(100) - 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) + 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))
            pygame.draw.line(windowSurfaceObj, yellowColor, (int(318+(int(w2) + int(bcorrect)/int(100) + 5)/int(2)),int(238 + (int(h2) - int(acorrect)/int(100) - 5)/int(2))), (int(318 + (int(w2) + int(bcorrect)/int(100) - 5)/int(2)), int(238 + int(int(h2) - int(acorrect)/int(100) + 5)/int(2))))

   if not fc or use_Pi_Cam or not camera_connected or thres:
      if maxwin != crop:
         if menu == 0:
            if not Cwindow:
               pygame.draw.rect(windowSurfaceObj, bredColor, Rect(w2 - c1, h2 - c2, crop, crop), 1)
               #pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(minc+2),1)
            else:
               pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(crop/2)+1,1)
               #pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(minc+2),1)
               if calibrate == 1:
                  pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(crop/2.667)+1,1)
                  pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(crop/4)+1,1)
                  pygame.draw.circle(windowSurfaceObj, bredColor, (int((w2-c1)+int(crop/2)),int((h2-c2)+int(crop/2))), int(crop/8)+1,1)
         else:
            if not Cwindow:            
               pygame.draw.rect(windowSurfaceObj, bredColor, Rect(318 + ((w2 - c1)/2), 238 + ((h2 - c2)/2), crop/2, crop/2), 1)
            else:
               pygame.draw.circle(windowSurfaceObj, bredColor, (318 + int((w2-c1)/2) + int(crop/4), 239 + int((h2-c2)/2) + int(crop/4)), int(crop/4)+1,1)
         
      if menu == 0:
         pygame.draw.line(windowSurfaceObj,    bredColor, (w2 - 4, h2),     (w2 + 4, h2))
         pygame.draw.line(windowSurfaceObj,    bredColor, (w2,     h2 - 4), (w2,     h2 + 4))
         if calibrate == 1:
            if cal_count > (samples *3) + 6:
               pygame.draw.line(windowSurfaceObj,yellowColor,(w2, h2),(w2 + (crop/2 + 5), h2))
               pygame.draw.line(windowSurfaceObj,bredColor,  (w2 - (crop/2 + 5), h2),(w2 , h2))
               pygame.draw.line(windowSurfaceObj,bredColor,  (w2,h2 - (crop/2 + 5)), (w2,h2 + (crop/2 + 5)))
            else:
               pygame.draw.line(windowSurfaceObj,bredColor,   (w2 - (crop/2 + 5), h2),(w2 + (crop/2 + 5), h2))
               pygame.draw.line(windowSurfaceObj,yellowColor, (w2,h2 - (crop/2 + 5)), (w2,h2))
               pygame.draw.line(windowSurfaceObj,bredColor,   (w2,h2), (w2,h2 + (crop/2 + 5)))

            pygame.draw.line(windowSurfaceObj,bredColor, (w2 - (crop/3 + 5),h2 - (crop/3 + 5)), (w2 + (crop/3 + 5),h2 + (crop/3 + 5)))
            pygame.draw.line(windowSurfaceObj,bredColor, (w2 + (crop/3 + 5),h2 - (crop/3 + 5)), (w2 - (crop/3 + 5),h2 + (crop/3 + 5)))
            if cal_count == samples + 5 or cal_count == (samples * 4)+ 10:
               pygame.draw.line(windowSurfaceObj,purpleColor,(w2 + int(obcorrect/100), h2  - int (oacorrect/100)),(w2 + int(bcorrect/100), h2 - int (acorrect/100)),2)

      else:
         pygame.draw.rect(windowSurfaceObj,bredColor, Rect(318+((w2 - c1)/2) + (crop/4) - 1, 238+((h2 - c2)/2) + (crop/4) - 1, 2, 2), 1)
            
      if not auto_g:
         if DKeys == 1:
            if menu == 0:
               keys(0,Vcorrt,    16, 9,          0, 0, 0, 0, 0, 0, 0, 0)
               keys(0,Hcorrt,    16, 9, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
               if show_time == 1 and menu == 0:
                  now = datetime.datetime.now()
                  timestamp = now.strftime("%H:%M:%S")
                  keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)
                    
            else:
               pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
               keys(0,Vcorrt,    16, 9, 630, 0, 0, 450, 0, 0, 0, 0)
               keys(0,Hcorrt,    16, 9, 715, 0, 0, 450, 0, 0, 0, 0)
               pygame.display.update(625,450, 175,50)
         else:
            if Vcorrt[3:4] == "n":
               vdr = "+"
            else:
               vdr = "-"
            if menu == 0:
               keys(0,"Dec" + vdr + Vcorrt[4:9],    16, 9,          0, 0, 0, 0, 0, 0, 0, 0)
               if show_time == 1 and menu == 0:
                  now = datetime.datetime.now()
                  timestamp = now.strftime("%H:%M:%S")
                  keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)

            else:
               pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
               keys(0,"Dec" + vdr + Vcorrt[4:9], 16, 9, 630, 1, 1, 450, 1, 1, 1, 1)
               
            if Hcorrt[3:4] == "e":
               hdr = "+"
            else:
               hdr = "-"
            if menu == 0:
               keys(0," RA" + hdr + Hcorrt[4:9],    16, 9, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
            else:
               keys(0," RA" + hdr + Hcorrt[4:9],    16, 9, 715, 0, 0, 450, 0, 0, 0, 0)
               pygame.display.update(625,450, 800,500)
            
      else:
         if ttot > 1:
            if DKeys == 1:
               if menu == 0:
                  keys(0,Vcorrt,    16, 1,          0, 0, 0, 0, 0, 0, 0, 0)
                  keys(0,Hcorrt,    16, 1, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
                  if show_time == 1 and menu == 0:
                     now = datetime.datetime.now()
                     timestamp = now.strftime("%H:%M:%S")
                     keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)
               else:
                  pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
                  keys(0,Vcorrt,    16, 1, 630, 0, 0, 450, 0, 0, 0, 0)
                  keys(0,Hcorrt,    16, 1, 715, 0, 0, 450, 0, 0, 0, 0)
                  pygame.display.update(625,450, 800,500)
            else:
               if Vcorrt[3:4] == "n":
                  vdr = "+"
               else:
                  vdr = "-"
               if menu == 0:
                  keys(0,"Dec" + vdr + Vcorrt[4:9],    16, 1,          0, 0, 0, 0, 0, 0, 0, 0)
                  if show_time == 1 and menu == 0:
                     now = datetime.datetime.now()
                     timestamp = now.strftime("%H:%M:%S")
                     keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)
               else:
                  pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
                  keys(0,"Dec" + vdr + Vcorrt[4:9], 16, 1, 630, 1, 1, 450, 1, 1, 1, 1)
               
               if Hcorrt[3:4] == "e":
                  hdr = "+"
               else:
                  hdr = "-"
               if menu == 0:
                  keys(0," RA" + hdr + Hcorrt[4:9],    16, 1, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
               else:
                  keys(0," RA" + hdr + Hcorrt[4:9],    16, 1, 715, 0, 0, 450, 0, 0, 0, 0)
                  pygame.display.update(625,450, 800,500)
               
            
         else:
            if DKeys == 1:
               if menu == 0:
                  keys(0,Vcorrt,    16, 2,          0, 0, 0, 0, 0, 0, 0, 0)
                  keys(0,Hcorrt,    16, 2, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
                  if show_time == 1 and menu == 0:
                     now = datetime.datetime.now()
                     timestamp = now.strftime("%H:%M:%S")
                     keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)
               else:
                  pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
                  keys(0,Vcorrt,    16, 2, 630, 0, 0, 450, 0, 0, 0, 0)
                  keys(0,Hcorrt,    16, 2, 715, 0, 0, 450, 0, 0, 0, 0)
                  pygame.display.update(625,450, 800,500)
            else:
               if Vcorrt[3:4] == "n":
                  vdr = "+"
               else:
                  vdr = "-"
               if menu == 0:
                  keys(0,"Dec" + vdr + Vcorrt[4:9],    16, 2,          0, 0, 0, 0, 0, 0, 0, 0)
                  if show_time == 1 and menu == 0:
                     now = datetime.datetime.now()
                     timestamp = now.strftime("%H:%M:%S")
                     keys(0,timestamp, 16, 7, int(Disp_Width/2 - Disp_Width/30), 0, 0, 0, 0, 0, 0, 0)
               else:
                  pygame.draw.rect(windowSurfaceObj, blackColor, Rect(625, 450, 710, 500), 0)
                  keys(0,"Dec" + vdr + Vcorrt[4:9], 16, 2, 630, 1, 1, 450, 1, 1, 1, 1)
               
               if Hcorrt[3:4] == "e":
                  hdr = "+"
               else:
                  hdr = "-"
               if menu == 0:
                  keys(0," RA" + hdr + Hcorrt[4:9],    16, 2, Disp_Width - 80, 0, 0, 0, 0, 0, 0, 0)
               else:
                  keys(0," RA" + hdr + Hcorrt[4:9],    16, 2, 715, 0, 0, 450, 0, 0, 0, 0)
                  pygame.display.update(625,450, 800,500)
            
   if Display == 1:
      pygame.display.update(0, 0, Disp_Width + 150, height)
   else:
      if menu == 0:
         pygame.display.update(0, 0, Disp_Width, height)
      else:
         pygame.display.update(318, 238, Disp_Width/2,240)
         
   if esc1 > 0 and time.time() - esctimer > 2:
      esc1 = 2
      keys(0,"Esc",fs,2,b3x,bw,2,b3y, bh, 2, 2, 1)

   # calibrate DEC

   if calibrate and cal_count == 0:
      newscale = nscale
      oauto_g = auto_g
      auto_g = 0
      oauto_win = auto_win
      auto_win = 0
      oauto_t = auto_t
      auto_t = 1
      if auto_rotate == 1:
         Cang = 0
         Aang = 0
      ocrop = crop
      crop = maxwin - 2
      if Cwindow == 1:
         mmq, mask, change = MaskChange()
      cal_count +=1
      
   elif calibrate and cal_count < samples + 1:
      if samples > 0:
         cal_count +=1
      
   elif calibrate and cal_count == samples + 1:
      offset3 = offset3 + int(bcorrect/100)
      offset4 = offset4 - int(acorrect/100)
      cal_count +=1
      
   elif calibrate and (cal_count == samples + 2 or cal_count == samples + 3)  :
      if ttot < 6:
         calibrate = 0
         cal_count = -1
         crop = ocrop
         auto_g = oauto_g
         auto_win = oauto_win
         auto_t = oauto_t
         if Cwindow == 1:
            mmq, mask, change = MaskChange()
         keys(0,"TELESCOPE",fs,1,b3x+bw/5,bw,0,b3y-2, bh, 5, 0, 1)
         esc1 = 0
         keys(0,"Esc",fs,5,b3x,bw,2,b3y, bh, 2, 2, 0)
         keys(0,"cen",fs,7,b3x,bw,1,b3y, bh, 3, 0, 0)
         keys(0," tre",fs,7,b3x,bw,1,b3y, bh, 3, 2, 0)
         keys(0,"scale all",             fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
         keys(0,str(int(Cang)),          fs,   7,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
         if use_Pi_Cam and camera_connected:
            keys(0,"ISO",                   fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
            keys(0,str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
            if not rpiISO:
               keys(0,'auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         if not use_Pi_Cam and camera_connected:
            button(b2x, 1, b2y, 6, bw, 2, bh, 0,1)
            if Webcam == 0:
               keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
               keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
            elif  Webcam == 1:
               keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
               keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
            elif  Webcam > 1:
               keys(0,"  eV",               fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
               keys(0,str(rpiev),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         pygame.draw.rect(windowSurfaceObj, redColor, Rect(b3x+(bw / 1.8),b3y + bh*4.45, bw*2 - 8, bh/3.6))
         keys(0,"NO STAR",fs-2, 2,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
         no_star = 1
         pygame.display.update()
         change = 1
         
      if calibrate and cal_count == samples + 2:
         keys(0,str(int(threshold)),fs,3,b1x,bw,5,b1y, bh, 4, 3, 1)
         zt = 0
         scale_t = 1
         while zt <= zoom:
            scale_t *= rpiscalex[zt]
            zt += 1
         cal_time = int((calibrate_time * 1000) / scale_t)
         tim = int(cal_time/5)
         pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.4, bw*2 - 8, bh/3))
         pygame.display.update()
      if calibrate and cal_count == samples + 3:
         tim = cal_time
         oacorrect = acorrect
         obcorrect = bcorrect
      if calibrate and serial_connected:
         blan = "0000" + str(int(tim))
         if nsi == 0:
            move = ':Mgs' + blan[(len(blan))-4:len(blan)]
            button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
            keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
            lx200(move, ':Mgw0000', decN, decS)
            time.sleep((tim/1000))
            button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
            keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
         else:
            move = ':Mgn' + blan[(len(blan))-4:len(blan)]
            button(b3x, 2, b3y, 2, bw, 1, bh, 1)
            keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            lx200(move, ':Mgw0000', decN, decS)
            time.sleep((tim/1000))
            button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
            keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
      if calibrate and (use_RPiGPIO or use_Seeed or use_PiFaceRP):
         if nsi == 0:
            button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
            keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posy -=(tim/100)
               posx -= (tim/1000)
            time.sleep(tim/1000)
            button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
            keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         else:
            button(b3x, 2, b3y, 2, bw, 1, bh, 1,0)
            keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posy +=(tim/100)
               posx += (tim/1000)
            time.sleep(tim/1000)
            button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
            keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
        
      change = 1
      cal_count +=1
      time.sleep((1))
      
   elif calibrate and cal_count < (samples * 2) + 4:
      if samples > 0:
         cal_count +=1
         
      
   elif calibrate and cal_count == (samples * 2)  + 4:
      ccorrect = acorrect - oacorrect
      dcorrect = bcorrect - obcorrect
      if (abs(ccorrect)) > move_limit or (abs(dcorrect)) > move_limit:
         if dcorrect == 0:
            dcorrect = 0.01
         Dang = math.degrees(math.atan(ccorrect / dcorrect))
         if ccorrect >= 0 and dcorrect >= 0:
            Dang = int(90 - Dang)
         if ccorrect < 0 and dcorrect >= 0:
            Dang = int(90 + (0-Dang))
         if ccorrect < 0 and dcorrect < 0:
            Dang = int(0 - (90 + Dang))
         if ccorrect >= 0 and dcorrect < 0:
            Dang = int(0 - (90 + Dang))
         keys(0,str(Dang),fs-2, 2,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
         newscale = int(tim/(math.sqrt(((ccorrect/100)*(ccorrect/100))+((dcorrect/100)*(dcorrect/100)))))
         if newscale < 0:
            newscale = 0 - newscale
      else:
         pygame.draw.rect(windowSurfaceObj, redColor, Rect(b3x+(bw / 1.8),b3y + bh*4.45, bw*2 - 8, bh/3.6))
         keys(0,"NO MOVE",fs-2, 2,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
         no_move = 1
         pygame.display.update()
         
      cal_count +=1
      change = 1
      
   elif calibrate and (cal_count == (samples * 2) + 5 or cal_count == (samples * 2) + 6):
      if cal_count == (samples * 2) + 5:
         tim = int(cal_time/5)
      else:
         tim = cal_time
      if serial_connected:
         if nsi == 0:
            blan = "0000" + str(int(tim))
            move = ':Mgn' + blan[(len(blan))-4:len(blan)]
            button(b3x, 2, b3y, 2, bw, 1, bh, 1,0)
            keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            lx200(move, ':Mgw0000', decN, decS)
            time.sleep((tim/1000))
            button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
            keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
         else:
            blan = "0000" + str(int(tim))
            move = ':Mgs' + blan[(len(blan))-4:len(blan)]
            button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
            keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
            lx200(move, ':Mgw0000', decN, decS)
            time.sleep((tim/1000))
            button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
            keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
            
      if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
         if nsi == 0:
            button(b3x, 2, b3y, 2, bw, 1, bh, 1,0)
            keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posy +=(tim/100)
            time.sleep(tim/1000)
            button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
            keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         else:
            button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
            keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posy -=(tim/100)
            time.sleep(tim/1000)
            button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
            keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            
      cal_count +=1
      
      
   # calibrate RA

   elif (calibrate and cal_count > ((samples *2) + 6) and cal_count <  (samples * 3) + 7) or (calibrate and nr == 0 and cal_count == (samples *3) + 6):
      if samples > 0:
         cal_count +=1

   elif calibrate and cal_count == (samples * 3) + 7:
      offset3 = offset3 + int(bcorrect/100)
      offset4 = offset4 - int(acorrect/100)
      cal_count +=1
      
   elif calibrate and (cal_count == (samples *3) + 8 or cal_count == (samples *3) + 9):
      keys(0," CALIB  RA",fs,3,b3x+bw/5,bw,0,b3y-2,bh, 5, 0, 1)
      if ttot < 6:
         calibrate = 0
         cal_count = -1
         crop = ocrop
         auto_g = oauto_g
         auto_win = oauto_win
         auto_t = oauto_t
         if Cwindow == 1:
            mmq, mask, change = MaskChange()
         keys(0,"TELESCOPE",fs,1,b3x+bw/5,bw,0,b3y-2, bh, 5, 0, 1)
         esc1 = 0
         keys(0,"Esc",fs,5,b3x,bw,2,b3y, bh, 2, 2, 0)
         keys(0,"cen",fs,7,b3x,bw,1,b3y, bh, 3, 0, 0)
         keys(0," tre",fs,7,b3x,bw,1,b3y, bh, 3, 2, 0)
         keys(0,"scale all",             fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
         keys(0,str(int(Cang)),          fs,   7,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
         if use_Pi_Cam and camera_connected:
            keys(0,"ISO",                   fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
            keys(0,str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
            if not rpiISO:
               keys(0,'auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         if not use_Pi_Cam and camera_connected:
            button(b2x, 1, b2y, 6, bw, 2, bh, 0,0)
            if Webcam == 0:
               keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
               keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
            elif Webcam == 1:
               keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
               keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
            elif Webcam  > 1:
               keys(0,"  eV",               fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
               keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
               keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
               keys(0,str(rpiev),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         pygame.draw.rect(windowSurfaceObj, yellowColor, Rect(b3x+(bw / 1.8),b3y + bh*4.45, bw*2 - 8, bh/3.6))
         keys(0,"NO STAR",fs-2, 3,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
         no_star = 1
         pygame.display.update()
         change = 1
         
      if cal_count == (samples * 3) + 8:
         tim = int(cal_time/20)
      if cal_count == (samples * 3) + 9:
         tim = cal_time
         oacorrect = acorrect
         obcorrect = bcorrect
      if calibrate and serial_connected:
         if ewi == 0:
            blan = "0000" + str(int(tim))
            move = ':Mgw' + blan[(len(blan))-4:len(blan)]
            button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            lx200(move, ':Mgs0000', decN, decS)
            time.sleep(tim/1000)
            button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
         else:
            blan = "0000" + str(int(tim))
            move = ':Mge' + blan[(len(blan))-4:len(blan)]
            button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
            lx200(move, ':Mgs0000', decN, decS)
            time.sleep((tim/1000))
            button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
            
      if calibrate and (use_RPiGPIO or use_Seeed or use_PiFaceRP):
         if ewi == 0:
            button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posx +=(tim/100)
               posy += (tim/1000)
            time.sleep(tim/1000)
            button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         else:
            button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posx -=(tim/100)
               posy -= (tim/1000)
            time.sleep(tim/1000)
            button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            
      change = 1
      cal_count +=1
      time.sleep((1))
   elif calibrate and cal_count > ((samples * 3)  + 9) and cal_count <  (samples * 4) + 10 or (calibrate and nr == 0 and cal_count == (samples *3) + 9):
      if samples > 0:
         cal_count +=1

      
   elif calibrate and cal_count == (samples * 4) + 10:
      ccorrect = acorrect - oacorrect
      dcorrect = bcorrect - obcorrect
      if (abs(ccorrect)) > move_limit or (abs(dcorrect)) > move_limit:
         if dcorrect == 0:
            dcorrect = 0.01
         Rang = math.degrees(math.atan(ccorrect / dcorrect))
         if ccorrect >= 0 and dcorrect >= 0:
            Rang = int(90 - Rang)
         if ccorrect < 0 and dcorrect >= 0:
            Rang = int(90 + (0-Rang))
         if ccorrect < 0 and dcorrect < 0:
            Rang = int(0 - (90 + Rang))
         if ccorrect >= 0 and dcorrect < 0:
            Rang = int(0 - (90 + Rang))
         Rang = Rang - 90
         if Rang < -180:
            Rang = Rang + 360
         pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.4, bw*2 - 8, bh/3))
         pygame.display.update()
         keys(0,str(Rang),fs-2, 3,b3x+(bw * 1.5),bw,0,b3y, bh, 5, 2, 2)
      
         if abs(Dang) > 90 and abs(Rang) < 90 :
            nsi += 1
            if nsi > 1:
               nsi = 0
            if Dang > 100:
               Dang = 180 - Dang
            if Dang < -100:
               Dang = -180 - Dang
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.4, bw*1 - 8, bh/3))
            pygame.display.update()
            keys(0,str(Dang),fs-2, 2,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
            
         if abs(Rang) > 90 and abs(Dang) < 90 :
            ewi +=1
            if ewi > 1:
               ewi = 0
            if Rang > 100:
               Rang = 180 - Rang
            if Rang < -100:
               Rang = -180 - Rang
               
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw * 1.5),b3y + bh*4.4, bw*1 - 8, bh/3))
            pygame.display.update()
            keys(0,str(Rang),fs-2, 3,b3x+(bw * 1.5),bw,0,b3y, bh, 5, 2, 2)
            
         if abs(Rang) > 90 and abs(Dang) > 90 :
            ewi +=1
            if ewi > 1:
               ewi = 0
            nsi +=1
            if nsi > 1:
               nsi = 0
            if Rang > 100:
               Rang = 180 - Rang
            if Rang < -100:
               Rang = -180 - Rang
            if Dang > 100:
               Dang = 180 - Dang
            if Dang < -100:
               Dang = -180 - Dang
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.4, bw*2 - 8, bh/3))
            pygame.display.update()
            keys(0,str(Dang),fs-2, 2,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
            keys(0,str(Rang),fs-2, 3,b3x+(bw * 1.5),bw,0,b3y, bh, 5, 2, 2)
            
         if abs(Dang - Rang) < 1000:
            time.sleep(1)
            Aang = int((Dang + Rang)/2)
            pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.4, bw*2 - 8, bh/3))
            pygame.display.update()
            keys(0,str(Aang),fs-2, 9,b3x+(bw),bw,0,b3y, bh, 5, 2, 2)
            
         wscale = int(tim/(math.sqrt(((ccorrect/100)*(ccorrect/100))+((dcorrect/100)*(dcorrect/100)))))
         if wscale < 0:
            wscale = 0 - wscale
         wscale = int(wscale / 2)
         newscale = int(newscale / 2)
         escale = wscale
         nscale = newscale
         sscale = nscale
         
      else:
         pygame.draw.rect(windowSurfaceObj, yellowColor, Rect(b3x+(bw / 1.8),b3y + bh*4.45, bw*2 - 8, bh/3.6))
         keys(0,"NO MOVE",fs-2, 3,b3x+(bw / 1.8),bw,0,b3y, bh, 5, 2, 2)
         no_move = 1
         pygame.display.update()
      crop = ocrop
      auto_g = oauto_g
      auto_win = oauto_win
      auto_t = oauto_t
      if Cwindow:
         mmq, mask, change = MaskChange()
      change = 1
      calibrate = 0
      if serial_connected:
         if ewi == 0:
            blan = "0000" + str(int(tim * 1.2))
            move = ':Mge' + blan[(len(blan))-4:len(blan)]
            button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
            lx200(move, ':Mgs0000', decN, decS)
            time.sleep((tim * 1.2)/1000)
            button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
         else:
            blan = "0000" + str(int(tim * 1.2))
            move = ':Mgw' + blan[(len(blan))-4:len(blan)]
            button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            lx200(move, ':Mgs0000', decN, decS)
            time.sleep((tim * 1.2)/1000)
            button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
      if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
         if ewi == 0:
            button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posx -=(tim/100)
            time.sleep((tim * 1.2) /1000)
            button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
         else:
            button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
            keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            if camera_connected == 0:
               posx -=(tim/100)
            time.sleep((tim * 1.2) /1000)
            button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
            keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
            DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
            
      keys(0,"TELESCOPE",fs,1,b3x+bw/5,bw,0,b3y-2, bh, 5, 0, 1)
      esc1 = 0
      keys(0,"Esc",fs,5,b3x,bw,2,b3y, bh, 2, 2, 0)
      keys(0,"cen",fs,7,b3x,bw,1,b3y, bh, 3, 0, 0)
      keys(0," tre",fs,7,b3x,bw,1,b3y, bh, 3, 2, 0)
      if auto_rotate == 0:
         keys(0,"scale all",             fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
         keys(0,str(int(Cang)),          fs,   7,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
      if use_Pi_Cam and camera_connected:
         keys(0,"ISO",                   fs,   6,        b2x,         bw  , 0,     b2y, bh, 6, 0, 1)
         keys(0,str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         if not rpiISO:
            keys(0,'auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
      if not use_Pi_Cam and camera_connected:
         button(b2x, 1, b2y, 6, bw, 2, bh, 0,1)
         if Webcam == 0:
            keys(0,"Gamma",              fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
            keys(0," -",                 fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
            keys(0,"+",                  fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
            keys(0,str(gamma),           fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         elif Webcam == 1:
            keys(0,"Sharpness",          fs-1, 6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
            keys(0," -",                 fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
            keys(0,"+",                  fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
            keys(0,str(sharpness),       fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         elif Webcam > 1:
            keys(0,"  eV",               fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
            keys(0," -",                 fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
            keys(0,"+",                  fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
            keys(0,str(rpiev),           fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
      change = 1
      cal_count = 0

   if calibrate and (no_star or no_move):
      no_star = 0
      no_move = 0
      time.sleep(2)
      pygame.draw.rect(windowSurfaceObj, blackColor, Rect(b3x+(bw / 1.8),b3y + bh*4.45, bw*2 - 8, bh/3.6))
      change = 1
      pygame.display.update()

      
# read mouse or Keyboard

   buttonx = pygame.mouse.get_pressed()
   
   # change window by holding left hand mouse button and moving cursor
   if buttonx[mouse_button] != 0 and menu == 0 and store == 0 and not calibrate:
      pos = pygame.mouse.get_pos()
      xouse = pos[0]
      youse = pos[1]
      if xouse < Disp_Width and youse < Disp_Height:
         if graph == 0 or (graph > 0 and (xouse < pox or youse > poy + 258)):
            store = 1
   elif buttonx[mouse_button] != 0  and menu == 0 and store > 0:
      pos = pygame.mouse.get_pos()
      mousexx = pos[0]
      mouseyy = pos[1]
      rad = int(math.sqrt((mousexx - xouse) * (mousexx - xouse) +(mouseyy - youse) * (mouseyy - youse)))
      rad = max(rad, int(minwin/2))
      rad = min(rad, int((maxwin-4)/2))
      if (xouse + rad) > Disp_Width:
         rad = Disp_Width - xouse
      if (xouse - rad) < 0:
         rad = xouse
      if (youse + rad) > Disp_Height:
         rad = Disp_Height - youse
      if (youse - rad) < 0:
         rad = youse
      pygame.draw.circle(windowSurfaceObj, bredColor, (xouse,youse), 2,1)
      pygame.draw.circle(windowSurfaceObj, bredColor, (xouse,youse), rad,1)
      pygame.display.update()
      store = 2
         
   # increment parameters by holding left hand mouse button
   if buttonx[0] != 0 or mousepress == 1 and store == 0 and calibrate == 0:
      press = 1
      mousepress = 0
      pos = pygame.mouse.get_pos()
      mousex = pos[0]
      mousey = pos[1]
      if Display == 1:
         x = int(mousex/bw)
         if mousey > Disp_Height:
            y = int((mousey-Disp_Height)/bh)
            z = (10*x) + (y)
      else:
         if menu == 0 and mousex > Disp_Width:
            if mousey < bh * 5:
               x = int((mousex - Disp_Width)/bw)
               y = int(mousey/bh) + 1
               z = 10*x + y
            if mousey > bh*5 and mousey < bh*10:
               x = int((mousex - Disp_Width)/bw) + 6
               y = int((mousey - 5*bh)/bh) + 1
               z = 10*x + y
            if mousey > bh*10:
               x = int((mousex - Disp_Width)/bw) + 12
               y = int((mousey - 10*bh)/bh) + 1
               z = 10*x + y
         if menu == 1:
            if mousey < bh * 5 and mousex < bw * 6:
               x = int((mousex)/bw)
               y = int(mousey/bh) + 1
               z = 10*x + y
            if mousey > bh*5 and mousey < bh*10 and mousex < bw * 6:
               x = int((mousex)/bw) + 6
               y = int((mousey - 5*bh)/bh) + 1
               z = 10*x + y
            if mousey < bh*5 and mousex > bw*6:
               x = int((mousex)/bw) + 6
               y = int((mousey)/bh) + 1
               z = 10*x + y
               
      if z == 161  and zoom > Image_window:
         if use_Pi_Cam and camera_connected:
            os.killpg(p.pid, signal.SIGTERM)
            restart = 1
         offset6 -= 5 * (math.cos((0-Cang) * (3.14159/180)))
         offset5 -= 5 * (math.sin((0-Cang) * (3.14159/180)))
         if (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2) or (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
            offset5 += 5 * (math.sin((0-Cang) * (3.14159/180)))
            offset6 += 5 * (math.cos((0-Cang) * (3.14159/180)))
      elif z == 172 and zoom > Image_window:
         if use_Pi_Cam and camera_connected:
            os.killpg(p.pid, signal.SIGTERM)
            restart = 1
         offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
         offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
         if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
            offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
            offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
      elif z == 152 and zoom > Image_window:
         if use_Pi_Cam and camera_connected:
            os.killpg(p.pid, signal.SIGTERM)
            restart = 1
         offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
         offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
         if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
            offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
            offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
      elif z == 163 and zoom > Image_window:
         if use_Pi_Cam and camera_connected:
            os.killpg(p.pid, signal.SIGTERM)
            restart = 1
         offset6 += 5 * (math.cos((0-Cang) * (3.14159/180)))
         offset5 += 5 * (math.sin((0-Cang) * (3.14159/180)))
         if (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2) or (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
            offset5 -= 5 * (math.sin((0-Cang) * (3.14159/180)))
            offset6 -= 5 * (math.cos((0-Cang) * (3.14159/180)))
      elif z == 4:
         if (use_Pi_Cam or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1))) and camera_connected:
            if Webcam > 1:
               rpired -=20
            else:
               rpired -=1
         else:
            saturation -=1
         if use_Pi_Cam and camera_connected:
            rpiredx = Decimal(rpired)/Decimal(100)
         elif not use_Pi_Cam and camera_connected and (Webcam == 0 or Webcam > 1):
            rpiredx = max(rpired, usb_min_rx)
            rpistr = "v4l2-ctl -c red_balance=" + str(rpiredx) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         elif not use_Pi_Cam and camera_connected and Webcam == 1:
            saturation = max(saturation, usb_min_sa)
            rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         change = 1
      elif z == 14:
         if (use_Pi_Cam or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1))) and camera_connected:
            if Webcam > 1:
               rpired +=20
            else:
               rpired +=1
         else:
            saturation +=1
         if use_Pi_Cam and camera_connected:
            rpiredx = Decimal(rpired)/Decimal(100)
         elif not use_Pi_Cam and camera_connected and (Webcam == 0 or Webcam > 1):
            rpiredx = min(rpired, usb_max_rx)
            rpistr = "v4l2-ctl -c red_balance=" + str(rpiredx) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         elif not use_Pi_Cam and camera_connected and Webcam == 1:
            saturation = min(saturation, usb_max_sa)
            rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         change = 1
      elif z == 5:
         if (use_Pi_Cam or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1))) and camera_connected:
            if Webcam > 1:
               rpiblue -=20
            else:
               rpiblue -=1
         else:
            color_temp -=100
         if use_Pi_Cam and camera_connected:
            rpibluex = Decimal(rpiblue)/Decimal(100)
         elif not use_Pi_Cam and camera_connected and (Webcam == 0 or Webcam > 1):
            rpibluex = max(rpiblue, usb_min_bx)
            rpistr = "v4l2-ctl -c blue_balance=" + str(rpibluex) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         elif not use_Pi_Cam and camera_connected and Webcam == 1:
            color_temp = max(color_temp, usb_min_ct)
            rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         change = 1
      elif z == 15:
         if (use_Pi_Cam or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1))) and camera_connected:
            if Webcam > 1:
               rpiblue +=20
            else:
               rpiblue +=1
         else:
            color_temp +=100
         if use_Pi_Cam and camera_connected:
            rpibluex = Decimal(rpiblue)/Decimal(100)
         elif not use_Pi_Cam and camera_connected and (Webcam == 0 or Webcam > 1):
            rpibluex = min(rpiblue, usb_max_bx)
            rpistr = "v4l2-ctl -c blue_balance=" + str(rpibluex) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         elif not use_Pi_Cam and camera_connected and Webcam == 1:
            color_temp = min(color_temp, usb_max_ct)
            rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         change = 1
      elif z == 61:
         rpibr -=2
         if not use_Pi_Cam and camera_connected:
            rpibr = max(rpibr, usb_min_br)
         else:
            rpibr = max(rpibr, 0)
         change = 1
      elif z == 71:
         rpibr +=2
         if not use_Pi_Cam and camera_connected:
            rpibr = min(rpibr, usb_max_br)
         else:
            rpibr = min(rpibr, 100)
         change = 1
      elif z == 62:
         rpico -= 2
         if not use_Pi_Cam and camera_connected:
            rpico = max(rpico, usb_min_co)
         else:
            rpico = max(rpico, -100)
         change = 1
      elif z == 72:
         rpico += 2
         if not use_Pi_Cam and camera_connected:
            rpico = min(rpico, usb_max_co)
         else:
            rpico = min(rpico, 100)
         change = 1
      elif z == 63 and not use_Pi_Cam and camera_connected and not Auto_Gain and (scene_mode == 0):
         if Webcam == 0 :
            exposure -=1
         else:
            exposure -=10
         exposure = max(exposure,usb_min_ex)
         change = 1
      elif z == 73 and not use_Pi_Cam and camera_connected and not Auto_Gain and (scene_mode == 0):
         if Webcam == 0 :
            exposure +=1
         else:
            exposure +=10
         exposure = min(exposure,usb_max_ex)
         change = 1
      elif z == 64 and not use_Pi_Cam and camera_connected and not Auto_Gain and Webcam < 2:
         gain -=1
         gain = max(gain,usb_min_gn)
         change = 1
      elif z == 74 and not use_Pi_Cam and camera_connected and not Auto_Gain and Webcam < 2:
         gain +=1
         gain = min(gain,usb_max_gn)
         change = 1
      elif z == 64 and not use_Pi_Cam and camera_connected and Webcam > 1:
         scene_mode = 0
         rpistr = "v4l2-ctl -c scene_mode=" + str(scene_mode) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         keys(0,str(scene_mode),      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
         if Auto_Gain == 0:
             keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
         change = 1
      elif z == 74 and not use_Pi_Cam and camera_connected and Webcam > 1:
         scene_mode = 8
         rpistr = "v4l2-ctl -c scene_mode=" + str(scene_mode) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         keys(0,str(scene_mode),      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
         keys(0,str(exposure),        fs,       0,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
         change = 1
      elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam == 0:
         gamma -=1
         gamma = max(gamma,usb_min_ga)
         change = 1
      elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam == 0:
         gamma +=1
         gamma = min(gamma,usb_max_ga)
         change = 1
      elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam == 1:
         sharpness -=1
         sharpness = max(sharpness,usb_min_sh)
         change = 1
      elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam == 1:
         sharpness +=1
         sharpness = min(sharpness,usb_max_sh)
         change = 1
      elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam > 1:
         rpiev -=1
         rpiev = max(rpiev,usb_min_ev)
         change = 1
      elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and Webcam > 1:
         rpiev +=1
         rpiev = min(rpiev,usb_max_ev)
         change = 1
      elif z == 63 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
         if rpiss < 20000:
            inc = 1000
         if rpiss >= 20000 and rpiss <= 490000:
            inc = 10000
         if rpiss > 490000:
            inc = 100000
         rpiss -= inc
         if rpiss <= 1000:
            rpiss = 1000
         change = 1
      elif z == 73 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
         if rpiss < 20000:
            inc = 1000
         if rpiss >= 20000 and rpiss <= 490000:
            inc = 10000
         if rpiss > 490000:
            inc = 100000
         rpiss += inc
         if rpiss >= 6000000:
            rpiss = 6000000
         change = 1
      elif z == 81:
         nscale -= 10
         nscale = max(nscale, 10)
         change = 1
      elif z == 91:
         nscale += 10
         nscale = min(nscale, 800)
         change = 1
      elif z == 82:
         sscale -=10
         sscale = max(sscale, 10)
         change = 1
      elif z == 92:
         sscale +=10
         sscale = min(sscale, 800)
         change = 1
      elif z == 83:
         escale -=10
         escale = max(escale, 10)
         change = 1
      elif z == 93:
         escale +=10
         escale = min(escale, 800)
         change = 1
      elif z == 84:
         wscale -=10
         wscale = max(wscale, 10)
         change = 1
      elif z == 94:
         wscale +=10
         wscale = min(wscale, 800)
         change = 1
      elif z == 85 and esc1 == 0:
         nscale -=10
         sscale -=10
         wscale -=10
         escale -=10
         nscale = max(nscale, 10)
         sscale = max(sscale, 10)
         escale = max(escale, 10)
         wscale = max(wscale, 10)
         change = 1
      elif z == 95 and esc1 == 0:
         nscale +=10
         sscale +=10
         wscale +=10
         escale +=10
         nscale = min(nscale, 800)
         sscale = min(sscale, 800)
         escale = min(escale, 800)
         wscale = min(wscale, 800)
         change = 1
      elif z == 85 and esc1 > 0:
         Cang -=1
         Cang = max(Cang,-95)
         keys(0,str(int(Cang)),           fs,       2,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
      elif z == 95 and esc1 > 0:
         Cang +=1
         Cang = min(Cang,95)
         keys(0,str(int(Cang)),           fs,       2,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
      elif z == 43 and esc1 == 0:
         threshold -= 1
         threshold = max(threshold, 1)
         auto_t = 0
         change = 1
      elif z == 53 and esc1 == 0:
         threshold += 1
         threshold = min(threshold, 100)
         auto_t = 0
         change = 1
      elif z == 54:
         Interval = Intervals
         Interval += 1
         Intervals = Interval
         auto_i = 0
         change = 1
      elif z == 44:
         Interval = Intervals
         Interval -= 1
         Intervals = Interval
         if Interval < 1:
            Interval = 1
            Intervals = Interval
         auto_i = 0
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
         pcount = min(pcount, 99)
         change = 1
      elif z == 103 and photoon and not photo:
         pcount -= 1
         pcount = max(pcount, 1)
         change = 1
      elif z == 65 and use_Pi_Cam and esc1 == 0:
         if rpiISO > 0:
            rpiISO -= 100
         change = 1
      elif z == 75 and use_Pi_Cam and esc1 == 0:
         if rpiISO < 800:
            rpiISO += 100
         change = 1
      elif z == 65 and esc1 > 0:
         calibrate_time -=1
         calibrate_time = max(calibrate_time,2)
         zt = 0
         scale_t = 1
         while zt <= zoom:
            scale_t *= rpiscalex[zt]
            zt += 1
         cal_time = int((calibrate_time * 1000) / scale_t)
         keys(0,str((cal_time/1000)),   fs,       2,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         change = 1
      elif z == 75 and esc1 > 0:
         calibrate_time +=1
         calibrate_time = min(calibrate_time,50)
         zt = 0
         scale_t = 1
         while zt <= zoom:
            scale_t *= rpiscalex[zt]
            zt += 1
         cal_time = int((calibrate_time * 1000) / scale_t)
         keys(0,str((cal_time/1000)),   fs,       2,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         change = 1
      elif esc1 > 0 and z == 132:
         calibrate = 1
         cal_count = 0
         keys(0," CALIB DEC",fs,2,b3x+bw/5,bw,   0,     b3y-2, bh, 5, 0, 1)
         change = 1
         
   for event in pygame.event.get():
       if event.type == QUIT:
          if use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
          pygame.quit()
          sys.exit()

       elif (event.type == MOUSEBUTTONUP or event.type == KEYDOWN) and not calibrate:
          start = time.time()
          xcount =     0
          ycount =     0
          ymax =       0
          totvcor =    0
          tothcor =    0
          count =      1
          xvcor = [0]*11
          xhcor = [0]*11
          keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
          keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
          if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
          keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
          keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
          if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
          restart = 0
          z =  0
          kz = 0
          if event.type == KEYDOWN:
             kz = event.key

          if event.type == MOUSEBUTTONUP:
             if store > 0:
                offset3 = (xouse - Disp_Width/2) 
                offset4 = (youse - Disp_Height/2)
                if store == 2:
                   crop = (rad) * 2
                   if crop < 0:
                      crop = 0-crop
                   if Cwindow:
                      mmq, mask, change = MaskChange()
                change = 1
             mousex, mousey = event.pos
             if Display == 1:
                x = int(mousex/bw)
                if mousey > Disp_Height:
                   y = int((mousey-Disp_Height)/bh)
                   z = (10*x) + y
             else:
                if menu == 0 and mousex > Disp_Width:
                   if mousey < bh * 5:
                      x = int((mousex - Disp_Width)/bw)
                      y = int(mousey/bh) + 1
                      z = 10*x + y
                   if mousey > bh*5 and mousey < bh*10:
                      x = int((mousex - Disp_Width)/bw) + 6
                      y = int((mousey - 5*bh)/bh) + 1
                      z = 10*x + y
                   if mousey > bh*10:
                      x = int((mousex - Disp_Width)/bw) + 12
                      y = int((mousey - 10*bh)/bh) + 1
                      z = 10*x + y
                if menu == 1:
                   if mousey < bh * 5 and mousex < bw * 6:
                      x = int((mousex)/bw)
                      y = int(mousey/bh) + 1
                      z = 10*x + y
                   if mousey > bh*5 and mousey < bh*10 and mousex < bw * 6:
                      x = int((mousex)/bw) + 6
                      y = int((mousey - 5*bh)/bh) + 1
                      z = 10*x + y
                   if mousey < bh*5 and mousex > bw*6:
                      x = int((mousex)/bw) + 6
                      y = int((mousey)/bh) + 1
                      z = 10*x + y
                      
             # set threshold by clicking on the graph         
             if (Display == 0 and menu == 0) or Display > 1:
                pox = Disp_Width - 52
             else:
                pox = Disp_Width + 70
                pov = 50
             if graph > 0 and mousex > pox and mousex < pox + pov and mousey > poy and mousey < poy + 258:
                level = 276 - mousey
                if esc1 == 0:
                   threshold = maxtot - level
                   threshold = max(threshold, 1)
                elif esc1 > 0 and auto_t == 0:
                   m_thr_limit = level - mintot
                   keys(0,str(int(m_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
                   esc2 = 1
                   esc1 = 2
                   esctimer = time.time()
                elif esc1 > 0 and auto_t == 1:
                   a_thr_limit = level - mintot
                   keys(0,str(int(a_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
                   esc2 = 1
                   esc1 = 2
                   esctimer = time.time()
                change = 1
                
             else:
                if menu == 1 and mousex > 318 and mousex < 638 and mousey > 238 and mousey < 478 :
                   offset3 = ((mousex - 318) - (Disp_Width/4)) * 2
                   offset4 = ((mousey - 238) - (Disp_Height/4)) * 2
                   
                #switch Display   
                if (Display == 0 and mousex > 736  and mousex < 800 and mousey > 416 and mousey < 448) :
                   menu +=1
                   if menu > 1:
                      menu = 0
                   if menu == 0:
                      bh = 32
                      bw = 32
                      b1x = b2x = b3x = Disp_Width
                      b1y = -bh
                      b2y = bh*4
                      b3y = bh*9
                      pygame.draw.rect(windowSurfaceObj, blackColor, Rect(0,0,800, 480), 0)
                      z = 24
                      switch = 1
                   else:
                      bh = 46
                      bw = 52
                      b1x = b2x = 0
                      b3x = bw*6 
                      b1y = -bh
                      b2y = bh*4 + 1
                      b3y = -bh
                      pygame.draw.rect(windowSurfaceObj, blackColor, Rect(0,0,800,480), 0)
                      pygame.draw.rect(windowSurfaceObj, greyColor,  Rect(736,416,64,32), 0)
                      pygame.draw.rect(windowSurfaceObj, lgryColor,  Rect(736,416,64,2), 0)
                      pygame.draw.rect(windowSurfaceObj, lgryColor,  Rect(736,416,1,32), 0)
                      keys(0," FULL", 12, 6, 748, 0, 0, 416, 0, 0, 0, 0)
                      keys(0,"Display", 12, 6, 748, 0, 0, 432, 0, 0, 0, 0)
                      z = 24
                      switch = 1
                # move window by clicking on image
                if mousex < Disp_Width and mousey < Disp_Height and menu == 0 :
                   if graph == 0 or (graph > 0 and (mousex < pox or mousey > poy + 258)):
                      start = time.time()
                      xcount =  0
                      ycount =  0
                      totvcor = 0
                      tothcor = 0
                      count =   1
                      if nr > 0:
                         mxq = []
                         mxp = []
                         mxo = []
                      while count <= 10:
                         xvcor[count] = 0
                         xhcor[count] = 0
                         count += 1
                      if store == 0:
                         offset3o = offset3
                         offset4o = offset4
                         offset3 = mousex - Disp_Width/2
                         offset4 = mousey - Disp_Height/2
                         if (Disp_Width/2 + offset3 + crop/2) >= Disp_Width or (Disp_Width/2 + offset3 - crop/2) <= 1:
                            offset3 = offset3o
                            offset4 = offset4o
                         if (Disp_Height/2 + offset4 + crop/2) >= Disp_Height or (Disp_Height/2 + offset4 - crop/2) <= 1:
                            offset3 = offset3o
                            offset4 = offset4o
          store = 0
                      
          if ((z > 60 and z < 65) or (z > 70 and z < 75) or (z == 65 and esc1 ==0) or (z==75 and esc1 ==0) or z == 5 or z == 4 or z == 15 or z == 14) and use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
             
          if esc1 > 0 and z != 132 and z != 33 and z != 43 and z != 53 and z != 141 and z != 143 and z != 154 and z != 85 and z != 95 and z != 65 and z != 75 and kz != K_ESCAPE and esc2 != 1:
             esc1 = 0
             keys(0,"Esc",fs,5,b3x,bw,2,b3y, bh, 2, 2, 0)
             keys(0,"threshold", fs-1,6,b1x,bw,4,b1y, bh, 4, 0, 1)
             keys(0,str(int(threshold)),fs,3,b1x,bw,5,b1y, bh, 4, 3, 1)
             keys(0,"cen",                      fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
             keys(0," tre",                     fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
             if auto_rotate == 0:
                keys(0,"scale all",             fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
                keys(0,str(int(Cang)),          fs,   7,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
             if use_Pi_Cam and camera_connected:
                keys(0,"ISO",                   fs,   6,        b2x,         bw,  0,     b2y, bh, 6, 0, 1)
                keys(0,str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                if not rpiISO:
                   keys(0,'auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
             if not use_Pi_Cam and camera_connected:
                button(b2x, 1, b2y, 6, bw, 2, bh, 0,1)
                if Webcam == 0:
                   keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                   keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                elif Webcam == 1:
                   keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                   keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                elif Webcam > 1:
                   keys(0,"  eV",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                   keys(0,str(rpiev),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
 
             
          if z == 115 or kz == 304 or kz == 303:
             con_cap += 1
             if con_cap > 1:
                con_cap = 0
             change = 1
          elif z == 65 and use_Pi_Cam and esc1 == 0 and press == 0:
             if rpiISO > 0 and press == 0:
                rpiISO -= 100
             restart =1
             change = 1
          elif z == 65 and esc1 > 0 and press == 0:
             calibrate_time -=1
             calibrate_time = max(calibrate_time,2)
             zt = 0
             scale_t = 1
             while zt <= zoom:
                scale_t *= rpiscalex[zt]
                zt += 1
             cal_time = int((calibrate_time * 1000) / scale_t)
             keys(0,str((cal_time/1000)),   fs,       2,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
             change = 1
          elif z == 75 and esc1 > 0 and press == 0:
             calibrate_time +=1
             calibrate_time = min(calibrate_time,50)
             zt = 0
             scale_t = 1
             while zt <= zoom:
                scale_t *= rpiscalex[zt]
                zt += 1
             cal_time = int((calibrate_time * 1000) / scale_t)
             keys(0,str((cal_time/1000)),   fs,       2,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
             change = 1
          elif z == 43 and esc1 == 0:
             threshold -= 1
             threshold = max(threshold, 1)
             auto_t = 0
             change = 1
          elif z == 53 and esc1 == 0:
             threshold += 1
             threshold = min(threshold, 100)
             auto_t = 0
             change = 1
          elif z == 75 and use_Pi_Cam and esc1 == 0 and press == 0:
            if rpiISO < 800 and press == 0:
               rpiISO += 100
            restart = 1
            change = 1
          elif z == 54 and press == 0:
             Interval = Intervals
             Interval += 1
             Intervals = Interval
             auto_i = 0
             change = 1
          elif z == 44 and press == 0:
             Interval = Intervals
             Interval -= 1
             Intervals = Interval
             if Interval < 1:
                Interval = 1
             Intervals = Interval
             auto_i = 0
             change = 1
          elif z == 81 and press == 0:
             nscale -= 10
             nscale = max(nscale, 10)
             change = 1
          elif z == 91 and press == 0:
             nscale += 10
             nscale = min(nscale, 800)
             change = 1
          elif z == 82 and press == 0:
             sscale -=10
             sscale = max(sscale, 10)
             change = 1
          elif z == 92 and press == 0:
             sscale +=10
             sscale = min(sscale, 800)
             change = 1
          elif z == 83 and press == 0:
             escale -=10
             escale = max(escale, 10)
             change = 1
          elif z == 93 and press == 0:
             escale +=10
             escale = min(escale, 800)
             change = 1
          elif z == 84 and press == 0:
             wscale -=10
             wscale = max(wscale, 10)
             change = 1
          elif z == 94 and press == 0:
             wscale +=10
             wscale = min(wscale, 800)
             change = 1
          elif z == 85 and press == 0 and esc1 == 0:
             nscale -=10
             sscale -=10
             wscale -=10
             escale -=10
             nscale = max(nscale, 10)
             sscale = max(sscale, 10)
             escale = max(escale, 10)
             wscale = max(wscale, 10)
             change = 1
          elif z == 85 and press == 0 and esc1 > 0:
             Cang -=1
             Cang = max(Cang,-90)
             keys(0,str(int(Cang)),           fs,       2,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
          elif z == 95 and press == 0 and esc1 > 0:
             Cang +=1
             Cang = min(Cang,90)
             keys(0,str(int(Cang)),           fs,       2,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
          elif z == 95 and press == 0 and esc1 == 0:
             nscale +=10
             sscale +=10
             wscale +=10
             escale +=10
             nscale = min(nscale, 800)
             sscale = min(sscale, 800)
             escale = min(escale, 800)
             wscale = min(wscale, 800)
             change = 1
          elif z == 35 and press == 0:
             mind = minc * 10
             mind += 1
             minc = Decimal(mind)/Decimal(10)
             minc = min(minc, 50)
             change = 1
          elif z == 25 and press == 0:
             mind = minc * 10
             mind -= 1
             minc = Decimal(mind)/Decimal(10)
             minc = max(minc, 0.1)
             change = 1
          elif z == 112 and photoon and not photo and press == 0:
             ptime += 10
             ptime = min(ptime, 990)
             change = 1
          elif z == 102 and photoon and not photo and press == 0:
             ptime -= 10
             ptime = max(ptime, 10)
             change = 1
          elif z == 113 and photoon and not photo and press == 0:
             pcount += 1
             pcount = min(pcount, 99)
             change = 1
          elif z == 103 and photoon and not photo and press == 0:
             pcount -= 1
             pcount = max(pcount, 1)
             change = 1
          elif z == 143 and esc1 == 1:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if serial_connected:
                lx200(':Q#', ':Q#', decN, decS)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
             keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
             keys(0,Dkey[1], fs,   6, b3x, bw, 0, b3y, bh, 3, 2, 1)
             keys(0,Dkey[2], fs,   6, b3x, bw, 2, b3y, bh, 3, 2, 1)
             pygame.quit()
             sys.exit()
                
          elif z == 154 and esc1 == 0:
             Cwindow +=1
             if Cwindow > 1:
                Cwindow = 0
             if Cwindow:
                mmq, mask, change = MaskChange()

             esc1 = 0
             keys(0,"Esc", fs, 5, b3x, bw, 2, b3y, bh, 2, 2, 1)
             keys(0,"cen",                      fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 0, 1)
             keys(0," tre",                     fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 2, 1)
             change = 1
             
          elif z == 141 or kz == K_ESCAPE:
             if esc1 == 0:
                esc1 = 1
                keys(0,"Esc", fs, 3, b3x, bw, 2, b3y, bh, 2, 2, 1)
                keys(0,"CAL",                fs,       2,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
                keys(0," ......",            fs,       2,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
                if camera_connected:
                   zt = 0
                   scale_t = 1
                   while zt <= zoom:
                      scale_t *= rpiscalex[zt]
                      zt += 1
                   cal_time = int((calibrate_time * 1000) / scale_t)
                   keys(0,"CAL Time",                 fs-1,     2,        b2x,         bw  , 0,     b2y, bh, 6, 0, 1)
                   keys(0,str((cal_time/1000)),   fs,       2,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                if auto_rotate == 0 :
                   keys(0,"Cam Angle",             fs-1,     2,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
                   keys(0,str(int(Cang)),          fs,       2,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
                if auto_t == 1:
                   keys(0,str(int(a_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
                else:
                   keys(0,str(int(m_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
                esctimer = time.time()
             elif esc1 == 1:
                if use_Pi_Cam and camera_connected:
                   os.killpg(p.pid, signal.SIGTERM)
                if serial_connected:
                   lx200(':Q#', ':Q#', decN, decS)
                if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                   DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
                keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
                keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
                keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
                pygame.quit()
                if power_down == 0:
                   if not use_Pi_Cam and camera_connected and Webcam < 2:
                      cam.stop()
                   sys.exit()
                else:
                   os.system("sudo shutdown -h now")
             elif esc1 == 2:
                esc1 = 0
                keys(0,"Esc", fs, 5, b3x, bw, 2, b3y, bh, 2, 2, 1)
                keys(0,"threshold", fs-1,6,b1x,bw,4,b1y, bh, 4, 0, 1)
                keys(0,str(int(threshold)),fs,3,b1x,bw,5,b1y, bh, 4, 3, 1)
                keys(0,"cen",                   fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 0, 1)
                keys(0," tre",                  fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 2, 1)
                keys(0,"scale all",             fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 1)
                keys(0,str(int(Cang)),          fs,   7,        b2x,         bw,   3,     b2y, bh, 6, 3, 1)
                if use_Pi_Cam and camera_connected:
                   keys(0,"ISO",                fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                   keys(0,str(rpiISO),          fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                   if not rpiISO:
                      keys(0,'auto',            fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                if not use_Pi_Cam and camera_connected:
                   button(b2x, 1, b2y, 6, bw, 2, bh, 0,1)
                   if Webcam == 0:
                      keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                      keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                   elif Webcam == 1:
                      keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                      keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                   elif Webcam > 1:
                      keys(0,"  eV",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 1)
                      keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 1)
                      keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 1)
                      keys(0,str(rpiev),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
                change = 1

          elif z == 114 or kz == K_s:
             if menu == 0:
                button(b2x, 6, b2y, 5, bw, 1, bh, 1,0)
                keys(0,"Scr", fs, 1, b2x, bw, 5, b2y, bh, 5, 0, 1)
                keys(0,"cap", fs, 1, b2x, bw, 5, b2y, bh, 5, 2, 1)
             else:
                button(b2x, 6, b2y, 5, bw, 1, bh, 1,0)
                keys(0,"Screen", fs, 1, b2x, bw, 5, b2y, bh, 5, 0, 1)
                keys(0,"capture", fs, 1, b2x, bw, 5, b2y, bh, 5, 2, 1)
             now = datetime.datetime.now()
             timestamp = now.strftime("%y%m%d%H%M%S")
             pygame.image.save(windowSurfaceObj, '/home/pi/scr' + str(timestamp) + "_"  + str(pct) + '.bmp')
             if menu == 0:
                button(b2x, 6, b2y, 5, bw, 1, bh, 0,0)
                keys(0,"Scr", fs, 6, b2x, bw, 5, b2y, bh, 5, 0, 1)
                keys(0,"cap", fs, 6, b2x, bw, 5, b2y, bh, 5, 2, 1)
             else:
                button(b2x, 6, b2y, 5, bw, 1, bh, 0,0)
                keys(0,"Screen", fs, 6, b2x, bw, 5, b2y, bh, 5, 0, 1)
                keys(0,"capture", fs, 6, b2x, bw, 5, b2y, bh, 5, 2, 1)
             keys(0,"S",   fs, 5, b2x, bw, 5, b2y, bh, 5, 0, 1)
             pct += 1
          elif z == 104 and use_Pi_Cam and camera_connected:
             os.killpg(p.pid, signal.SIGTERM)
             if menu == 0:
                button(b2x, 5, b2y, 5, bw, 1, bh, 1,0)
                keys(0,"pic", fs, 1, b2x, bw, 4, b2y, bh, 5, 0, 1)
                keys(0,"cap", fs, 1, b2x, bw, 4, b2y, bh, 5, 2, 1)
             else:
                button(b2x, 5, b2y, 5, bw, 1, bh, 1,0)
                keys(0,"picture", fs, 1, b2x, bw, 4, b2y, bh, 5, 0, 1)
                keys(0,"capture", fs, 1, b2x, bw, 4, b2y, bh, 5, 2, 1)
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
             if Pi_Cam == 2:
                path = rpistr + ' -w 3280 -h 2464'
             if Pi_Cam == 1:
                path = rpistr + ' -w 2592 -h 1944'
             os.system(path)
             if menu == 0:
                button(b2x, 5, b2y, 5, bw, 1, bh, 0,0)
                keys(0,"pic", fs, 6, b2x, bw, 4, b2y, bh, 5, 0, 1)
                keys(0,"cap", fs, 6, b2x, bw, 4, b2y, bh, 5, 2, 1)
             else:
                button(b2x, 5, b2y, 5, bw, 1, bh, 0,0)
                keys(0,"picture", fs, 6, b2x, bw, 4, b2y, bh, 5, 0, 1)
                keys(0,"capture", fs, 6, b2x, bw, 4, b2y, bh, 5, 2, 1)
             pcu += 1
             restart = 1
          elif z == 104 and not use_Pi_Cam and camera_connected:
             Auto_Gain +=1
             if Auto_Gain > 1:
                Auto_Gain = 0
             change = 1
          elif (z == 151 or z == 161 or z == 171 or kz == K_0) and zoom == Image_window : 
             offset4 -= 5
             if ((Disp_Height/2 + offset4 + crop/2) >= height) or ((Disp_Height/2 + offset4 - crop/2) <= 1):
                offset4 += 5
             if z == 151:
                offset3 -= 5
                if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                   offset3 += 5
             if z == 171:
                offset3 += 5
                if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                   offset3 -= 5
          elif (z == 153 or z == 163 or z == 173 or kz == K_9) and zoom == Image_window :
             offset4 += 5
             if ((Disp_Height/2 + offset4 + crop/2) >= height) or ((Disp_Height/2 + offset4 - crop/2) <= 1):
                offset4 -= 5
             if z == 153:
                offset3 -= 5
                if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                   offset3 += 5
             if z == 173:
                offset3 += 5
                if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                   offset3 -= 5
          elif (z == 172 or kz == K_8) and zoom == Image_window : 
             offset3 += 5
             if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                offset3 -= 5
          elif (z == 152 or kz == K_7) and zoom == Image_window :
             offset3 -= 5
             if ((Disp_Width/2 + offset3 + crop/2) >= width) or ((Disp_Width/2 + offset3 - crop/2) <= 1):
                offset3 += 5

          elif (z == 151 or z == 161 or z == 171) and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 -= 5 * (math.cos((0-Cang) * (3.14159/180)))
             offset5 -= 5 * (math.sin((0-Cang) * (3.14159/180)))
             if (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2) or (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
                offset5 += 5 * (math.sin((0-Cang) * (3.14159/180)))
                offset6 += 5 * (math.cos((0-Cang) * (3.14159/180)))
             if z == 151:
                offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
                offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
                if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2) or (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2):
                   offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
                   offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
             if z == 171:
                offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
                offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
                if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2) or (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or(offset6 < 0 and offset6 <= Disp_Height/2 - h/2):
                   offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
                   offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
                   
          elif (z == 153 or z == 163 or z == 173) and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 += 5 * (math.cos((0-Cang) * (3.14159/180)))
             offset5 += 5 * (math.sin((0-Cang) * (3.14159/180)))
             if (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2) or (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
                offset5 -= 5 * (math.sin((0-Cang) * (3.14159/180)))
                offset6 -= 5 * (math.cos((0-Cang) * (3.14159/180)))
             if z == 173:
                offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
                offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
                if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2) or (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or(offset6 < 0 and offset6 <= Disp_Height/2 - h/2):
                   offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
                   offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
             if z == 153:
                offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
                offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
                if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2) or (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2):
                   offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
                   offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
          elif z == 172 and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
             offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
             if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
                offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
                offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
          elif z == 152 and zoom > Image_window:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
                restart = 1
             offset6 -= 5 * (math.cos((90-Cang) * (3.14159/180)))
             offset5 -= 5 * (math.sin((90-Cang) * (3.14159/180)))
             if (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
                offset5 += 5 * (math.sin((90-Cang) * (3.14159/180)))
                offset6 += 5 * (math.cos((90-Cang) * (3.14159/180)))
                
          elif z == 162 and zoom > Image_window:
             offtry = 0
             Hip = int(math.sqrt((offset3) * (offset3) + (offset4) * (offset4)))
             if offset3 != 0 :
                offset3a = offset3
                offset4a = offset4
                if Cang != 0:
                   Hang = (math.atan(offset4/offset3))
                   if offset3 < 0 and offset4 < 0 or offset3 < 0 and offset4 >= 0:
                      offset3a = 0-(Hip * math.cos(Hang + (Cang * (3.14159/180))))
                      offset4a = 0-(Hip * math.sin(Hang + (Cang * (3.14159/180))))
                   if offset3 >=0 and offset4 < 0 or offset3 >=0 and offset4 >= 0:
                      offset3a = (Hip * math.cos(Hang + (Cang * (3.14159/180))))
                      offset4a = (Hip * math.sin(Hang + (Cang * (3.14159/180))))
                if not use_Pi_Cam:
                   offmoves = 5
                else:
                   offmoves = 10
                while offtry < offmoves:
                   offset6 += int(offset4a/10)
                   offset5 += int(offset3a/10)
                   if (offset6 > 0 and offset6 >= h/2 - Disp_Height/2) or (offset6 < 0 and offset6 <= Disp_Height/2 - h/2) or (offset5 > 0 and offset5 >= w/2 - Disp_Width/2) or (offset5 < 0 and offset5 <= Disp_Width/2 - w/2):
                      offset6 -= int(offset4a/10)
                      offset5 -= int(offset3a/10)
                      offtry = offmoves
                   offtry += 1
                offset3 = 0
                offset4 = 0
             

             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if camera_connected == 0:
                posx =  Disp_Width/2
                posy = Disp_Height/2
             restart = 1
          elif z == 162 and zoom == Image_window:
             offset3 = 0
             offset4 = 0
             if camera_connected == 0:
                posx =  Disp_Width/2
                posy = Disp_Height/2
          elif z == 63 and not use_Pi_Cam and camera_connected and press == 0 and Auto_Gain == 0 and ( Webcam > 1 and scene_mode == 0):
             if Webcam == 0 :
                exposure -=1
             else:
                exposure -=10
             exposure = max(exposure,usb_min_ex)
             if Webcam == 0:
                rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
             elif Webcam == 1:
                rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
             elif Webcam > 1:
                rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
             keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 73 and not use_Pi_Cam and camera_connected and press == 0 and Auto_Gain == 0 and ( Webcam > 1 and scene_mode == 0):
             if Webcam == 0:
                exposure +=1
             else:
                exposure +=10
             exposure = min(exposure,usb_max_ex)
             keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
             if Webcam == 0:
                rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
             elif Webcam == 1:
                rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
             elif Webcam > 1:
                rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
                os.system (rpistr)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 64 and not use_Pi_Cam and camera_connected and press == 0 and Auto_Gain == 0:
             if Webcam < 2:
                gain -=1
                gain = max(gain,usb_min_gn)
                rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
             elif Webcam > 1:
                scene_mode = 0
                rpistr = "v4l2-ctl -c scene_mode=" + str(scene_mode) + " -d " + str(dve)
                keys(0,str(scene_mode),      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                if Auto_Gain == 0:
                    keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 74 and not use_Pi_Cam and camera_connected and press == 0 and Auto_Gain == 0:
             if Webcam < 2:
                gain +=1
                gain = min(gain,usb_max_gn)
                rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
             elif Webcam > 1:
                scene_mode = 8
                rpistr = "v4l2-ctl -c scene_mode=" + str(scene_mode) + " -d " + str(dve)
                keys(0,str(scene_mode),      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                keys(0,str(exposure),           fs,       0,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam == 0:
             gamma -=1
             gamma = max(gamma,usb_min_ga)
             rpistr = "v4l2-ctl -c gamma=" + str(gamma) + " -d " + str(dve)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam == 0:
             gamma +=1
             gamma = min(gamma,usb_max_ga)
             rpistr = "v4l2-ctl -c gamma=" + str(gamma) + " -d " + str(dve)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam == 1:
             sharpness -=1
             sharpness = max(sharpness,usb_min_sh)
             rpistr = "v4l2-ctl -c sharpness=" + str(sharpness) + " -d " + str(dve)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam > 1:
             rpiev +=1
             rpiev = min(rpiev,usb_max_ev)
             change = 1
          elif z == 65 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam > 1:
             rpiev -=1
             rpiev = max(rpiev,usb_min_ev)
             change = 1
          elif z == 75 and not use_Pi_Cam and camera_connected and esc1 == 0 and press == 0 and Webcam == 1:
             sharpness +=1
             sharpness = min(sharpness,usb_max_sh)
             rpistr = "v4l2-ctl -c sharpness=" + str(sharpness) + " -d " + str(dve)
             p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             change = 1
          elif z == 61 and camera_connected:
             if press == 0:
                rpibr -=2
                if not use_Pi_Cam and camera_connected:
                   rpibr = max(rpibr, usb_min_br)
                else:
                   rpibr = max(rpibr, 0)
             if camera_connected and not use_Pi_Cam  and press == 0:
                rpistr = "v4l2-ctl -c brightness=" + str(rpibr)  + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 71 and camera_connected:
             if press == 0:
                rpibr +=2
                if not use_Pi_Cam and camera_connected:
                   rpibr = min(rpibr, usb_max_br)
                else:
                   rpibr = min(rpibr, 100)

             if camera_connected and not use_Pi_Cam  and press == 0:
                rpistr = "v4l2-ctl -c brightness=" + str(rpibr) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 62 and camera_connected:
             if press == 0:
                rpico -= 2
                if not use_Pi_Cam and camera_connected:
                   rpico = max(rpico, usb_min_co)
                else:
                   rpico = max(rpico, -100)
             if camera_connected and not use_Pi_Cam  and press == 0:
                rpistr = "v4l2-ctl -c contrast=" + str(rpico) + " -d " + str(dve) 
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 72 and camera_connected:
             if press == 0:
                rpico += 2
                if not use_Pi_Cam and camera_connected:
                   rpico = min(rpico, usb_max_co)
                else:
                   rpico = min(rpico, 100)
             if camera_connected and not use_Pi_Cam  and press == 0:
                rpistr = "v4l2-ctl -c contrast=" + str(rpico) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 63 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
             if rpiss < 20000:
                inc = 1000
             if rpiss >= 20000 and rpiss <= 490000:
                inc = 10000
             if rpiss > 490000:
                inc = 100000
             if press == 0:
                rpiss -= inc
             if rpiss <= 1000:
                rpiss = 1000
             restart = 1
             change = 1
          elif z == 73 and use_Pi_Cam and (rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2'):
             if rpiss < 20000:
                inc = 1000
             if rpiss >= 20000 and rpiss <= 490000:
                inc = 10000
             if rpiss > 490000:
                inc = 100000
             if press == 0:
                rpiss += inc
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
          elif z == 132 and esc1 == 0:
             auto_c += 1
             auto_g =   1
             auto_win = 1
             oCwindow = Cwindow
             Cwindow = 0
             ocrop = crop
             change = 1#
             if auto_c > 1:
                auto_c =   0
                auto_win = 0
                crop = ocrop
             if auto_c == 0:
                keys(0,"cen",  fs, 7, b3x, bw, 1, b3y, bh, 3, 0, 1)
                keys(0," tre", fs, 7, b3x, bw, 1, b3y, bh, 3, 2, 1)
             else:
                keys(0,"cen",  fs, 1, b3x, bw, 1, b3y, bh, 3, 0, 1)
                keys(0," tre", fs, 1, b3x, bw, 1, b3y, bh, 3, 2, 1)

          elif z == 121:
             decN = not decN
             change = 1
          elif z == 123:
             decS = not decS
             change = 1
          elif z == 31:
             nr +=1
             if nr > 3:
                nr = 0
                mxq = []
                mxp = []
                mxo = []
             samples = nr * navscale
             if nr > 0:
                nav  =    [0]* navscale * 3
                nav2 =    [0]* navscale * 3
                nav3 =    [0]* navscale * 3
                nav4 =    [0]* navscale * 3
                nstart = 1
           
             change = 1
          elif (z == 105 or kz == K_c) and auto_g:
             cls = not cls
             change = 1

          elif z == 52 or kz == K_f:
             auto_win = 0
             crop += 4
             crop = min(crop, maxwin)
             if (Disp_Width/2 + offset3 + crop/2) >= width:
                crop -= 4
             if (Disp_Width/2 + offset3 - crop/2) <= 1:
                crop -= 4
             if (Disp_Height/2 + offset4 + crop/2) >= height:
                crop -= 4
             if (Disp_Height/2 + offset4 - crop/2) <= 1:
                crop -= 4
             if Cwindow == 1:
                mmq, mask, change = MaskChange()
             change = 1

          elif z == 42 or kz == K_w:
             auto_win = 0
             crop -= 4
             crop = max(crop, minwin)
             if Cwindow:
                mmq, mask, change = MaskChange()
             change = 1

          elif (z == 101 or z == 111 or kz == K_o) and photoon:
             photo = not photo
             if not photo:
                camera = 0
                button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
                keys(0,"",  fs, photo, b2x+ (bw/1.5), bw, 4, b2y, bh, 2, 3, 1)
                keys(0,"",  fs, photo, b2x+14, bw, 5, b2y, bh, 2, 3, 1)
                if use_RPiGPIO or photoon:
                   GPIO.output(C_OP, GPIO.LOW)
                   po = 0
             if photo:
                pcount2 = pcount
                button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
                keys(1,"1", fs, photo, b2x+ (bw/1.5), bw, 4, b2y, bh, 2, 3, 1)
                ptime2 = time.time() + ptime
                camera = 1
                if use_RPiGPIO or photoon:
                   if pmlock == 1:
                      GPIO.output(C_OP, GPIO.HIGH)
                      po = 1
                      time.sleep(0.5)
                      GPIO.output(C_OP, GPIO.LOW)
                      po = 0
                      time.sleep(0.5)
                   GPIO.output(C_OP, GPIO.HIGH)
                   po = 1
             change = 1

          elif z == 53 and esc1 > 0:
             if auto_t == 1:
                a_thr_limit += 1
                keys(0,str(int(a_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
             else:
                m_thr_limit += 1
                keys(0,str(int(m_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
             esc1 = 2
             esctimer = time.time()
          elif z == 43 and esc1 > 0:
             if auto_t == 1:
                a_thr_limit -= 1
                a_thr_limit = max(a_thr_limit, 1)
                keys(0,str(int(a_thr_limit)),fs,2, b1x,bw,5,b1y, bh, 4, 3, 1)
             else:
                m_thr_limit -= 1
                m_thr_limit = max(m_thr_limit, 1)
                keys(0,str(int(m_thr_limit)),fs,2, b1x,bw,5,b1y, bh, 4, 3, 1)
             esc1 = 2
             esctimer = time.time()

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

          elif (z == 133 or kz == K_DOWN) and esc1 == 0:
             if serial_connected:
                tim = mincorpiredr*10
                blan = "0000" + str(int(tim))
                move = ':Mgs' + blan[(len(blan))-4:len(blan)]
                button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
                keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
                lx200(move, ':Mgw0000', decN, decS)
                button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
                keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                button(b3x, 2, b3y, 4, bw, 1, bh, 1,0)
                keys(0,Dkey[3], fs-1, 1, b3x, bw, 1, b3y, bh, 4, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                time.sleep(mincor/100)
                button(b3x, 2, b3y, 4, bw, 1, bh, 0,0)
                keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif (z == 131 or kz == K_UP) and esc1 == 0:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mgn' + blan[(len(blan))-4:len(blan)]
                button(b3x, 2, b3y, 2, bw, 1, bh, 1,0)
                keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
                lx200(move, ':Mgw0000', decN, decS)
                button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
                keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                button(b3x, 2, b3y, 2, bw, 1, bh, 1,0)
                keys(0,Dkey[0], fs-1, 1, b3x, bw, 1, b3y, bh, 2, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                time.sleep(mincor/100)
                button(b3x, 2, b3y, 2, bw, 1, bh, 0,0)
                keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif (z == 122 or kz == K_LEFT) and esc1 == 0:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mgw' + blan[(len(blan))-4:len(blan)]
                button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
                keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
                lx200(move, ':Mgs0000', decN, decS)
                button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
                keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                button(b3x, 1, b3y, 3, bw, 1, bh, 1,0)
                keys(0,Dkey[1], fs, 1, b3x, bw, 0, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                time.sleep(mincor/100)
                button(b3x, 1, b3y, 3, bw, 1, bh, 0,0)
                keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif (z == 142 or kz == K_RIGHT) and esc1 == 0:
             if serial_connected:
                tim = mincor*10
                blan = "0000" + str(int(tim))
                move = ':Mge' + blan[(len(blan))-4:len(blan)]
                button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
                keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
                lx200(move, ':Mgs0000', decN, decS)
                button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
                keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                button(b3x, 3, b3y, 3, bw, 1, bh, 1,0)
                keys(0,Dkey[2], fs, 1, b3x, bw, 2, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA =  R_ON(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                time.sleep(mincor/100)
                button(b3x, 3, b3y, 3, bw, 1, bh, 0,0)
                keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             change = 1

          elif (z == 143 or kz == K_END) and esc1 == 0:
             auto_g = 0
             auto_c = 0
             auto_win = 0
             crop = ocrop
             Cwindow = oCwindow
             if Cwindow == 1:
                mmq, mask, change = MaskChange()
             keys(0,"cen",                      fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
             keys(0," tre",                     fs,       7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
             if serial_connected:
                lx200(':Q#', ':Q#', decN, decS)
             if use_RPiGPIO or use_Seeed or use_PiFaceRP or use_crelay:
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(0, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(1, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(2, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
                DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA = R_OFF(3, DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
             keys(0,Dkey[0], fs-1, 6, b3x, bw, 1, b3y, bh, 2, 2, 1)
             keys(0,Dkey[3], fs-1, 6, b3x, bw, 1, b3y, bh, 4, 2, 1)
             keys(0,Dkey[1], fs, 6, b3x, bw, 0, b3y, bh, 3, 2, 1)
             keys(0,Dkey[2], fs, 6, b3x, bw, 2, b3y, bh, 3, 2, 1)
             change = 1

          elif esc1 > 0 and z == 132:
                calibrate = 1
                cal_count = 0
                keys(0," CALIB DEC",fs,2,b3x+bw/5,bw,   0,     b3y-2, bh, 5, 0, 1)
                change = 1
                
          elif z == 34 or kz == K_i:
                auto_i = not auto_i
                change = 1

          elif z == 21:
                hist +=1
                if hist > 3:
                   hist = 0
                if hist > 0:
                   nr = 1
                   samples = nr * navscale
                   auto_t = 1
                   nycle = 0
                   nstart = 1
                   Cwindow = 1
                else:
                   nr = 0
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
             if (use_Pi_Cam or (not use_Pi_Cam and Webcam == 0)) and camera_connected:
                rpired -=1
             else:
               saturation -=1
             if use_Pi_Cam and camera_connected:
                rpiredx = Decimal(rpired)/Decimal(100)
             elif not use_Pi_Cam and camera_connected and press == 0 and (Webcam == 0 or Webcam > 1):
                rpiredx = max(rpired, usb_min_rx)
                rpistr = "v4l2-ctl -c red_balance=" + str(rpiredx) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             elif not use_Pi_Cam and camera_connected and press == 0 and Webcam == 1:
                saturation = max(saturation, usb_min_sa)
                rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 14:
             if (use_Pi_Cam or (not use_Pi_Cam and Webcam == 0)) and camera_connected:
                rpired +=1
             else:
                saturation +=1
             if use_Pi_Cam and camera_connected:
                rpiredx = Decimal(rpired)/Decimal(100)
             elif not use_Pi_Cam and camera_connected and press == 0 and (Webcam == 0 or Webcam > 1):
                rpiredx = min(rpired, usb_max_rx)
                rpistr = "v4l2-ctl -c red_balance=" + str(rpiredx) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             elif not use_Pi_Cam and camera_connected and press == 0 and Webcam == 1:
                saturation = min(saturation, usb_max_sa)
                rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 5:
             if (use_Pi_Cam or (not use_Pi_Cam and Webcam == 0)) and camera_connected:
                rpiblue -=1
             else:
                color_temp -=100
             if use_Pi_Cam and camera_connected:
                rpibluex = Decimal(rpiblue)/Decimal(100)
             elif not use_Pi_Cam and camera_connected and press == 0 and (Webcam == 0 or Webcam > 1):
                rpibluex = max(rpiblue, usb_min_bx)
                rpistr = "v4l2-ctl -c blue_balance=" + str(rpibluex) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             elif not use_Pi_Cam and camera_connected and press == 0 and Webcam == 1:
                color_temp = max(color_temp, usb_min_ct)
                rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 15:
             if (use_Pi_Cam or (not use_Pi_Cam and Webcam == 0)) and camera_connected:
                rpiblue +=1
             else:
                color_temp +=100
             if use_Pi_Cam and camera_connected:
                rpibluex = Decimal(rpiblue)/Decimal(100)
             elif not use_Pi_Cam and camera_connected and press == 0 and (Webcam == 0 or Webcam > 1):
                rpibluex = min(rpiblue, usb_max_bx)
                rpistr = "v4l2-ctl -c blue_balance=" + str(rpibluex) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             elif not use_Pi_Cam and camera_connected and press == 0 and Webcam == 1:
                color_temp = min(color_temp, usb_max_ct)
                rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
                p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
             restart = 1
             change = 1
          elif z == 13 or kz == K_h:
             thres += 1
             if thres > 2:
                thres = 0
             change = 1
          elif z == 12 or kz == K_g:
             graph += 1
             if graph > 2:
                graph = 0
                if menu == 1:
                   pygame.draw.rect(windowSurfaceObj, blackColor, Rect(Disp_Width + 69, 9, 54, 269), 0)
                   pygame.display.update()
             change = 1
          elif z == 2 or kz == K_p:
             plot += 1
             if plot > 2:
                plot = 0
                if menu == 1:
                   pygame.draw.rect(windowSurfaceObj, blackColor, Rect(Disp_Width + 16, 9, 54, 269), 0)
                   pygame.display.update()
             change = 1
          elif z == 32 or kz == K_w:
             auto_win = not auto_win
             change = 1
          elif z == 33 or kz == K_t:
             auto_t = not auto_t
             if auto_t == 0 and threshold < 1:
                threshold = 1
             if esc1 > 0 and auto_t == 1:
                keys(0,str(int(a_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
             if esc1 > 0 and auto_t == 0:
                keys(0,str(int(m_thr_limit)),fs,2,b1x,bw,5,b1y, bh, 4, 3, 1)
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
             if (not use_Pi_Cam and Webcam == 0and zoom < usb_max_res + 2) or (not use_Pi_Cam and Webcam == 1 and zoom < usb_max_res + 1) or (use_Pi_Cam and Pi_Cam == 2 and zoom < 9) or (use_Pi_Cam and Pi_Cam == 1 and zoom < 7):
                zoom += 1
                if nr > 0:
                   mxq = []
                   mxp = []
                   mxo = []
                if camera_connected:
                   w = rpiwidth[zoom]
                   h = rpiheight[zoom]
                   if use_Pi_Cam:
                      scalex = rpiscalex[zoom]
                      scaley = rpiscaley[zoom]
                   else:
                      scalex = rpiscalex[usb_max_res - zoom + 2]
                      scaley = rpiscaley[usb_max_res - zoom + 2]

                   if Webcam == 0 and zoom == 3:
                      scalex = 1.25
                      scaley = 1.25
    
                   nscale /= scaley
                   escale /= scalex
                   sscale /= scaley
                   wscale /= scalex
                   offset5 = int((offset5 + offset3)*scalex)
                   offset6 = int((offset6 + offset4)*scaley)
                   if offset5 > 0 and offset5 >= w/2 - Disp_Width/2:
                      offset5 = w/2 - Disp_Width/2
                   if offset5 < 0 and offset5 <= Disp_Width/2 - w/2:
                      offset5 = Disp_Width/2 - w/2
                   if offset6 > 0 and offset6 >= h/2 - Disp_Height/2:
                      offset6 = h/2 - Disp_Height/2
                   if offset6 < 0 and offset6 <= Disp_Height/2 - h/2:
                      offset6 = Disp_Height/2 - h/2
                   offset3 = 0
                   offset4 = 0
                   if not zoom:
                      offset3 /= 2
                      offset4 /= 2
                if not camera_connected:
                   wd = 20 + zoom*4
                   hd = wd
                   posx =  (Disp_Width/2)-(wd/2)
                   posy = (Disp_Height/2)-(hd/2)
                   offset3 = 0
                   offset4 = 0
             restart = 1
             change = 1
          elif z == 45 or kz == K_q:
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if zoom > min_res and (use_Pi_Cam == 1 or (use_Pi_Cam ==0 and Webcam < 2)):
                zoom -= 1
                if nr > 0:
                   mxq = []
                   mxp = []
                   mxo = []
                if camera_connected:
                   w = rpiwidth[zoom]
                   h = rpiheight[zoom]
                   if use_Pi_Cam:
                      scalex = rpiscalex[zoom + 1]
                      scaley = rpiscalex[zoom + 1]
                   else:
                      scalex = rpiscalex[usb_max_res - zoom + 1]
                      scaley = rpiscaley[usb_max_res - zoom + 1]
                      
                   if Webcam == 0 and zoom == 3:
                      scalex = 1.25
                      scaley = 1.25
                      
                   nscale *= scaley
                   escale *= scalex
                   sscale *= scaley
                   wscale *= scalex
                   offset5 = int((offset5 + offset3)/scalex)
                   offset6 = int((offset6 + offset4)/scaley)
                   if offset5 > 0 and offset5 >= w/2 - Disp_Width/2:
                      offset5 = w/2 - Disp_Width/2
                   if offset5 < 0 and offset5 <= Disp_Width/2 - w/2:
                      offset5 = Disp_Width/2 - w/2
                   if offset6 > 0 and offset6 >= h/2 - Disp_Height/2:
                      offset6 = h/2 - Disp_Height/2
                   if offset6 < 0 and offset6 <= Disp_Height/2 - h/2:
                      offset6 = Disp_Height/2 - h/2
                   offset3 = 0
                   offset4 = 0
                   if not zoom:
                      offset3 /= 2
                      offset4 /= 2
                if not camera_connected:
                   wd = 20 + zoom*4
                   hd = wd
                   posx =  (Disp_Width/2)-(wd/2)
                   posy = (Disp_Height/2)-(hd/2)
                   offset3 = 0
                   offset4 = 0
             restart = 1
             change = 1
          elif z == 22 or kz == K_n or kz == K_d:
             nsi = not nsi
             change = 1

          elif z == 24:
             if switch == 0:
                Night = not Night
             switch = 0
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
             button(      b1x, 1,          b1y, 2,  bw, 2, bh, auto_g,0)
             button(      b1x, 3,          b1y, 2,  bw, 1, bh, hist,0)
             button(      b1x, 4,          b1y, 2,  bw, 1, bh, nr,0)
             button(      b1x, 1,          b1y, 3,  bw, 1, bh, plot,0)
             button(      b1x, 1,          b1y, 4,  bw, 1, bh, log,0)
             button(      b1x, 2,          b1y, 3,  bw, 1, bh, graph,0)
             button(      b1x, 2,          b1y, 4,  bw, 1, bh, thres,0)
             button(      b1x, 4,          b1y, 3,  bw, 1, bh, auto_win,0)
             button(      b1x, 4,          b1y, 4,  bw, 1, bh, auto_t,0)
             button(      b1x, 4,          b1y, 5,  bw, 1, bh, auto_i,0)
             button(      b1x, 3,          b1y, 3,  bw, 1, bh, nsi,0)
             button(      b1x, 3,          b1y, 4,  bw, 1, bh, ewi,0)
             button(      b1x, 3,          b1y, 6,  bw, 2, bh, 0,0)
             button(      b1x, 3,          b1y, 5,  bw, 1, bh, 0,0)
             for cy in range (2, 7):
                button(   b1x, 5,          b1y, cy, bw, 2, bh, 0,0)
                button(   b2x, 3,          b2y, cy, bw, 2, bh, 0,0)
             cy = 3
             for cy in range (3,7):
                button(   b2x, 1,          b2y, cy, bw, 2, bh, 0,0)
             button(      b1x, 1,          b1y, 5,  bw, 2, bh, 0,0)
             button(      b1x, 1,          b1y, 6,  bw, 2, bh, 0,0)
             button(      b2x, 1,          b2y, 2,  bw, 2, bh, 0,0)
             if photoon:
                button(   b2x, 5,          b2y, 2,  bw, 2, bh, 0,0)
                button(   b2x, 5,          b2y, 3,  bw, 2, bh, 0,0)
                button(   b2x, 5,          b2y, 4,  bw, 2, bh, 0,0)
             if use_Pi_Cam:
                button(   b2x, 5, b2y, 5, bw, 1, bh, 0,0)
             else:
                button(   b2x, 5, b2y, 5, bw, 1, bh, Auto_Gain,0)
             button(      b2x, 6,          b2y, 5,  bw, 1, bh, 0,0)
             button(      b2x, 6,          b2y, 6,  bw, 1, bh, con_cap,0)
             button(      b3x, 1,          b3y, 3,  bw, 1, bh, 0,0)
             button(      b3x, 1,          b3y, 2,  bw, 1, bh, decN,0)
             button(      b3x, 1,          b3y, 4,  bw, 1, bh, decS,0)
             button(      b3x, 2,          b3y, 2,  bw, 1, bh, 0,0)
             button(      b3x, 2,          b3y, 4,  bw, 1, bh, 0,0)
             #if decN:
             #   button(   b3x, 2,          b3y, 2,  bw, 1, bh, 0,0)
             #else:
             #   button(   b3x, 2,          b3y, 2,  bw, 1, bh, 1,0)
             #if decS:
             #   button(   b3x, 2,          b3y, 4,  bw, 1, bh, 0,0)
             #else:
             #   button(   b3x, 2,          b3y, 4,  bw, 1, bh, 1,0)
             button(      b3x, 3,          b3y, 3,  bw, 1, bh, 0,0)
             button(      b3x, 5,          b3y, 2,  bw, 1, bh, 0,0)
             button(      b3x, 5,          b3y, 4,  bw, 1, bh, 0,0)
             button(      b3x, 4,          b3y, 3,  bw, 1, bh, 0,0)
             button(      b3x, 6,          b3y, 3,  bw, 1, bh, 0,0)
             button(      b3x, 1,          b3y, 6,  bw, 1, bh, 0,0)
             button(      b3x, 2,          b3y, 6,  bw, 1, bh, 0,0)
             button(      b3x, 3,          b3y, 6,  bw, 1, bh, 0,0)
             if use_config > 0:
                button(   b3x, use_config, b3y, 6,  bw, 1, bh, 3,0)
             button(      b3x, 4,          b3y, 6,  bw, 1, bh, 0,0)
             button(      b3x, 5,          b3y, 6,  bw, 1, bh, 0,0)
             button(      b3x, 6,          b3y, 6,  bw, 1, bh, 0,0)
             if Display == 0 and menu == 0:
                button(   b3x, 6, b3y, 5, bw, 1, bh, 0,0)
             keys(0,str(int(nscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 2, 3, 0)
             keys(0,str(int(sscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 3, 3, 0)
             keys(0,str(int(escale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 4, 3, 0)
             keys(0,str(int(wscale)),           fs,   3,        b2x,         bw,   3,     b2y, bh, 5, 3, 0)
             keys(0,str(int(threshold)),        fs,   3,        b1x,         bw,   5,     b1y, bh, 4, 3, 0)
             keys(0,str(int(Interval)),         fs,   3,        b1x,         bw,   5,     b1y, bh, 5, 3, 0)
             keys(0,str(zoom),                  fs,   3,        b1x,         bw,   5,     b1y, bh, 6, 3, 0)
             keys(0,str(int(minc)),             fs,   3,        b1x,         bw,   3,     b1y, bh, 6, 3, 0)

             msg = rgb[rgbw]
             if rgbw < 5:
                keys(0,msg,                     fs,   rgbw+2,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
             else:
                keys(0,msg,                     fs,   rgbw+1,   b1x,         bw,   5,     b1y, bh, 2, 3, 0)
             if crop != maxwin:
                keys(0,str(crop),               fs,   3,        b1x,         bw, 5, b1y, bh, 3, 3, 0)
             else:
                keys(0,"max",                   fs,   3,        b1x,         bw, 5, b1y, bh, 3, 3, 0)
             keys(0,"AWin",                     fs-1, auto_win, b1x,         bw,   3,     b1y, bh, 3, 1, 0)
             keys(0,"W",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 3, 1, 0)
             keys(0,"AThr",                     fs-1, auto_t,   b1x,         bw,   3,     b1y, bh, 4, 1, 0)
             keys(0,"T",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 4, 1, 0)
             keys(0,"AutoG",                    fs,   auto_g,   b1x,         bw,   0,     b1y, bh, 2, 1, 0)
             keys(0,"A",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 2, 1, 0)
             if hist <= 2:
                keys(0,"Hist",                  fs,   hist,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
             else:
                keys(0,"2x2",                   fs,   hist,     b1x,         bw,   2,     b1y, bh, 2, 1, 0)
             keys(0,"Log",                      fs,   log,      b1x,         bw,   0,     b1y, bh, 4, 1, 0)
             keys(0,"L",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 4, 1, 0)
             keys(0,"Gph",                      fs,   graph,    b1x,         bw,   1,     b1y, bh, 3, 1, 0)
             keys(0,"G",                        fs,   5,        b1x,         bw,   1,     b1y, bh, 3, 1, 0)
             keys(0,"Plot",                     fs,   plot,     b1x,         bw,   0,     b1y, bh, 3, 1, 0)
             keys(0,"P",                        fs,   5,        b1x,         bw,   0,     b1y, bh, 3, 1, 0)
             keys(0,"Thr",                      fs,   thres,    b1x,         bw,   1,     b1y, bh, 4, 1, 0)
             keys(0,"h",                        fs,   5,        b1x+fs/1.5,  bw,   1,     b1y, bh, 4, 1, 0)
             keys(0,Dkey[12],                   fs,   nsi,      b1x,         bw,   2,     b1y, bh, 3, 1, 0)
             keys(0,Dkey[13],                   fs,   ewi,      b1x,         bw,   2,     b1y, bh, 4, 1, 0)
             if DKeys == 1:
                keys(0,"N",                     fs,   5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
                keys(0,"E",                     fs,   5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)
             else:
                keys(0,"D",                     fs,   5,        b1x,         bw,   2,     b1y, bh, 3, 1, 0)
                keys(0,"R",                     fs,   5,        b1x,         bw,   2,     b1y, bh, 4, 1, 0)
             keys(0,"AInt",                     fs-1, auto_i,   b1x,         bw,   3,     b1y, bh, 5, 1, 0)
             keys(0,"I",                        fs-1, 5,        b1x+fs/1.5,  bw,   3,     b1y, bh, 5, 1, 0)
             keys(0,"rgbw",                     fs,   6,        b1x,         bw,   4,     b1y, bh, 2, 0, 0)
             keys(0,"b",                        fs,   5,        b1x+fs,      bw,   4,     b1y, bh, 2, 0, 0)
             keys(0," <",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 2, 4, 0)
             keys(0,">",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 2, 4, 0)
             keys(0,"window",                   fs,   6,        b1x,         bw,   4,     b1y, bh, 3, 0, 0)
             keys(0," -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 3, 4, 0)
             keys(0,"+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 3, 4, 0)
             keys(0,"threshold",                fs-1, 6,        b1x,         bw,   4,     b1y, bh, 4, 0, 0)
             keys(0," -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 4, 4, 0)
             keys(0,"+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 4, 4, 0)
             keys(0,"interval",                 fs,   6,        b1x,         bw,   4,     b1y, bh, 5, 0, 0)
             keys(0," -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 5, 4, 0)
             keys(0,"+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 5, 4, 0)
             keys(0,"Zoom",                     fs,   6,        b1x,         bw,   4,     b1y, bh, 6, 0, 0)
             keys(0," -",                       fs,   6,        b1x,         bw,   4,     b1y, bh, 6, 4, 0)
             keys(0,"+",                        fs,   6,        b1x+bw-fs,   bw,   5,     b1y, bh, 6, 4, 0)
             keys(0,"Min Corr",                 fs,   6,        b1x,         bw,   2,     b1y, bh, 6, 0, 0)
             keys(0," -",                       fs,   6,        b1x,         bw,   2,     b1y, bh, 6, 4, 0)
             keys(0,"+",                        fs,   6,        b1x+bw-fs,   bw,   3,     b1y, bh, 6, 4, 0)
             keys(0,Dkey[8],                    fs-1, 6,        b2x,         bw,   2,     b2y, bh, 2, 0, 0)
             keys(0," -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 2, 4, 0)
             keys(0,"+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 2, 4, 0)
             keys(0,Dkey[9],                    fs-1, 6,        b2x,         bw,   2,     b2y, bh, 3, 0, 0)
             keys(0," -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 3, 4, 0)
             keys(0,"+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 3, 4, 0)
             keys(0,Dkey[11],                   fs,   6,        b2x,         bw,   2,     b2y, bh, 4, 0, 0)
             keys(0," -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 4, 4, 0)
             keys(0,"+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 4, 4, 0)
             keys(0,Dkey[10],                   fs,   6,        b2x,         bw,   2,     b2y, bh, 5, 0, 0)
             keys(0," -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 5, 4, 0)
             keys(0,"+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 5, 4, 0)
             keys(0,"scale all",                fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 0, 0)
             keys(0," -",                       fs,   6,        b2x,         bw,   2,     b2y, bh, 6, 4, 0)
             keys(0,"+",                        fs,   6,        b2x+bw-fs,   bw,   3,     b2y, bh, 6, 4, 0)
             if (use_Pi_Cam and camera_connected) or (not use_Pi_Cam and camera_connected):
                keys(0,"Brightness",            fs-2, 6,        b2x,         bw,   0,     b2y, bh, 2, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 2, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 2, 4, 0)
                keys(0,str(rpibr),              fs,   3,        b2x,         bw,   1,     b2y, bh, 2, 3, 0)
                keys(0,str(rpico),              fs,   3,        b2x,         bw,   1,     b2y, bh, 3, 3, 0)
                keys(0,"Contrast",              fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 3, 4, 0)
             if not use_Pi_Cam and camera_connected:
                keys(0,"Exposure",              fs-1,     6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
                keys(0," -",                    fs,       6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
                keys(0,"+",                     fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
                keys(0,str(exposure),           fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
                if Webcam == 0 :
                   keys(0,"Gamma",              fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
                   keys(0,str(gamma),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                   keys(0,"Adj Red",            fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
                   keys(0,"Adj Blue",           fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
                   keys(0,str(rpiredx),         fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
                   keys(0,str(rpibluex),        fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
                   keys(0,"Gain",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
                   keys(0,str(gain),            fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                elif Webcam == 1:
                   keys(0,"Sharpness",          fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
                   keys(0,str(sharpness),       fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                   keys(0,"Saturation",         fs-1,     6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
                   keys(0,"Color Temp",         fs-2,     6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
                   keys(0,str(saturation),      fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
                   keys(0,str(color_temp),      fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
                   keys(0,"Gain",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
                   keys(0,str(gain),            fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                elif Webcam > 1:
                   keys(0,"  eV",               fs-1,     6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
                   keys(0,str(rpiev),           fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                   keys(0,"Adj Red",            fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
                   keys(0,"Adj Blue",           fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
                   keys(0," -",                 fs,       6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
                   keys(0,"+",                  fs,       6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
                   keys(0,str(rpiredx),         fs,       3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
                   keys(0,str(rpibluex),        fs,       3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)
                   keys(0,"Exp Mode",           fs-1,     6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
                   keys(0," -",                 fs,       6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
                   keys(0,"+",                  fs,       6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
                   if scene_mode == 0:
                       keys(0,"None ",          fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                   else:
                       keys(0,"Night",          fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)

                
             if use_Pi_Cam and camera_connected:
                keys(0,str(rpico),              fs,   3,        b2x,         bw,   1,     b2y, bh, 3, 3, 0)
                rpiexa = rpimodesa[rpiexno]
                if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
                   keys(0,str(int(rpiss/1000)), fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
                else:
                   keys(0,str(int(rpiev)),      fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 0)
                keys(0,(rpimodesa[rpiexno]),    fs,   3,        b2x,         bw,   1,     b2y, bh, 5, 3, 0)
                keys(0,str(rpiISO),             fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                if not rpiISO:
                   keys(0,'auto',               fs,   3,        b2x,         bw,   1,     b2y, bh, 6, 3, 0)
                keys(0,"Contrast",              fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 3, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 3, 4, 0)
                if rpiex == 'off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
                   keys(0,"Exp Time",           fs-1, 6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
                else:
                   keys(0,"     eV",            fs,   6,        b2x,         bw,   0,     b2y, bh, 4, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 4, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 4, 4, 0)
                keys(0,"ISO",                   fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 6, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 6, 4, 0)
                keys(0,"Exp Mode",              fs-1, 6,        b2x,         bw,   0,     b2y, bh, 5, 0, 0)
                keys(0," <",                    fs,   6,        b2x,         bw,   0,     b2y, bh, 5, 4, 0)
                keys(0,">",                     fs,   6,        b2x+bw-fs,   bw,   1,     b2y, bh, 5, 4, 0)
                keys(0,"Adj Red",               fs,   6,        b1x,         bw,   0,     b1y, bh, 5, 0, 0)
                keys(0," -",                    fs,   6,        b1x,         bw,   0,     b1y, bh, 5, 4, 0)
                keys(0,"+",                     fs,   6,        b1x+bw-fs,   bw,   1,     b1y, bh, 5, 4, 0)
                keys(0,"Adj Blue",              fs,   6,        b1x,         bw,   0,     b1y, bh, 6, 0, 0)
                keys(0," -",                    fs,   6,        b1x,         bw,   0,     b1y, bh, 6, 4, 0)
                keys(0,"+",                     fs,   6,        b1x+bw-fs,   bw,   1,     b1y, bh, 6, 4, 0)
                if use_Pi_Cam:
                   rpiredx = Decimal(rpired)/Decimal(100)
                   rpibluex = Decimal(rpiblue)/Decimal(100)
                keys(0,str(rpiredx),            fs,   3,        b1x,         bw,   1,     b1y, bh, 5, 3, 0)
                keys(0,str(rpibluex),           fs,   3,        b1x,         bw,   1,     b1y, bh, 6, 3, 0)

             keys(0,Dkey[0],                    fs-1, 6,        b3x,         bw,   1,     b3y, bh, 2, 2, 0)
             keys(0,Dkey[2],                    fs,   6,        b3x,         bw,   2,     b3y, bh, 3, 2, 0)
             keys(0,Dkey[3],                    fs-1, 6,        b3x,         bw,   1,     b3y, bh, 4, 2, 0)
             keys(0,Dkey[1],                    fs,   6,        b3x,         bw,   0,    b3y, bh, 3, 2, 0)

             keys(0," Up",                      fs-1, 6,        b3x,         bw,   4,     b3y, bh, 2, 2, 0)
             keys(0,"Right",                    fs-2, 6,        b3x,         bw,   5,     b3y, bh, 3, 2, 0)
             keys(0,"Down",                     fs-2, 6,        b3x,         bw,   4,     b3y, bh, 4, 2, 0)
             keys(0,"Left",                     fs-2, 6,        b3x,         bw,   3,     b3y, bh, 3, 2, 0)

             keys(0,"Esc",                      fs,   5,        b3x,         bw,   2,     b3y, bh, 2, 2, 0)
             keys(0,"DEC",                      fs-1, decN,     b3x,         bw,   0,     b3y, bh, 2, 0, decN)
             keys(0,"  N",                      fs-1, decN,     b3x,         bw,   0,     b3y, bh, 2, 2, decN)
             keys(0,"nr",                       fs,   nr,       b1x,         bw,   3,     b1y, bh, 2, 1, nr)
             keys(0,"DEC",                      fs-1, decS,     b3x,         bw,   0,     b3y, bh, 4, 0, decS)
             keys(0,"  S",                      fs-1, decS,     b3x,         bw,   0,     b3y, bh, 4, 2, decS)
             keys(0," R1",                      fs,   6,        b3x,         bw,   0,     b3y, bh, 6, 1, 0)
             keys(0,"1",                        fs,   5,        b3x+fs,      bw,   0,     b3y, bh, 6, 1, 1)
             keys(0," R2",                      fs,   6,        b3x,         bw,   1,     b3y, bh, 6, 1, 0)
             keys(0,"2",                        fs,   5,        b3x+fs,      bw,   1,     b3y, bh, 6, 1, 0)
             keys(0," R3",                      fs,   6,        b3x,         bw,   2,     b3y, bh, 6, 1, 0)
             keys(0,"3",                        fs,   5,        b3x+fs,      bw,   2,     b3y, bh, 6, 1, 0)
             keys(0," S1",                      fs,   6,        b3x,         bw,   3,     b3y, bh, 6, 1, 0)
             keys(0," S2",                      fs,   6,        b3x,         bw,   4,     b3y, bh, 6, 1, 0)
             keys(0," S3",                      fs,   6,        b3x,         bw,   5,     b3y, bh, 6, 1, 0)
             if Display == 0 and menu == 0:
                keys(0,"Menu",                  fs-2, 6,        b3x,         bw,   5,     b3y, bh, 5, 1, 0)
             keys(0,"RELOAD cfg",               fs-2, 7,        b3x+bw/10,    bw,   0,     b3y, bh, 5, 4, 0)
             keys(0,"SAVE cfg",                 fs-2, 7,        b3x+bw/10,    bw,   3,     b3y, bh, 5, 4, 0)
             if Night:
                keys(0,"Day",                   fs-1, 6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
             else:
                keys(0,"Night",                 fs-1, 6,        b1x,         bw,   2,     b1y, bh, 5, 1, 0)
             keys(0,"TELESCOPE",                fs,   1,        b3x+bw/5,    bw,   0,     b3y-2, bh, 5, 0, 0)
             keys(0,"WINDOW",                   fs,   1,        b3x+bw/6,    bw,   3,     b3y-2, bh, 5, 0, 0)
             keys(0,"Stop",                     fs,   7,        b3x,         bw,   2,     b3y, bh, 4, 1, 0)
             keys(0,"cen",                      fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 0, 0)
             keys(0," tre",                     fs,   7,        b3x,         bw,   1,     b3y, bh, 3, 2, 0)
             keys(0,"cen",                      fs,   7,        b3x,         bw,   4,     b3y, bh, 3, 0, 0)
             keys(0," tre",                     fs,   7,        b3x,         bw,   4,     b3y, bh, 3, 2, 0)
             if menu == 0:
                keys(0,"con",                   fs-1, con_cap,  b2x,         bw,   5,     b2y, bh, 6, 0, 0)
                keys(0,"cap",                   fs,   con_cap,  b2x,         bw,   5,     b2y, bh, 6, 2, 0)
             else:
                keys(0,"constant",              fs-1, con_cap,  b2x,         bw,   5,     b2y, bh, 6, 0, 0)
                keys(0,"capture",               fs,   con_cap,  b2x,         bw,   5,     b2y, bh, 6, 2, 0)
             if use_Pi_Cam:
                if menu == 0:
                   keys(0,"pic",                fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 0, 0)
                   keys(0,"cap",                fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 2, 0)
                else:
                   keys(0,"picture",            fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 0, 0)
                   keys(0,"capture",            fs,   6,        b2x,         bw,   4,     b2y, bh, 5, 2, 0)
             if not use_Pi_Cam:
                keys(0,"Auto",                  fs,   Auto_Gain,b2x,         bw,   4,     b2y, bh, 5, 0, 0)
                keys(0,"Gain",                  fs,   Auto_Gain,b2x,         bw,   4,     b2y, bh, 5, 2, 0)      
             if menu == 0:
                keys(0,"Scr",                   fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
                keys(0,"cap",                   fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 2, 0)
             else:
                keys(0,"Screen",                fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)
                keys(0,"capture",               fs,   6,        b2x,         bw,   5,     b2y, bh, 5, 2, 0)
                
             keys(0,"S",                        fs,   5,        b2x,         bw,   5,     b2y, bh, 5, 0, 0)

             if photoon:
                button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
                keys(0,"PHOTO",                 fs,   photo,    b2x,         bw,   4,     b2y, bh, 2, 0, 0)
                keys(0,"O",                     fs,   5,        b2x+fs*1.5,  bw,   4,     b2y, bh, 2, 0, 0)
                keys(0,"P-Time",                fs,   6,        b2x,         bw,   4,     b2y, bh, 3, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   4,     b2y, bh, 3, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   5,     b2y, bh, 3, 4, 0)
                keys(0,str(ptime),              fs,   3,        b2x,         bw,   5,     b2y, bh, 3, 3, 0)
                keys(0,"P-Count",               fs,   6,        b2x,         bw,   4,     b2y, bh, 4, 0, 0)
                keys(0," -",                    fs,   6,        b2x,         bw,   4,     b2y, bh, 4, 4, 0)
                keys(0,"+",                     fs,   6,        b2x+bw-fs,   bw,   5,     b2y, bh, 4, 4, 0)
                keys(0,str(pcount),             fs,   3,        b2x,         bw,   5,     b2y, bh, 4, 3, 0)
             button(b2x, 5, b2y, 6, bw, 1, bh, cls,0)
             keys(0,"CLS",                      fs,   cls,      b2x,         bw,   4,     b2y, bh, 6, 1, 0)
             keys(0,"C",                        fs,   5,        b2x,         bw,   4,     b2y, bh, 6, 1, 0)
             if photo == 1:
                keys(1,str(pcount + 1 - pcount2),    fs, photo, b2x+ (bw/1.5),     bw, 4, b2y, bh, 2, 3, 1)
             if Display != 1 and menu == 0:
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 15, bh*10 + bh/3 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*10 + bh/3),      (Disp_Width + bw*3 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                                                                                 
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 5,  bh*10 + bh/3 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*10 + bh/3),      (Disp_Width + bw*5 + bw/4 + 10, bh*10 + bh/3),      2)
                                                                                                                                                 
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 5,  bh*12 + bh/3),      (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*5 + bw/4 + 15, bh*12 + bh/3 + 10), (Disp_Width + bw*5 + bw/4 + 10, bh*12 + bh/3 + 10), 2)
                                                                                                                                                    
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 15, bh*12 + bh/3),      (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width + bw*3 + bw/4 + 5,  bh*12 + bh/3 + 10), (Disp_Width + bw*3 + bw/4 + 10, bh*12 + bh/3 + 10), 2)
                
             if Display != 1 and menu == 1:
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 25,  bh*1 - bh/2),      (Disp_Width - bw*3 + bw/4 + 35, bh*1 - bh/2 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 25,  bh*1 - bh/2),      (Disp_Width - bw*3 + bw/4 + 25,  bh*1 - bh/2 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 25,  bh*1 - bh/2),      (Disp_Width - bw*3 + bw/4 + 30, bh*1 - bh/2),      2)
                                                                                                                                                 
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 35, bh*1 - bh/2),      (Disp_Width - bw*1 + bw/4 + 25,  bh*1 - bh/2 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 35, bh*1 - bh/2),      (Disp_Width - bw*1 + bw/4 + 35, bh*1 - bh/2 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 35, bh*1 - bh/2),      (Disp_Width - bw*1 + bw/4 + 30, bh*1 - bh/2),      2)
                                                                                                                                                 
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 25,  bh*3 - bh/2),      (Disp_Width - bw*1 + bw/4 + 35, bh*3 - bh/2 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 35, bh*3 - bh/2 + 10), (Disp_Width - bw*1 + bw/4 + 35, bh*3 - bh/2 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*1 + bw/4 + 35, bh*3 - bh/2 + 10), (Disp_Width - bw*1 + bw/4 + 30, bh*3 - bh/2 + 10), 2)
                                                                                                                                                    
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 35, bh*3 - bh/2),      (Disp_Width - bw*3 + bw/4 + 25,  bh*3 - bh/2 + 10), 2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 25,  bh*3 - bh/2 + 10), (Disp_Width - bw*3 + bw/4 + 25,  bh*3 - bh/2 + 5),  2)
                pygame.draw.line(windowSurfaceObj, greyColor, (Disp_Width - bw*3 + bw/4 + 25,  bh*3 - bh/2 + 10), (Disp_Width - bw*3 + bw/4 + 30, bh*3 - bh/2 + 10), 2)

                pygame.draw.rect(windowSurfaceObj, greyColor, Rect(736,416,64,32), 0)
                pygame.draw.rect(windowSurfaceObj, lgryColor, Rect(736,416,64,2), 0)
                pygame.draw.rect(windowSurfaceObj, lgryColor, Rect(736,416,1,32), 0)
                keys(0," FULL", 12, 6, 748, 0, 0, 416, 0, 0, 0, 0)
                keys(0,"Display", 12, 6, 748, 0, 0, 432, 0, 0, 0, 0)

             pygame.display.update()
             change = 1
          elif z == 23 or kz == K_e or kz == K_r:
             ewi = not ewi
             change = 1
          elif (z == 155 or z == 165 or z == 175 or kz == K_4 or kz == K_5 or kz == K_6):
             
             if use_Pi_Cam and camera_connected:
                os.killpg(p.pid, signal.SIGTERM)
             if kz == K_4 :
                z = 155
             elif kz == K_5:
                z = 165
             elif kz == K_6:
                z = 175
             deffile = "config" + str(int((z-145)/10))
             if z == 155:
                keys(0," S1",                   fs,   1,        b3x,         bw,   3,     b3y, bh, 6, 1, 1)
             elif z == 165:
                keys(0," S2",                   fs,   1,        b3x,         bw,   4,     b3y, bh, 6, 1, 1)
             elif z == 175:
                keys(0," S3",                   fs,   1,        b3x,         bw,   5,     b3y, bh, 6, 1, 1)
             timp = [str(int(auto_g)),str(int(nscale)),str(int(sscale)),str(int(escale)),str(int(wscale)),str(int(ewi)),str(int(nsi)),str(int(crop)),str(int(offset3)),str(int(offset5)),str(int(offset6)),
                     str(int(offset4)),str(int(Intervals)),str(int(log)),str(rgbw),str(int(threshold)),str(int(thres)),str(graph),str(int(auto_i)),str(plot),str(int(auto_win)),str(int(auto_t)),str(zoom),str(int(rpibr)),
                     str(int(rpico)),str(int(rpiev)),str(int(rpiss/1000)),str(int(rpiISO)),str(rpiexno),str(int(hist)),str(int(nr)),str(int(decN)),str(int(decS)),str(int(rpired)),str(int(rpiblue)),
                     str(int(pcount)),str(int(ptime)),str(camera_connected),str(serial_connected),str(use_Pi_Cam),str(use_RPiGPIO),str(photoon),str(use_Seeed),str(use_PiFaceRP),str(use_config),str(Display), 
                     str(int(Disp_Width)),str(Night),str(Image_window),str(usb_max_res),str(Frame),str(bho),str(bwo),str(int(N_OP)),str(int(E_OP)),str(int(S_OP)),str(int(W_OP)),str(int(C_OP)),str(int(AC_OP)),
                     str(rpineg),str(int(bits)),str(int(minc*10)),str(int(a_thr_limit)),str(int(m_thr_limit)),str(int(calibrate_time)),str(int(Cang)),str(int(exposure)),str(int(gain)),str(int(gamma)),
                     str(int(Auto_Gain)),str(int(sharpness)),str(int(saturation)),str(int(color_temp/10))]
             with open(deffile + '.txt', 'w') as f:
                for item in timp:
                   f.write("%s\n" % item)

             if z == 155:
                keys(0," S1", fs, 6, b3x, bw, 3, b3y, bh, 6, 1, 1)
             elif z == 165:
                keys(0," S2", fs, 6, b3x, bw, 4, b3y, bh, 6, 1, 1)
             elif z == 175:
                keys(0," S3", fs, 6, b3x, bw, 5, b3y, bh, 6, 1, 1)

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
             deffile = "config" + str(int((z-115)/10))
             if z == 125:
                keys(0," R1", fs, 1, b3x, bw, 0, b3y, bh, 6, 1, 1)
             elif z == 135:
                keys(0," R2", fs, 1, b3x, bw, 1, b3y, bh, 6, 1, 1)
             elif z == 145:
                keys(0," R3", fs, 1, b3x, bw, 2, b3y, bh, 6, 1, 1)
             if os.path.exists(deffile + ".txt"):
                configs = []
                with open(deffile + ".txt", "r") as file:
                   line = file.readline()
                   while line:
                      configs.append(line.strip())
                      line = file.readline()
                configs = list(map(int,configs))
                auto_g = configs[0]
                nscale = configs[1]
                sscale = configs[2]
                escale = configs[3]
                wscale = configs[4]
                ewi = configs[5]
                nsi = configs[6]
                crop = configs[7]
                offset3 = configs[8]
                offset5 = configs[9]
                offset6 = configs[10]
                offset4 = configs[11]
                Intervals = configs[12]
                log = configs[13]
                rgbw = configs[14]
                threshold = configs[15]
                thres = configs[16]
                graph = configs[17]
                auto_i = configs[18]
                plot = configs[19]
                auto_win = configs[20]
                auto_t = configs[21]
                zoom = configs[22]
                rpibr = configs[23]
                rpico = configs[24]
                rpiev = configs[25]
                rpiss = configs[26] * 1000
                rpiISO = configs[27]
                rpiexno = configs[28]
                hist = configs[29]
                nr = configs[30]
                decN = configs[31]
                decS = configs[32]
                rpired = configs[33]
                rpiblue = configs[34]
                pcount = configs[35]
                ptime = configs[36]
                camera_connected = configs[37]
                serial_connected = configs[38]
                use_Pi_Cam = configs[39]
                use_RPiGPIO = configs[40]
                photoon = configs[41]
                use_Seeed = configs[42]
                use_PiFaceRP = configs[43]
                use_config = configs[44]
                Display = configs[45]
                Disp_Width = configs[46]
                Night = configs[47]
                Image_window = configs[48]
                usb_max_res = configs[49]
                Frame = configs[50]
                bho = configs[51]
                bwo = configs[52]
                N_OP = configs[53]
                E_OP = configs[54]
                S_OP = configs[55]
                W_OP = configs[56]
                C_OP = configs[57]
                AC_OP = configs[58]
                rpineg = configs[59]
                bits = configs[60]
                minc = configs[61]/10
                a_thr_limit = configs[62]
                m_thr_limit = configs[63]
                calibrate_time = configs[64]
                Cang = configs[65]
                exposure = configs[66]
                gain = configs[67]
                gamma = configs[68]
                Auto_Gain = configs[69]
                sharpness = configs[70]
                saturation = configs[71]
                color_temp  = configs[72] * 10
                if Cwindow :
                   mmq, mask, change = MaskChange()
                   
             if z == 125:
                keys(0," R1", fs, 6, b3x,    bw, 0, b3y, bh, 6, 1, 1)
                keys(0,"1",   fs, 5, b3x+fs, bw, 0, b3y, bh, 6, 1, 1)
             elif z == 135:
                keys(0," R2", fs, 6, b3x,    bw, 1, b3y, bh, 6, 1, 1)
                keys(0,"2",   fs, 5, b3x+fs, bw, 1, b3y, bh, 6, 1, 1)
             elif z == 145:
                keys(0," R3", fs, 6, b3x,    bw, 2, b3y, bh, 6, 1, 1)
                keys(0,"3",   fs, 5, b3x+fs, bw, 2, b3y, bh, 6, 1, 1)
             restart = 1
             change = 1
          press = 0

   if change :
      change = 0
      if oldscene_mode != scene_mode:
          if scene_mode == 0:
              keys(0,"None ",      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
          else:
              keys(0,"Night",      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)  
          oldscene_mode = scene_mode
      if oldInterval != Interval:
         keys(0,str(int(Interval)), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
         oldInterval = Interval
      if oldphoto != photo and photoon:
         if photo == 0:
            button(b2x, 5, b2y, 2, bw, 2, bh, photo,0)
         keys(0,"PHOTO", fs, photo, b2x, bw, 4, b2y, bh, 2, 0, 1)
         keys(0,"O", fs, 5, b2x+fs*1.5, bw, 4, b2y, bh, 2, 0, 1)
         oldphoto = photo
      if oldcon_cap != con_cap:
         button(b2x, 6, b2y, 6, bw, 1, bh, con_cap,0)
         if menu == 0:
            keys(0,"con", fs-1, con_cap, b2x, bw, 5, b2y, bh, 6, 0, 1)
            keys(0,"cap", fs, con_cap, b2x, bw, 5, b2y, bh, 6, 2, 1)
         else:
            keys(0,"constant", fs-1, con_cap, b2x, bw, 5, b2y, bh, 6, 0, 1)
            keys(0,"capture", fs, con_cap, b2x, bw, 5, b2y, bh, 6, 2, 1)
         oldcon_cap = con_cap
      if oldauto_win != auto_win:
         button(b1x, 4, b1y, 3, bw, 1, bh, auto_win,0)
         keys(0,"AWin", fs-1, auto_win, b1x, bw, 3, b1y, bh, 3, 1, 1)
         keys(0,"W", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 3, 1, 1)
         oldauto_win = auto_win
      if oldauto_i != auto_i:
         button(b1x, 4, b1y, 5, bw, 1, bh, auto_i,0)
         keys(0,"AInt", fs-1, auto_i, b1x, bw, 3, b1y, bh, 5, 1, 1)
         keys(0,"I", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 5, 1, 1)
         oldauto_i = auto_i
      if oldnsi != nsi:
         button(b1x, 3, b1y, 3, bw, 1, bh, nsi,0)
         keys(0,Dkey[12], fs, nsi, b1x, bw, 2, b1y, bh, 3, 1, 1)
         if DKeys == 1:
            keys(0,"N", fs, 5, b1x, bw, 2, b1y, bh, 3, 1, 1)
         else:
            keys(0,"D", fs, 5, b1x, bw, 2, b1y, bh, 3, 1, 1)
         oldnsi = nsi
      if oldewi != ewi:
         button(b1x, 3, b1y, 4, bw, 1, bh, ewi,0)
         keys(0,Dkey[13], fs, ewi, b1x, bw, 2, b1y, bh, 4, 1, 1)
         if DKeys == 1:
            keys(0,"E", fs, 5, b1x, bw, 2, b1y, bh, 4, 1, 1)
         else:
            keys(0,"R", fs, 5, b1x, bw, 2, b1y, bh, 4, 1, 1)
         oldewi = ewi
      if oldauto_t != auto_t:
         button(b1x, 4, b1y, 4, bw, 1, bh, auto_t,0)
         keys(0,"AThr", fs-1, auto_t, b1x, bw, 3, b1y, bh, 4, 1, 1)
         keys(0,"T", fs-1, 5, b1x+fs/1.5, bw, 3, b1y, bh, 4, 1, 1)
         oldauto_t = auto_t
      if oldauto_g != auto_g:
         button(b1x, 1, b1y, 2, bw, 2, bh, auto_g,0)
         keys(0,"AutoG", fs, auto_g, b1x, bw, 0, b1y, bh, 2, 1, 1)
         keys(0,"A", fs, 5, b1x, bw, 0, b1y, bh, 2, 1, 1)
         oldauto_g = auto_g
      if oldlog != log:
         button(b1x, 1, b1y, 4, bw, 1, bh, log,0)
         keys(0,"Log", fs, log, b1x, bw, 0, b1y, bh, 4, 1, 1)
         keys(0,"L", fs, 5, b1x, bw, 0, b1y, bh, 4, 1, 1)
         oldlog = log
      if oldgraph != graph:
         button(b1x, 2, b1y, 3, bw, 1, bh, graph,0)
         keys(0,"Gph", fs, graph, b1x, bw, 1, b1y, bh, 3, 1, 1)
         keys(0,"G", fs, 5, b1x, bw, 1, b1y, bh, 3, 1, 1)
         oldgraph = graph
      if oldplot != plot:
         button(b1x, 1, b1y, 3, bw, 1, bh, plot,0)
         keys(0,"Plot", fs, plot, b1x, bw, 0, b1y, bh, 3, 1, 1)
         keys(0,"P", fs, 5, b1x, bw, 0, b1y, bh, 3, 1, 1)
         oldplot = plot
      if oldthres != thres:
         button(b1x, 2, b1y, 4, bw, 1, bh, thres,0)
         keys(0,"Thr", fs, thres, b1x, bw, 1, b1y, bh, 4, 1, 1)
         keys(0,"h", fs, 5, b1x+fs/1.5, bw, 1, b1y, bh, 4, 1, 1)
         oldthres = thres
      if oldptime != ptime and photoon:
         keys(0,str(ptime), fs, 3, b2x, bw, 5, b2y, bh, 3, 3, 1)
         oldptime = ptime
      if oldpcount != pcount and photoon:
         keys(0,str(pcount), fs, 3, b2x, bw, 5, b2y, bh, 4, 3, 1)
         oldpcount = pcount
      if oldnscale != nscale:
         keys(0,str(int(nscale)), fs, 3, b2x, bw, 3, b2y, bh, 2, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldnscale = nscale
      if oldsscale != sscale:
         keys(0,str(int(sscale)), fs, 3, b2x, bw, 3, b2y, bh, 3, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldsscale = sscale
      if oldescale != escale:
         keys(0,str(int(escale)), fs, 3, b2x, bw, 3, b2y, bh, 4, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldescale = escale
      if oldwscale != wscale:
         keys(0,str(int(wscale)), fs, 3, b2x, bw, 3, b2y, bh, 5, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldwscale = wscale
      if oldthreshold != threshold and esc1 == 0:
         keys(0,str(int(threshold)), fs, 3, b1x, bw, 5, b1y, bh, 4, 3, 1)
         oldthreshold = threshold
      if oldInterval != Interval:
         keys(0,str(int(Interval)), fs, 3, b1x, bw, 5, b1y, bh, 5, 3, 1)
      if oldrpired != rpired :
         if use_Pi_Cam == 1 or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1)):
            keys(0,str(rpiredx), fs, 3, b1x, bw, 1, b1y, bh, 5, 3, 1)
         if not use_Pi_Cam  and (Webcam == 0 or Webcam > 1)  and camera_connected:
            rpistr = "v4l2-ctl -c red_balance=" + str(rpired) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldrpired = rpired
      if oldrpiblue != rpiblue :
         if use_Pi_Cam == 1 or (not use_Pi_Cam and (Webcam == 0 or Webcam > 1)):
            keys(0,str(rpibluex), fs, 3, b1x, bw, 1, b1y, bh, 6, 3, 1)
         if not use_Pi_Cam and (Webcam == 0 or Webcam > 1) and camera_connected:
            rpistr = "v4l2-ctl -c blue_balance=" + str(rpiblue) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldrpiblue = rpiblue
      if oldsaturation != saturation :
         if not use_Pi_Cam and Webcam == 1 and camera_connected:
               keys(0,str(saturation), fs, 3, b1x, bw, 1, b1y, bh, 5, 3, 1)
               rpistr = "v4l2-ctl -c saturation=" + str(saturation) + " -d " + str(dve)
               p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldsaturation = saturation
      if oldcolor_temp != color_temp :
         if not use_Pi_Cam and Webcam == 1 and camera_connected:
            keys(0,str(color_temp), fs, 3, b1x, bw, 1, b1y, bh, 6, 3, 1)
            rpistr = "v4l2-ctl -c white_balance_temperature=" + str(color_temp) + " -d " + str(dve)
            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldcolor_temp = color_temp
      if oldzoom != zoom:
         keys(0,str(zoom), fs, 3, b1x, bw, 5, b1y, bh, 6, 3, 1)
         if esc1 ==0:
            oldzoom = zoom
      if oldrgbw != rgbw:
         msg = rgb[rgbw]
         if rgbw < 5:
            keys(0,msg, fs, rgbw + 2, b1x, bw, 5, b1y, bh, 2, 3, 1)
         else:
            keys(0,msg, fs, rgbw + 1, b1x, bw, 5, b1y, bh, 2, 3, 1)
         oldrgbw = rgbw
      if oldcrop != crop:
         if crop != maxwin:
            keys(0,str(crop), fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)
         else:
            keys(0,"max", fs, 3, b1x, bw, 5, b1y, bh, 3, 3, 1)
         oldcrop = crop
      if oldrpibr != rpibr and camera_connected:
         keys(0,str(rpibr), fs, 3, b2x, bw, 1, b2y, bh, 2, 3, 1)
         oldrpibr = rpibr
      if oldrpico != rpico and camera_connected :
         keys(0,str(rpico), fs, 3, b2x, bw, 1, b2y, bh, 3, 3, 1)
         oldrpico = rpico
      if oldrpiss != rpiss and camera_connected and use_Pi_Cam:
         keys(0,str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         oldrpiss = rpiss
      if oldrpiexno != rpiexno:
         rpiexa = rpimodesa[rpiexno]
         keys(0,(rpimodesa[rpiexno]), fs, 3, b2x, bw, 1, b2y, bh, 5, 3, 1)
         if rpimodes[rpiexno] != "off":
            keys(0,str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         else:
            keys(0,str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa== 'vlon2' or rpiexa == 'spor2':
            keys(0,"Exp Time", fs-1, 6, b2x, bw, 0, b2y, bh, 4, 0, 1)
         else:
            keys(0,"     eV", fs, 6, b2x, bw, 0, b2y, bh, 4, 0, 1)
         if rpiexa == ' off' or rpiexa == 'nigh2' or rpiexa == 'fwor2' or rpiexa == 'vlon2' or rpiexa == 'spor2':
            keys(0,str(int(rpiss/1000)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         else:
            keys(0,str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         keys(0,(rpimodesa[rpiexno]), fs, 3, b2x, bw, 1, b2y, bh, 5, 3, 1)
         oldrpiexno = rpiexno
      if oldrpiISO != rpiISO and camera_connected and use_Pi_Cam:
         keys(0,str(rpiISO), fs, 3, b2x, bw, 1, b2y, bh, 6, 3, 1)
         if not rpiISO:
            keys(0,'auto', fs, 3, b2x, bw, 1, b2y, bh, 6, 3, 1)
         oldrpiISO = rpiISO
      if oldrpiev != rpiev and camera_connected and use_Pi_Cam:
         keys(0,str(int(rpiev)), fs, 3, b2x, bw, 1, b2y, bh, 4, 3, 1)
         oldrpiev = rpiev
      if oldrpiev != rpiev and camera_connected and not use_Pi_Cam and Webcam > 1:
         keys(0,str(rpiev),            fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         rpistr = "v4l2-ctl -c auto_exposure_bias=" + str(rpiev + 12) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldrpiev = rpiev
         
      if oldhist != hist:
         button(b1x, 3, b1y, 2, bw, 1, bh, hist,0)
         if hist <= 2:
            keys(0,"Hist", fs, hist, b1x, bw, 2, b1y, bh, 2, 1, 1)
         else:
            keys(0,"2x2", fs, hist, b1x, bw, 2, b1y, bh, 2, 1, 1)
            
         oldhist = hist
      if oldnr != nr:
         samples = nr * navscale
         button(b1x, 4, b1y, 2, bw, 1, bh, nr,0)
         keys(0,"nr", fs, nr, b1x, bw, 3, b1y, bh, 2, 1, 1)
         oldnr = nr
      if olddecN != decN:
         button(b3x, 1, b3y, 2, bw, 1, bh, decN,0)
         keys(0,"DEC", fs-1, decN, b3x, bw, 0, b3y, bh, 2, 0, 1)
         keys(0,"  N", fs-1, decN, b3x, bw, 0, b3y, bh, 2, 2, 1)
         olddecN = decN
      if olddecS != decS:
         button(b3x, 1, b3y, 4, bw, 1, bh, decS,0)
         keys(0,"DEC", fs-1, decS, b3x, bw, 0, b3y, bh, 4, 0, 1)
         keys(0,"  S", fs-1, decS, b3x, bw, 0, b3y, bh, 4, 2, 1)
         olddecS = decS
      if oldcls != cls:
         button(b2x, 5, b2y, 6, bw, 1, bh, cls,0)
         keys(0,"CLS", fs, cls, b2x, bw, 4, b2y, bh, 6, 1, 1)
         keys(0,"C",   fs, 5, b2x, bw, 4, b2y, bh, 6, 1, 1)
         oldcls = cls
      if oldminc != minc:
         keys(0,str(minc),                fs,       3,        b1x,         bw,   3,     b1y, bh, 6, 3, 1)
         mincor = int(Decimal(minc)* Decimal((nscale + sscale + wscale + escale)/4))
         oldminc = minc
      if oldexposure != exposure and not use_Pi_Cam:
         exposure = int (exposure)
         keys(0,str(exposure), fs,       3,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
         if Webcam == 0 and camera_connected:
            rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
         elif Webcam == 1 and camera_connected:
            rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
         elif Webcam > 1 and camera_connected:
            rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldexposure = exposure
      if oldgain != gain and not use_Pi_Cam and camera_connected:
         gain = int(gain)
         keys(0,str(gain),     fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
         rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldgain = gain
      if oldgamma != gamma and not use_Pi_Cam and Webcam == 0 and camera_connected:
         keys(0,str(gamma),    fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         rpistr = "v4l2-ctl -c gamma=" + str(gamma) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldgamma = gamma
      if oldsharpness != sharpness and not use_Pi_Cam and Webcam == 1 and camera_connected:
         keys(0,str(sharpness),    fs,       3,        b2x,         bw,   1,     b2y, bh, 6, 3, 1)
         rpistr = "v4l2-ctl -c sharpness=" + str(sharpness) + " -d " + str(dve)
         p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
         oldsharpness = sharpness
      if oldAuto_Gain != Auto_Gain:
         if not use_Pi_Cam and camera_connected:
            button(b2x, 5, b2y, 5, bw, 1, bh, Auto_Gain,0)
            keys(0,"Auto",fs,Auto_Gain,b2x,bw,4,b2y, bh, 5, 0, 1)
            keys(0,"Gain",fs,Auto_Gain,b2x,bw,4,b2y, bh, 5, 2, 1)
            if Auto_Gain == 1:
               keys(0,str(exposure),fs,0,b2x,bw,1,     b2y, bh, 4, 3, 1)
               if Webcam < 2:
                  keys(0,str(gain),fs,0,b2x,bw,1,     b2y, bh, 5, 3, 1)
               if Webcam == 0:
                  rpistr = "v4l2-ctl -c gain_automatic=1" + " -d " + str(dve)
               if Webcam == 1:
                  rpistr = "v4l2-ctl -c exposure_auto=3" + " -d " + str(dve)
               if Webcam > 1:
                  rpistr = "v4l2-ctl -c auto_exposure=0" + " -d " + str(dve)
               p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
            else:
               if Webcam == 0:
                  rpistr = "v4l2-ctl -c gain_automatic=0" + " -d " + str(dve)
               if Webcam == 1:
                  rpistr = "v4l2-ctl -c exposure_auto=1" + " -d " + str(dve)
               if Webcam > 1:
                  rpistr = "v4l2-ctl -c auto_exposure=1" + " -d " + str(dve)
               p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                
               if exposure > 0:   
                  exposure -=10
                  if Webcam == 0:
                     rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
                  if Webcam == 1:
                     rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
                  if Webcam > 1:
                     rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
                  p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
               exposure +=10
               if Webcam == 0:
                  rpistr = "v4l2-ctl -c exposure=" + str(exposure) + " -d " + str(dve)
               if Webcam == 1:
                  rpistr = "v4l2-ctl -c exposure_absolute=" + str(exposure) + " -d " + str(dve)
               if Webcam > 1:
                     rpistr = "v4l2-ctl -c exposure_time_absolute=" + str(exposure) + " -d " + str(dve)
               p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
               if Webcam < 2:
                  if gain > 0:
                     gain -=1
                     rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
                     p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                  gain +=1
                  rpistr = "v4l2-ctl -c gain=" + str(gain) + " -d " + str(dve)
                  p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
               if scene_mode == 0:
                  keys(0,"None ",      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
               else:
                  keys(0,"Night",      fs,       3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
               if scene_mode == 0:
                  keys(0,str(exposure), fs,   3,        b2x,         bw,   1,     b2y, bh, 4, 3, 1)
               if Webcam < 2:
                  keys(0,str(gain),     fs,   3,        b2x,         bw,   1,     b2y, bh, 5, 3, 1)
         oldAuto_Gain = Auto_Gain
       
   # restart Pi_Cam subprocess
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
      off5 = max(off5,0)
      off6 = (Decimal(0.5) - (Decimal(height)/Decimal(2))/Decimal(h)) + (Decimal(offset6)/Decimal(h))
      off6 = max(off6,0)
      widx =  Decimal(width)/Decimal(w)
      heiy = Decimal(height)/Decimal(h)
      rpistr += " -w " + str(width) + " -h " + str(height) + " -roi " + str(off5) + "," + str(off6) + ","+str(widx) + "," + str(heiy)#
      if rpineg:
         rpistr += " -ifx negative "
      p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
      restart = 0

