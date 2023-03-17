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
    acc_recv_count = 0
    gyro_recv_count = 0
    accOutputFile = None
    gyroOutputFile = None

    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Respond to commandChain
        if topic == 'commandChain':
            print("Recieved commandChain argument")
            if data['command'] == 'stop':
                print("stopping specWriteToCSV loop")
                #Close the output files
                accOutputFile.close()
                gyroOutputFile.close()
                break

        #Handle acceleration data
        if data['type'] == 'acc':
            if acc_recv_count == 0:
                #Initialize the output file
                now = datetime.datetime.now()
                accOutputFileName = "outputFiles/" + ''.join(str(data['macAddress']).split(":")) + "_" + now.strftime('%Y-%m-%dT%H.%M.%S.%f') + "_"+ ''.join(str(data['macAddress']).split(":")) + "_Accelerometer.csv"
                print("The accelerometer output path is: " + accOutputFileName)

                #Generate that file
                accOutputFile = open(accOutputFileName, "w")
                accWriter = csv.writer(accOutputFile)

                #Initialize the top row
                accTopLabels = ['epoc (ms)', 'timestamp (-0700)', 'elapsed(s)', 'x-axis (g)', 'y-axis (g)', 'z-axis (g)']
                #Write it in CSV format to the output file
                accWriter.writerow(accTopLabels)


            #Having initialized it, add a line with data
            dataRow = [data['timestamp'], '', '', data['x'], data['y'], data['z']]
            accWriter.writerow(dataRow)
            logFile.write(topic + ": " + str(data) + "\n")
            #Increment the recv_count
            acc_recv_count += 1

        #Handle gyroscope data
        if data['type'] == 'gyro':
            if gyro_recv_count == 0:
                #Initialize the output file
                now = datetime.datetime.now()
                gyroOutputFileName = "outputFiles/" + ''.join(str(data['macAddress']).split(":")) + "_" + now.strftime('%Y-%m-%dT%H.%M.%S.%f') + "_"+ ''.join(str(data['macAddress']).split(":")) + "_Gyroscope.csv"
                print("The gyroscope output path is: " + gyroOutputFileName)

                #Generate that file
                gyroOutputFile = open(gyroOutputFileName, "w")
                gyroWriter = csv.writer(gyroOutputFile)

                #Initialize the top row
                gyroTopLabels = ['epoc (ms)', 'timestamp (-0700)', 'elapsed(s)', 'x-axis (deg/s)', 'y-axis (deg/s)', 'z-axis (deg/s)']
                #Write it in CSV format to the output file
                gyroWriter.writerow(gyroTopLabels)


            #Having initialized it, add a line with data
            dataRow = [data['timestamp'], '', '', data['x'], data['y'], data['z']]
            gyroWriter.writerow(dataRow)
            logFile.write(topic + ": " + str(data) + "\n")
            #Increment the recv_count
            gyro_recv_count += 1

#---------------------------------------------------------------
