import simplejson as json
from datetime import datetime

DEBUG = False

# TTN catch-all decoder, just adds the following properties:
# * acp_id (derived from dev_id)
# * acp_ts (derived from ttn network server [metadata][time]

class Decoder(object):
    def __init__(self, settings=None):
        print("   ttn_catchall  init()")

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("ttn_catchall test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #cambridge-sensor-network/devices/ttn_catchall-test-3/up

        if ("cambridge-sensor-network" in topic):  #check if application name appears in the topic
            if DEBUG:
                print("ttn_catchall test() success")
            return True
        #elif ("dev_id" in msg):  #dev_id for example, can be any other key
        #    msg=json.loads(message.payload)
        #    if (decoder_name in msg["dev_id"]):
        #        return True
        #    #elif...
        #    else:
        #        return False
        if DEBUG:
            print("ttn_catchall test() fail")
        return False


    def decode(self, topic, message_bytes):
        inc_msg = str(message_bytes,'utf-8')

        if DEBUG:
            print("ttn_catchall decode str {}".format(inc_msg))

        msg_dict = json.loads(inc_msg)

        # extract sensor id
        # add acp_id to original message
        msg_dict["acp_id"] = msg_dict["dev_id"]

        type_array = msg_dict["dev_id"].split("-")

        if len(type_array) >= 3:
            msg_dict["acp_type_id"] = type_array[0]+"-"+type_array[1]

        # extract timestamp
        try:
            datetime_string = msg_dict["metadata"]["time"]
            date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            epoch_start = datetime(1970, 1, 1)
            # trim off the nanoseconds
            acp_ts = str((datetime.strptime(datetime_string[:-4]+"Z", date_format) - epoch_start).total_seconds())
            # add acp_ts to original message
            msg_dict["acp_ts"] = acp_ts
        except Exception as e:
            print("ttn_catchall decode() {} exception {}".format(type(e), e))
            # DecoderManager will add acp_ts using server time

        return msg_dict

    # end ttn_catchall
