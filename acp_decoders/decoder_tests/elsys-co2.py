
# Script to test the elsys decoder
# python elsys-co2.py

import base64
from decoders.elsys import Decoder
import simplejson as json

d  = Decoder()

result = d.decode('', """
{ "dev_id": "elsys-co2-0461e7", "payload_raw": "AQDnAiEEACQFAgYBsAcOTQ==", "metadata": { "time": "2021-02-05T08:56:40.366103402Z"}}
""".encode('utf-8'))

print(json.dumps(result,indent=4))
