#!/bin/bash

##################################
# run.sh
# Used to start acp_decoders
##################################

# Find the directory this script is being run from
# typically "/home/acp_prod/acp_local_mqtt/acp_decoders"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$SCRIPT_DIR/acp_decoders/run.sh >>/var/log/acp_prod/acp_decoders.log 2>/var/log/acp_prod/acp_decoders.err

