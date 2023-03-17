#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: Originally 6/18/19, Converted to block 11/10/20
Title: CirclingAndEscape
Description: Show how a PID controller leads to circling, and then fix it with
              an extra term. (Added inputs and outputs)
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

#---------------------------Sideparts---------------------------------
class Sider(pygame.sprite.Sprite):
    def __init__(self):
        super(Sider, self).__init__()
        #Size
        self.surf = pygame.Surface((10,10))
        #Color
        self.surf.fill((100,100,100))
        #Start Location
        self.currentX = 350
        self.currentY = 250

        self.rect = self.surf.get_rect(center=(self.currentX, self.currentY))

#-------------------------Plane Class--------------------------------#
class Plane(pygame.sprite.Sprite):
    def __init__(self):
        super(Plane, self).__init__()
        #Size
        self.surf = pygame.Surface((50,50))
        #Color
        self.surf.fill((0,0,0))
        #Start Location
        self.currentX = 350
        self.currentY = 250
        self.orientation = 0
        self.turnRadius = 96

        #Main body
        pygame.draw.ellipse(self.surf, (255,255,255), (10,20,40,10))
        #Wing
        pygame.draw.ellipse(self.surf, (255,255,255), (30,5,10,40))
        #Tail
        pygame.draw.ellipse(self.surf, (255,255,255), (10,17,10,15))
        #Window
        pygame.draw.ellipse(self.surf, (0,0,0), (40,22,7,5))

        self.rect = self.surf.get_rect(center=(self.currentX, self.currentY))

        #Stored original image
        self.storedImage = self.surf

    def update(self):
        #Move the plane to the approximate
        approximateX = round(self.currentX)
        approximateY = round(self.currentY)
        self.surf = pygame.transform.rotate(self.storedImage, self.orientation)
        self.rect = self.surf.get_rect(center=(approximateX, approximateY))


        #Keep player on screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > 800:
            self.rect.right = 800
        if self.rect.top <= 0:
            self.rect.top = 0
        elif self.rect.bottom >= 600:
            self.rect.bottom = 600

#----------------------Goal Class---------------------------
class Goal(pygame.sprite.Sprite):
    def __init__(self):
        super(Goal, self).__init__()
        self.surf = pygame.Surface((20,20))
        self.surf.fill((0,0,0))
        self.currentX = 400
        self.currentY = 300
        pygame.draw.circle(self.surf, (0,255,0), (10,10), 10, 0)
        self.rect = self.surf.get_rect(center=(self.currentX,self.currentY))

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

    #Initialize Plane and Goal and Siders
    plane = Plane()
    goal = Goal()
    leftSider = Sider()
    rightSider = Sider()

    #Take the original surface

    #Initialize sprite groups
    all_sprites = pygame.sprite.Group()
    all_sprites.add(plane)
    all_sprites.add(goal)
    #all_sprites.add(leftSider)
    #all_sprites.add(rightSider)

    #-------------------------------------------------
    #------------Send initial message out-------------;
    #-------------------------------------------------
    #Let everything else get set up
    time.sleep(1)

    print("Sending initial message out")
    #Organize the data;
    sendData = {'signalTag': 'envUpdate',
    'error': 1,
    'goalX': goal.currentX,
    'goalY': goal.currentY,
    'planeX': plane.currentX,
    'planeY': plane.currentY,
    'planeOrientation': plane.orientation }


    #Publish it
    pubTopic = pubTopics[0]
    pubSocket.send_string(pubTopic, zmq.SNDMORE)
    pubSocket.send_json(sendData)
    #--------------------------------------------------
    #-------------------------------------------------

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
        time.sleep(0.1)
        #---------HANDLE EVENTS--------------------
        #------------pygame events-----------------
        for event in pygame.event.get():
            #Check for KEYDOWNs
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
            elif event.type == QUIT:
                running = False

        #Check the pressed keys to control
        pressed_keys = pygame.key.get_pressed()


        #-----------CASA Events-------------------
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()
        #Process it
        if data['signalTag'] ==  'planeUpdate':
            #Update the plane data;
            plane.currentX = data['currentX']
            plane.currentY = data['currentY']
            plane.orientation = data['orientation']

            #Update;
            plane.update()

        #----------Publish CASA data----------------------------------------------
        #Do the necessary calculations
        #Error;
        #Calculate the orientation to the objective
        deltaX = goal.currentX - plane.currentX
        deltaY = -(goal.currentY - plane.currentY) #Negative to flip the coordinate system)

        #Calculate desired orientation (It is relative to the forward x direction)
        angleToGoal = math.degrees(math.atan2(deltaY, deltaX))

        #Convert to 0-360 to be in absolute
        if angleToGoal < 0:
            angleToGoal = 360 + angleToGoal

        #Now, calculate the difference between the two angles
        error = angleToGoal - plane.orientation
        print("The angle to goal is: " + str(angleToGoal))
        #print("The initial error is: " + str(error))

        error = (error + 180) % 360 - 180
        print("Error is: " + str(error))
        #Organize the data;
        sendData = {'signalTag': 'envUpdate',
        'error': error,
        'goalX': goal.currentX,
        'goalY': goal.currentY,
        'planeX': plane.currentX,
        'planeY': plane.currentY,
        'planeOrientation': plane.orientation }


        #Publish it
        pubTopic = pubTopics[0]
        pubSocket.send_string(pubTopic, zmq.SNDMORE)
        pubSocket.send_json(sendData)

        #----------------------SCREEN UPDATING--------------------------------
        #Clear Screen
        screen.fill((0,0,0))

        #Blit everything to screen
        for entity in all_sprites:
            screen.blit(entity.surf, entity.rect)

        #Print all of the path
        if (printPath == True):
            pathCounter += 1
            if pathCounter > pathFrequency:
                #Reset path counter.
                pathCounter = 0
                pathObj = {'x': plane.currentX, 'y': plane.currentY}
                pathQueue.appendleft(pathObj)
                if len(pathQueue) > pathLength:
                    pathQueue.pop()
            #Print all of them whether drawing a new one or not
            for object in pathQueue:
                pygame.draw.circle(screen, pathColor, (object['x'], object['y']), pathMarkerRad, 0)

        #Print the side points
        #Now, get the two angles
        leftAngle = plane.orientation + 90
        rightAngle = plane.orientation - 90
        if rightAngle < 0:
            rightAngle = 360 + rightAngle

        #Now, calculate a point in those directions
        leftPointX = plane.currentX + (plane.turnRadius * math.cos(math.radians(leftAngle)))
        leftPointY = plane.currentY + (plane.turnRadius * -(math.sin(math.radians(leftAngle)))) #To switch to the flipped y coordinates

        rightPointX = plane.currentX + (plane.turnRadius * math.cos(math.radians(rightAngle)))
        rightPointY = plane.currentY + (plane.turnRadius * -(math.sin(math.radians(rightAngle))))

        #Draw the side points
        pygame.draw.circle(screen, (0,0,255), (rightPointX, rightPointY), 5, 0)
        pygame.draw.circle(screen, (0,0,255), (leftPointX, leftPointY), 5, 0)

        #Check for collision
        if pygame.sprite.collide_rect(plane,goal):
            #plane.kill()
            print("Killed")

        #Update display
        pygame.display.flip()

        #Add delay to sync on all computers
        clock.tick(60)

    #Close the display when everything is done
    pygame.display.quit()
    pygame.quit()
