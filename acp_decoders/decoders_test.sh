#!/usr/bin/env python3

import argparse
import os, sys
import json
from datetime import datetime
from acp_decoders import DecoderManager

DEBUG = True

####################################################################
# Set up argument parsing
####################################################################

def parse_init():
    parser = argparse.ArgumentParser(description='Test run json sensor reading through acp_decoders.')
    parser.add_argument('topic',help='The MQTT topic, e.g. v3/cambridge-net-3@ttn/devices/elsys-co2-010203/up.')
    parser.add_argument('jsonfile',help='The JSON file containing the reading message from TTN, e.g. decoder_tests/elsys-co2.json.')

    return parser

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':

    parser = parse_init()
    args = parser.parse_args()

    dm = DecoderManager()

    dm.read_settings()

    with open(args.jsonfile,"r") as json_file:
        msg = json_file.read()

    msg_bytes = bytes(msg,'utf-8')

    decoded = dm.handle_input_message(args.topic,msg_bytes,testing=True)

    print("Decoded Summary:")
    print(f'  Sensor: {decoded["acp_id"]}')
    print(f'  acp_ts: {decoded["acp_ts"]} (UTC {datetime.fromtimestamp(float(decoded["acp_ts"]),tz=None)})')
    print(f'  acp_type_id: {decoded["acp_type_id"]}')
    print("Decoded Message:")
    print(json.dumps(decoded,indent=4))
