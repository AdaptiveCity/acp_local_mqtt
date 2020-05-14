#!/bin/bash

##################################
# run.sh
# Used to start acp_decoders
##################################

# Find the directory this script is being run from
# typically "/home/acp_prod/acp_local_mqtt"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# QUIT if acp_decoders is already running
pid=$(pgrep -f "python3 acp_decoders.py")
if [ $? -eq 0 ]
then
    echo $(date '+%s') $SCRIPT_DIR/run.sh FAIL: acp_decoders.py already running as PID $pid
    echo $(date '+%s') $SCRIPT_DIR/run.sh FAIL: acp_decoders.py already running as PID $pid >>/var/log/acp_prod/acp_decoders.err
    exit 1
fi

# otherwise, run acp_decoders

cd $SCRIPT_DIR/acp_decoders

source venv/bin/activate
nohup python3 acp_decoders.py >>/dev/null 2>>/var/log/acp_prod/acp_decoders.err & disown
exit 0

