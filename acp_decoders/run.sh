#!/bin/bash

##################################
# run.sh
# Used to start acp_decoders
##################################

# Find the directory this script is being run from
# typically "/home/acp_prod/acp_local_mqtt/acp_decoders"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

pid=$(pgrep -f "python3 acp_decoders.py")

if [ $? -eq 0 ]
then
    echo $(date '+%s') $SCRIPT_DIR/run.sh FAIL: acp_decoders.py already running as PID $pid
    exit 1
else
    source venv/bin/activate
    python3 acp_decoders.py
    exit 0
fi

