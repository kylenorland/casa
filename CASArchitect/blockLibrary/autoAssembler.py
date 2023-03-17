#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 11/2/20
Description: Compares with connected computers, and determines if they are on the same rigid body.
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque

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
    #Used variables
    otherSensors = []
    knownSensors = {}
    thisSensor = {'x': 0, 'y':0, 'z':0}


    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        if 'comparison' in data:
            if data['sensorName'] not in knownSensors:
                knownSensors[data['sensorName']] = {'x': 0, 'y': 0, 'z':0, 'difference': 0}
            else:
                sensorObject = knownSensors[data['sensorName']]
                sensorObject['x']= data['x']
                sensorObject['y']= data['y']
                sensorObject['z']= data['z']
                sensorObject['difference'] = abs(sensorObject['x'] - thisSensor['x']) + abs(sensorObject['y'] - thisSensor['y']) + abs(sensorObject['z'] - thisSensor['z'])
        elif 'x' in data:
            thisSensor['x'] = data['x']
            thisSensor['y'] = data['y']
            thisSensor['z'] = data['z']

        #Publish
        pubTopic = pubTopics[0]
        pubSocket.send_string(pubTopic, zmq.SNDMORE)
        pubSocket.send_json(data)
