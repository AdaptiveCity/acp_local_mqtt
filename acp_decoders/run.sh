#!/bin/bash

##################################
# run.sh
# Used to start acp_decoders
##################################

# Find the directory this script is being run from
# typically "/home/acp_prod/acp_local_mqtt/acp_decoders"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

source venv/bin/activate

python3 acp_decoders.py

# note SHOULD PIPE OUTPUT TO /var/log/acp_prod

