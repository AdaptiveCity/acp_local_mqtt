import base64
import simplejson as json
from datetime import datetime

DEBUG = False

class Decoder(object):
    def __init__(self, settings=None):
        print("    Adeunis V3 init()")

        self.name = "adeunis"

        if settings is not None and "decoded_property" in settings:
            self.decoded_property = settings["decoded_property"]
        else:
            self.decoded_property = "payload_cooked"

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("Adeunis test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #cambridge-sensor-network/devices/adeunis-test-3/up

        if topic.startswith("v3/") and "/adeunis-test-" in topic:  #check if decoder name appears in the topic
            if DEBUG:
                print("Adeunis test() success")
            return True
        #elif ("dev_id" in msg):  #dev_id for example, can be any other key
        #    msg=json.loads(message.payload)
        #    if (decoder_name in msg["dev_id"]):
        #        return True
        #    #elif...
        #    else:
        #        return False
        if DEBUG:
            print("Adeunis test() fail")
        return False


    def decode(self, topic, message_bytes):
        ttn_version = 3 if topic.startswith("v3/") else 2

        inc_msg = str(message_bytes,'utf-8')

        if DEBUG:
            print("Adeunis decode str {}".format(inc_msg))

        msg_dict = json.loads(inc_msg)

        if DEBUG:
            print("\nAdeunis decode() DECODED:\n")

        if ttn_version==2:
            rawb64 = msg_dict["payload_raw"]
        else:
            rawb64 = msg_dict["uplink_message"]["frm_payload"]

        if DEBUG:
            print("Adeunis decode() rawb64 {}".format(rawb64))

        decoded = self.decodePayload(self.b64toBytes(rawb64))

        # Add decoded to original message
        msg_dict[self.decoded_property] = decoded

        if DEBUG:
            print("Adeunis decode() decoded {}".format(decoded))

        # extract sensor id
        # add acp_id to original message
        if ttn_version==2:
            msg_dict["acp_id"] = msg_dict["dev_id"]
        else:
            msg_dict["acp_id"] = msg_dict["end_device_ids"]["device_id"]

        msg_dict["acp_type_id"] = "adeunis-test"

        # extract timestamp
        try:
            if ttn_version==2:
                datetime_string = msg_dict["metadata"]["time"]
            else:
                datetime_string = msg_dict["uplink_message"]["received_at"]
            date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            epoch_start = datetime(1970, 1, 1)
            # trim off the nanoseconds
            acp_ts = str((datetime.strptime(datetime_string[:-4]+"Z", date_format) - epoch_start).total_seconds())
            # add acp_ts to original message
            msg_dict["acp_ts"] = acp_ts
        except Exception as e:
            print("Adeunis decode() {} exception while extracting timestamp (no metadata property in message?) {}".format(type(e), e))
            # DecoderManager will add acp_ts using server time

        return msg_dict


    def bin8dec(self, bin):
        num=bin&0xFF;
        if (0x80 & num):
            num = - (0x0100 - num);
        return num

    def bin16dec(self, bin):
        num=bin&0xFFFF;
        if (0x8000 & num):
            num = - (0x010000 - num);
        return num

    def hexToBytes(self, hex):
        bytes = []
        for c in range(0,len(hex),2):
            bytes.append(int(hex[c: c+2],16))
        return bytes

    def b64ToHex(self, b64):
        return base64.b64decode(b64).hex()

    def b64toBytes(self,b64):
        if DEBUG:
            print("Adeunis b64toBytes() {}".format(b64))
        return base64.b64decode(b64)

    def decodePayload(self,bytes):
        if DEBUG:
            print("Adeunis decodePayload() bytes[{}] {}".format(bytes,len(bytes)))

        decoded = {}

        offset = 1 # index into payload for next field

        #// Temperature
        if (bytes[0] & 0x80):  #// temperature present
            decoded['temperature'] = bytes[offset] # // note only works for positive temps
            offset += 1

        #// Button press
        if (bytes[0] & 0x20): # // Button was pressed
            decoded['button'] = True

        #// GPS
        if (bytes[0] & 0x10): # // gps present

            # Latitude

            degrees = (bytes[offset] >> 4) * 10 + (bytes[offset] & 0x0F)
        #//decoded['lat_deg'] = degrees;

            minutes = ((bytes[offset+1] >> 4) * 10 +
                       (bytes[offset+1] & 0x0F) +
                       (bytes[offset+2] >> 4) / 10 +
                       (bytes[offset+2] & 0x0F) / 100 +
                       (bytes[offset+3] >> 4) / 1000)

            #//decoded['lat_mins'] = minutes;

            lat_south = bytes[offset+3] & 0x01
            decoded['latitude'] = round((-1 if lat_south  else 1) * degrees + minutes / 60, 8)

            offset += 4

            # Longitude

            degrees = (bytes[offset] >> 4) * 100 + (bytes[offset] & 0x0F) * 10 + (bytes[offset+1] >> 4)
            #//decoded['lng_deg'] = degrees;

            minutes = (bytes[offset+1] & 0x0F) * 10 + (bytes[offset+2] >> 4) + (bytes[offset+2] & 0x0F) / 10 + (bytes[offset+3] >> 4) / 100
            #//decoded['lng_mins'] = minutes;

            lng_west = bytes[offset+3] & 0x01
            decoded['longitude'] = round((-1 if lng_west else 1) * degrees + minutes / 60, 8)

            decoded['gps_reception'] = bytes[offset+4] >> 4
            decoded['gps_satellites'] = bytes[offset+4] & 0x0F

            offset += 5


        if (bytes[0] & 0x08):  #// Uplink count present
            decoded['uplink_counter'] = bytes[offset]
            offset += 1


        if (bytes[0] & 0x04): #// Downlink count present
            decoded['downlink_counter'] = bytes[offset]
            offset += 1


        # battery voltage in mV
        if (bytes[0] & 0x02):  #// battery mV present
            decoded['battery'] = (bytes[offset] * 256 + bytes[offset+1]) / 1000
            offset += 2


        if (bytes[0] & 0x01):  #// RSSI and SNR present
            decoded['rssi'] = -bytes[offset]; #// rssi always negative
            offset += 1
            decoded['snr'] =   bytes[offset] if (bytes[offset] < 128) else -(256 - bytes[offset]); #// snr in 2's complement


        return decoded
    # end Adeunis
