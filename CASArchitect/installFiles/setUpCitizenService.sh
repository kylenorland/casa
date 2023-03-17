#!/bin/bash
echo "Setting Up Citizen Service"
systemctl stop citizenService.service
sudo rm -f /etc/systemd/system/citizenService.service
sudo cp /home/pi/Desktop/CASArchitect/installFiles/citizenService.service /etc/systemd/system/citizenService.service
systemctl start citizenService.service
systemctl enable citizenService.service
systemctl is-active citizenService.service
