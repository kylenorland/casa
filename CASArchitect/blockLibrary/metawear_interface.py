#Head Material
#leftPorts=1
#rightPorts=1
#type=mwSensorDriver
#done


#Block Description
'''
Author: Kyle Norland
Date: 9/24/20 Update 11/9/20
Description: Metawear gyroscope streaming block
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import os
import datetime
import platform
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
import threading
from threading import Event
import signal
import random


#Globals
keepRunning = True

#-------------------------------------
#-----------LOAD ARGUMENTS------------
#-------------------------------------
#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "gyro--"
with open("blockLogs/gyroStreamLog.txt", "w") as logfile:
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
            #Take the start and run time quickly
            globalStartTime = time.time()
            globalRunTime = jsonArch['runTime']
            logfile.write(macAddress + "\n")
        except:
            logfile.write("Something in the json loading process broke"+ "\n")
            print("Something in the json loading process broke")
    #------------------

    #---------------------------------------
    #-------Connect to messaging back end----------
    #---------------------------------------
    context = zmq.Context()

    pubSocket = context.socket(zmq.PUB)
    pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))

    subSocket = context.socket(zmq.SUB)
    subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

    for subTopic in subTopics:
        subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())
        print("Subscribing to: " + subTopic + "\n")

    #Subscribe to the command chain.
    subTopic = 'commandChain'
    subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

    #---------------------------------------------------------------------
    # -------Metawear State declaration with Data Handlers-----------------
    #---------------------------------------------------------------------
    # Define the data handler
    class State:
        def __init__(self, device):
            self.device = device
            self.samples = 0
            self.callback = FnVoid_VoidP_DataP(self.data_handler)
            self.gyro_callback = FnVoid_VoidP_DataP(self.gyro_data_handler)

        def data_handler(self, ctx, data):
            sendLoad = parse_value(data)
            sendString = str(sendLoad) + "\n"
            outData = {"timestamp": str(time.time() * 1000) ,"type": "acc", "x": sendLoad.x,  "y": sendLoad.y, "z": sendLoad.z, "macAddress": str(macAddress)}

            # Publish it
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(outData)

        def gyro_data_handler(self, ctx, data):
            sendLoad = parse_value(data)
            outData = {"timestamp": str(time.time() * 1000) ,"type": "gyro", "x": sendLoad.x,  "y": sendLoad.y, "z": sendLoad.z, "macAddress": str(macAddress)}

            # Publish it
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(outData)


    #--------------------------------------------
    #----Connect to the metawear sensor----------
    #--------------------------------------------
    states = []
    logfile.write(str(datetime.datetime.now().time()) + "\n")
    logfile.write("Connecting to " + str(macAddress) + "\n")

    #Continuous connection attempt process
    isConnected = False
    while(isConnected == False):
        try:
            print("Trying to connect")
            d = MetaWear(macAddress)
            # d = MetaWear("F2:1F:6E:61:E0:07")
            d.connect()
            logfile.write("Connected to " + d.address + "\n")
            isConnected = True
        except Exception as e:
            print(e)
            print("Retrying connection")
            time.sleep(0.5)
        print("Connected to " + d.address + "\n")
        logfile.write(str(datetime.datetime.now().time()) + "\n")


    # Buzz it
    libmetawear.mbl_mw_haptic_start_motor(d.board, 50, 1000)
    pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
    libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
    libmetawear.mbl_mw_led_write_pattern(d.board, byref(pattern), LedColor.GREEN)
    libmetawear.mbl_mw_led_play(d.board)
    sleep(1)
    libmetawear.mbl_mw_led_stop_and_clear(d.board)

    # Add the device
    states.append(State(d))

    #--------------------------------------------------------------------------------------------------
    #----------Multi-Thread Functions for Acc, Gyro, Buzz Response---- (Hopefully it doesn't interfere)
    #--------------------------------------------------------------------------------------------------
    #Start with just multithreading the buzz response
    class BuzzThread(threading.Thread):
        def __init__(self, s, subSocket, pubSocket, runTime):
            threading.Thread.__init__(self)
            self.s = s
            self.subSocket = subSocket
            self.pubSocket = pubSocket
            self.runTime = runTime

        def run(self):
            print("Starting buzz thread")
            startTime = time.time()
            currentTime = startTime
            global keepRunning

            while (currentTime - startTime < self.runTime) and (keepRunning == True):
                #Receive the data
                topic = self.subSocket.recv_string()
                data = self.subSocket.recv_json()
                print("Interface recieved topic: " + str(topic))
                print(str(data))

                ##Ensure that both csv and value input can be done.
                if topic == "commandChain":
                    if data['command'] == 'stop':
                    #Shut down.
                        keepRunning = False
                else:
                    if 'value' in data:     #Buzz for one second at 50%
                        logfile.write("Buzzing at :" + str(time.time()))
                        libmetawear.mbl_mw_haptic_start_motor(s.device.board, 50, 1000)
                        time.sleep(1)
                    elif 'type' in data:
                        if data['type'] == 'lightSignal':
                            pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
                            libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
                            libmetawear.mbl_mw_led_write_pattern(s.device.board, byref(pattern), LedColor.RED)
                            libmetawear.mbl_mw_led_play(s.device.board)

                            sleep(data['duration'])
                            libmetawear.mbl_mw_led_stop_and_clear(s.device.board)

                    else:
                        #logfile.write("On: " + data['On'] + "Off: " + data['Off'] + " Amplitude: " + str(data['Amplitude']))
                        if float(data['On']) > 0:
                            libmetawear.mbl_mw_haptic_start_motor(s.device.board, int(float(data['Amplitude'])*100), int(float(data['On'])*1000))
                            time.sleep(float(data['On']))
                            time.sleep(float(data['Off']))
    #------------------------------------------------------------------------------------
    #--------------Configure the device------------
    #----------------------------------------------
    for s in states:
        buzzRunTime = globalRunTime - (time.time() - globalStartTime) - 1 #Start the buzzer with the remaining seconds.
        logfile.write("Configuring device")
        #Start Buzz Thread
        bThread = BuzzThread(s, subSocket, pubSocket, buzzRunTime)
        bThread.start()

        #Configure acceleration
        libmetawear.mbl_mw_acc_set_odr(s.device.board, 25.0)
        libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

        #Configure gyroscope
        libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, GyroBmi160Odr._25Hz)
        libmetawear.mbl_mw_gyro_bmi160_set_range(s.device.board, GyroBmi160Range._2000dps)
        libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board)

        # Get acc signal and register callback
        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        # Subscribe to acceleration
        libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.callback)

        #Get gyro signal and register callback
        gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_subscribe(gyro, None, s.gyro_callback)

        #Enable sampling and start the board
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
        libmetawear.mbl_mw_acc_start(s.device.board)

        libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)
        libmetawear.mbl_mw_gyro_bmi160_start(s.device.board)

        #Time to run
        #-------------------------------------------------------
        #--------------Runtime, buzz listener is active---------
        #-------------------------------------------------------
        currentTime = time.time()

        while (currentTime - globalStartTime < globalRunTime - 1) and (keepRunning == True):
            time.sleep(0.25)
            currentTime = time.time()

        print("metawear_interface exiting loop")
        #----------------------------------------------------------
        #------------Ending Data Collection and Shutting Down------
        #----------------------------------------------------------
        # Disable the accelerometer
        libmetawear.mbl_mw_acc_stop(s.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

        #Disable gyroscope
        libmetawear.mbl_mw_gyro_bmi160_stop(s.device.board)
        libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(s.device.board)

        # Unsubscribe from acc
        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal)

        #Unsubscribe from gyro
        gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

        #Disconnect from debugger
        libmetawear.mbl_mw_debug_disconnect(s.device.board)

        s.device.disconnect()
        print("Sensor Disconnected")
        logfile.write("Disconnected")
