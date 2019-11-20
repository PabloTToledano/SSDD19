#!/bin/bash
#Lo que hay que hacer es recoger la salida del downloader para luego poder meterla como entrada del orchestrator
PROXY=$(tempfile)
./Downloader.py --Ice.Config=Server.config>$PROXY 

sleep 1

./orchestrator.py --Ice.Config=Server.config "$(cat $PROXY)"


