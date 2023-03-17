#Head Material
#leftPorts=1
#rightPorts=0
#type=outputInterface
#done

#Block Description
'''
Author: Kyle Norland
Date: 11/3/20
Description: Takes an json input and writes to two csv files in a specific way for the project.
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
import csv
import datetime

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

#Subscribe to command chain
subSocket.setsockopt(zmq.SUBSCRIBE, "commandChain".encode())
#------------------------------------------
#--------RUN LOOP------------------------
#--------------------------------------
#outputPath = ""
#Currently using direct to file output for this block (Write error handling later)
#outputFileName = "outputFiles/csvOutput" + str(subTopic) + "-" + str(time.localtime()[3]) + ":" + str(time.localtime()[4]) + ":" + str(time.localtime()[5]) + ".csv"

with open("blockLogs/csvOutLog.txt", "w") as logFile:
    haptic_recv_count = 0
    hapticOutputFile = None

    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Respond to commandChain
        if topic == 'commandChain':
            print("Recieved commandChain argument")
            if data['command'] == 'stop':
                print("stopping specHapticToCSV loop")
                #Close the output files
                hapticOutputFile.close()
                break

        #Handle haptic data, filtering for only that with timestamp in it.
        if 'timestamp' in data:
            if haptic_recv_count == 0:
                now = datetime.datetime.now()
                hapticOutputFileName = "outputFiles/" + now.strftime('%Y-%m-%dT%H.%M.%S.%f') + "_Haptic.csv"
                print("The haptic output path is: " + hapticOutputFileName)

                #Generate that file
                hapticOutputFile = open(hapticOutputFileName, "w")
                hapticWriter = csv.writer(hapticOutputFile)

                #Initialize the top row
                hapticTopLabels = ['Timestamp', 'Sensor Name', 'Preset']
                #Write it in CSV format to the output file
                hapticWriter.writerow(hapticTopLabels)

            #Having initialized it, add a line with data
            dataRow = [data['timestamp'], data['buttonName'], data['preset']]
            hapticWriter.writerow(dataRow)
            logFile.write(topic + ": " + str(data) + "\n")
            #Increment the recv_count
            haptic_recv_count += 1
#---------------------------------------------------------------
