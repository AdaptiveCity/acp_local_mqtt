import base64
import simplejson as json
from datetime import datetime

DEBUG = False

class Decoder(object):
    def __init__(self, settings=None):
        print("    sensedge init()")

        self.name = "sensedge"

        if settings is not None and "decoded_property" in settings:
            self.decoded_property = settings["decoded_property"]
        else:
            self.decoded_property = "payload_cooked"

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("sensedge test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #cambridge-sensor-network/devices/adeunis-test-3/up

        if topic.startswith("v3/") and "/snsedg-" in topic:  #check if decoder name appears in the topic
            if DEBUG:
                print("sensedge test() success")
            return True
        if DEBUG:
            print("sensedge test() fail")
        return False


    def decode(self, topic, message_bytes):
        # First lets set a flag for which version of TTN we're dealing with
        ttn_version = 3 if topic.startswith("v3/") else 2

        inc_msg = str(message_bytes,'utf-8')

        if DEBUG:
            print("sensedge decode str {}".format(inc_msg))

        msg_dict = json.loads(inc_msg)

        # extract sensor id
        # add acp_id to original message
        if ttn_version==2:
            msg_dict["acp_id"] = msg_dict["dev_id"]
        else:
            msg_dict["acp_id"] = msg_dict["end_device_ids"]["device_id"]

        type_array = msg_dict["acp_id"].split("-")

        if len(type_array) >= 3:
            msg_dict["acp_type_id"] = type_array[0]+"-"+type_array[1]

        if DEBUG:
            print("\nsensedge decode() DECODED:\n")

        if ttn_version==2:
            rawb64 = msg_dict["payload_raw"]
        else:
            rawb64 = msg_dict["uplink_message"]["frm_payload"]

        if DEBUG:
            print("sensedge decode() rawb64 {}".format(rawb64))

        decoded = self.decodePayload(self.b64toBytes(rawb64))

        # Add decoded to original message
        msg_dict[self.decoded_property] = decoded

        if DEBUG:
            print("sensedge decode() decoded {}".format(decoded))

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
            print("sensedge metadata.time decode() {} exception {}".format(type(e), e))
            # DecoderManager will add acp_ts using server time

        return msg_dict


    def bin8dec(self, bin):
        num = bin & 0xFF
        if (0x80 & num):
            num = - (0x0100 - num)
        return num

    def bin16dec(self, bin):
        num= bin & 0xFFFF
        if (0x8000 & num):
            num = - (0x010000 - num)
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
            print("sensedge b64toBytes() {}".format(b64))
        return base64.b64decode(b64)

    def temp(self,T1,T01):
        if T1 != 0 or T01 > 0:
            if T1 > 128:
                return 0 - (256 - (T1 - (256 - T01) / 100 ))
            else:
                return T1 + T01 / 100
        else:
            return 0 - (T1 + (256 - T01) / 100 )

    def decodePayload(self,bytes):
        if DEBUG:
            print("sensedge decodePayload() bytes[{}] {}".format(bytes,len(bytes)))

        decoded = {}

        if len(bytes) == 7: # If Data Packet
            Status = bytes[0]
            Distance = bytes[1] << 8 | bytes[2]
            Reliability = bytes[3]
            Battery = bytes[4]
            TC1 = bytes[5]
            TC01 = bytes[6]

            decoded['status'] = Status
            decoded['distance'] = Distance
            decoded['reliability'] = Reliability
            decoded['temperature'] = self.temp(TC1,TC01)
            decoded['battery'] = (Battery+100)/100

        else: # If Config packet
            Period = bytes[0]
            HeartbeatPeriod = bytes[1]
            MovementThreshold = bytes[2]
            PacketConfirm = bytes[3]
            HWANT = bytes[4]
            FW = bytes[5]

            if (HWANT > 192):
                ANT = "868/915"
                HW = HWANT - 192
            elif (HWANT > 64):
                ANT = "915"
                HW = HWANT - 64
            else:
                ANT = "868"
                HW = HWANT

            decoded['period'] = Period
            decoded['heartbeat_period'] = HeartbeatPeriod
            decoded['movement_threshold'] = MovementThreshold
            decoded['packet_confirm'] = PacketConfirm
            decoded['HW'] = HW
            decoded['antenna'] = ANT
            decoded['FW'] = FW

        return decoded

    # end sensedge
