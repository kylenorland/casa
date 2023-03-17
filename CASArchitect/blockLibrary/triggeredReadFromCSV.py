#Head Material
#leftPorts=1
#rightPorts=1
#type=inputInterface
#done


#Block Description
'''
Author: Kyle Norland
Date: 10/13/20
Description: Triggered signal reader from CSV
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys

#Special
import csv

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/readCSVLog.txt", "w")
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
        inputFileName = jsonArch['inputFiles'][0]
        print("The csv input file is: " + inputFileName)
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
#-------------------Run Loop---------------------------
#------------------------------------------------------
logfile.write("Publishing to: " + str(pubTopics[0]))

while True:
    #Receive the data
    topic = subSocket.recv_string()
    data = subSocket.recv_json()
    #Process it
    logfile.write(str(data) + "\n")

    #Ensure that both csv and value input can be done.
    if 'value' in data:     #If a one signal is recieved
        inputFile = open(inputFileName,"r")
        csv_reader = csv.reader(inputFile, delimiter=",")
        line_count = 0

        dataLabels = []
        sendTemplate = {}
        for row in csv_reader:
            if line_count == 0:
                # Initialize the first row as the json keys
                for i in range(0, len(row)):
                    dataLabels.append(str(row[i]))
                    sendTemplate[str(row[i])] = ' '
                #print(dataLabels)
                #print(sendTemplate)
                line_count += 1

            elif line_count != 0:
                #Create a json object and publish it.
                sendData = sendTemplate.copy()
                for i in range(0, len(row)):
                    sendData[dataLabels[i]] = row[i]

                #If its the first one in the sequence, also send the timestamp, buttonName and inputFileName
                if line_count == 1:
                    sendData['timestamp'] = data['timestamp']
                    sendData['buttonName'] = data['buttonName']
                    sendData['preset'] = inputFileName.split("/", 1)[1][:-4]

                #Publish it
                pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                pubSocket.send_json(sendData)

                line_count += 1

        inputFile.close()
