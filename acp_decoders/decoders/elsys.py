#
# Elsys sensor decoder
#
# Instantiate with:
#    decoder = Elsys(expand, decoded_property)
#    where:
#        expand = [True] | False:  decoder returns expanded original message with "payload_decoded" property.
#        decoded_property = <string> ["payload_decoded"]: contains property name to contain decoded message
#
# Implements:
#    test(message, params): returns true|false whether this decoder will handle message
#    decode(message, params): returns Python dictionary of decoded message, or raises DecodeError

DEBUG = False

import base64
import simplejson as json
from datetime import datetime

TYPE_TEMP         = 0x01 #temp 2 bytes -3276.8°C -->3276.7°C
TYPE_RH           = 0x02 #Humidity 1 byte  0-100%
TYPE_ACC          = 0x03 #acceleration 3 bytes X,Y,Z -128 --> 127 +/-63=1G
TYPE_LIGHT        = 0x04 #Light 2 bytes 0-->65535 Lux
TYPE_MOTION       = 0x05 #No of motion 1 byte  0-255
TYPE_CO2          = 0x06 #Co2 2 bytes 0-65535 ppm
TYPE_VDD          = 0x07 #VDD 2byte 0-65535mV
TYPE_ANALOG1      = 0x08 #VDD 2byte 0-65535mV
TYPE_GPS          = 0x09 #3bytes lat 3bytes long binary
TYPE_PULSE1       = 0x0A #2bytes relative pulse count
TYPE_PULSE1_ABS   = 0x0B #4bytes no 0->0xFFFFFFFF
TYPE_EXT_TEMP1    = 0x0C #2bytes -3276.5C-->3276.5C
TYPE_EXT_DIGITAL  = 0x0D #1bytes value 1 or 0
TYPE_EXT_DISTANCE = 0x0E     #2bytes distance in mm
TYPE_ACC_MOTION   = 0x0F     #1byte number of vibration/motion
TYPE_IR_TEMP      = 0x10     #2bytes internal temp 2bytes external temp -3276.5C-->3276.5C
TYPE_OCCUPANCY    = 0x11     #1byte data
TYPE_WATERLEAK    = 0x12     #1byte data 0-255
TYPE_GRIDEYE      = 0x13     #65byte temperature data 1byte ref+64byte external temp
TYPE_PRESSURE     = 0x14     #4byte pressure data (hPa)
TYPE_SOUND        = 0x15     #2byte sound data (peak/avg)
TYPE_PULSE2       = 0x16     #2bytes 0-->0xFFFF
TYPE_PULSE2_ABS   = 0x17     #4bytes no 0->0xFFFFFFFF
TYPE_ANALOG2      = 0x18     #2bytes voltage in mV
TYPE_EXT_TEMP2    = 0x19     #2bytes -3276.5C-->3276.5C
TYPE_EXT_DIGITAL2 = 0x1A     # 1bytes value 1 or 0
TYPE_EXT_ANALOG_UV= 0x1B     # 4 bytes signed int (uV)
TYPE_DEBUG        = 0x3D     # 4bytes debug

class Decoder(object):
    def __init__(self,settings=None):
        print("    Elsys init()")

        self.name = "elsys"

        self.decoded_property = settings["decoded_property"]

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("Elsys test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #cambridge-sensor-network/devices/elsys-ems-048f2b/up

        if ("elsys" in topic):  #check if decoder name appears in the topic
            if DEBUG:
                print("Elsys test() success")
            return True
        #elif ("dev_id" in msg):  #dev_id for example, can be any other key
        #    msg=json.loads(message.payload)
        #    if (decoder_name in msg["dev_id"]):
        #        return True
        #    #elif...
        #    else:
        #        return False
        if DEBUG:
            print("Elsys test() fail")
        return False


    def decode(self, topic, message_bytes):
        if DEBUG:
            print("Elsys decode() {}".format(message_bytes))

        inc_msg=str(message_bytes,'utf-8')

        if DEBUG:
            print("Elsys decode str {}".format(inc_msg))

        msg_dict = json.loads(inc_msg)

        # extract sensor id
        # add acp_id to original message
        msg_dict["acp_id"] = msg_dict["dev_id"]


        #printf(msg_dict)

        type_array = msg_dict["dev_id"].split("-")

        msg_dict["acp_type"] = type_array[0]+"-"+type_array[1]

        if DEBUG:
            print("\nElsys decode() DECODED:\n")

        rawb64 = msg_dict["payload_raw"]

        if DEBUG:
            print("Elsys decode() rawb64 {}".format(rawb64))

        try:
            decoded = self.decodePayload(msg_dict, self.b64toBytes(rawb64))
            msg_dict[self.decoded_property] = decoded
            if DEBUG:
                print("Elsys decode() decoded {}".format(decoded))
        except Exception as e:
            # DecoderManager will add acp_ts using server time
            print("Elsys decodePayload() {} exception {}".format(type(e), e))
            msg_dict["ERROR"] = "acp_decoder elsys decodePayload exception"
            return msg_dict

        if DEBUG:
            print("Elsys decode() acp_id {}".format(msg_dict["acp_id"]))

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
            # DecoderManager will add acp_ts using server time
            print("Elsys decode() timestamp {} exception {}".format(type(e), e))

        if DEBUG:
            print("\nElsys decode() FINITO: {} {}\n".format(msg_dict["acp_id"], msg_dict["acp_ts"]))

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
            print("b64toBytes")
        return base64.b64decode(b64)

    def decodePayload(self, msg_dict, data):
        obj = {}

        acp_type = msg_dict["acp_type"]

        if DEBUG:
            print("data ",data," len ",len(data))

        i = 0
        while(i<len(data)):
            #Temperature
            if data[i] == TYPE_TEMP:
                temp=(data[i+1]<<8)|(data[i+2])
                temp=self.bin16dec(temp)
                obj["temperature"]=temp/10
                i=i+2

            #Humidity
            elif data[i] == TYPE_RH:
                rh=(data[i+1])
                obj["humidity"]=rh
                i+=1

            #Acceleration
            elif data[i] == TYPE_ACC:
                obj["x"]=self.bin8dec(data[i+1])
                obj["y"]=self.bin8dec(data[i+2])
                obj["z"]=self.bin8dec(data[i+3])
                i+=3

            #Light
            elif data[i] == TYPE_LIGHT:
                obj["light"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #Motion sensor(PIR)
            elif data[i] == TYPE_MOTION:
                obj["motion"]=(data[i+1])
                i+=1

            #CO2
            elif data[i] == TYPE_CO2:
                obj["co2"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #Battery level
            elif data[i] == TYPE_VDD:
                obj["vdd"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #Analog input 1
            elif data[i] == TYPE_ANALOG1:
                obj["analog1"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #gps
            elif data[i] ==  TYPE_GPS:
                obj["lat"]=(data[i+1]<<16)|(data[i+2]<<8)|(data[i+3])
                obj["lng"]=(data[i+4]<<16)|(data[i+5]<<8)|(data[i+6])
                i+=6

            #Pulse input 1
            elif data[i] == TYPE_PULSE1:
                obj["pulse1"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #Pulse input 1 absolute value
            elif data[i] ==  TYPE_PULSE1_ABS:
                pulseAbs=(data[i+1]<<24)|(data[i+2]<<16)|(data[i+3]<<8)|(data[i+4])
                obj["pulseAbs"]=pulseAbs
                i+=4

            #External temp
            elif data[i] ==TYPE_EXT_TEMP1:
                temp=(data[i+1]<<8)|(data[i+2])
                temp=self.bin16dec(temp)
                obj["externalTemperature"]=temp/10
                i+=2

            #Digital input
            elif data[i] == TYPE_EXT_DIGITAL:
                obj["digital"]=(data[i+1])
                i+=1
                if acp_type == "elsys-ems" and len(data) < 5 :
                    msg_dict["acp_event"] = "openclose"
                    msg_dict["acp_event_value"] = "open" if obj["digital"] == 0 else "close"

            #Distance sensor input
            elif data[i] == TYPE_EXT_DISTANCE:
                obj["distance"]=(data[i+1]<<8)|(data[i+2])
                obj["JBJB"]="my debug here"
                i+=2

            #Acc motion
            elif data[i] == TYPE_ACC_MOTION:
                obj["accMotion"]=(data[i+1])
                i+=1

            #IR temperature
            elif data[i] == TYPE_IR_TEMP:
                iTemp=(data[i+1]<<8)|(data[i+2])
                iTemp=self.bin16dec(iTemp)
                eTemp=(data[i+3]<<8)|(data[i+4])
                eTemp=self.bin16dec(eTemp)
                obj["irInternalTemperature"]=iTemp/10
                obj["irExternalTemperature"]=eTemp/10
                i+=4

            #Body occupancy
            elif data[i] == TYPE_OCCUPANCY:
                obj["occupancy"]=(data[i+1])
                i+=1

            #Water leak
            elif data[i] == TYPE_WATERLEAK:
                obj["waterleak"]=(data[i+1])
                i+=1

            #Grideye data
            elif data[i] == TYPE_GRIDEYE:
                obj["grideye"]="8x8 missing"
                ref = data[i+1]
                i+=1
                obj.grideye = []
                for j in range(0,64):
                    obj.grideye[j]=ref+(data[1+i+j]/10.0)
                i+=64

            #External Pressure
            elif data[i] == TYPE_PRESSURE:
                temp=(data[i+1]<<24)|(data[i+2]<<16)|(data[i+3]<<8)|(data[i+4])
                obj["pressure"]=temp/1000
                i+=4

            #Sound
            elif data[i] == TYPE_SOUND:
                obj["soundPeak"]=data[i+1]
                obj["soundAvg"]=data[i+2]
                i+=2

            #Pulse 2
            elif data[i] == TYPE_PULSE2:
                obj["pulse2"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #Pulse input 2 absolute value
            elif data[i] == TYPE_PULSE2_ABS:
                obj["pulseAbs2"]=(data[i+1]<<24)|(data[i+2]<<16)|(data[i+3]<<8)|(data[i+4])
                i+=4

            #Analog input 2
            elif data[i] ==  TYPE_ANALOG2:
                obj["analog2"]=(data[i+1]<<8)|(data[i+2])
                i+=2

            #External temp 2
            elif data[i] == TYPE_EXT_TEMP2:
                temp=(data[i+1]<<8)|(data[i+2])
                temp=self.bin16dec(temp)
                obj["externalTemperature2"]=temp/10
                i+=2

            #Digital input 2
            elif data[i] ==  TYPE_EXT_DIGITAL2:
                obj["digital2"]=(data[i+1])
                i+=1

            #Load cell analog uV
            elif data[i] == TYPE_EXT_ANALOG_UV:
                obj["analogUv"] = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | (data[i + 4])
                i += 4

            else:
                print("Elsys decoder field not recognized {}".format(data[i]))
                i=len(data)

            i+=1

        return obj

