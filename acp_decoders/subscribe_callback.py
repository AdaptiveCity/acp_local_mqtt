#!/usr/bin/python
# -*- coding: utf-8 -*-

import paho.mqtt.subscribe as subscribe
import json
import secrets
import importlib
import time
import os

DEBUG=False
#|  PROPERTY_NAME   |  PROPERTY_VALUE      | DECODER  |
#|  dev_id          |  elsys[-co2-041ba9]  | elsys    |
# 
# for unique dict key combine prop_name+prop_val
# 
  
lookup_table={
    "dev_id_elsys-co2-041ba9":"elsys",
    "dev_id_elsys-eye-044504":"elsys",
}

def printf(a):
    if(DEBUG):
        print(a)


def save_to_file(data):

    ts=str(time.strftime("%H:%M-%d-%m-%Y"))
    unix_ts=str(int(time.time()))
    filename=unix_ts+"_"+ts+".json"

    # define the name of the directory to be created
    path = str(os.getcwd())+str(time.strftime("/data_bin/%Y/%m/%d/"))
    printf("Attempting to save in %s" %path)
    try:
        os.makedirs(path)
    except OSError:
        printf ("Creation of the directory %s failed (exists already)" % path)
    else:
        printf ("Successfully created the directory %s" % path)

    f= open(path+filename,"w+")
    f.write(str(data))
    f.close()
    printf("File was written %s" %(path+filename))

def import_all_libs():
    tree = os.listdir('modules')
    print(tree)
    for i in tree:
        path=str(os.getcwd())+"/modules/"+str(i)
        print("attempting ",path)
        module="modules."+i.split('.')[0]
        importlib.import_module(module, package=None)

def dynamic_import(lib):
  
    try:
        return importlib.import_module("modules."+lib, package=None)
    except :
        #Failed to find the right decoder -- return null decoder
        return importlib.import_module("modules.generic",package=None)     #to be changed to directly go to importlib.import_module(lib)

def print_msg(client, userdata, message):
    print(message.topic)
    printf("\n------------------INCOMING-----------------\n")

    dict_obj={}

    #loading the message and parsing it
    inc_msg=str(message.payload,'utf-8')

    msg_json=json.loads(inc_msg)
    printf(msg_json)
    printf("\n")
    
    #acquiring dev_id and dev_id_split to be used for decoder selection
    dev_id=msg_json["dev_id"]
    dev_id_split=dev_id.split('-')[0]

    printf(dev_id)
    printf("Decoder: "+str(dev_id_split))

    time=msg_json["metadata"]["time"]
    printf(time)

    printf("\n------------------DECODED------------------\n")

    rawb64=msg_json["payload_raw"]

    #loading the decoder based on the first word of dev_id
    decoder=dynamic_import(dev_id_split)
    printf("Decoder loaded... "+str(decoder.loaded))

    decoded=decoder.decodePayload(decoder.b64toBytes(rawb64))

    printf(rawb64)
    printf(decoded)
    
    printf("\n------------------WRITING------------------\n")

    #loading all of the parsed data into final json file to be stored in the file system
    dict_obj["acp_ts"]=time
    dict_obj["dev_id"]=dev_id
    dict_obj["payload_cooked"]=decoded
    #print(dict_obj)
    print(msg_json["hardware_serial"],msg_json["dev_id"])
    #print(msg_json["dev_id"])
    #try/catch to be removed -- debug
    try:
        save_to_file(json.dumps(dict_obj))
    except:
        save_to_file('{"data":"failed to write to disk"}')
    printf("\n------------------FINITO------------------\n")

    
def main():
    topic="cambridge-sensor-network/devices/+/up"                     #"cambridge-sensor-network/devices/elsys-eye-044501/#"
    printf("Starting MQTT subscription for %s" %topic)
    subscribe.callback(print_msg, topic, hostname="eu.thethings.network", auth={'username':secrets.username, 'password':secrets.password})


if __name__ == "__main__":
    main()

