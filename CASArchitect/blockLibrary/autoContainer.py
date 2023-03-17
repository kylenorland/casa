#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 2/9/21
Description: Test for a simple container app
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import subBlockLib

#Pull arguments
numArgs = len(sys.argv)
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
        print("Something in the json loading process broke")


#-----------------------------------------------------------------
#----------------Initialize Classes-------------------------------
#-----------------------------------------------------------------
sharedMemory = {"recieveQueue": deque(), "sendQueue": deque()}
#Note, the use of sharedMemory in this way is somewhat python specific, as python passes objects by reference, not value

context = zmq.Context()

#Notes, Reciever and Sender first
reciever = subBlockLib.Reciever(context, sharedMemory, proxyOutputPort, subTopics)
sender = subBlockLib.Sender(context, sharedMemory, proxyInputPort, pubTopics)
adder = subBlockLib.AddOne(sharedMemory)

#Loop them
keepRunning = True
while keepRunning:
    keepRunning = reciever.recieve(sharedMemory) #Exits if command recieved
    adder.add()
    sender.send(sharedMemory)

print("Auto container shutting down")
