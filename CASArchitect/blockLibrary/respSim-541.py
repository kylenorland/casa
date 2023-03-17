#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 9/9/20
Description: General purpose block template
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import math

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "mid block--"
#------------------
#--Pull arguments--
#------------------
numArgs = len(sys.argv)

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
    #print("Subscribing to: " + subTopic + "\n")


#------------------Objects/classes-------------------
globalIdCounter = 1000
objectDict = {}
commsManagerId = 57
globalOutputQueue = deque()

class CommsManager:
    def __init__(self, globalId):
        self.initialHandler = True
        self.globalId = globalId
        self.subObjects = []

    def addSubObject(self, objectId):
        self.subObjects.append(objectId)

    def recieveAndProcess(self,data):
        #Send to all sub objects
        for objectId in self.subObjects:
            print("sending to " + str(objectId))
            objectDict[str(objectId)].recieve(data)

        #Trigger the object's processing
        for objectId in self.subObjects:
            objectDict[str(objectId)].process()


#Plane object
class Plane:
    def __init__(self, globalId):
        #----------Flags-----------------
        self.initialHandler = False
        #--------------------------------

        #-------------Properties------------
        self.globalId = globalId
        self.currentX = 100
        self.currentY = 500
        self.turnRadius = 96
        self.angleSpeed = 3
        self.velocity = 5
        self.accelerationCap = 0.02
        self.orientation = 0
        self.maxTurnAngle = 3
        #-------------------------------
        #---------Internal Structures--------------
        self.recieveQueue = deque()
        #------------------------------------------

        #------------Structural Data----------------
        self.inputSignalTypes = ['combinedForce']
        self.outputSignalTypes = ['planeUpdate']
        #--------------------------------------

    def recieve(self, data):
        #Check if meets criteria
        if data['signalTag'] in self.inputSignalTypes:
            self.recieveQueue.append(data)

    def process(self):
        #Take from queue;
        data = self.recieveQueue.popleft()

        #Process it
        if data['signalTag'] == 'combinedForce':
            total = data['force']

            #Total is maxTurnAngle if higher than the max turn angle, or just the total if not;
            if abs(total) > abs(self.maxTurnAngle):
                actual = math.copysign(1,total) * self.maxTurnAngle #Negative because the actual right turn is in the clockwise direction
                print("Hit max angle")
            else:
                actual = total #Same reasoning as above

            #Now, update the plane properties.
            self.orientation = self.orientation + actual

            #Calculate velocity
            #Move in that direction
            self.currentX = self.currentX + (self.velocity * math.cos(math.radians(self.orientation)))
            self.currentY = self.currentY - (self.velocity * math.sin(math.radians(self.orientation))) #Flip back to upside down coordinates for display

            #Add output to the globalOutputQueue
            outputData = {'signalTag': 'planeUpdate',
            'currentX': self.currentX,
            'currentY': self.currentY,
            'orientation': self.orientation
            }

            globalOutputQueue.append(outputData)


#-----------------Initialize objects-----------------
def initializeObjects():
    #Declare globals used;

    global globalIdCounter
    global commsManagerId
    #One commsManager
    newCommsManager = CommsManager(globalIdCounter)
    objectDict[str(globalIdCounter)] = newCommsManager

    commsManagerId = newCommsManager.globalId
    globalIdCounter += 1
    #One plane;
    newPlane = Plane(globalIdCounter)
    objectDict[str(globalIdCounter)] = newPlane
    #Add to commsManager subObjects
    objectDict[str(commsManagerId)].addSubObject(newPlane.globalId)
    globalIdCounter += 1

initializeObjects()


#-------------------Run Loop-------------------------
while True:
    #Receive the data
    topic = subSocket.recv_string()
    data = subSocket.recv_json()

    #Send it through the system
    for object in objectDict.values():
        if(object.initialHandler == True):
            object.recieveAndProcess(data)

    #Publish full globalOutputQueue
    while len(globalOutputQueue) > 0:
        outputObject = globalOutputQueue.popleft()

        pubTopic = pubTopics[0]
        pubSocket.send_string(pubTopic, zmq.SNDMORE)
        pubSocket.send_json(outputObject)
