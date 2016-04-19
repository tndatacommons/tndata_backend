#!/bin/bash

# Kill all of our existing rqworkers
echo ''
echo "Looking for 'manage.py rqworker default' processes..."
ps aux  | grep 'python manage.py rqworker default' | wc -l

echo ''
echo "Killing them..."
sudo kill $(ps aux  | grep 'python manage.py rqworker default' | awk '{print $2}')

echo ''
echo "Now: "
ps aux  | grep 'python manage.py rqworker default' | awk '{print $1, $2, $11}'
echo ''
echo ''
