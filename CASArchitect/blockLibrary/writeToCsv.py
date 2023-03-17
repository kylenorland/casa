#Head Material
#leftPorts=1
#rightPorts=1
#type=outputInterface
#done

#Block Description
'''
Author: Kyle Norland
Date: 9/24/20 Update 10/12/20
Description: Takes an json input and writes to a csv output file in order.
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
import csv

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
        outputFileName = jsonArch['outputFiles'][0]
        print("The csv input file is: " + outputFileName)
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

#Subscribe to command chain
subSocket.setsockopt(zmq.SUBSCRIBE, "commandChain".encode())
#------------------------------------------
#--------RUN LOOP------------------------
#--------------------------------------
#outputPath = ""
#Currently using direct to file output for this block (Write error handling later)
#outputFileName = "outputFiles/csvOutput" + str(subTopic) + "-" + str(time.localtime()[3]) + ":" + str(time.localtime()[4]) + ":" + str(time.localtime()[5]) + ".csv"

with open("blockLogs/csvOutLog.txt", "w") as logFile:
    recv_count = 0
    with open(outputFileName, "w") as outputFile:
        writer = csv.writer(outputFile)

        while True:
            #Receive the data
            topic = subSocket.recv_string()
            data = subSocket.recv_json()

            #Respond to commandChain
            if topic == 'commandChain':
                print("Recieved commandChain argument")
                if data['command'] == 'stop':
                    print("stopping writeToCSV loop")
                    break

                #print(str(data['command']))

            if recv_count == 0:
                #Initialize the top row then save data
                #Write it in CSV format to the output file
                writer.writerow(list(data.keys()))
                logFile.write(topic + ": " + str(data) + "\n")
                writer.writerow(list(data.values()))
                recv_count += 1

            elif recv_count != 0:
                #Print it to log file
                logFile.write(topic + ": " + str(data) + "\n")

                #Write it in CSV format to the output file
                writer.writerow(list(data.values()))

                recv_count += 1

#---------------------------------------------------------------
