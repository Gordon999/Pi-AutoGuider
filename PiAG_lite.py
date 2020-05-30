#!/usr/bin/env python3
import threading, queue
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import math
import cv2
import numpy as np
import pygame
from pygame.locals import *
import os

# v0.2

# set default parameters
crop        = 90      # size of detection window *
threshold   = 0       # 0 = auto *
scale       = 100     # mS/pixel *
fps         = 12      # set camera fps *
mode        = 2       # set camera mode ['off',  'auto', 'night', 'sports', 'verylong', 'fireworks'] *
speed       = 80000   # mS x 1000 *
ISO         = 0       # 0 = auto or 100,200,400,800 *
brightness  = 50      # set camera brightness *
contrast    = 50      # set camera contrast *
Night       = 0       # 0 = off, 1 = ON *
Auto_G      = 0       # 0 = off, 1 = ON *
min_corr    = 100     # mS, no guiding correction applied below this *
interval    = 10      # Interval between corrections in Frames *
InvRA       = 0       # set to 1 to invert RA comands eg E<>W *
InvDEC      = 0       # set to 1 to invert DEC comands eg N<>S *
preview     = 0       # show detected star pixels *
c_mask      = 1       # set to 1 for circular window
use_RPiGPIO = 1       # set to 1 if using GPIO outputs for control

# * user adjustable within script whilst running

# check PiAGconfig.txt exists, if not then write default values
if not os.path.exists('PiAGconfig.txt'):
    points = [crop,threshold,scale,fps,mode,speed,ISO,brightness,contrast,Night,Auto_G,min_corr,interval,InvRA,InvDEC,preview,c_mask,use_RPiGPIO]
    with open('PiAGconfig.txt', 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read PiAGconfig.txt
config = []
with open("PiAGconfig.txt", "r") as file:
   line = file.readline()
   while line:
      config.append(line.strip())
      line = file.readline()
config = list(map(int,config))

crop        = config[0]
threshold   = config[1]
scale       = config[2]
fps         = config[3]
mode        = config[4]
speed       = config[5]
ISO         = config[6]
brightness  = config[7]
contrast    = config[8]
Night       = config[9]
Auto_G      = config[10]
min_corr    = config[11]
interval    = config[12]
InvRA       = config[13]
InvDEC      = config[14]
preview     = config[15]
c_mask      = config[16]
use_RPiGPIO = config[17]


# set variables
width = 1920
height = 1088
a = 320
b = 181
br = 50
co = 0
w = 960
h = 544
xo = 0
yo = 0
zoom = 2
frames = 0
correct = ":Mgn0000:Mge0000"
RAstr =""
DECstr=""
RAon = 1
DECon = 1
serial_connected = 0

#import serial
if os.path.exists('/dev/ttyACM0') == True:
    import serial
    ser = serial.Serial('/dev/ttyACM0', 9600)
    serial_connected = 1
elif os.path.exists('/dev/ttyACM1') == True:
    import serial
    ser = serial.Serial('/dev/ttyACM1', 9600)
    serial_connected = 1

#Telescope control GPIO 'physical/BOARD' pins
N_OP         =       22 # 22
S_OP         =       18 # 18
E_OP         =       24 # 24
W_OP         =       16 # 16

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
   GPIO.output(E_OP, GPIO.LOW)
   GPIO.output(W_OP, GPIO.LOW)
   GPIO.output(S_OP, GPIO.LOW)
   GPIO.output(N_OP, GPIO.LOW)


#===================================================================================
# Generate mask for Circular window
#===================================================================================
if not os.path.exists('/run/shm/CMask.bmp'):
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
mask = pygame.image.load('/run/shm/CMask.bmp')
  
x = int(width/2) - a
y = int(height/2) - b

pygame.init()
windowSurfaceObj = pygame.display.set_mode((800, 480), 0, 24)
pygame.display.set_caption('Pi-AutoGuider Lite')

modes =  ['off',  'auto', 'night', 'sports', 'verylong', 'fireworks']
widths = [640, 800, 960, 1280, 1620, 1920, 2592, 3280]
scales = [1, 1.25, 1.5, 2, 2.531, 3, 4.047, 5.125]
scalex = int(scale / scales[zoom])

global greyColor, redColor, greenColor, blueColor, dgryColor, lgryColor, blackColor, whiteColor, purpleColor, yellowColor
bredColor =   pygame.Color(255,   0,   0)
lgryColor =   pygame.Color(192, 192, 192)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color( 50,  20,  20) if Night else pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128,  70,  70) if Night else pygame.Color(128, 128, 128)
dgryColor =   pygame.Color(  0,   0,   0) if Night else pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 128,   0) if Night else pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(128,   0, 128) if Night else pygame.Color(255,   0, 255)
yellowColor = pygame.Color(128, 128,   0) if Night else pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 150) if Night else pygame.Color(  0,   0, 255)
redColor =    pygame.Color(250,   0,   0) if Night else pygame.Color(200,   0,   0)


def button(col,row, bColor):
   colors = [greyColor, dgryColor, dgryColor, dgryColor, yellowColor]
   Color = colors[bColor]
   bx = 640 + (col * 80)
   by = row * 40
   pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,79,40))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx,by),(bx+80,by))
   pygame.draw.line(windowSurfaceObj,greyColor,(bx+79,by),(bx+79,by+40))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx,by),(bx,by+39))
   pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+39),(bx+79,by+39))
   pygame.display.update(bx, by, 80, 40)
   return

def text(col,row,fColor,top,upd,msg,fsize,bcolor):
   colors =  [dgryColor, greenColor, yellowColor, redColor, greenColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   Color  =  colors[fColor]
   bColor =  colors[bcolor]
   
   bx = 640 + (col * 80)
   by = row * 40
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj =       pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj =       pygame.font.Font(None, int(fsize))
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj =    msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+1,70,20))
       msgRectobj.topleft = (bx + 5, by + 3)
   else:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+29,by+18,51,21))
       msgRectobj.topleft = (bx + 29, by + 18)
       
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1:
      pygame.display.update(bx, by, 80, 40)

for c in range(0,2):
    for d in range(0,10):
        button(c,d,0)

text(0,7,2,0,1,"Crop",14,7)
text(0,7,3,1,1,str(crop),18,7)
text(1,0,2,0,1,"Threshold",14,7)
if threshold > 0:
    text(1,0,3,1,1,str(threshold),18,7)
else:
   text(1,0,3,1,1,"Auto",18,7)
text(0,1,2,0,1,"Zoom",14,7)
text(0,1,3,1,1,str(zoom),18,7)
text(1,7,2,0,1,"mS/pixel",14,7)
text(1,7,3,1,1,str(scalex),18,7)
text(0,2,5,0,1,"FPS",14,7)
text(0,2,3,1,1,str(fps),18,7)
text(1,2,5,0,1,"Mode",14,7)
text(1,2,3,1,1,modes[mode],18,7)
text(0,3,5,0,1,"Shutter mS",14,7)
text(0,3,3,1,1,str(int(speed/1000)),18,7)
text(1,3,5,0,1,"ISO",14,7)
if ISO != 0:
    text(1,3,3,1,1,str(ISO),18,7)
else:
   text(1,3,3,1,1,"Auto",18,7)
text(0,4,5,0,1,"Brightness",14,7)
text(0,4,3,1,1,str(brightness),18,7)
text(1,4,5,0,1,"Contrast",14,7)
text(1,4,3,1,1,str(contrast),18,7)
text(0,5,2,0,1,"RA offset",14,7)
text(0,5,3,1,1,str(xo),18,7)
text(1,5,2,0,1,"DEC offset",14,7)
text(1,5,3,1,1,str(yo),18,7)
text(0,6,2,0,1,"Min'm Corr",14,7)
text(0,6,3,1,1,str(min_corr),18,7)
text(1,6,2,0,1,"Interval",14,7)
text(1,6,3,1,1,str(interval),18,7)
if Auto_G == 0:
    button(0,0,0)
    text(0,0,9,0,1,"AUTO",15,7)
    text(0,0,9,1,1,"GUIDE",15,7)
else:
    button(0,0,1)
    text(0,0,1,0,1,"AUTO",15,0)
    text(0,0,1,1,1,"GUIDE",15,0)
if preview == 1:
    button(1,1,1)
    text(1,1,1,0,1,"Preview",14,0)
    text(1,1,1,1,1,"Threshold",13,0)
else:
    button(1,1,0)
    text(1,1,0,0,1,"Preview",14,7)
    text(1,1,0,1,1,"Threshold",13,7)
   
text(0,8,0,0,1,"Invert RA",14,7)
text(1,8,0,0,1,"Invert DEC",14,7)
text(0,9,1,0,1,"RA ON",14,7)
text(1,9,1,0,1,"DEC ON",14,7)

# initialize the camera 
camera = PiCamera()
camera.resolution = (width, height)
camera.iso = ISO
camera.shutter_speed = speed
camera.exposure_mode = modes[mode]
camera.framerate = fps
camera.brightness = brightness
camera.contrast = contrast
camera.hflip = True
rawCapture = PiRGBArray(camera, size=(width, height))
time.sleep(2)
camera.shutter_speed = speed
w = widths[zoom]
h = int(w/1.7647)
x = int((w/2) - 320 + xo)
y = int((h/2) - 181 + yo)
dim = (w, h)

def lx200(RAstr,DECstr):
   if serial_connected:
      ser.write(bytes(RAstr.encode('ascii')))
      time.sleep(0.1)
      ser.write(bytes(DECstr.encode('ascii')))
   return

def func1(correct,q):
  global use_RPiGPIO,serial_connected,preview,RAon,DECon,mask,frames,widths,modes,scale,ISO,speed,fps,brightness,contrast
  global width,height,zoom,xo,yo,b,crop,a,x,y,w,h,dim,threshold,InvRA,InvDEC,scalex,scale,Auto_G,RAstr,DECstr,min_corr,Night
  global mode,interval
  for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frames +=1
    image = frame.array
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    cropped = resized[y:y+362,x:x+640]
    crop2 = cropped[(0-b)-crop:(0-b)+crop,a-crop:a+crop]
    gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
    if c_mask == 1:
        smask = pygame.transform.scale(mask, [crop*2, crop*2])
        img = pygame.surfarray.array3d(smask)
        new_img = img[:, :, 0]
        new_img[new_img > 50] = 1
        gray = gray * new_img
    min_p = np.min(gray)
    max_p = np.max(gray)
    if threshold > 0:
        threshold2 = threshold
    else:
        threshold2 = ((max_p - min_p) + min_p) *.66
    gray[gray <  threshold2] = 0
    gray[gray >= threshold2] = 1
    if preview == 1:
        gray2 = gray *255
        backtorgb = cv2.cvtColor(gray2,cv2.COLOR_GRAY2RGB)
        backtorgb[:, :, 2:] = 0
        imagep = pygame.surfarray.make_surface(backtorgb)
        imagep = pygame.transform.rotate(imagep,90)
    ttot = np.sum(gray)
    column_sums = gray.sum(axis=0)
    row_sums = gray.sum(axis=1)
    acorrect = 0
    atot = 0
    while atot < int(ttot/2):
      atot += column_sums[acorrect]
      acorrect +=1
    bcorrect = 0
    btot = 0
    while btot < int(ttot/2):
      btot += row_sums[bcorrect]
      bcorrect +=1
    acorrect -= int(crop)
    bcorrect -= int(crop)
    if InvRA == 1:
       acorrect = 0 - acorrect
    if InvDEC == 1:
       bcorrect = 0 - bcorrect
    pygame.draw.rect(windowSurfaceObj, (0,0,0), Rect(640,440,160,24), 0)
    update = 0
    RAstr  = ":Mge0000"
    DECstr = ":Mgn0000"
    if abs(acorrect) > min_corr/scalex and ttot > 10 and (max_p - min_p) > 90 and ttot < (crop * crop)/2 and RAon == 1:
        if acorrect < 0:
            RAstr = ":Mge" + ("0000" + str(int(abs(acorrect) * scalex)))[-4:]
        else:
            RAstr = ":Mgw" + ("0000" + str(int(acorrect * scalex)))[-4:]
        if Auto_G == 1:
            text(0,11,1,0,1,RAstr,14,8)
        else:
            text(0,11,9,0,1,RAstr,14,8)
        update = 1
  
    if abs(bcorrect) > min_corr/scalex  and ttot > 10 and (max_p - min_p) > 90 and ttot < (crop * crop)/2 and DECon == 1:
        if bcorrect < 0:
            DECstr = ":Mgn" + ("0000" + str(int(abs(bcorrect) * scalex)))[-4:]
        else:
            DECstr = ":Mgs" + ("0000" + str(int(bcorrect * scalex)))[-4:]
        if Auto_G == 1:
            text(1,11,1,0,1,DECstr,14,8)
        else:
            text(1,11,9,0,1,DECstr,14,8)
        update = 1

    correct = RAstr+DECstr
    if frames > interval and update == 1 and Auto_G == 1:
        q.put(correct)
        r.put(correct)
        if serial_connected:
           lx200(RAstr,DECstr)
        frames = 0
    imagez = pygame.surfarray.make_surface(cropped)
    imagez = pygame.transform.rotate(imagez,90)
    windowSurfaceObj.blit(imagez, (0, 0))
    if preview == 1:
        imagep.set_colorkey(0, pygame.RLEACCEL)
        windowSurfaceObj.blit(imagep, (a-crop,b-crop))
    if RAon == 1:
        pygame.draw.rect(windowSurfaceObj, (200,200,200), Rect(a - crop,b - int(min_corr/scalex) ,crop*2,2*int(min_corr/scalex)), 1)
    if DECon == 1:
        pygame.draw.rect(windowSurfaceObj, (200,200,200), Rect(a  - int(min_corr/scalex),b - crop ,2*int(min_corr/scalex),crop*2), 1)
    if c_mask == 1:
        pygame.draw.circle(windowSurfaceObj,(0,255,0), (a,b),crop,2)
    else:
        pygame.draw.rect(windowSurfaceObj, (0,255,0), Rect(a  - crop,b - crop ,crop*2,crop*2), 2)
    if ttot > 10 and (max_p - min_p) > 90 and ttot < (crop * crop)/2:
        if Auto_G == 1:
            pygame.draw.rect(windowSurfaceObj, (255,0,0), Rect(a + acorrect-2,b - bcorrect-2,4,4), 1)
        else:
            pygame.draw.rect(windowSurfaceObj, (255,0,255), Rect(a + acorrect-2,b - bcorrect-2,4,4), 1)
    pygame.display.update()
    rawCapture.truncate(0)

    for event in pygame.event.get():
       if event.type == QUIT:
           pygame.quit()

       elif (event.type == MOUSEBUTTONUP):
           mousex, mousey = event.pos
           if mousex > crop and mousex < (640-crop) and mousey > crop and mousey < (362-crop):
               a = mousex
               b = mousey
           if mousex > 640:
               e = int((mousex-640)/40)
               f = int(mousey/40)
               g = (f*4) + e
               if g == 29:
                   crop +=1
                   crop = min(crop,180)
                   if a-crop < 1 or b-crop < 1 or a+crop > 640 or b+crop > 360:
                      crop -=1
                   text(0,7,3,1,1,str(crop),18,7)
               elif g == 28:
                   crop -=1
                   crop = max(crop,10)
                   text(0,7,3,1,1,str(crop),18,7)
               elif g == 3:
                   threshold +=1
                   threshold = min(threshold,255)
                   if threshold > 0:
                       text(1,0,3,1,1,str(threshold),18,7)
                   else:
                       text(1,0,3,1,1,"Auto",18,7)
               elif g == 2:
                   threshold -=1
                   threshold = max(threshold,0)
                   if threshold > 0:
                       text(1,0,3,1,1,str(threshold),18,7)
                   else:
                       text(1,0,3,1,1,"Auto",18,7)
               elif g == 5:
                   zoom +=1
                   if zoom < 7:
                       xo = (xo * (widths[zoom]/widths[zoom-1]))
                       yo = (yo * (widths[zoom]/widths[zoom-1]))
                       text(1,5,3,1,1,str(int(yo)),18,7)
                       text(0,5,3,1,1,str(int(xo)),18,7)
                       text(0,5,2,0,1,"RA offset",14,7)
                       text(1,5,2,0,1,"DEC offset",14,7)
                       text(0,1,3,1,1,str(zoom),18,7)
                       scalex = scale / scales[zoom]
                       text(1,7,3,1,1,str(int(scalex)),18,7)
                       w = widths[zoom]
                       h = int(w/1.7647)
                       x = int((w/2) - 320 + xo)
                       y = int((h/2) - 181 + yo)
                       dim = (w, h)
                   if zoom > 6:
                       zoom = 6
                  
                   
               elif g == 4:
                   zoom -=1
                   zoom = max(zoom,0)
                   xo = (xo * (widths[zoom]/widths[zoom+1]))
                   yo = (yo * (widths[zoom]/widths[zoom+1]))
                   if zoom == 0:
                      xo = 0
                      yo = 0
                      text(0,5,0,0,1,"RA offset",14,7)
                      text(1,5,0,0,1,"DEC offset",14,7)
                   text(0,5,3,1,1,str(int(xo)),18,7)
                   text(1,5,3,1,1,str(int(yo)),18,7)
                   text(0,1,3,1,1,str(zoom),18,7)
                   scalex = scale / scales[zoom]
                   text(1,7,3,1,1,str(int(scalex)),18,7)
                   w = widths[zoom]
                   h = int(w/1.7647)
                   x = int((w/2) - 320 + xo)
                   y = int((h/2) - 181 + yo)
                   dim = (w, h)
                   
               elif g == 31:
                   scale +=1
                   scalex = int(scale / scales[zoom])
                   scalex = min(scalex,255)
                   text(1,7,3,1,1,str(scalex),18,7)
               elif g == 30:
                   scale -=1
                   scalex = int(scale / scales[zoom])
                   scalex = max(scalex,0)
                   text(1,7,3,1,1,str(scalex),18,7)
               elif g == 9:
                   fps +=1
                   fps = min(fps,40)
                   camera.framerate = fps
                   text(0,2,3,1,1,str(fps),18,7)
                   camera.shutter_speed = int((1/fps) * 1000000)
                   speed = camera.shutter_speed
                   text(0,3,3,1,1,str(int(speed/1000)),18,7)
               elif g == 8:
                   fps -=1
                   fps = max(fps,1)
                   camera.framerate = fps
                   text(0,2,3,1,1,str(fps),18,7)
                   camera.shutter_speed = int((1/fps) * 1000000)
                   speed = camera.shutter_speed
                   text(0,3,3,1,1,str(int(speed/1000)),18,7)
               elif g == 11:
                   mode +=1
                   mode = min(mode,5)
                   camera.exposure_mode = modes[mode]
                   text(1,2,3,1,1,modes[mode],18,7)
               elif g == 10:
                   mode -=1
                   mode = max(mode,0)
                   camera.exposure_mode = modes[mode]
                   text(1,2,3,1,1,modes[mode],18,7)
               elif g == 13:
                   speed +=1000
                   speed = min(speed,6000000)
                   camera.shutter_speed = speed
                   fps = int(1/(speed/1000000))
                   camera.framerate = fps
                   text(0,3,3,1,1,str(int(speed/1000)),18,7)
                   text(0,2,3,1,1,str(fps),18,7)
               elif g == 12:
                   speed -=1000
                   speed = max(speed,1000)
                   camera.shutter_speed = speed
                   fps = int(1/(speed/1000000))
                   camera.framerate = fps
                   text(0,3,3,1,1,str(int(speed/1000)),18,7)
                   text(0,2,3,1,1,str(fps),18,7)
               elif g == 15:
                   if ISO == 0:
                       ISO +=100
                   else:
                       ISO = ISO * 2
                   ISO = min(ISO,800)
                   camera.iso = ISO
                   if ISO != 0:
                       text(1,3,3,1,1,str(ISO),18,7)
                   else:
                       text(1,3,3,1,1,"Auto",18,7)
               elif g == 14:
                   if ISO == 100:
                       ISO -=100
                   else:
                       ISO = int(ISO / 2)
                   ISO = max(ISO,0)
                   camera.iso = ISO
                   if ISO != 0:
                       text(1,3,3,1,1,str(ISO),18,7)
                   else:
                       text(1,3,3,1,1,"Auto",18,7)
               elif g == 17:
                   brightness +=1
                   brightness = min(brightness,100)
                   camera.brightness = brightness
                   text(0,4,3,1,1,str(brightness),18,7)
               elif g == 16:
                   brightness -=1
                   brightness = max(brightness,0)
                   camera.brightness = brightness
                   text(0,4,3,1,1,str(brightness),18,7)
               elif g == 19:
                   contrast +=1
                   contrast = min(contrast,100)
                   camera.contrast = contrast
                   text(1,4,3,1,1,str(contrast),18,7)
               elif g == 18:
                   contrast -=1
                   contrast = max(contrast,-100)
                   camera.contrast = contrast
                   text(1,4,3,1,1,str(contrast),18,7)
               elif g == 21:
                   xo +=1
                   if int((w/2) - 320 + xo) + 640 > w:
                       xo -=1
                   text(0,5,3,1,1,str(int(xo)),18,7)
                   x = int((w/2) - 320 + xo)
                   y = int((h/2) - 181 + yo)
               elif g == 20:
                   xo -=1
                   if int((w/2) - 320 + xo) <= 0:
                       xo +=1
                   text(0,5,3,1,1,str(int(xo)),18,7)
                   x = int((w/2) - 320 + xo)
                   y = int((h/2) - 181 + yo)
               elif g == 23:
                   yo +=1
                   if int((h/2) - 181 + yo) + 362 > h:
                       yo -=1
                   text(1,5,3,1,1,str(int(yo)),18,7)
                   x = int((w/2) - 320 + xo)
                   y = int((h/2) - 181 + yo)
               elif g == 22:
                   yo -=1
                   if int((h/2) - 181 + yo) <= 0:
                       yo +=1
                   text(1,5,3,1,1,str(int(yo)),18,7)
                   x = int((w/2) - 320 + xo)
                   y = int((h/2) - 181 + yo)
               elif g == 25:
                   min_corr +=50
                   min_corr = min(min_corr,1000)
                   text(0,6,3,1,1,str(min_corr),18,7)
               elif g == 24:
                   min_corr -=50
                   min_corr = max(min_corr,0)
                   text(0,6,3,1,1,str(min_corr),18,7)
               elif g == 27:
                   interval +=1
                   interval = min(interval,100)
                   text(1,6,3,1,1,str(interval),18,7)
               elif g == 26:
                   interval -=1
                   interval = max(interval,1)
                   text(1,6,3,1,1,str(interval),18,7)
               
               elif g == 0 or g == 1:
                   Auto_G +=1
                   if Auto_G > 1:
                       Auto_G = 0
                       button(0,0,0)
                       text(0,0,9,0,1,"AUTO",15,7)
                       text(0,0,9,1,1,"GUIDE",15,7)
                       GPIO.output(E_OP, GPIO.LOW)
                       GPIO.output(W_OP, GPIO.LOW)
                       start_ew = 0
                   else:
                       button(0,0,1)
                       text(0,0,1,0,1,"AUTO",15,0)
                       text(0,0,1,1,1,"GUIDE",15,0)
               elif g ==6 or g == 7:
                   preview +=1
                   if preview > 1:
                       preview = 0
                       button(1,1,0)
                       text(1,1,0,0,1,"Preview",14,7)
                       text(1,1,0,1,1,"Threshold",13,7)
                   else:
                       button(1,1,1)
                       text(1,1,1,0,1,"Preview",14,0)
                       text(1,1,1,1,1,"Threshold",13,0)
               elif g == 32 or g == 33:
                   InvRA +=1
                   if InvRA > 1:
                       InvRA = 0
                       button(0,8,0)
                       text(0,8,0,0,1,"Invert RA",14,7)
                   else:
                       button(0,8,1)
                       text(0,8,1,0,1,"Invert RA",14,0)
               elif g == 34 or g == 35:
                   InvDEC +=1
                   if InvDEC > 1:
                       InvDEC = 0
                       button(1,8,0)
                       text(1,8,0,0,1,"Invert DEC",14,7)
                   else:
                       button(1,8,1)
                       text(1,8,1,0,1,"Invert DEC",14,0)
               elif g == 36 or g == 37:
                   RAon +=1
                   if RAon > 1:
                       RAon = 0
                       button(0,9,1)
                       text(0,9,9,0,1,"RA OFF",14,0)
                   else:
                       button(0,9,0)
                       text(0,9,1,0,1,"RA ON",14,7)
               elif g == 38 or g == 39:
                   DECon +=1
                   if DECon > 1:
                       DECon = 0
                       button(1,9,1)
                       text(1,9,9,0,1,"DEC OFF",14,0)
                   else:
                       button(1,9,0)
                       text(1,9,1,0,1,"DEC ON",14,7)
                       
               # save config
               config[0]  = crop
               config[1]  = threshold
               config[2]  = scale 
               config[3]  = fps
               config[4]  = mode
               config[5]  = speed
               config[6]  = ISO
               config[7]  = brightness
               config[8]  = contrast
               config[9]  = Night
               config[10] = Auto_G
               config[11] = min_corr
               config[12] = interval
               config[13] = InvRA
               config[14] = InvDEC
               config[15] = preview
               config[16] = c_mask
               config[17] = use_RPiGPIO

               with open('PiAGconfig.txt', 'w') as f:
                   for item in config:
                       f.write("%s\n" % item)

def func2(correct,q):
    while True:
      correct = q.get()
      RAdir = correct[3:4]
      RAval = int(correct[4:8])
      if RAval > 0:
          start_RA = time.time()
          while time.time() - start_RA < abs(RAval)/1000:
             if RAdir == "e":
                 GPIO.output(E_OP, GPIO.HIGH)
             if RAdir == "w":
                 GPIO.output(W_OP, GPIO.HIGH)
      GPIO.output(E_OP, GPIO.LOW)
      GPIO.output(W_OP, GPIO.LOW)

def func3(correct,q):
    while True:
      correct = r.get()
      DECdir = correct[11:12]
      DECval = int(correct[12:])
      if DECval > 0:
          start_DEC = time.time()
          while time.time() - start_DEC < abs(DECval)/1000:
             if DECdir == "n":
                 GPIO.output(N_OP, GPIO.HIGH)
             if DECdir == "s":
                 GPIO.output(S_OP, GPIO.HIGH)
      GPIO.output(N_OP, GPIO.LOW)
      GPIO.output(S_OP, GPIO.LOW)

q = queue.Queue()
r = queue.Queue()
thread1 = threading.Thread(target=func1,args=(correct,q))
thread2 = threading.Thread(target=func2,args=(correct,q))
thread3 = threading.Thread(target=func3,args=(correct,q))
thread1.start()
thread2.start()
thread3.start()


                      

