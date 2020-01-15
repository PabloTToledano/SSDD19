#!/bin/sh
#

echo "Downloading audio..."
./client.py -d <url> \
--Ice.Config=client.config

echo ""
echo "List request..."
./client.py --Ice.Config=client.config

echo ""
echo "Init transfer..."
./client.py -t <file_name> \
--Ice.Config=client.config