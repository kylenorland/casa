#!/bin/bash

echo "Starting SSH Activation"

sudo systemctl enable ssh
sudo systemctl start ssh
