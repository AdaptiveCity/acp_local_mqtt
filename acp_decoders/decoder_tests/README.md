# Decoder test scripts

E.g. `python adeunis.py`
```
    Adeunis init()
{
    "dev_id": "adeunis-test-123",
    "payload_raw": "nxRSBXJgAABZgBf+/hBfFwc=",
    "metadata": {
        "time": "2021-02-05T08:56:40.366103402Z"
    },
    "payload_cooked": {
        "device": "adeunis_test",
        "temperature": 20,
        "latitude": 52.09543333333333,
        "longitude": 0.09966666666666667,
        "gps_reception": 1,
        "gps_satellites": 7,
        "uplink_counter": 254,
        "downlink_counter": 254,
        "battery": 4.191,
        "rssi": -23,
        "snr": 7
    },
    "acp_id": "adeunis-test-123",
    "acp_type_id": "adeunis-test",
    "acp_ts": "1612515400.366103"
}
```
The decoder `acp_decoders/decoders/adeunis.py` is called with a stub test message, and the `payload_cooked` property is added.
