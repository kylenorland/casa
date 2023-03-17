#Head Material
#leftPorts=1
#rightPorts=1
#type=mwSensorDriver
#done


#Block Description
'''
Author: Kyle Norland
Date: 9/25/20
Description: Connects to a metawear sensor and buzzes it for 1 second at 50% when it recieves a value of 1 (Length and intensity preset for now)
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import sys
import datetime
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
import time

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "mid block--"

#Open log file
with open("blockLogs/buzzLog.txt", "w") as logfile:
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
            macAddress = jsonArch['sensorMacs'][0]
            print("The mac address is: " + str(macAddress))
        except:
            logfile.write("Something in the json loading process broke"+ "\n")
            print("Something in the json loading process broke")
    #------------------


    #----------------------------------------------
    #----------Connect to the metawear sensor------
    #-----------------------------------------------

    sensors = []

    # Define the data handler
    class mwSensor:
        def __init__(self, device):
            self.device = device
            self.samples = 0
            self.callback = FnVoid_VoidP_DataP(self.data_handler)

        def data_handler(self, ctx, data):
            sendLoad = parse_value(data)
            sendString = str(sendLoad) + "\n"
            data = {"value": sendString}


    logfile.write(str(datetime.datetime.now().time()) + "\n")
    
    logfile.write("Connecting to " + str(macAddress) + "\n")
    try:
        print("Trying to connect to: " + str(macAddress))
        d = MetaWear(macAddress)
        #d = MetaWear("F2:1F:6E:61:E0:07")
        d.connect()
        logfile.write("Connected to " + d.address + "\n")
        print("Connected to " + d.address + "\n")
    except:
        time.sleep(2)
        print("Retrying connection")
        d.connect()
        
    logfile.write(str(datetime.datetime.now().time()) + "\n")

    # Buzz it initially
    libmetawear.mbl_mw_haptic_start_motor(d.board, 50, 1000)
    time.sleep(1)

    # Add the device
    sensors.append(mwSensor(d))
    s = mwSensor(d)
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)


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
    #---------------Action loop----------------------------
    #-------------------------------------------------
    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Process it
        logfile.write(str(data) + "\n")

        #Ensure that both csv and value input can be done.
        if 'value' in data:     #Buzz for one second at 50%
            logfile.write("Buzzing at :" + str(time.time()))
            libmetawear.mbl_mw_haptic_start_motor(s.device.board, 50, 1000)
            time.sleep(1)
        else:
            logfile.write("OnOff: " + data['OnOff'] + " Intensity: " + str(data['Intensity'] + " Time: " + data['Time']))
            if data['OnOff'] == "1":
                libmetawear.mbl_mw_haptic_start_motor(s.device.board, int(float(data['Intensity'])*100), int(float(data['Time'])*1000))
                time.sleep(float(data['Time']))
            if data['OnOff'] == "0":
                time.sleep(float(data['Time']))


