
# Script to test the Adeuinis decoder
# python adeunis.py

import base64
from decoders.radiobridge import Decoder
import simplejson as json

d  = Decoder()

result = d.decode('', """
{ "dev_id": "rad-ath-003d0f",
  "payload_raw": "Ew0ABiBkAA==",
  "metadata": { "time": "2021-02-05T08:56:40.366103402Z"}
}
""".encode('utf-8'))

print(json.dumps(result,indent=4))
