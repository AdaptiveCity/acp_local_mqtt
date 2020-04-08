#!/bin/bash

echo Reloading decoders

pid=$(pgrep -f "python3 acp_decoders.py")

if [ $? -eq 0 ]
then
  echo "Sending reload (SIGALRM) signal to:"
  ps --no-header $pid
  kill -SIGALRM $pid
  exit 0
else
  echo "ERROR: acp_decoders not running?"
  exit 1
fi
