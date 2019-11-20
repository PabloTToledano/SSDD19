#!/bin/bash
#Lo que hay que hacer es recoger la salida del downloader para luego poder meterla como entrada del orchestrator
proxy_downloader=$(./Downloader.py --Ice.Config="Server.config")
echo "$proxy_downloader"