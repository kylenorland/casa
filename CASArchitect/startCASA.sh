#!/bin/bash
echo "Starting CASA"

echo "Starting Front End Server"
gnome-terminal --geometry=80x20+30+30 -- bash -c 'python3 testBedServer.py;$SHELL'

echo "Starting local citizen server"
gnome-terminal --geometry=80x20+30+450 -- bash -c 'python3 citizenServer.py;$SHELL'

firefox localhost:5000

#read varname


