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
import random

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
    #Initialize a set of dots with random locations
    xLow = 0
    xHigh = 500
    yLow = 0
    yHigh = 500
    numGroupOne = 5
    numGroupTwo = 5
    numDots = numGroupOne + numGroupTwo
    dotArray = []
    dotData = {'dotArray': []}

    #Generate an array/list with random coordinates

    for i in range(0, numGroupOne):
        newDot = {'x': random.randint(0, xHigh),
        'y': random.randint(0, yHigh),
        'group': 0,
        'value': 0}
        dotData['dotArray'].append(newDot)

    for i in range(0, numGroupTwo):
        newDot = {'x': random.randint(0, xHigh),
        'y': random.randint(0, yHigh),
        'group': 1,
        'value': 0}
        dotData['dotArray'].append(newDot)

    #--------------------
    #-------Run loop------
    #--------------------
    keepRunning = True
    while keepRunning:
        #----Receive the data-----
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Handle exit command;
        if topic == "commandChain":
            if data['command'] == 'stop':
            #Shut down.
                keepRunning = False
        else:
            #Handle magnitude data
            if 'magnitudes' in data:
                groupOneMag = data['magnitudes'][0]
                groupTwoMag = data['magnitudes'][1]

            #Process it
            #Assign step magnitude
            for dot in dotData['dotArray']:
                #If group (2) is 0, input groupOneMag
                if dot['group'] == 0:
                    dot['value'] = groupOneMag
                elif dot['group'] == 1:
                    dot['value'] = groupTwoMag

            #Calculate effects (For now, randomly move)
            for dot in dotData['dotArray']:
                if dot['value'] == 1: #If it is moving
                    #Change the y randomly
                    dot['y'] += 1 #random.randint(-1,1)

            print(str(dotData['dotArray'][0]['y']) + " is the y value")

            #Publish it
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(dotData)
