#!/usr/bin/python3
import json
import subprocess
import threading
#import asyncio
import requests
import zmq
import random
import sys
import time
import os
from subprocess import Popen, PIPE
from flask import Flask, render_template, request, jsonify
#from bleak import discover


app = Flask(__name__)

#Globals for device
device = None


def runSystem(compManagerPath, compManagerName, compManagerArguments):
    print("Running System")
    #commandString = 'python3 ' + compManagerPath + "/" + compManagerName + " " + json.dumps(compManagerArguments)

    #folderPath = "blockLibrary/"
    #block['proxyInputPort'], block['proxyOutputPort'], json.dumps(block)
    
    #ToDo: Actually fix this
    #Temp fix, since windows seems to be running python instead of python3
    if(str(sys.platform) == 'win32'):
        cmd = ["python", compManagerName, json.dumps(compManagerArguments)]
    else:
        cmd = ["python3", compManagerName, json.dumps(compManagerArguments)]
    newProcess = subprocess.Popen(cmd, shell=False)


#-----------------------------------------
#-----------ROUTES------------------------
#-----------------------------------------


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/participating", methods=['Get'])
def participatingResponse():
    response = {'participating':True,
                'name':'raspy1',
                'id':1,
                'type':'fullComputer'}
    return jsonify(response)

@app.route("/scanEnvironment", methods=['Get'])
def scanEnvironmentHandler():
    print("Starting Scan")
    '''
    parsedScanFile = open("envConfig/parsedScan.txt", 'w')
    #Scans for bluetooth, and then adds any named metawear to the file.
    #This could be shifted easily when new device types are needed.
    response = {'foundDevices': []}
    async def run():
        devices = await discover()
        for d in devices:
            if str(d.name) == 'MetaWear':
                parsedScanFile.write(d.address + '\n')
                response['foundDevices'].append(str(d.address))
                print(d)
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(run())
    parsedScanFile.close()
    '''
    print("Testing OS")
    print("OS is: " + sys.platform)

    if(str(sys.platform) == 'darwin'):
        print("Can't run a bluetooth scan on a mac right now, sorry. If you add a rasbperry pi or linux machine to your system that'll work.")
        response = {'foundDevices': []}
        return jsonify(response)

    elif(str(sys.platform)) == 'win32':
        print("Windows doesn't support bluetooth scanning well, so it's not enabled. Add a raspberry pi or linux machine to use this feature.")
        response = {'foundDevices': []}
        return jsonify(response)
    else:
        scanTime = 4
        commandString = 'sudo timeout -s SIGINT ' + str(scanTime) + 's hcitool -i hci0 lescan > envConfig/btscan.txt'
        subprocess.run(commandString, shell=True)
        #process = Popen(['sudo', 'timeout -s SIGINT 4s hcitool -i hci0 lescan > btscan.txt'], stdout=PIPE, stderr=PIPE)
        #process.wait()

        scanFile = open("envConfig/btscan.txt", 'r')
        parsedScanFile= open("envConfig/parsedScan.txt", 'w')
        devices = []
        for line in scanFile:
            if (line[0:2] == 'LE'):
                print("First line")
            elif (line[18:26] == 'MetaWear'):
                #print("Detected " + line[0:17])
                connectionString = line[0:17]
                if(connectionString not in devices):
                    devices.append(str(connectionString))
        for device in devices:
            parsedScanFile.write(device + '\n')
            macs = []
            macs.append(device)
            serialMacs = json.dumps(macs)
        print(devices)
        #Close the files
        scanFile.close()
        parsedScanFile.close()


    response = {'foundDevices': devices}
    return jsonify(response)

@app.route("/pushSystem", methods=['POST'])
def pushSystem():
    print("System Pushed")
    content = request.get_json(force=True)
    #Pretty print
    with open('envConfig/prettyExternalArgs.txt', 'w') as pretty_file:
        for object in content['blocks']:
            pretty_file.write(str(object) + "\n")


    #Dump to file (Actually used)
    serial_content = json.dumps(content['blocks'])
    with open('envConfig/externalArgs.txt', 'w') as json_file:
        json_file.write(serial_content)
    return json.dumps({"status": "pushed"})

@app.route("/runSystem", methods=['POST'])
def respondToRunSystem():
    content = request.get_json(force=True)
    print("Route to run system hit")
    print(content)

    compManagerPath = r'.'
    compManagerName = "compManager.py"
    compManagerArguments = {"runTime": content['runTime']}
    runThread = threading.Thread(target=runSystem(compManagerPath, compManagerName, compManagerArguments))
    runThread.start()

    return json.dumps({"status": "running"})

@app.route("/stopSystem", methods=['POST'])
def respondToStopSystem():
    content = request.get_json(force=True)
    print("Route to stop system hit")
    print(content)

    #Open runFile
    with open('envConfig/runFile.txt') as json_file:
        data = json.load(json_file)
        commsSubPort = data['commsSubPort']

    #Initialize zmq context;
    context = zmq.Context()
    #Connect to the commsSubPort as a publisher.
    pubSocket = context.socket(zmq.PUB)
    pubSocket.connect("tcp://127.0.0.1:" + str(commsSubPort))

    #Give time to connect;
    time.sleep(1)
    #Send signal to compManager
    print("Sending compManagerRequest")
    pubTopic = 'compManagerRequest'
    sendData = {'signalBody': 'stop_system'}

    pubSocket.send_string(pubTopic, zmq.SNDMORE)
    pubSocket.send_json(sendData)

    return json.dumps({"status": "stopping system"})

if __name__=='__main__':
    app.run(host='0.0.0.0', port="9612")
    #app.run(port="8000")
