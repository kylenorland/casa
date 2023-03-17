#Head Material
#leftPorts=1
#rightPorts=0
#done


#Block Description
'''
Author: Kyle Norland
Date: 10-24-20
Purpose: Take incoming x,y acc data and make a ball move
'''

#Libary Imports
import pygame
import math
import threading
import zmq
import json
import time
import sys

#Globals
x = 0;
y = 0;

#zmq initialization
#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "mid block--"
with open("blockLogs/animationLog.txt", "w") as logfile:
    logfile.write(str(time.localtime()))
    #------------------
    #--Pull arguments--
    #------------------
    numArgs = len(sys.argv)
    logfile.write("There are " + str(numArgs) + " arguments" + "\n")
    print("There are " + str(numArgs) + " arguments")

    if numArgs >= 3:
        proxyInputPort = int(sys.argv[1])
        proxyOutputPort = int(sys.argv[2])
        stringArchitecture = sys.argv[3]
        try:
            jsonArch = json.loads(stringArchitecture)
            subTopics = jsonArch['subTopics']
            pubTopics = jsonArch['pubTopics']
            blockName = jsonArch['blockName']
            runTime = jsonArch['runTime']
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

    #Threader to split out acceleration and update x,y
    class InputThread(threading.Thread):
        def __init__(self, subSocket, pubSocket):
            threading.Thread.__init__(self)
            self.subSocket = subSocket
            self.pubSocket = pubSocket

        def run(self):
            global x
            global y
            while True:
                #Receive the data
                topic = self.subSocket.recv_string()
                data = self.subSocket.recv_json()

                if str(data['type']) == 'gyro':
                    x = float(data['x'])
                    y = float(data['y'])
                    print("-")

    iThread = InputThread(subSocket, pubSocket)
    iThread.start()


#With iThread in back, run pygame
screen = pygame.display.set_mode((720, 480))
clock = pygame.time.Clock()
FPS = 15  # Frames per second.

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Ball:
    xPosition = 0;
    yPosition = 0;
    screenCenterX = 400;
    screenCenterY = 200;
    color = BLACK;
    recentX = []
    recentY = []
    def __init__(self):
        color = (0,0,0)

    def update(self):
        #Update location
        global x
        global y

        self.recentX.append(x)
        self.recentY.append(y)
        if len(self.recentX) > 5:
            self.recentX.pop(0)
        if len(self.recentY) > 5:
            self.recentY.pop(0)
        self.xPosition = int(sum(self.recentX)/len(self.recentX))
        self.yPosition = int(sum(self.recentY)/len(self.recentY))

    def drawBone(self):
        pygame.draw.circle(screen, (0,0,255), (self.xPosition + self.screenCenterX, self.yPosition + self.screenCenterY), 10,  2)

mainBall = Ball()

#Only run the animation for 2 seconds less than run time.
startTime = time.time()
currentTime = startTime
while time.time() - startTime < runTime - 2:
    clock.tick(FPS)

    #Clear screen
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.display.quit()
            pygame.quit()
            exit()

    mainBall.update()
    mainBall.drawBone()

    pygame.display.update()  # Or pygame.display.flip()
