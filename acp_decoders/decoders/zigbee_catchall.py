import simplejson as json
from datetime import datetime

DEBUG = False

# Zigbee catch-all decoder, just adds the following properties:
# Only changes topic:
#  csn-zigbee/acp_id -> acp/acp_id/csn-zigbee
class Decoder(object):
    def __init__(self, settings=None):
        print("   zigbee_catchall init()")

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("zigbee_catchall test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #cambridge-sensor-network/devices/zigbee_catchall-test-3/up

        if ("csn-zigbee" in topic):  #check if application name appears in the topic
            if DEBUG:
                print("zigbee_catchall test() success")
            return True
        #elif ("dev_id" in msg):  #dev_id for example, can be any other key
        #    msg=json.loads(message.payload)
        #    if (decoder_name in msg["dev_id"]):
        #        return True
        #    #elif...
        #    else:
        #        return False
        if DEBUG:
            print("zigbee_catchall test() fail")
        return False


    def decode(self, topic, message_bytes):
        inc_msg = str(message_bytes,'utf-8')

        if DEBUG:
            print("zigbee_catchall decode str {}".format(inc_msg))

        # Zigbee topic is "csn-zigbee/<acp_id>[/<other stuff>]"
        topic_parts = topic.split('/',2) # split into max 4 topic_parts

        output_topic = "acp/"+topic_parts[1]+"/"+topic_parts[0]

        if len(topic_parts) > 2:
            output_topic += "/" + topic_parts[2]

        # For this version of the decoder the original message from
        # deconz2acp will be published unchanged.
        msg_dict = json.loads(message_bytes)
        return msg_dict

    # end zigbee_catchall
