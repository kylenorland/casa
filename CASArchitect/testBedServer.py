#!/usr/local/bin/python3
#!/usr/bin/env python3


# Author: Kyle Norland
#----------------------------
#---------IMPORTS------------
#----------------------------
import json
import subprocess
import threading
import asyncio
import requests
import zmq
import random
import sys
import time
import os
import socket
import ipaddress
#import bleak


from subprocess import Popen, PIPE
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

#-------------------------
#-------GLOBALS--------
#------------------------
pubSocket = None
runningIps = []
running_processes = []

#Establish zmq context
context = zmq.Context()

#-------------------------
#-------FUNCTIONS--------
#------------------------

#------------------------------Web Interface Functions--------------------------------
def btscan(scanTime):
    print("Starting Central Bluetooth Scan Procedure")
    uncleanedResults = []
    response = {'foundDevices': []}

    #Send requests to all computers in list.
    async def asyncBTScan(IP):
        r = requests.get("http://" + str(IP) + ":9612/scanEnvironment")
        for device in r.json()['foundDevices']:
            uncleanedResults.append(device)

    #Open computer file
    async def mainScan():
        tasks = []
        with open('envConfig/computerList.txt') as json_file:
            data = json.load(json_file)
            for computer in data['computers']:
                newTask = asyncio.create_task(asyncBTScan(computer['ip']))
                tasks.append(newTask)

            for task in tasks:
                await task
    #Run the scan
    asyncio.run(mainScan())

    #Remove duplicates
    for i in uncleanedResults:
        if i not in response['foundDevices']:
            response['foundDevices'].append(i)
    print(str(response['foundDevices']))


    #Write it to the parsedScan for now
    parsedScanFile= open("envConfig/parsedScan.txt", 'w')
    for device in response['foundDevices']:
        parsedScanFile.write(device + '\n')
    parsedScanFile.close()

    serialResponse = json.dumps(response)
    return serialResponse

def computerScan(network):
    # Author: Kyle Norland
    # Concurrent port scanning from Gunhan Oral: https://gunhanoral.com/python/async-port-check/

    #Needed to avoid no event loop error
    asyncio.set_event_loop(asyncio.new_event_loop())

    #------------------------------------------
    #---------ASYNCHRONOUS SCAN FUNCTIONS   ----------
    #----------------------------------------

    async def check_port(ip, port, loop):
        conn = asyncio.open_connection(ip, port, loop=loop)
        try:
            reader, writer = await asyncio.wait_for(conn, timeout=3)
            print(ip, port, 'ok')
            return (ip, port, True)
        except:
            # print(ip, port, 'nok')
            return (ip, port, False)
        finally:
            if 'writer' in locals():
                writer.close()

    async def check_port_sem(sem, ip, port, loop):
        async with sem:
            return await check_port(ip, port, loop)

    async def run(dests, ports, loop):
        sem = asyncio.Semaphore(400)  # Change this value for concurrency limitation
        tasks = [asyncio.ensure_future(check_port_sem(sem, d, p, loop)) for d in dests for p in ports]
        responses = await asyncio.gather(*tasks)
        return responses

    #-----------------------------------------------
    #---------------Start of the actual code running (main)--------
    #-----------------------------------------------------------
    #Get the current ip network

    #Get the local ip address
    #From: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    print("The local ip is: " + str(IP))

    #Initialize ipv4 address:
    octets = str(IP).split('.')
    firstPartIp = str(octets[0]) + "." + str(octets[1]) + "." + str(octets[2]) + "."
    print("First part ip: " + firstPartIp)
    #--Gets the destination ip addresses and the ports that are desired to be scanned.
    dests = []  # destinations
    for i in range(0, 255):
        #dest = "192.168.87." + str(i)  # Change this based on the current network
        dest = firstPartIp + str(i)  # Change this based on the current network
        dests.append(dest)
    ports = [9612]  # ports

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(dests, ports, loop))
    loop.run_until_complete(future)
    print("Done")
    # print('#'*50)
    # print('Results: ', future.result())

    # Request the details from computers with available ports, and put those details in the text file.
    computerList = open("envConfig/computerList.txt", "w")

    data = {}
    data['computers'] = []


    for result in future.result():
        if (result[2] == True):
            print(result[0])
            r = requests.get('http://' + str(result[0]) + ':' + str(result[1]) + '/participating')
            # print(r.status_code)
            # print(r.headers)
            data['computers'].append({
                'ip': result[0],
                'name': json.loads(r.content)["name"]
            })
            print(json.loads(r.content)["name"])

    with open('envConfig/computerList.txt', 'w') as outfile:
        json.dump(data, outfile)

def refreshBlocks(directory):
    #Create the stub of the blocksList file
    outObject = {"blocks":[]}


    outFile = open("envConfig/blocksList.txt", "w")
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            #Generate new block
            newBlock = {}
            newBlock['name'] = filename[:-3]

            #Open the file and check its top information
            f = open(directory + "/" + filename, "r")
            nothing = f.readline()      #Scrap first part

            for i in range(0, 50):   #Just to make sure it doesn't break everything with a weird EOF
                inputsLine = f.readline()   #Get input
                if inputsLine:
                    inputsLine = inputsLine.strip()
                    if inputsLine == "#done":
                        #print("Breaking on done")
                        break
                    #If line is not the done one, split on "="
                    splitLine = inputsLine.split("=")
                    key = splitLine[0].strip()[1:]
                    value = splitLine[1].strip()
                    #print(key)
                    #print(value)

                    newBlock[str(key)] = str(value)

                    '''
                    inputsLine = inputsLine.strip()

                    newBlock['leftPorts'] = inputsLine[8]

                    outputsLine = f.readline()  # Get output
                    newBlock['rightPorts'] = outputsLine[9]
                    '''
            #print(str(newBlock))
            #Add the object to the list
            outObject['blocks'].append(newBlock)
            #Close the file
            f.close()

    #Dump the whole object into the file
    json.dump(outObject, outFile)
    print("Finished block refresh")
    outFile.close()

def getFileInputs(directory):
    #Create the stub of the blocksList file
    outObject = {"inputs":[]}

    outFile = open("envConfig/fileInputsList.txt", "w")
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            #Generate new input
            newInput = {}
            newInput['name'] = filename
            newInput['leftPorts'] = 0
            newInput['rightPorts'] = 1
            newInput['filePath'] = directory + "/" + filename
            #Add the object to the list
            outObject['inputs'].append(newInput)
            #Close the file
    #Dump the whole object into the file
    json.dump(outObject, outFile)
    print("Finished inputFile load")
    outFile.close()

def getFileOutputs(directory):
    #Create the stub of the blocksList file
    outObject = {"outputs":[]}

    outFile = open("envConfig/fileOutputsList.txt", "w")
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            #Generate new input
            newInput = {}
            newInput['name'] = filename
            newInput['leftPorts'] = 1
            newInput['rightPorts'] = 0
            newInput['filePath'] = directory + "/" + filename
            #Add the object to the list
            outObject['outputs'].append(newInput)
            #Close the file
    #Dump the whole object into the file
    json.dump(outObject, outFile)
    print("Finished outputFile load")
    outFile.close()


#------------------------------Drawio Interface Functions--------------------------------
def start_drawio_change_listener_function(scanTime):
    print("Starting Drawio Change Listener")
    
    #----------------------Global Variables----------------------
    uncleanedResults = []
    response = {'foundDevices': []}
    
    #------------------------Run the Code------------------------
    #Send requests to all computers in list.
    async def asyncBTScan(IP):
        r = requests.get("http://" + str(IP) + ":9612/scanEnvironment")
        for device in r.json()['foundDevices']:
            uncleanedResults.append(device)

    #Open computer file
    async def mainScan():
        tasks = []
        with open('envConfig/computerList.txt') as json_file:
            data = json.load(json_file)
            for computer in data['computers']:
                newTask = asyncio.create_task(asyncBTScan(computer['ip']))
                tasks.append(newTask)

            for task in tasks:
                await task
    #Run the scan
    asyncio.run(mainScan())

    #-----------------------Post Function Runs Code--------------------------
    #Remove duplicates
    for i in uncleanedResults:
        if i not in response['foundDevices']:
            response['foundDevices'].append(i)
    print(str(response['foundDevices']))


    #Write it to the parsedScan for now
    parsedScanFile= open("envConfig/parsedScan.txt", 'w')
    for device in response['foundDevices']:
        parsedScanFile.write(device + '\n')
    parsedScanFile.close()

    serialResponse = json.dumps(response)
    return serialResponse
    
    

def stop_drawio_change_listener_function(scanTime):
    print("Starting Central Bluetooth Scan Procedure")
    uncleanedResults = []
    response = {'foundDevices': []}

    #Send requests to all computers in list.
    async def asyncBTScan(IP):
        r = requests.get("http://" + str(IP) + ":9612/scanEnvironment")
        for device in r.json()['foundDevices']:
            uncleanedResults.append(device)

    #Open computer file
    async def mainScan():
        tasks = []
        with open('envConfig/computerList.txt') as json_file:
            data = json.load(json_file)
            for computer in data['computers']:
                newTask = asyncio.create_task(asyncBTScan(computer['ip']))
                tasks.append(newTask)

            for task in tasks:
                await task
    #Run the scan
    asyncio.run(mainScan())

    #Remove duplicates
    for i in uncleanedResults:
        if i not in response['foundDevices']:
            response['foundDevices'].append(i)
    print(str(response['foundDevices']))


    #Write it to the parsedScan for now
    parsedScanFile= open("envConfig/parsedScan.txt", 'w')
    for device in response['foundDevices']:
        parsedScanFile.write(device + '\n')
    parsedScanFile.close()

    serialResponse = json.dumps(response)
    return serialResponse



#------------------------------Drawn Interface Functions--------------------------------


#--------------------------
#----------ROUTES----------
#---------------------------

#-----------------------Web Pages---------------------------------
@app.route("/")
def main():
    #Return the starting page
    return render_template('landing_page.html')

@app.route("/web_interface.html")
def return_web_interface():
    #Return the web interface page
    return render_template('web_interface.html')

@app.route("/drawio_interface.html")
def return_drawio_interface():
    #Return the drawio interface page
    return render_template('drawio_interface.html')

@app.route("/drawn_interface.html")
def return_drawn_interface():
    #Return the drawn interface page
    return render_template('drawn_interface.html')    

#-----------------Shared Functionality---------------------------

#--------------Drawio Interface Functionality----------------------------  
@app.route("/startDrawioChangeListener", methods=['POST'])
def start_drawio_change_listener():
    global running_processes
    print("HI")
    requestData = request.json
    print(requestData)
    saveName = request.json['saveName']
    print("Starting drawio listener")
    
    #Start the process (sys.executable goes and finds the python executable)
    new_process = subprocess.Popen([sys.executable, "drawio_software/drawio_reader.py", os.path.join('.', 'drawio_software'), saveName, os.path.join('.', 'drawio_software', 'outputs')])
    
    #Add process to record
    new_process_dict = {'name': 'drawio_listener', 'process': new_process}
    running_processes.append(new_process_dict)
    
    print("updated process dict")
    print(running_processes)
    
            
    #testThread = threading.Thread(target=start_drawio_change_listener_function, args=(4,))
    #testThread.start()
    return json.dumps({"status": "Drawio Listener Started"})

@app.route("/stopDrawioChangeListener")
def stop_drawio_change_listener():
    global running_processes
    #Stop the Process
    print("Stopping drawio listener")
    for process_dict in running_processes:
        if process_dict['name'] == 'drawio_listener':
            process_dict['process'].terminate()
        
        #Remove the process entry if it has that name.
    
    print("updated process dict")
    print(running_processes)
    
    #testThread = threading.Thread(target=stop_drawio_change_listener_function, args=(4,))
    #testThread.start()
    return json.dumps({"status": "Drawio Listener Stopped"})
    
@app.route("/startDrawioSystem")
def start_drawio_run_system():
    global running_processes
    print("Starting drawio system")
    
    #Start the process (sys.executable goes and finds the python executable)
    log_file_path = os.path.join('drawio_software', 'blockLogs', 'process_runtime.txt')
    with open(log_file_path, 'w') as f:
        new_process = subprocess.Popen([sys.executable, "drawio_software/process_runtime.py"])
        #new_process = subprocess.Popen([sys.executable, "drawio_software/process_runtime.py"], stdout=f)
    #Add process to record
    new_process_dict = {'name': 'drawio_runtime', 'process': new_process}
    running_processes.append(new_process_dict)
    
    print("updated process dict")
    print(running_processes)
    
            
    #testThread = threading.Thread(target=start_drawio_change_listener_function, args=(4,))
    #testThread.start()
    return json.dumps({"status": "Drawio Listener Started"})
    return json.dumps({"status": "Drawio Run System Started"})

@app.route("/stopDrawioSystem")
def stop_drawio_run_system():
    print("Stopping drawio system")
    
    #Connect to the 9600 port as a publisher.
    pubSocket = context.socket(zmq.PUB)
    pubSocket.bind("tcp://127.0.0.1:" + str(9600))

    #Give time to connect;
    time.sleep(1)
    
    #Send signal to compManager
    print("Sending compManagerRequest")
    pubTopic = 'compManagerRequest'
    sendData = {'signalBody': 'stop_system'}

    pubSocket.send_string(pubTopic, zmq.SNDMORE)
    pubSocket.send_json(sendData)
    
    
    return json.dumps({"status": "Drawio Run System Stopped"})



#--------------Drawn Interface Functionality----------------------------  

#--------------Web Interface Functionality----------------------------    

@app.route("/getIP")
def handleIPRequest():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()

    ipObject = {"ip": IP}
    serialJson = json.dumps(ipObject)
    return serialJson

@app.route("/getSensors")
def basic_return():
    f = open('envConfig/parsedScan.txt', 'r')
    macs = []
    for line in f:
        macs.append(line.strip())
    f.close()
    serialMacs = json.dumps(macs)
    return serialMacs

@app.route("/refreshBlocks")
def refBlocks():
    print("Route to refresh blocks hit")
    directory = r'blockLibrary'     #r' means a raw string (escape codes ignored)
    runThread = threading.Thread(target=refreshBlocks(directory))
    runThread.start()
    return json.dumps({"status": "Blocks Refreshed"})

@app.route("/getBlocks")
def getBlocks():
    with open('envConfig/blocksList.txt') as json_file:
        data = json.load(json_file)
        serialList = json.dumps(data)
        return serialList

@app.route("/getComputers")
def getComputers():
    with open('envConfig/computerList.txt') as json_file:
        data = json.load(json_file)
        serialList = json.dumps(data)
        return serialList

@app.route("/getInputs")
def getInputs():
    '''
    #Bind to the pub sub port
    startPubSub("5556")
    '''
    with open('envConfig/inputsList.txt') as json_file:
        data = json.load(json_file)
        #Scan and add the input files

        serialList = json.dumps(data)
        return serialList

@app.route("/getFileInputs")
def handleFileInputRequest():
    #Run the directory scanner.
    getFileInputs("inputFiles")
    with open('envConfig/fileInputsList.txt') as json_file:
        data = json.load(json_file)
        #Scan and add the input files
        serialList = json.dumps(data)
        return serialList

@app.route("/getFileOutputs")
def handleFileOutputRequest():
    #Run the directory scanner.
    getFileOutputs("outputFiles")
    with open('envConfig/fileOutputsList.txt') as json_file:
        data = json.load(json_file)
        #Scan and add the input files
        serialList = json.dumps(data)
        return serialList


@app.route("/handleInputs", methods=['POST'])
def handleInputs():
    content = request.json
    print(request.json)
    topic = request.json['topic']
    message = request.json['message']
    print(str(topic) + " " + str(message))
    pubSocket.send_string("%d %s" % (int(topic), message))

    return json.dumps({"status": "input recieved"})

@app.route("/btscan")
def bluetoothScan():
    testThread = threading.Thread(target=btscan, args=(4,))
    testThread.start()
    return("hi")

@app.route("/computerScan")
def cScan():
    compThread = threading.Thread(target=computerScan, args=("192.168.87.",))
    compThread.start()
    return("hi")

@app.route("/pushSystem", methods=['POST'])
def pushSystem():
    pushJSON = request.json
    #address = "http://192.168.87.115:9612/tester"
    #x = requests.post(address, json={'value':'hello'})

    #Create list of all connected ips as participatingIps
    participatingIps = []
    for pushGroup in pushJSON['pushGroups']:
        participatingIps.append(pushGroup['ip'])

    #Create boundManager for each
    boundManager = {}
    boundManager['name'] = 'boundManager'
    boundManager['path'] = 'boundManager.py'
    boundManager['subTopics'] = []
    boundManager['pubTopics'] = []
    boundManager['sensorMacs'] = []
    #No ip initialized here
    boundManager['participatingIps'] = participatingIps

    #Push to all the connected computers
    for pushGroup in pushJSON['pushGroups']:
        ip = pushGroup['ip']
        sendData = pushGroup
        newBoundManager = boundManager.copy()
        #Initialize its own block ids
        blockIdList = []
        for block in sendData['blocks']:
            blockIdList.append(block['pubTopics'][0])   #Its id
        newBoundManager['computerIp'] = ip
        newBoundManager['internalIds'] = blockIdList
        #Add a new entry for external entries
        newBoundManager['externalSubs'] = []
        for block in sendData['blocks']:
            for subId in block['subTopics']:
                if subId not in newBoundManager['internalIds']: #If it's not a local subscription, add to this list
                    newBoundManager['externalSubs'].append(subId)
        sendData['blocks'].append(newBoundManager)
        address = "http://" + ip + ":" + "9612" + "/pushSystem"
        print(address)

        res = requests.post(address, json=sendData) #Must be json type

    return json.dumps({"status": "pushed"})

@app.route("/runSystem", methods=['POST'])
def respondToRunSystem():
    content = request.json
    print("Route to run system hit, sending signal out")

    global runningIps
    runningIps = []
    #Signal to connected computers to run
    for ip in content['ips']:
        #Add to the global list;

        runningIps.append(ip)

        #Pass the request on to citizen servers
        runData = {"runTime": content['runTime']}
        print(runData)
        address = "http://" + ip + ":" + "9612" + "/runSystem"
        res = requests.post(address, json=runData)
        print(res.text)

    return json.dumps({"status": "running"})

@app.route("/stopSystem", methods=['POST'])
def respondToStopSystem():
    content = request.json
    print("Route to stop system hit, sending signal out")

    #Signal to connected computers to stop
    global runningIps
    for ip in runningIps:
        stopData = {"stopDetails": 'default'}
        address = "http://" + ip + ":" + "9612" + "/stopSystem"
        res = requests.post(address, json=stopData)
        print(res.text)

    return json.dumps({"status": "stopping system"})

@app.route("/saveSystem", methods=['POST'])
def handleSaveSystemRequest():
    saveName = request.json['saveName']
    data = request.json['saveData']

    print("Saving system at: " + str(saveName))

    #Pretty print (Not actually used)
    with open('savedSystems/prettySave.txt', 'w') as pretty_file:
        for object in data['allObjects']:
            pretty_file.write(str(object) + "\n")

    #Save it to file (used)
    with open('savedSystems/' + str(saveName), 'w') as outfile:
        json.dump(data, outfile)

    #Return all good message
    return json.dumps({"status": "system saved"})

@app.route("/loadSystem", methods=['POST'])
def handleLoadSystemRequest():
    requestData = request.json
    print('Retrieving file stored at: ' + str(requestData['loadName']))
    loadPath = 'savedSystems/' + str(requestData['loadName'])
    #Retrieve saved system and return it to the front end
    with open(loadPath) as json_file:
        data = json.load(json_file)
        return data
#--------------------------
#-------RUN MAIN-----------
#--------------------------
if __name__ == "__main__":
    app.run()
