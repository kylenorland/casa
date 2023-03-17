#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: Originally 1/5/21
Title: multiDotSim
Description: An output visualizer for two dimensional x, y information.
'''

#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import pygame
from pygame.locals import *
import random #For randomly placing the enemies
import math
import os

#Fix for ALSA error
os.environ['SDL_AUDIODRIVER'] = 'dsp'
#--------------------------------------------------------------
#---------------------------Pygame set up-----------------------
#--------------------------------------------------------------
#Set up clock
clock = pygame.time.Clock()
FPS = 20  # Frames per second.

#---------------------------Dots---------------------------------
class Dot(pygame.sprite.Sprite):
    def __init__(self):
        super(Dot, self).__init__()
        self.x = 100
        self.y = 100
        self.radius = 10
        self.color = (255,0,0)
        #Size
        self.surf = pygame.Surface((25,25))
        #Color
        self.surf.fill((255,255,255))
        pygame.draw.circle(self.surf, self.color, (10,10), self.radius, 0)
        self.rect = self.surf.get_rect(center=(self.x, self.y))

    def update(self):
        #Move the plane to the approximate
        #print("Y value of : " + self.y)
        approximateX = round(self.x)
        approximateY = round(self.y)
        self.rect = self.surf.get_rect(center=(approximateX, approximateY))

        print("Updating: " + str(approximateX) + " " +  str(approximateY))
        #Keep player on screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > 500:
            self.rect.right = 500
        if self.rect.top <= 0:
            self.rect.top = 0
        elif self.rect.bottom >= 500:
            self.rect.bottom = 500

#--------------------------------------------------------------
#---------------------------Block/CASA set up--------------------
#--------------------------------------------------------------
#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "mid block--"
with open("blockLogs/midLog.txt", "w") as logfile:
    logfile.write(str(time.localtime()))
    #------------------
    #--Pull arguments--
    #------------------
    numArgs = len(sys.argv)
    logfile.write("There are " + str(numArgs) + " arguments" + "\n")
    #print("There are " + str(numArgs) + " arguments")

    if numArgs >= 3:
        proxyInputPort = int(sys.argv[1])
        proxyOutputPort = int(sys.argv[2])
        stringArchitecture = sys.argv[3]
        try:
            jsonArch = json.loads(stringArchitecture)
            subTopics = jsonArch['subTopics']
            pubTopics = jsonArch['pubTopics']
            blockName = jsonArch['blockName']
        except:
            logfile.write("Something in the json loading process broke"+ "\n")
            print("Something in the json loading process broke")
    #------------------

    #---------------------------------------
    #-------Connect to the sockets----------
    #---------------------------------------
    context = zmq.Context()

    pubSocket = context.socket(zmq.PUB)
    pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))

    subSocket = context.socket(zmq.SUB)
    subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

    for subTopic in subTopics:
        subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())
        logfile.write("Subscribing to: " + subTopic + "\n")


    #-------------------------------------------------------------
    #-------------------Initialization----------------------------
    #-------------------------------------------------------------
    #-------------------------Game Operation--------------------
    #Initialize pygame
    pygame.init()

    #Create screen
    screen = pygame.display.set_mode((800,600))

    #Initialize Dots and put in group

    dotList = []
    numDots = 10
    for i in range(0, numDots):
        dot = Dot()
        dotList.append(dot)


    #-------------------------------------------------------------
    #-------------------Run loop----------------------------------
    #-------------------------------------------------------------
    running = True

    #Glocals
    printPath = True
    pathLength = 40
    pathFrequency = 5 #Frames
    pathCounter = 0
    pathQueue = deque()
    pathColor = (255,255,255)
    pathMarkerRad = 3

    while running:
        clock.tick(FPS)

        #---------HANDLE EVENTS--------------------
        #------------pygame events-----------------
        for event in pygame.event.get():
            #Check for KEYDOWNs
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
            elif event.type == QUIT:
                running = False


        #-----------CASA Events-------------------
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()
        #Process it
        #Handle exit command;
        if topic == "commandChain":
            if data['command'] == 'stop':
            #Shut down.
                running = False
        else:
            #print("in pre-dot array")
            #print("dotArray in " + str(('dotArray' in data)))
            if 'dotArray' in data:
                #Update all the dots;
                #print("Hi")
                for i in range(0,numDots):
                    dotList[i].x =  data['dotArray'][i]['x']
                    dotList[i].y =  data['dotArray'][i]['y']

                #Update the dots;
                #print("The dotList has " + str(len(dotList)) + " entries")
                for dot in dotList:
                    dot.update()

        #----------------------SCREEN UPDATING and Print all entities--------------------------------
        #Clear Screen
        screen.fill((255,255,255))

        #Blit everything to screen
        for dot in dotList:
            screen.blit(dot.surf, dot.rect)


        pygame.display.flip()

    #Close the display when everything is done
    pygame.display.quit()
    pygame.quit()
