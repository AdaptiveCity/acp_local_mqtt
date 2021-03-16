##################################################################
##################################################################
# acp_decoders (re-written GMQTT -> PAHO)
#
# Dynamically loads multiple Decoder classes, each providing
#     .test(topic,msg_bytes)
#     .decode(topic, msg_bytes)
#
# Iterates through each incoming message and testing
# against each decoder. On first successful .test() will call
# .decode() - see handle_input_message() - and then
# re-publish the decoded message.
#
# Uses 'settings.json' for required input/output connect info.
#
##################################################################
##################################################################

import simplejson as json

import asyncio
import os
import sys
import signal
import time
import importlib
from datetime import datetime, timezone

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

import paho.mqtt.client as mqtt

# gmqtt compatible with uvloop
import uvloop

log_level = 2 # 3=default, 2=info, 1=debug

#import logging
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')


##################################################################
##################################################################
# DecoderManager
##################################################################
##################################################################

class DecoderManager():

    ###################
    # Sync class init
    ###################
    def __init__(self):
        print("acp_decoders_paho.py DecoderManager __init__", flush=True)
        print("{} acp_decoders_paho.py initialized\n".format(self.ts_string()),file=sys.stderr,flush=True)

        # load settings.json into self.settings
        self.read_settings()


    #####################################
    # Signal handler for SIGINT, SIGTERM
    #####################################
    def ask_exit(self,*args):
        self.STOP.set()

    #####################################
    # Signal handler for SIGALRM
    #####################################
    def reload(self,*args):
        self.load_decoders_file()

    #####################################
    # Return current timestamp as string
    #####################################
    def ts_string(self):
        return '{:.6f}'.format(time.time())

    ###############################################################
    # initialization
    ###############################################################
    def start(self):
        print("{} acp_decoders started\n".format(self.ts_string()),file=sys.stderr,flush=True)
        # Define async events for exit and reload (will set via signals)
        #self.STOP = asyncio.Event()
        #self.RELOAD = asyncio.Event()

        self.client = mqtt.Client("acp_decoders_paho"+str(log_level)+"_"+datetime.now().strftime("%Y-%m-%d"))

        # Connect input and output MQTT brokers (which can be same or different)
        self.connect_mqtt()

        self.client.loop_forever()


    def connect_mqtt(self):
        print("\n{} connecting to MQTT {}:{} as {}".format(
            self.ts_string(),
            self.settings["input_mqtt"]["host"],
            self.settings["input_mqtt"]["port"],
            self.settings["input_mqtt"]["user"],
            ),file=sys.stderr,flush=True)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe

        user = self.settings["input_mqtt"]["user"]
        password = self.settings["input_mqtt"]["password"]
        host = self.settings["input_mqtt"]["host"]
        port = self.settings["input_mqtt"]["port"]

        self.client.username_pw_set(user, password=password)

        self.client.connect(host, port, keepalive=30)

    ###############################################################
    # Sensor data message handler for incoming messages
    ###############################################################

    def handle_input_message(self, topic, msg_bytes, testing=False):
        acp_ts = self.ts_string()
        msg_is_decoded = False
        for decoder in self.decoders:
            try:
                if decoder["decoder"].test(topic, msg_bytes):
                    decoded = decoder["decoder"].decode(topic, msg_bytes)
                    # If no acp_ts from decoder, insert from server time
                    if not "acp_ts" in decoded:
                        decoded["acp_ts"] = acp_ts

                    if log_level < 3:
                        print("{} {} decoded by {}".format(
                            acp_ts,
                            decoded["acp_id"],
                            decoder["name"]), flush=True)

                    msg_is_decoded = True
                    break # terminate the loop through decoders when first is found
            except:
                print("{} acp_decoders.py exception from decoder {}:".format(acp_ts, decoder["name"]),
                      file=sys.stderr,
                      flush=True)

        # testing=True will bypass MQTT and return the decoded message
        if testing:
            if msg_is_decoded:
                return decoded
            else:
                print("Message not decoded")
        elif msg_is_decoded:
            self.send_output_message(topic, decoded)
        else:
            print("{} Incoming message not decoded\n{}\n".format(
                acp_ts,
                msg_bytes), file=sys.stderr, flush=True)

    ##########################################################################
    # Publish decoded message to output topic.
    # E.g. input topic might be 'csn/status/tele/power'
    # Output topic will be <prefix>/<acp_id>/<original topic>.
    # i.e. 'acp/tas-pow-45c7e8/csn/status/tele/power'
    # where 'tas-pow-45c7e8' is the acp_id derived by a decoder.
    ##########################################################################

    def send_output_message(self, topic_in, decoded_dict):
        # Build output topic <prefix>/<acp_id>/<original topic>
        output_topic = self.settings["output_mqtt"]["topic_prefix"]
        if "acp_id" in decoded_dict:
            output_topic += decoded_dict["acp_id"]+"/"
        else:
            output_topic += "unknown_id/"
        output_topic += topic_in
        if log_level < 3:
            print("{} Publishing topic {}".format(
                self.ts_string(),
                output_topic), flush=True)

        # Publish output message
        msg_bytes = json.dumps(decoded_dict)
        if log_level < 2:
            print("{} publishing {}".format(self.ts_string(),msg_bytes), flush=True)

        self.client.publish(output_topic, msg_bytes, qos=0)

    ###############################################################
    # MQTT INPUT
    ###############################################################

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            print('{} Connected to {} as {}'.format(
                self.ts_string(),
                self.settings["input_mqtt"]["host"],
                self.settings["input_mqtt"]["user"]),file=sys.stderr, flush=True)
            print('{} Subscribing to {}'.format(
                self.ts_string(),
                self.settings["input_mqtt"]["topic"]),file=sys.stderr, flush=True)
            self.client.subscribe('#',1) # default is qos=0
        else:
            print("Bad connection Returned code=",rc)
            print('{} Connect FAILED to {} as {} rc={}'.format(
                self.ts_string(),
                self.settings["input_mqtt"]["host"],
                self.settings["input_mqtt"]["user"]),
                rc,
                file=sys.stderr, flush=True)

    def on_message(self, client, userdata, message):
        # IMPORTANT! We avoid a loop by ignoring input messages with the output prefix
        if not message.topic.startswith(self.settings["output_mqtt"]["topic_prefix"]):
            if log_level < 2:
                print("{} acp_decoders INPUT MSG: {}\n{}".format(
                    self.ts_string(),
                    message.topic,
                    message.payload),file=sys.stderr, flush=True)
            elif log_level < 3:
                print("{} acp_decoders INPUT MSG: {}".format(
                    self.ts_string(),
                    message.topic), flush=True)
            self.handle_input_message(message.topic, message.payload)
        elif log_level < 3:
            print("{} acp_decoders skipping INPUT MSG on output topic: {}".format(
                self.ts_string(),
                message.topic),flush=True)

    def on_disconnect(self,client, userdata, rc):
        print("\n{} acp_decoders INPUT Disconnected".format(
            self.ts_string()),file=sys.stderr,flush=True)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print('{} acp_decoders INPUT SUBSCRIBED to {}'.format(
            self.ts_string(),
            self.settings["input_mqtt"]["topic"]),file=sys.stderr, flush=True)

    ###############################################################
    # MQTT OUTPUT
    ###############################################################

    def output_on_connect(self, client, flags, rc, properties):
        # Log a connection statement to stdout and stderr
        print('OUTPUT Connected to {} as {}'.format(
            self.settings["output_mqtt"]["host"],
            self.settings["output_mqtt"]["user"]), flush=True)
        print('{} INPUT Connected to {} as {}'.format(
            self.ts_string(),
            self.settings["output_mqtt"]["host"],
            self.settings["output_mqtt"]["user"]),file=sys.stderr,flush=True)

    def output_on_disconnect(self, client, packet, exc=None):
        print('OUTPUT Disconnected', flush=True)
        print("{} OUTPUT Disconnected\n".format(self.ts_string()),file=sys.stderr,flush=True)

    # These GMQTT methods here for completeness although not used

    def output_on_message(self, client, topic, msg_bytes, qos, properties):
        print('OUTPUT RECV MSG?:', msg_bytes, flush=True)

    def output_on_subscribe(self, client, mid, qos, properties):
        print('{} OUTPUT SUBSCRIBED?'.format(self.ts_string()), flush=True)

    ###############################################################
    # Settings, including loading enabled decoders
    #
    # Builds self.settings from file "settings.json"
    # Then loads decoders listed in the setting "decoders_file"
    ###############################################################

    def read_settings(self):
        with open('settings.json', 'r') as sf:
            settings_data = sf.read()

            # parse file
        self.settings = json.loads(settings_data)
        self.load_decoders_file()
        print("{} settings.json loaded".format(self.ts_string()),file=sys.stderr,flush=True)

    def load_decoders_file(self):
        # getting settings filename for decoders list (json)
        decoders_file = self.settings["decoders_file"]

        # read the json file
        with open(decoders_file, 'r') as df:
            decoders_data = df.read()

        # parse to a python dictionary
        decoders_obj = json.loads(decoders_data)

        # store the new list of decoders as settings["decoders"]
        self.settings["decoders"] = decoders_obj["decoders"]

        # import/reload the decoders
        self.import_decoders(self.settings["decoders"])

    # import a list of decoder names
    def import_decoders(self, new_decoders):
        self.decoders = []
        for decoder_name in new_decoders:
            self.import_decoder(decoder_name)

    # import a decoder, given name
    # Will add { "name": , "decoder": } to self.decoders list
    def import_decoder(self, decoder_name):
        print("loading Decoder {}".format(decoder_name), flush=True)
        module_name = 'decoders.'+decoder_name
        # A new module can be imported with importlib.import_module()
        # BUT an already loaded module must use importlib.reload for update to work.
        if module_name in sys.modules:
            module = sys.modules[module_name]
            importlib.reload(module)
        else:
            module = importlib.import_module(module_name)
        # now we have the refreshed/new module, so put Decoder on list self.decoders
        decoder = module.Decoder(self.settings)
        print("    loaded Decoder {}".format(decoder_name), flush=True)
        self.decoders.append({"name": decoder_name, "decoder": decoder })

    ###############################################################
    # CLEANUP on EXIT SIGNAL (SIGINT or SIGTERM)
    ###############################################################

    def finish(self):
        #await self.STOP.wait()
        print("\nDecoderManager interrupted, closing MQTT clients", flush=True)
        print("{} DecoderManager interrupted - disconnecting\n".format(
            self.ts_string()),file=sys.stderr,flush=True)
        #await self.input_client.disconnect()
        #await self.output_client.disconnect()


###################################################################
# Program main
# Sets up asyncio, runs async_main()
###################################################################
if __name__ == '__main__':

    print(f'acp_decoders_paho loaded')

    # Instantiate a DecoderManager
    decoder_manager = DecoderManager()

    # Add signal handlers for EXIT and RELOAD
    #loop.add_signal_handler(signal.SIGINT, decoder_manager.ask_exit)
    #loop.add_signal_handler(signal.SIGTERM, decoder_manager.ask_exit)
    #loop.add_signal_handler(signal.SIGALRM, decoder_manager.reload)

    decoder_manager.start()

    # This call to 'finish' awaits the 'STOP' event
    #await decoder_manager.finish()

    # Client(client_id=””, clean_session=True, userdata=None, protocol=MQTTv311, transport=”tcp”)

    #client = mqtt.Client()
    #client.username_pw_set('csn_node', password='csn_node')
    #client.on_message = on_message
    #print(f'connecting ijl20-iot')
    #client.connect('localhost')
    #client.loop_start()
    #client.subscribe('test')
    #client.publish('test',f'acp_decoders_paho')
    #print(f'finished')
    #time.sleep(4) # wait
    #client.loop_stop() #stop the loop
