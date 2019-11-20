#!/bin/bash
#En principio debe coger argumentos del bash y pasárselos al client
if [$# -ne 3]; 
then
    echo "Sintaxis incorrecta. Ejecuta el programa ./run_client.sh <proxy> <url>"
else
    ./Client.py $1 $2
fi