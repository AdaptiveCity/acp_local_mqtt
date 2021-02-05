
# Script to test the Adeuinis decoder
# python adeunis-test.py

import base64
from decoders.adeunis import Decoder
import simplejson as json

d  = Decoder()

result = d.decode('', '{ "dev_id": "adeunis-test-123", "payload_raw": "nxRSBXJgAABZgBf+/hBfFwc=", "metadata": { "time": "2021-02-05T08:56:40.366103402Z"}}'.encode('utf-8'))

print(json.dumps(result,indent=4))
