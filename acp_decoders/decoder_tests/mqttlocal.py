
# Script to test the Adeuinis decoder
# python adeunis.py

import base64
from decoders.mqttlocal import Decoder
import simplejson as json

d  = Decoder()

result = d.decode('csn/monnit-Temperature-481994', 'foo'.encode('utf-8'))

print(json.dumps(result,indent=4))
