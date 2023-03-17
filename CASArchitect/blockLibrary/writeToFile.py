#Head Material
#leftPorts=1
#rightPorts=0
#done

#Block Description
'''
Author: Kyle Norland
Date: 9/16/20
Description: Takes an input, and writes it to a file.
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
subTopics = ['bats']
pubTopics = []
data = "value"
blockName = "sinkBlock"

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
pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort)) #NOT BIND!!

subSocket = context.socket(zmq.SUB)
subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

for subTopic in subTopics:
    print(subTopic)
    subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())


#------------------------------------------
#--------RUN LOOP------------------------
#--------------------------------------
#outputPath = ""
outputFileName = "outputFiles/sensorOutput.txt"

with open("blockLogs/writeOutLog.txt", "w") as logFile:
    with open(outputFileName, "w") as outputFile:
        while True:
            #Receive the data
            topic = subSocket.recv_string()
            data = subSocket.recv_json()

            #Process it
            data['value'] = data['value'] + blockName
            print(data['value'])

            #Print it to log file
            logFile.write(topic + ": " + data['value'] + "\n")

            #Print it to output file:
            outputFile.write(topic + ": " + data['value'] + "\n")
#---------------------------------------------------------------





