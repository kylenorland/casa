#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 1/5/20
Description: Simulates arm movement
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
screen = pygame.display.set_mode((720, 480))
clock = pygame.time.Clock()
FPS = 20  # Frames per second.

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Bone:
    desiredAngle = 0
    topHaptic = False
    bottomHaptic = False
    endLocation = [0,10]
    startLocation = [0,0]

    def __init__(self, startLocation, angle, length, prevBone):
        self.startLocation = startLocation
        self.angle = angle
        self.realAngle = angle
        self.length = length
        self.prevBone = prevBone
        self.angleChange = 0

    def update(self):
        #Update location
        self.startLocation = self.prevBone.endLocation
        #print(self.startLocation)
        #Update angles
        if self.topHaptic == True:
            self.angle = self.angle + 1
        if self.bottomHaptic == True:
            self.angle = self.angle - 1

        #calculate the end position
        self.realAngle = self.prevBone.realAngle + self.angle
        #print(self.realAngle)
        endX = self.prevBone.endLocation[0] + (math.cos(math.radians(self.realAngle)) * self.length)
        endY = self.prevBone.endLocation[1] + (-math.sin(math.radians(self.realAngle)) * self.length)
        self.endLocation = [endX, endY]

    def drawBone(self):
        pygame.draw.line(screen, (200,50,100), self.startLocation, self.endLocation, 2)


class localController:
    toDo = True

#--------------------------------------------------------------
#---------------------------Block/CASA set up--------------------
#--------------------------------------------------------------
#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/generatorLog.txt", "w")
logfile.write("Got to here")
#------------------
#--Pull arguments--
#------------------
numArgs = len(sys.argv)
print("There are " + str(numArgs) + " arguments")

if numArgs >= 3:
    proxyInputPort = int(sys.argv[1])
    proxyOutputPort = int(sys.argv[2])
    stringArchitecture = sys.argv[3]
    try:
        print(stringArchitecture)
        jsonArch = json.loads(stringArchitecture)
        subTopics = jsonArch['subTopics']
        pubTopics = jsonArch['pubTopics']
        blockName = jsonArch['blockName']
    except:
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

#-------------------------------------------------------------
#-------------------Initialization----------------------------
#-------------------------------------------------------------
#-------------------------Game Operation--------------------
#initialize the bones
startBone = Bone([200,320], 90, 10, None)
startBone.endLocation = [200,300]
torso = Bone(startBone.endLocation, 0, 100, startBone)
humerus = Bone(torso.endLocation, -90, 100, torso)
forearm = Bone(humerus.endLocation,15, 100, humerus)

boneArray = [torso, humerus, forearm]


#--------------------------------------------------
#------------Run Loop------------------------------
#--------------------------------------------------
i=0
while True:
    clock.tick(FPS)

    #Clear screen
    screen.fill(WHITE)


    pressed = pygame.key.get_pressed()

    humerus.angleChange = 0
    forearm.angleChange = 0

    if pressed[pygame.K_w]:
        humerus.angle = humerus.angle + 1
        humerus.angleChange = 1
    if pressed[pygame.K_s]:
        humerus.angle = humerus.angle - 1
        humerus.angleChange = 1
    if pressed[pygame.K_a]:
        forearm.angle = forearm.angle + 1
        forearm.angleChange = 1
    if pressed[pygame.K_d]:
        forearm.angle = forearm.angle - 1
        forearm.angleChange = 1


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.display.quit()
            pygame.quit()
            exit()

    #Draw start bone
    pygame.draw.line(screen, (0,0,0), startBone.startLocation, startBone.endLocation, 5)

    #Draw rest of bones
    for bone in boneArray:
        bone.update()
        bone.drawBone()
        #print("drew bone")

    pygame.display.update()  # Or pygame.display.flip()

    #Publish to socket
    #-------------------------------------------------------------
    #Generate the data
    data = {'magnitudes': [humerus.angleChange, forearm.angleChange]}
    i += 1
    #print(str(i) + "  " + str(data['magnitudes']))

    #Publish it
    pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
    pubSocket.send_json(data)
