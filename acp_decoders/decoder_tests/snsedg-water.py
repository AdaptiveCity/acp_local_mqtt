
# Script to test the sensedge decoder
# python snsedg-water.py

import base64
from decoders.sensedge import Decoder
import simplejson as json

d  = Decoder()

result = d.decode('', """
{ "dev_id": "snsedg-water-0935eb",
   "payload_raw": "AAPfP8gQGw==",
   "metadata": { "time": "2021-02-05T08:56:40.366103402Z"}
}
""".encode('utf-8'))

print(json.dumps(result,indent=4))
