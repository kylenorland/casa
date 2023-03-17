#!/bin/bash

#Author: Kyle Norland
#Purpose: Set up what's needed to run metawear on a linux computer
#Date: 10/12/20
#Base off of https://mbientlab.com/tutorials/PyLinux.html

hcitool dev

sudo apt-get -y install bluetooth pi-bluetooth bluez blueman bluez-utils
sudo apt install -y git python3-pip libbluetooth-dev libboost-all-dev
echo "Done installing, check if it works"

echo "Restarting the bluetooth"
#sudo /etc/init.d/bluetooth restart

#Install metawear
pip3 install metawear

#systemctl status bluetooth

#sudo systemctl start bluetooth

