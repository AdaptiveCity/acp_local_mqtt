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

    if decoded is None:
        exit(1)

    print("\nDecoded Message:")
    print(json.dumps(decoded,indent=4))

    print("\nDecoded Summary:")
    # acp_id
    print(f'  Sensor: {decoded["acp_id"]}')

    # acp_ts
    acp_ts_datetime = datetime.fromtimestamp(float(decoded["acp_ts"]),tz=None)
    timestamp_delta = (datetime.now() - acp_ts_datetime).total_seconds()
    print(f'  acp_ts: {decoded["acp_ts"]} (UTC {acp_ts_datetime})')
    if timestamp_delta < 1:
        print(f'          Timestamp not recovered from message, now() used instead')

    # acp_type_id
    if "acp_type_id" in decoded:
        print(f'  acp_type_id: {decoded["acp_type_id"]}')
    else:
        print(f'  acp_type_id not found in decoded message')

    # payload_cooked
    if "payload_cooked" in decoded:
        print(f'  payload_cooked: {json.dumps(decoded["payload_cooked"],indent=4)}')
    else:
        print(f'  payload_cooked not found in decoded message')
