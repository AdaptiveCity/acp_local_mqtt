#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR

nohup acp_decoders/run.sh >>/var/log/acp_prod/acp_decoders.log 2>>/var/log/acp_prod/acp_decoders.err & disown

