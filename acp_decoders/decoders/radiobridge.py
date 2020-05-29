#
# RadioBridge sensor decoder
#
# Instantiate with:
#
#    from decoders.radiobridge import Decoder as RadioBridge
#    decoder = RadioBridge(settings) # default settings=None
#    where:
#       settings["decoded_property"] contains property name to contain decoded message
#       e.g. settings["decoded_property"] = "payload_cooked" (default if settings=None)
#
# Implements:
#    test(topic, message_bytes): returns true|false whether this decoder will handle message
#    decode(topic, message_bytes): returns Python dictionary of original message + decoded_property.
#

# This Python update from Javascript original:
#    https://github.com/RadioBridge/Packet-Decoder
#    RADIO BRIDGE PACKET DECODER v1.0
#    (c) 2019 RadioBridge USA by John Sheldon

DEBUG = True

import base64
import simplejson as json
from datetime import datetime

# General defines used in decode
RESET_EVENT = 0x00
SUPERVISORY_EVENT = 0x01
TAMPER_EVENT = 0x02
LINK_QUALITY_EVENT = 0xFB
RATE_LIMIT_EXCEEDED_EVENT = 0xFC
TEST_MESSAGE_EVENT = 0xFD
DOWNLINK_ACK_EVENT = 0xFF
DOOR_WINDOW_EVENT = 0x03
PUSH_BUTTON_EVENT = 0x06
CONTACT_EVENT = 0x07
WATER_EVENT = 0x08
TEMPERATURE_EVENT = 0x09
TILT_EVENT = 0x0A
ATH_EVENT = 0x0D
ABM_EVENT = 0x0E
TILT_HP_EVENT = 0x0F
ULTRASONIC_EVENT = 0x10
SENSOR420MA_EVENT = 0x11
THERMOCOUPLE_EVENT = 0x13
VOLTMETER_EVENT = 0x14
CUSTOM_SENSOR_EVENT = 0x15
GPS_EVENT = 0x16
HONEYWELL5800_EVENT = 0x17
MAGNETOMETER_EVENT = 0x18
VIBRATION_LB_EVENT = 0x19
VIBRATION_HB_EVENT = 0x1A

class Decoder(object):
    def __init__(self,settings=None):
        print("    RadioBridge init()")

        self.name = "radiobridge"

        if settings is not None and "decoded_property" in settings:
            self.decoded_property = settings["decoded_property"]
        else:
            self.decoded_property = "payload_cooked"

        return

    def test(self, topic, message_bytes):

        if DEBUG:
            print("RadioBridge test() {} {}".format(topic, message_bytes))
        #regular topic format:
        #csn-radiobridge/devices/<acp_id>/up

        if ("/rad-" in topic):  #check if decoder name appears in the topic
            if DEBUG:
                print("RadioBridge test() success")
            return True

        if DEBUG:
            print("RadioBridge test() fail")
        return False


    def decode(self, topic, message_bytes):
        if DEBUG:
            print("RadioBridge decode() {}".format(message_bytes))

        inc_msg=str(message_bytes,'utf-8')

        if DEBUG:
            print("RadioBridge decode str {}".format(inc_msg))

        msg_dict = json.loads(inc_msg)

        # extract sensor id
        # add acp_id to original message
        msg_dict["acp_id"] = msg_dict["dev_id"]


        #printf(msg_dict)

        type_array = msg_dict["dev_id"].split("-")

        msg_dict["acp_type"] = type_array[0]+"-"+type_array[1]

        if DEBUG:
            print("\nRadioBridge decode() DECODED:\n")

        rawb64 = msg_dict["payload_raw"]

        if DEBUG:
            print("RadioBridge decode() rawb64 {}".format(rawb64))

        try:
            decoded_payload = self.decodePayload(msg_dict, self.b64toBytes(rawb64))
            if decoded_payload is not None:
                msg_dict[self.decoded_property] = decoded_payload
            if DEBUG:
                print("RadioBridge decode() decoded {}".format(decoded_payload))
        except Exception as e:
            # DecoderManager will add acp_ts using server time
            print("RadioBridge decodePayload() {} exception {}".format(type(e), e))
            msg_dict["ERROR"] = "acp_decoder RadioBridge decodePayload exception"
            return msg_dict

        if DEBUG:
            print("RadioBridge decode() acp_id {}".format(msg_dict["acp_id"]))

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
            print("RadioBridge decode() timestamp {} exception {}".format(type(e), e))

        if DEBUG:
            print("\nRadioBridge decode() FINITO: {} {}\n".format(msg_dict["acp_id"], msg_dict["acp_ts"]))

        return msg_dict

    # Here we decode the original 'payload' from the RadioBridge sensor that was
    # provided in the "payload_raw" property of the message from TTN
    def decodePayload(self, msg_dict, payload_bytes):

        acp_type = msg_dict["acp_type"]

        if DEBUG:
            print("data ",payload_bytes," len ",len(payload_bytes))

        # the event type is defined in the second byte
        event = payload_bytes[1]

        if event == RESET_EVENT:
            decoded = self.handle_RESET(payload_bytes)
        elif event == SUPERVISORY_EVENT:
            decoded = self.handle_SUPERVISORY(payload_bytes)
        elif event == TAMPER_EVENT:
            decoded = self.handle_TAMPER(payload_bytes)
        elif event == LINK_QUALITY_EVENT:
            decoded = self.handle_LINK_QUALITY(payload_bytes)
        elif event == RATE_LIMIT_EXCEEDED_EVENT:
            decoded = self.handle_RATE_LIMIT_EXCEEDED(payload_bytes)
        elif event == TEST_MESSAGE_EVENT:
            decoded = self.handle_TEST_MESSAGE(payload_bytes)
        elif event == DOWNLINK_ACK_EVENT:
            decoded = self.handle_DOWNLINK_ACK(payload_bytes)
        elif event == DOOR_WINDOW_EVENT:
            decoded = self.handle_DOOR_WINDOW(payload_bytes)
        elif event == PUSH_BUTTON_EVENT:
            decoded = self.handle_PUSH_BUTTON(payload_bytes)
        elif event == CONTACT_EVENT:
            decoded = self.handle_CONTACT(payload_bytes)
        elif event == WATER_EVENT:
            decoded = self.handle_WATER(payload_bytes)
        elif event == TEMPERATURE_EVENT:
            decoded = self.handle_TEMPERATURE(payload_bytes)
        elif event == TILT_EVENT:
            decoded = self.handle_TILT(payload_bytes)
        elif event == ATH_EVENT:
            decoded = self.handle_ATH(payload_bytes)
        elif event == ABM_EVENT:
            decoded = self.handle_ABM(payload_bytes)
        elif event == TILT_HP_EVENT:
            decoded = self.handle_TILT_HP(payload_bytes)
        elif event == ULTRASONIC_EVENT:
            decoded = self.handle_ULTRASOVIBRATION_HBNIC(payload_bytes)
        elif event == SENSOR420MA_EVIBRATION_HBVENT:
            decoded = self.handle_SENSOR420MA(payload_bytes)
        elif event == THERMOCOUPLE_EVENT:
            decoded = self.handle_THERMOCOUPLE(payload_bytes)
        elif event == VOLTMETER_EVENT:
            decoded = self.handle_VOLTMETER(payload_bytes)
        elif event == CUSTOM_SENSOR_EVENT:
            decoded = self.handle_CUSTOM_SENSOR(payload_bytes)
        elif event == GPS_EVENT:
            decoded = self.handle_GPS(payload_bytes)
        elif event == HONEYWELL5800_EVENT:
            decoded = self.handle_HONEYWELL5800(payload_bytes)
        elif event == MAGNETOMETER_EVENT:
            decoded = self.handle_MAGNETOMETER(payload_bytes)
        elif event == VIBRATION_LB_EVENT:
            decoded = self.handle_VIBRATION_LB(payload_bytes)
        elif event == VIBRATION_HB_EVENT:
            decoded = self.handle_VIBRATION_HB(payload_bytes)
        else:
            return None
        # add packet counter and protocol version to the end of the decode
        # The first byte contains the protocol version (upper nibble) and packet counter (lower nibble)
        PacketCounter = payload_bytes[0] & 0x0f
        ProtocolVersion = (payload_bytes[0] >> 4) & 0x0f

        decoded["packet_count"] = PacketCounter
        decoded["protocol_version"] = ProtocolVersion

        return decoded

    # ==================    RESET EVENT    ====================
    def handle_RESET(self, payload_bytes):

        decoded = {}
        decoded["event"] = "reset"

        # third byte is device type, convert to hex format for case statement
        DeviceTypeByte = payload_bytes[2]

        # device types are enumerated below
        if DeviceTypeByte == 0x01 :
                DeviceType = "Door/Window Sensor"
        elif DeviceTypeByte == 0x02 :
                DeviceType = "Door/Window High Security"
        elif DeviceTypeByte == 0x03 :
                DeviceType = "Contact Sensor"
        elif DeviceTypeByte == 0x04 :
                DeviceType = "No-Probe Temperature Sensor"
        elif DeviceTypeByte == 0x05 :
                DeviceType = "External-Probe Temperature Sensor"
        elif DeviceTypeByte == 0x06 :
                DeviceType = "Single Push Button"
        elif DeviceTypeByte == 0x07 :
                DeviceType = "Dual Push Button"
        elif DeviceTypeByte == 0x08 :
                DeviceType = "Acceleration-Based Movement Sensor"
        elif DeviceTypeByte == 0x09 :
                DeviceType = "Tilt Sensor"
        elif DeviceTypeByte == 0x0A :
                DeviceType = "Water Sensor"
        elif DeviceTypeByte == 0x0B :
                DeviceType = "Tank Level Float Sensor"
        elif DeviceTypeByte == 0x0C :
                DeviceType = "Glass Break Sensor"
        elif DeviceTypeByte == 0x0D :
                DeviceType = "Ambient Light Sensor"
        elif DeviceTypeByte == 0x0E :
                DeviceType = "Air Temperature and Humidity Sensor"
        elif DeviceTypeByte == 0x0F :
                DeviceType = "High-Precision Tilt Sensor"
        elif DeviceTypeByte == 0x10 :
                DeviceType = "Ultrasonic Level Sensor"
        elif DeviceTypeByte == 0x11 :
                DeviceType = "4-20mA Current Loop Sensor"
        elif DeviceTypeByte == 0x12 :
                DeviceType = "Ext-Probe Air Temp and Humidity Sensor"
        elif DeviceTypeByte == 0x13 :
                DeviceType = "Thermocouple Temperature Sensor"
        elif DeviceTypeByte == 0x14 :
                DeviceType = "Voltage Sensor"
        elif DeviceTypeByte == 0x15 :
                DeviceType = "Custom Sensor"
        elif DeviceTypeByte == 0x16 :
                DeviceType = "GPS"
        elif DeviceTypeByte == 0x17 :
                DeviceType = "Honeywell 5800 Bridge"
        elif DeviceTypeByte == 0x18 :
                DeviceType = "Magnetometer"
        elif DeviceTypeByte == 0x19 :
                DeviceType = "Vibration Sensor - Low Frequency"
        elif DeviceTypeByte == 0x1A :
                DeviceType = "Vibration Sensor - High Frequency"
        else:
                DeviceType = "Device Undefined"

        decoded["device_type"] = DeviceType

        # the hardware version has the major version in the upper nibble, and the minor version in the lower nibble
        HardwareVersion = ((payload_bytes[3] >> 4) & 0x0f) + "." + (payload_bytes[3] & 0x0f)

        decoded["hardware_version"] = HardwareVersion

        # the firmware version has two different formats depending on the most significant bit
        FirmwareFormat = (payload_bytes[4] >> 7) & 0x01

        # FirmwareFormat of 0 is old format, 1 is new format
        # old format is has two sections x.y
        # new format has three sections x.y.z
        if FirmwareFormat == 0 :
            FirmwareVerison = payload_bytes[4] + "." + payload_bytes[5]
        else:
            FirmwareVerison = ((payload_bytes[4] >> 2) & 0x1F) + "." + ((payload_bytes[4] & 0x03) + ((payload_bytes[5] >> 5) & 0x07)) + "." + (payload_bytes[5] & 0x1F)

        decoded["firmware_format"] = FirmwareVerison

        return decoded

    # ================   SUPERVISORY EVENT   ==================
    def handle_SUPERVISORY(self, payload_bytes):
        decoded = {}
        decoded["event"] = "supervisory"

        # note that the sensor state in the supervisory message is being depreciated, so those are not decoded here

        # battery voltage is in the format x.y volts where x is upper nibble and y is lower nibble
        BatteryLevel = ((payload_bytes[4] >> 4) & 0x0f) + "." + (payload_bytes[4] & 0x0f)

        decoded["battery_level"]= float(BatteryLevel)

        # the accumulation count is a 16-bit value
        AccumulationCount = (payload_bytes[9] * 256) + payload_bytes[10]
        decoded["accumulation_count"]= AccumulationCount

        # decode bits for error code byte
        TamperSinceLastReset = (payload_bytes[2] >> 4) & 0x01
        decoded["tamper_reset"] = TamperSinceLastReset

        CurrentTamperState = (payload_bytes[2] >> 3) & 0x01
        decoded["tamper_current"] = CurrentTamperState

        ErrorWithLastDownlink = (payload_bytes[2] >> 2) & 0x01
        decoded["downlink_error"] = ErrorWithLastDownlink

        BatteryLow = (payload_bytes[2] >> 1) & 0x01
        decoded["battery_low"] = BatteryLow

        RadioCommError = payload_bytes[2] & 0x01
        decoded["radio_error"] = RadioCommError

        return decoded

    # ==================   TAMPER EVENT    ====================
    def handle_TAMPER(self, payload_bytes):
        decoded = {}
        decoded["event"] = "tamper"

        TamperState = payload_bytes[2]

        # tamper state is 0 for open, 1 for closed
        if (TamperState == 0):
            decoded["tamper_state"] = "open"
        else:
            decoded["tamper_start"] = "closed"

        return decoded

    # ==================   LINK QUALITY EVENT    ====================
    def handle_LINK_QUALITY(self, payload_bytes):
        decoded = {}
        decoded["event"] = "link_quality"

        CurrentSubBand = payload_bytes[2]
        decoded["sub_band"] = CurrentSubBand

        RSSILastDownlink = payload_bytes[3]
        decoded["rssi"] = RSSILastDownlink

        SNRLastDownlink = payload_bytes[4]
        decoded["snr"] = SNRLastDownlink

        return decoded

    # ==================   RATE LIMIT EXCEEDED EVENT    ====================
    def handle_RATE_LIMIT_EXCEEDED(self, payload_bytes):
        decoded = {}
        # this feature is depreciated so it is not decoded here
        decoded["event"] = "rate_limit_exceeded_DEPRECATED"

        return decoded

    # ==================   TEST MESSAGE EVENT    ====================
    def handle_TEST_MESSAGE(self, payload_bytes):
        decoded = {}
        # this feature is depreciated so it is not decoded here
        decoded["event"] = "test_message_DEPRECATED"

        return decoded

    # ================  DOOR/WINDOW EVENT  ====================
    def handle_DOOR_WINDOW(self, payload_bytes):
        decoded = {}
        decoded["event"] = "door_window"

        SensorState = payload_bytes[2]

        # 0 is closed, 1 is open
        if (SensorState == 0):
            decoded["state"] = "closed"
        else:
            decoded["state"] = "open"

        return decoded

    # ===============  PUSH BUTTON EVENT   ===================
    def handle_PUSH_BUTTON(self, payload_bytes):
        decoded = {}
        decoded["event"] = "push_button"

        ButtonID = payload_bytes[2]

        # 01 and 02 used on two button
        if ButtonID ==  0x01:
            ButtonReference = "button_1"
        elif ButtonID == 0x02 :
            ButtonReference = "button_2"
        # 03 is single button
        elif ButtonID == 0x03 :
            ButtonReference = "button_1"
        # 12 when both buttons pressed on two button
        elif ButtonID == 0x12 :
            ButtonReference = "button_1&2"
        else:
            ButtonReference = "undefined"

        decoded["button_id"] = ButtonReference

        ButtonState = payload_bytes[3]

        if ButtonState == 0 :
            SensorStateDescription = "pressed"
        elif ButtonState == 1:
            SensorStateDescription = "released"
        elif ButtonState ==  2:
            SensorStateDescription = "held"
        else:
            SensorStateDescription = "undefined"

        decoded["button_state"] = SensorStateDescription

        return decoded

    # =================   CONTACT EVENT   =====================
    def handle_CONTACT(self, payload_bytes):
        decoded = {}
        decoded["event"] = "contact"

        ContactState = payload_bytes[2]

        # if state byte is 0 then shorted, if 1 then opened
        if ContactState == 0:
            SensorState = "closed"
        else:
            SensorState = "open"

        decoded["state"] = SensorState

        return decoded

    # ===================  WATER EVENT  =======================
    def handle_WATER(self, payload_bytes):
        decoded = {}
        decoded["event"] = "water"

        SensorState = payload_bytes[2]

        if (SensorState == 0):
            decoded["state"] = "wet"
        else:
            decoded["state"] = "dry"

        WaterRelativeResistance = payload_bytes[3]

        decoded["relative_resistance"] = WaterRelativeResistance

        return decoded

    # ================== TEMPERATURE EVENT ====================
    def handle_TEMPERATURE(self, payload_bytes):
        decoded = {}
        decoded["event"] = "temperature"

        TemperatureEvent = payload_bytes[2]

        if TemperatureEvent == 0:
            TemperatureEventDescription = "periodic_report"
        elif TemperatureEvent == 1:
            TemperatureEventDescription = "above_threshold"
        elif TemperatureEvent == 2:
            TemperatureEventDescription = "below_threshold"
        elif TemperatureEvent == 3:
            TemperatureEventDescription = "change_increase"
        elif TemperatureEvent == 4:
            TemperatureEventDescription = "change_decrease"
        else:
            TemperatureEventDescription = "undefined"

        decoded["temperature_event"] = TemperatureEventDescription

        # current temperature reading
        CurrentTemperature = self.byte_to_signed_int(payload_bytes[3])
        decoded["temperature"] = CurrentTemperature

        # relative temp measurement for use with an alternative calibration table
        RelativeMeasurement = payload_bytes[4]
        decoded["relative_temperature"] = RelativeMeasurement

        return decoded

    # ====================  TILT EVENT  =======================
    def handle_TILT(self, payload_bytes):
        decoded = {}
        decoded["event"] = "tilt"

        TiltEvent = payload_bytes[2]

        if TiltEvent == 0:
            TiltEventDescription = "transition_vertical"
        elif TiltEvent == 1:
            TiltEventDescription = "transition_horizontal"
        elif TiltEvent == 2:
            TiltEventDescription = "change_vertical"
        elif TiltEvent == 3:
            TiltEventDescription = "change_horizontal"
        else:
            TiltEventDescription = "undefined"

        decoded["tilt_event"] = TiltEventDescription

        TiltAngle = payload_bytes[3]

        decoded["tilt_angle"] = TiltAngle

        return decoded

    # =============  AIR TEMP & HUMIDITY EVENT  ===============
    def handle_ATH(self, payload_bytes):
        decoded = {}
        decoded["event"] = "air_temperature_humidity"

        ATHEvent = payload_bytes[2]

        if ATHEvent == 0:
            ATHDescription = "periodic_report"
        elif ATHEvent == 1:
            ATHDescription = "temperature_above_threshold"
        elif ATHEvent == 2:
            ATHDescription = "temperature_below_threshold"
        elif ATHEvent == 3:
            ATHDescription = "temperature_change_increase"
        elif ATHEvent == 4:
            ATHDescription = "temperature_change_decrease"
        elif ATHEvent == 5:
            ATHDescription = "humidity_above_threshold"
        elif ATHEvent == 6:
            ATHDescription = "humidity_below_threshold"
        elif ATHEvent == 7:
            ATHDescription = "humidity_change_increase"
        elif ATHEvent == 8:
            ATHDescription = "humidity_change_decrease"
        else:
            ATHDescription = "undefined"

        decoded["ath_event"] = ATHDescription

        # integer and fractional values between two payload_bytes
        temp_sign = 1 # representing positive deg C
        # Get temp digits
        temp_digits = payload_bytes[3]
        # if msb of digits byte is '1', treat as zero except whole number is negative
        if temp_digits > 127:
            temp_sign = -1
            temp_digits = temp_digits - 128
        # Get temp fraction
        temp_fraction = (payload_bytes[4] >> 4) / 10

        Temperature = temp_sign * (temp_digits + temp_fraction)
        decoded["temperature"] = Temperature

        # integer and fractional values between two payload_bytes
        Humidity = payload_bytes[5] + (payload_bytes[6]>>4) / 10
        decoded["humidity"] = Humidity

        return decoded

    # ============  ACCELERATION MOVEMENT EVENT  ==============
    def handle_ABM(self, payload_bytes):
        decoded = {}
        decoded["event"] = "acceleration"

        ABMEvent = payload_bytes[2]

        if ABMEvent == 0:
            ABMEventDescription = "movement_start"
        else:
            ABMEventDescription = "movement_stop"

        decoded["abm_event"]= ABMEventDescription

        return decoded

    # =============  HIGH-PRECISION TILT EVENT  ===============
    def handle_TILT_HP(self, payload_bytes):
        decoded = {}
        decoded["event"] = "hp_tilt"

        TiltEvent = payload_bytes[2]

        if TiltEvent == 0:
            TiltEventDescription = "periodic_report"
        elif TiltEvent == 1:
            TiltEventDescription = "toward_0_vertical"
        elif TiltEvent == 2:
            TiltEventDescription = "away_0_vertical"
        elif TiltEvent == 3:
            TiltEventDescription = "change_toward_0_vertical"
        elif TiltEvent == 4:
            TiltEventDescription = "change_away_0_vertical"
        else:
            TiltEventDescription = "undefined"

        decoded["tilt_hp_event"] = TiltEventDescription

        # integer and fractional values between two payload_bytes
        Angle = payload_bytes[3] + payload_bytes[4] / 10
        decoded["angle"] = Angle

        Temperature = self.byte_to_signed_int(payload_bytes[5])
        decoded["temperature"] = Temperature

        return decoded

    # ===============  ULTRASONIC LEVEL EVENT  ================
    def handle_ULTRASONIC(self, payload_bytes):

        decoded = {}
        decoded["event"] = "ultrasonic_level"

        UltrasonicEvent = payload_bytes[2]

        if UltrasonicEvent == 0:
            UltrasonicEventDescription = "periodic_report"
        elif UltrasonicEvent == 1:
            UltrasonicEventDescription = "distance_above_threshold"
        elif UltrasonicEvent == 2:
            UltrasonicEventDescription = "distance_below_threshold"
        elif UltrasonicEvent == 3:
            UltrasonicEventDescription = "change_increase"
        elif UltrasonicEvent == 4:
            UltrasonicEventDescription = "change_decrease"
        else:
            UltrasonicEventDescription = "undefined"

        decoded["ultrasonic_event"] = UltrasonicEventDescription

        # distance is calculated across 16-bits
        Distance = ((payload_bytes[3] * 256) + payload_bytes[4])

        decoded["distance"] = Distance
        return decoded

    # ================  4-20mA ANALOG EVENT  ==================
    def handle_SENSOR420MA(self, payload_bytes):

        decoded = {}
        decoded["event"] = "sensor420ma"

        Sensor420mAEvent = payload_bytes[2]

        if Sensor420mAEvent == 0:
            Sensor420mAEventDescription = "periodic_report"
        elif Sensor420mAEvent == 1:
            Sensor420mAEventDescription = "above_threshold"
        elif Sensor420mAEvent == 2:
            Sensor420mAEventDescription = "below_threshold"
        elif Sensor420mAEvent == 3:
            Sensor420mAEventDescription = "change_increase"
        elif Sensor420mAEvent == 4:
            Sensor420mAEventDescription = "change_decrease"
        else:
            Sensor420mAEventDescription = "undefined"

        decoded["sensor420ma_event"] = Sensor420mAEventDescription

        # calculatec across 16-bits, convert from units of 10uA to mA
        Analog420Measurement = ((payload_bytes[3] * 256) + payload_bytes[4]) / 100

        decoded["current_milliamps"]= Analog420Measurement

        return decoded

    # =================  THERMOCOUPLE EVENT  ==================
    def handle_THERMOCOUPLE(self, payload_bytes):

        decoded = {}
        decoded["event"] = "thermocouple"

        ThermocoupleEvent = payload_bytes[2]

        if ThermocoupleEvent == 0:
            ThermocoupleEventDescription = "periodic_report"
        elif ThermocoupleEvent == 1:
            ThermocoupleEventDescription = "above_threshold"
        elif ThermocoupleEvent == 2:
            ThermocoupleEventDescription = "below_threshold"
        elif ThermocoupleEvent == 3:
            ThermocoupleEventDescription = "change_increase"
        elif ThermocoupleEvent == 4:
            ThermocoupleEventDescription = "change_decrease"
        else:
            ThermocoupleEventDescription = "Undefined"

        decoded["thermocouple_event"] = ThermocoupleEventDescription

        # decode is across 16-bits
        Temperature = parseInt(((payload_bytes[3] * 256) + payload_bytes[4]) / 16)

        decoded["temperature"] = Temperature # "°C"

        Faults = payload_bytes[5]

        # decode each bit in the fault byte
        FaultColdOutsideRange = (Faults >> 7) & 0x01
        FaultHotOutsideRange = (Faults >> 6) & 0x01
        FaultColdAboveThresh = (Faults >> 5) & 0x01
        FaultColdBelowThresh = (Faults >> 4) & 0x01
        FaultTCTooHigh = (Faults >> 3) & 0x01
        FaultTCTooLow = (Faults >> 2) & 0x01
        FaultVoltageOutsideRange = (Faults >> 1) & 0x01
        FaultOpenCircuit = Faults & 0x01

        # Decode faults (return as string)
        if Faults != 0 :
            Message = ""
            if (FaultColdOutsideRange):
                Message += ", Fault: The cold-Junction temperature is outside of the normal operating range"

            if (FaultHotOutsideRange):
                Message += ", Fault: The hot junction temperature is outside of the normal operating range"

            if (FaultColdAboveThresh):
                Message += ", Fault: The cold-Junction temperature is at or above than the cold-junction temperature high threshold"

            if (FaultColdBelowThresh):
                Message += ", Fault: The Cold-Junction temperature is lower than the cold-junction temperature low threshold"

            if (FaultTCTooHigh):
                Message += ", Fault: The thermocouple temperature is too high"

            if (FaultTCTooLow):
                Message += ", Fault: Thermocouple temperature is too low"

            if (FaultVoltageOutsideRange):
                Message += ", Fault: The input voltage is negative or greater than VDD"

            if (FaultOpenCircuit):
                Message += ", Fault: An open circuit such as broken thermocouple wires has been detected"

            decoded["faults"] = Message

        return decoded

    # ================  VOLTMETER ANALOG EVENT  ==================
    def handle_VOLTMETER(self, payload_bytes):

        decoded = {}
        decoded["event"] = "voltmeter"

        VoltmeterEvent = payload_bytes[2]

        if VoltmeterEvent == 0:
                VoltmeterEventDescription = "periodic_report"
        elif VoltmeterEvent == 1:
                VoltmeterEventDescription = "above_threshold"
        elif VoltmeterEvent == 2:
                VoltmeterEventDescription = "below_threshold"
        elif VoltmeterEvent == 3:
                VoltmeterEventDescription = "change_increase"
        elif VoltmeterEvent == 4:
                VoltmeterEventDescription = "change_decrease"
        else:
                VoltmeterEventDescription = "Undefined"

        decoded["voltmeter_event"] = VoltmeterEventDescription

        # voltage is measured across 16-bits, convert from units of 10mV to V
        VoltageMeasurement = ((payload_bytes[3] * 256) + payload_bytes[4]) / 100

        decoded["volts"] = VoltageMeasurement

        return decoded

    # ================  CUSTOM SENSOR EVENT  ==================
    def handle_CUSTOM_SENSOR(self, payload_bytes):

        decoded = {}
        decoded["event"] = "custom_sensor"

        # Custom sensors are not decoded here

        return decoded

    # ================  GPS EVENT  ==================
    def handle_GPS(self, payload_bytes):

        decoded = {}
        decoded["event"] = "gps"

        GPSStatus = payload_bytes[2]

        # decode status byte
        GPSValidFix = GPSStatus & 0x01

        if (GPSValidFix == 0):
            GPSValidFixDescription = "no_valid_fix"
        else:
            GPSValidFixDescription = "valid_fix"


        decoded["gps_status"] = GPSValidFixDescription

        # latitude and longitude calculated across 32 bits each, show 12 decimal places
        Latitude = (((payload_bytes[3] * (2 ^ 24)) + (payload_bytes[4] * (2 ^ 16)) + (payload_bytes[5] * (2 ^ 8)) + payload_bytes[6]) / (10 ^ 7))
        Latitude = (((payload_bytes[7] * (2 ^ 24)) + (payload_bytes[8] * (2 ^ 16)) + (payload_bytes[9] * (2 ^ 8)) + payload_bytes[10]) / (10 ^ 7))

        decoded["acp_lat"] = Latitude
        decoded["acp_lng"] = Longitude

        return decoded


    # ================  HONEYWELL 5800 EVENT  ==================
    def handle_HONEYWELL5800(self, payload_bytes):

        decoded = {}
        decoded["event"] = "honeywell5800"

        # honeywell sensor ID, 24-bits
        HWSensorID = (payload_bytes[2] * (2 ^ 16)) + (payload_bytes[3] * (2 ^ 8)) + payload_bytes[4]

        decoded["hw_sensor_id"] = HWSensorID

        HWEvent = payload_bytes[5]

        if HWEvent == 0:
            HWEventDescription = "status_code"
        elif HWEvent == 1:
            HWEventDescription = "error_Code"
        elif HWEvent == 2:
            HWEventDescription = "sensor_data_payload"
        else:
            HWEventDescription = "undefined"

        decoded["honeywell5800_event"] = HWEventDescription

        # represent the honeywell sensor payload in hex
        HWSensorPayload = hex((payload_bytes[6] * 256) + payload_bytes[7])

        decoded["sensor_payload"] = HWSensorPayload

        return decoded

    # ================  MAGNETOMETER EVENT  ==================
    def handle_MAGNETOMETER(self, payload_bytes):

        # TBD

        return None


    # ================  VIBRATION LOW BANDWIDTH EVENT  ==================
    def handle_VIBRATION_LB(self, payload_bytes):

        decoded = {}
        decoded["event"] = "vibration_lb"

        VibeEvent = payload_bytes[2]

        if VibeEvent == 0:
            VibeEventDescription = "periodic_report"
        elif VibeEvent == 4:
            VibeEventDescription = "x_above_threshold"
        elif VibeEvent == 5:
            VibeEventDescription = "x_above_threshold"
        elif VibeEvent == 6:
            VibeEventDescription = "y_above_threshold"
        elif VibeEvent == 7:
            VibeEventDescription = "y_below_threshold"
        elif VibeEvent == 8:
            VibeEventDescription = "z_above_threshold"
        elif VibeEvent == 9:
            VibeEventDescription = "z_above_threshold"
        elif VibeEvent == 11:
            VibeEventDescription = "excess_g_force"
        else:
            VibeEventDescription = "undefined"

        decoded["vibration_lb_event"] = VibeEventDescription

        # X, Y, and Z velocities are 16-bits
        XVelocity = (payload_bytes[3] * 256) + payload_bytes[4]
        YVelocity = (payload_bytes[5] * 256) + payload_bytes[6]
        ZVelocity = (payload_bytes[7] * 256) + payload_bytes[8]

        decoded["x_inches_per_second"] = XVelocity
        decoded["y_inches_per_second"] = YVelocity
        decoded["z_inches_per_second"] = ZVelocity

        # capture sign of temp
        VibeTemp = payload_bytes[9] # DEBUG SHOULD THIS BE SIGNED INT ???

        decoded["temperature"] = VibeTemp # "°C"

        return decoded

    # ================  VIBRATION HIGH BANDWIDTH EVENT  ==================
    def handle_VIBRATION_HB(self, payload_bytes):

        decoded = {}
        decoded["event"] = "vibration_hb"

        VibeEvent = payload_bytes[2]

        if VibeEvent == 1:
            VibeEventDescription = "periodic_report"
        elif VibeEvent == 2:
            VibeEventDescription = "above_threshold"
        elif VibeEvent == 3:
            VibeEventDescription = "below_threshold"
        elif VibeEvent == 10:
            VibeEventDescription = "excess_g_force"
        else:
            VibeEventDescription = "undefined"

        decoded["vibration_hb_event"] = VibeEventDescription

        # peak g-force
        PeakGForce = (payload_bytes[3] * 256) + payload_bytes[4]

        decoded["peak_g"] = PeakGForce

        # capture sign of temp
        VibeTemp = self.byte_to_signed_int(payload_bytes[5]) # DEBUG IS THIS THE FORMAT?

        decoded["temperature"] = VibeTemp

        return decoded


    # ==================   DOWNLINK EVENT  ====================
    def handle_DOWNLINK_ACK(self, payload_bytes):

        decoded = {}
        decoded["event"] = "downlink_ack"

        DownlinkEvent = payload_bytes[2]

        if (DownlinkEvent == 1):
            DownlinkEventDescription = "message_invalid"
        else:
            DownlinkEventDescription = "message_valid"

        decoded["downlink_ack_event"] = DownlinkEventDescription
        return decoded

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

    # used for some temperatures as 2's Compliment byte
    def byte_to_signed_int(self, number):
        if number > 127:
            return number - 256
        return number
