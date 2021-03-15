#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

systemctl status mosquitto --no-pager

echo
acp_decoders/status.sh
echo
