import simplejson as json
JSONDecodeError = json.errors.JSONDecodeError

## The mqtt local messages have the topic of the form csn/sensor-id/#

class Decoder:

    def __init__(self, settings=None):
        # Have default decoded_property if none given
        if not settings is None and "decoded_property" in settings:
            self.decoded_property = settings["decoded_property"]
        else:
            self.decoded_property = "payload_cooked"

    def test(self, topic, msg_bytes):
        if topic.split('/')[0] == 'csn':
            return True
        return False

    ## This decoder currently appends the acp_id and the acp_ts field to the payload
    def decode(self, topic, msg_bytes):
        # Get the sensor id from the topic
        sid = topic.split('/')[1]

        inc_msg = str(msg_bytes,'utf-8')

        try:
            msg_dict = json.loads(inc_msg)
        except JSONDecodeError:
            msg_dict = { "message": msg_bytes }

        msg_dict["acp_id"] = sid

        # DecoderManager will add "acp_ts"

        return msg_dict
