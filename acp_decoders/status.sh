#!/bin/bash

pid=$(pgrep -f "python3 acp_decoders.py")

if [ $? -eq 0 ]
then
  echo -e "\e[32m●\e[0m" acp_decoders running as PID $pid
  exit 0
else
  echo -e "\e[31m●\e[0m" "ERROR: acp_decoders not running?"
  exit 1
fi

