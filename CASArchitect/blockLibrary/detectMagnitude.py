#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 11/9/20
Description: Detects acceleration total magnitude and sends a light on signal.
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
    coolDownStart = 0
    currentTime = 0
    lightDuration = 0.5
    coolDownPeriod = lightDuration + 0.5
    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()
        #Process it
        if data['type'] == 'acc':
            #Calculate magnitude:
            magnitude = math.sqrt((data['x']**2) + (data['y']**2) + (data['z']**2))
            print(magnitude)
            if(magnitude > 1.5):
                currentTime = time.time()
                if((currentTime - coolDownStart) > coolDownPeriod):
                    print("Triggered")
                    sendData = {'type':'lightSignal', 'duration':lightDuration}
                    #Restart cooldown clock
                    coolDownStart = currentTime

                    #Send the data
                    pubTopic = pubTopics[0]
                    pubSocket.send_string(pubTopic, zmq.SNDMORE)
                    pubSocket.send_json(sendData)
