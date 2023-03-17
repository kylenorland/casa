#Head Material
#leftPorts=1
#rightPorts=1
#type=inputInterface
#done


#Block Description
'''
Author: Kyle Norland
Date: 10/13/20
Description: For BME 577, patient computer
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


logfile = open("blockLogs/bmeLocalPatientLog.txt", "w")
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

with open(inputFileName, "r") as inputFile:
    #Pause for a few seconds so that the boundary manager can begin to Run
    time.sleep(3)
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
            #print("hello one")
            #print(dataLabels)
            #print(sendTemplate)
            line_count += 1

        elif line_count != 0:
            #Create a json object and publish it, then wait for the response from the
            #Central computer with the current data and algorithm.
            localData = sendTemplate
            for i in range(0, len(row)):
                localData[dataLabels[i]] = row[i]
            #print("hi")
            print(localData)
            #Publish it
            pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
            pubSocket.send_json({'type':'request'})
            #print('sent')
            #Recieve the algorithm and current state from the central computer
            #and act on it.
            topic = subSocket.recv_string()
            data = subSocket.recv_json()
            currentAverage = data['currentAverage']
            totalNumber = data['totalNumber']

            totalSum = totalNumber * currentAverage
            newSum = float(totalSum) + float(localData['test_result'])
            newAverage = newSum / (totalNumber + 1)
            newNumber = totalNumber + 1

            #Send an update to the central server
            pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
            sendData = {'type':'update', 'average':newAverage, 'number': newNumber}
            pubSocket.send_json(sendData)
            #print('recieved')
            #print(data['currentAverage'])
            #print(data['totalNumber'])
            time.sleep(0.1)
            line_count += 1
