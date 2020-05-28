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
        #cambridge-sensor-network/devices/elsys-ems-048f2b/up

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
                msg_dict[self.decoded_property] = self.decoded_payload
            if DEBUG:
                print("RadioBridge decode() decoded {}".format(decoded_payload))
        except Exception as e:
            # DecoderManager will add acp_ts using server time
            print("RadioBridge decodePayload() {} exception {}".format(type(e), e))
            msg_dict["ERROR"] = "acp_decoder elsys decodePayload exception"
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
            decoded = handle_RESET(payload_bytes)
        elif event == SUPERVISORY_EVENT:
            decoded = handle_SUPERVISORY(payload_bytes)
        elif event == TAMPER_EVENT:
            decoded = handle_TAMPER(payload_bytes)
        elif event == LINK_QUALITY_EVENT:
            decoded = handle_LINK_QUALITY(payload_bytes)
        elif event == RATE_LIMIT_EXCEEDED_EVENT:
            decoded = handle_RATE_LIMIT_EXCEEDED(payload_bytes)
        elif event == TEST_MESSAGE_EVENT:
            decoded = handle_TEST_MESSAGE(payload_bytes)
        elif event == DOWNLINK_ACK_EVENT:
            decoded = handle_DOWNLINK_ACK(payload_bytes)
        elif event == DOOR_WINDOW_EVENT:
            decoded = handle_DOOR_WINDOW(payload_bytes)
        elif event == PUSH_BUTTON_EVENT:
            decoded = handle_PUSH_BUTTON(payload_bytes)
        elif event == CONTACT_EVENT:
            decoded = handle_CONTACT(payload_bytes)
        elif event == WATER_EVENT:
            decoded = handle_WATER(payload_bytes)
        elif event == TEMPERATURE_EVENT:
            decoded = handle_TEMPERATURE(payload_bytes)
        elif event == TILT_EVENT:
            decoded = handle_TILT(payload_bytes)
        elif event == ATH_EVENT:
            decoded = handle_ATH(payload_bytes)
        elif event == ABM_EVENT:
            decoded = handle_ABM(payload_bytes)
        elif event == TILT_HP_EVENT:
            decoded = handle_TILT_HP(payload_bytes)
        elif event == ULTRASONIC_EVENT:
            decoded = handle_ULTRASOVIBRATION_HBNIC(payload_bytes)
        elif event == SENSOR420MA_EVIBRATION_HBVENT:
            decoded = handle_SENSOR420MA(payload_bytes)
        elif event == THERMOCOUPLE_EVENT:
            decoded = handle_THERMOCOUPLE(payload_bytes)
        elif event == VOLTMETER_EVENT:
            decoded = handle_VOLTMETER(payload_bytes)
        elif event == CUSTOM_SENSOR_EVENT:
            decoded = handle_CUSTOM_SENSOR(payload_bytes)
        elif event == GPS_EVENT:
            decoded = handle_GPS(payload_bytes)
        elif event == HONEYWELL5800_EVENT:
            decoded = handle_HONEYWELL5800(payload_bytes)
        elif event == MAGNETOMETER_EVENT:
            decoded = handle_MAGNETOMETER(payload_bytes)
        elif event == VIBRATION_LB_EVENT:
            decoded = handle_VIBRATION_LB(payload_bytes)
        elif event == VIBRATION_HB_EVENT:
            decoded = handle_VIBRATION_HB(payload_bytes)
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
            if (TamperState == 0)
                decoded["tamper_state"] = "open"
            else
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
            if (SensorState == 0)
                decoded["state"] = "closed"
            else
                decoded["state"] = "open"

            return decoded

        # ===============  PUSH BUTTON EVENT   ===================
        case PUSH_BUTTON_EVENT:

            decoded.Message = "Event: Push Button"

            ButtonID = Hex(payload_bytes[2])

            switch (ButtonID) {
                # 01 and 02 used on two button
                case "01":
                    ButtonReference = "Button 1"
                    break
                case "02":
                    ButtonReference = "Button 2"
                    break
                # 03 is single button
                case "03":
                    ButtonReference = "Button 1"
                    break
                # 12 when both buttons pressed on two button
                case "12":
                    ButtonReference = "Both Buttons"
                    break
                default:
                    ButtonReference = "Undefined"
                    break
            }

            decoded.Message += ", Button ID: " + ButtonReference

            ButtonState = payload_bytes[3]

            switch (ButtonState) {
                case 0:
                    SensorStateDescription = "Pressed"
                    break
                case 1:
                    SensorStateDescription = "Released"
                    break
                case 2:
                    SensorStateDescription = "Held"
                    break
                default:
                    SensorStateDescription = "Undefined"
                    break
            }

            decoded.Message += ", Button State: " + SensorStateDescription

            break

        # =================   CONTACT EVENT   =====================
        case CONTACT_EVENT:

            decoded.Message = "Event: Dry Contact"

            ContactState = payload_bytes[2]

            # if state byte is 0 then shorted, if 1 then opened
            if (ContactState == 0)
                SensorState = "Contacts Shorted"
            else
                SensorState = "Contacts Opened"

            decoded.Message += ", Sensor State: " + SensorState

            break

        # ===================  WATER EVENT  =======================
        case WATER_EVENT:

            decoded.Message = "Event: Water"

            SensorState = payload_bytes[2]

            if (SensorState == 0)
                decoded.Message += ", State: Water Present"
            else
                decoded.Message += ", State: Water Not Present"

            WaterRelativeResistance = payload_bytes[3]

            decoded.Message += ", Relative Resistance: " + WaterRelativeResistance

            break

        # ================== TEMPERATURE EVENT ====================
        case TEMPERATURE_EVENT:

            decoded.Message = "Event: Temperature"

            TemperatureEvent = payload_bytes[2]

            switch (TemperatureEvent) {
                case 0:
                    TemperatureEventDescription = "Periodic Report"
                    break
                case 1:
                    TemperatureEventDescription = "Temperature Over Upper Threshold"
                    break
                case 2:
                    TemperatureEventDescription = "Temperature Under Lower Threshold"
                    break
                case 3:
                    TemperatureEventDescription = "Temperature Report-on-Change Increase"
                    break
                case 4:
                    TemperatureEventDescription = "Temperature Report-on-Change Decrease"
                    break
                default:
                    TemperatureEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Temperature Event: " + TemperatureEventDescription

            # current temperature reading
            CurrentTemperature = Convert(payload_bytes[3], 0)
            decoded.Message += ", Current Temperature: " + CurrentTemperature

            # relative temp measurement for use with an alternative calibration table
            RelativeMeasurement = Convert(payload_bytes[4], 0)
            decoded.Message += ", Relative Measurement: " + RelativeMeasurement

            break

        # ====================  TILT EVENT  =======================
        case TILT_EVENT:

            decoded.Message = "Event: Tilt"

            TiltEvent = payload_bytes[2]

            switch (TiltEvent) {
                case 0:
                    TiltEventDescription = "Transitioned to Vertical"
                    break
                case 1:
                    TiltEventDescription = "Transitioned to Horizontal"
                    break
                case 2:
                    TiltEventDescription = "Report-on-Change Toward Vertical"
                    break
                case 3:
                    TiltEventDescription = "Report-on-Change Toward Horizontal"
                    break
                default:
                    TiltEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Tilt Event: " + TiltEventDescription

            TiltAngle = payload_bytes[3]

            decoded.Message += ", Tilt Angle: " + TiltAngle

            break

        # =============  AIR TEMP & HUMIDITY EVENT  ===============
        case ATH_EVENT:

            decoded.Message = "Event: Air Temperature/Humidity"

            ATHEvent = payload_bytes[2]

            switch (ATHEvent) {
                case 0:
                    ATHDescription = "Periodic Report"
                    break
                case 1:
                    ATHDescription = "Temperature has Risen Above Upper Threshold"
	                break
                case 2:
                    ATHDescription = "Temperature has Fallen Below Lower Threshold"
                    break
                case 3:
                    ATHDescription = "Temperature Report-on-Change Increase"
                    break
                case 4:
                    ATHDescription = "Temperature Report-on-Change Decrease"
                    break
                case 5:
                    ATHDescription = "Humidity has Risen Above Upper Threshold"
                    break
                case 6:
                    ATHDescription = "Humidity has Fallen Below Lower Threshold"
                    break
                case 7:
                    ATHDescription = "Humidity Report-on-Change Increase"
                    break
                case 8:
                    ATHDescription = "Humidity Report-on-Change Decrease"
                    break
                default:
                    ATHDescription = "Undefined"
                    break
            }

            decoded.Message += ", ATH Event: " + ATHDescription

            # integer and fractional values between two payload_bytes
            Temperature = Convert((payload_bytes[3]) + ((payload_bytes[4] >> 4) / 10), 1)
            decoded.Message += ", Temperature: " + Temperature

            # integer and fractional values between two payload_bytes
            Humidity = +(payload_bytes[5] + ((payload_bytes[6]>>4) / 10)).toFixed(1)
            decoded.Message += ", Humidity: " + Humidity

            break

        # ============  ACCELERATION MOVEMENT EVENT  ==============
        case ABM_EVENT:

            decoded.Message = "Event: Acceleration-Based Movement"

            ABMEvent = payload_bytes[2]

            if (ABMEvent == 0)
                ABMEventDescription = "Movement Started"
            else
                ABMEventDescription = "Movement Stopped"

            decoded.Message += ", ABM Event: " + ABMEventDescription

            break

        # =============  HIGH-PRECISION TILT EVENT  ===============
        case TILT_HP_EVENT:

            decoded.Message = "Event: High-Precision Tilt"

            TiltEvent = payload_bytes[2]

            switch (TiltEvent) {
                case 0:
                    TiltEventDescription = "Periodic Report"
                    break
                case 1:
                    TiltEventDescription = "Transitioned Toward 0-Degree Vertical Orientation"
                    break
                case 2:
                    TiltEventDescription = "Transitioned Away From 0-Degree Vertical Orientation"
                    break
                case 3:
                    TiltEventDescription = "Report-on-Change Toward 0-Degree Vertical Orientation"
                    break
                case 4:
                    TiltEventDescription = "Report-on-Change Away From 0-Degree Vertical Orientation"
                    break
                default:
                    TiltEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Tilt HP Event: " + TiltEventDescription

            # integer and fractional values between two payload_bytes
            Angle = +(payload_bytes[3] + (payload_bytes[4] / 10)).toFixed(1)
            decoded.Message = ", Angle: " + Angle

            Temperature = Convert(payload_bytes[5], 0)
            decoded.Message = ", Temperature: " + Temperature

            break

        # ===============  ULTRASONIC LEVEL EVENT  ================
        case ULTRASONIC_EVENT:

            decoded.Message = "Event: Ultrasonic Level"

            UltrasonicEvent = payload_bytes[2]

            switch (UltrasonicEvent) {
                case 0:
                    UltrasonicEventDescription = "Periodic Report"
                    break
                case 1:
                    UltrasonicEventDescription = "Distance has Risen Above Upper Threshold"
                    break
                case 2:
                    UltrasonicEventDescription = "Distance has Fallen Below Lower Threshold"
                    break
                case 3:
                    UltrasonicEventDescription = "Report-on-Change Increase"
                    break
                case 4:
                    UltrasonicEventDescription = "Report-on-Change Decrease"
                    break
                default:
                    UltrasonicEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Ultrasonic Event: " + UltrasonicEventDescription

            # distance is calculated across 16-bits
            Distance = ((payload_bytes[3] * 256) + payload_bytes[4])

            decoded.Message += ", Distance: " + Distance
            break

        # ================  4-20mA ANALOG EVENT  ==================
        case SENSOR420MA_EVENT:

            decoded.Message = "Event: 4-20mA"

            Sensor420mAEvent = payload_bytes[2]

            switch (Sensor420mAEvent) {
                case 0:
                    Sensor420mAEventDescription = "Periodic Report"
                    break
                case 1:
                    Sensor420mAEventDescription = "Analog Value has Risen Above Upper Threshold"
                    break
                case 2:
                    Sensor420mAEventDescription = "Analog Value has Fallen Below Lower Threshold"
                    break
                case 3:
                    Sensor420mAEventDescription = "Report on Change Increase"
                    break
                case 4:
                    Sensor420mAEventDescription = "Report on Change Decrease"
                    break
                default:
                    Sensor420mAEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", 4-20mA Event: " + Sensor420mAEventDescription

            # calculatec across 16-bits, convert from units of 10uA to mA
            Analog420Measurement = ((payload_bytes[3] * 256) + payload_bytes[4]) / 100

            decoded.Message += ", Current Measurement in mA: " + Analog420Measurement

            break

        # =================  THERMOCOUPLE EVENT  ==================
        case THERMOCOUPLE_EVENT:

            decoded.Message = "Event: Thermocouple"

            ThermocoupleEvent = payload_bytes[2]

            switch (ThermocoupleEvent) {
                case 0:
                    ThermocoupleEventDescription = "Periodic Report"
                    break
                case 1:
                    ThermocoupleEventDescription = "Analog Value has Risen Above Upper Threshold"
                    break
                case 2:
                    ThermocoupleEventDescription = "Analog Value has Fallen Below Lower Threshold"
                    break
                case 3:
                    ThermocoupleEventDescription = "Report on Change Increase"
                    break
                case 4:
                    ThermocoupleEventDescription = "Report on Change Decrease"
                    break
                default:
                    ThermocoupleEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Thermocouple Event: " + ThermocoupleEventDescription

            # decode is across 16-bits
            Temperature = parseInt(((payload_bytes[3] * 256) + payload_bytes[4]) / 16)

            decoded.Message += ", Temperature: " + Temperature + "°C"

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

            # Decode faults
            if (Faults == 0)
                decoded.Message += ", Fault: None"
            else {
                if (FaultColdOutsideRange)
                    decoded.Message += ", Fault: The cold-Junction temperature is outside of the normal operating range"

                if (FaultHotOutsideRange)
                    decoded.Message += ", Fault: The hot junction temperature is outside of the normal operating range"

                if (FaultColdAboveThresh)
                    decoded.Message += ", Fault: The cold-Junction temperature is at or above than the cold-junction temperature high threshold"

                if (FaultColdBelowThresh)
                    decoded.Message += ", Fault: The Cold-Junction temperature is lower than the cold-junction temperature low threshold"

                if (FaultTCTooHigh)
                    decoded.Message += ", Fault: The thermocouple temperature is too high"

                if (FaultTCTooLow)
                    decoded.Message += ", Fault: Thermocouple temperature is too low"

                if (FaultVoltageOutsideRange)
                    decoded.Message += ", Fault: The input voltage is negative or greater than VDD"

                if (FaultOpenCircuit)
                    decoded.Message += ", Fault: An open circuit such as broken thermocouple wires has been detected"
            }

            break

        # ================  VOLTMETER ANALOG EVENT  ==================
        case VOLTMETER_EVENT:

            decoded.Message = "Event: Voltage Sensor"

            VoltmeterEvent = payload_bytes[2]

            switch (VoltmeterEvent) {
                case 0:
                    VoltmeterEventDescription = "Periodic Report"
                    break
                case 1:
                    VoltmeterEventDescription = "Voltage has Risen Above Upper Threshold"
                    break
                case 2:
                    VoltmeterEventDescription = "Voltage has Fallen Below Lower Threshold"
                    break
                case 3:
                    VoltmeterEventDescription = "Report on Change Increase"
                    break
                case 4:
                    VoltmeterEventDescription = "Report on Change Decrease"
                    break
                default:
                    VoltmeterEventDescription = "Undefined"
            }

            decoded.Message += ", Voltage Sensor Event: " + VoltmeterEventDescription

            # voltage is measured across 16-bits, convert from units of 10mV to V
            VoltageMeasurement = ((payload_bytes[3] * 256) + payload_bytes[4]) / 100

            decoded.Message += ", Voltage: " + VoltageMeasurement + "V"
            break


        # ================  CUSTOM SENSOR EVENT  ==================
        case CUSTOM_SENSOR_EVENT:

            decoded.Message = "Event: Custom Sensor"

            # Custom sensors are not decoded here

            break


        # ================  VOLTMETER ANALOG EVENT  ==================
        case GPS_EVENT:

            decoded.Message = "Event: GPS"

            GPSStatus = payload_bytes[2]

            # decode status byte
            GPSValidFix = GPSStatus & 0x01

            if (GPSValidFix == 0)
                GPSValidFixDescription = ", No Valid Fix"
            else
                GPSValidFixDescription = ", Valid Fix"


            decoded.Message += ", GPS Status: " + GPSValidFixDescription

            # latitude and longitude calculated across 32 bits each, show 12 decimal places
            Latitude = toFixed((((payload_bytes[3] * (2 ^ 24)) + (payload_bytes[4] * (2 ^ 16)) + (payload_bytes[5] * (2 ^ 8)) + payload_bytes[6]) / (10 ^ 7)), 12)
            Latitude = toFixed((((payload_bytes[7] * (2 ^ 24)) + (payload_bytes[8] * (2 ^ 16)) + (payload_bytes[9] * (2 ^ 8)) + payload_bytes[10]) / (10 ^ 7)), 12)

            decoded.Message += ", Latitude: " + Latitude + ", Longitude: " + Longitude

            break


        # ================  HONEYWELL 5800 EVENT  ==================
        case HONEYWELL5800_EVENT:

            decoded.Message = "Event: Honeywell 5800 Sensor Message"

            # honeywell sensor ID, 24-bits
            HWSensorID = (payload_bytes[2] * (2 ^ 16)) + (payload_bytes[3] * (2 ^ 8)) + payload_bytes[4]

            decoded.Message += ", Honeywell Sensor ID: " + HWSensorID

            HWEvent = payload_bytes[5]

            switch (HWEvent) {
                case 0:
                    HWEventDescription = "Status code"
                    break
                case 1:
                    HWEventDescription = "Error Code"
                    break
                case 2:
                    HWEventDescription = "Sensor Data Payload"
                    break
                default:
                    HWEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Honeywell Sensor Event: " + HWEventDescription

            # represent the honeywell sensor payload in hex
            HWSensorPayload = Hex((payload_bytes[6] * 256) + payload_bytes[7])

            decoded.Message += ", Sensor Payload: 0x" + HWSensorPayload

            break


        # ================  MAGNETOMETER EVENT  ==================
        case MAGNETOMETER_EVENT:

            # TBD

            break


        # ================  VIBRATION LOW BANDWIDTH EVENT  ==================
        case VIBRATION_LB_EVENT:

            decoded.Message = "Event: Vibration Low-Bandwidth"

            VibeEvent = payload_bytes[2]

            switch (VibeEvent) {
                case 0:
                    VibeEventDescription = "Low Frequency Periodic Report"
                    break
                case 4:
                    VibeEventDescription = "Low Frequency X-Axis Has Risen Above Upper Threshold"
                    break
                case 5:
                    VibeEventDescription = "Low Frequency X-Axis Has Fallen Below Lower Threshold"
                    break
                case 6:
                    VibeEventDescription = "Low Frequency Y-Axis Has Risen Above Upper Threshold"
                    break
                case 7:
                    VibeEventDescription = "Low Frequency Y-Axis Has Fallen Below Lower Threshold"
                    break
                case 8:
                    VibeEventDescription = "Low Frequency Z-Axis Has Risen Above Upper Threshold"
                    break
                case 9:
                    VibeEventDescription = "Low Frequency Z-Axis Has Fallen Below Lower Threshold"
                    break
                case 11:
                    VibeEventDescription = "Low Frequency Exceeded G-Force Range"
                    break
                default:
                    VibeEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Vibration Event: " + VibeEventDescription

            # X, Y, and Z velocities are 16-bits
            XVelocity = (payload_bytes[3] * 256) + payload_bytes[4]
            YVelocity = (payload_bytes[5] * 256) + payload_bytes[6]
            ZVelocity = (payload_bytes[7] * 256) + payload_bytes[8]

            decoded.Message += ", X-Axis Velocity: " + XVelocity + " inches/second"
            decoded.Message += ", Y-Axis Velocity: " + YVelocity + " inches/second"
            decoded.Message += ", Z-Axis Velocity: " + ZVelocity + " inches/second"

            # capture sign of temp
            VibeTemp = parseInt(payload_bytes[9])

            decoded.Message = ", Internal Temperature: " + VibeTemp + "°C"

            break

        # ================  VIBRATION HIGH BANDWIDTH EVENT  ==================
        case VIBRATION_HB_EVENT:

            decoded.Message = "Event: Vibration Low-Bandwidth"

            VibeEvent = payload_bytes[2]

            switch (VibeEvent) {
                case 1:
                    VibeEventDescription = "High Frequency Periodic Report"
                    break
                case 2:
                    VibeEventDescription = "High Frequency Vibration Above Upper Threshold"
                    break
                case 3:
                    VibeEventDescription = "High Frequency Vibration Below Lower Threshold"
                    break
                case 10:
                    VibeEventDescription = "High Frequency Exceeded G-Force Range"
                    break
                default:
                    VibeEventDescription = "Undefined"
                    break
            }

            decoded.Message += ", Vibration Event: " + VibeEventDescription

            # peak g-force
            PeakGForce = (payload_bytes[3] * 256) + payload_bytes[4]

            decoded.Message += ", Peak G-Force: " + PeakGForce

            # capture sign of temp
            VibeTemp = parseInt(payload_bytes[5])

            decoded.Message = ", Internal Temperature: " + VibeTemp + "°C"

            break


        # ==================   DOWNLINK EVENT  ====================
        case DOWNLINK_ACK_EVENT:

            decoded.Message = "Event: Downlink Acknowledge"

            DownlinkEvent = payload_bytes[2]

            if (DownlinkEvent == 1)
                DownlinkEventDescription = "Message Invalid"
            else
                DownlinkEventDescription = "Message Valid"

            decoded.Message += ", Downlink: " + DownlinkEventDescription
            break

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

    def Hex(self, decimal):
        decimal = ('0' + decimal.toString(16).toUpperCase()).slice(-2)
        return decimal

    def Convert(number, mode):
        switch (mode) {
            # for EXT-TEMP and NOP
            case 0:
                if number > 127:
                    result = number - 256
                else:
                    result = number
                break
            #for ATH temp
            case 1:
                if number > 127:
                    result = -+(number - 128).toFixed(1)
                else:
                    result = +number.toFixed(1) }
                break
        }
        return result
