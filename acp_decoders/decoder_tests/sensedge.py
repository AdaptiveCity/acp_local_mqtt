import base64
from decoders.sensedge import Decoder
import simplejson as json

d = Decoder()

# Hex payload_raw here:
b = bytes.fromhex('40084319C81D53')

b_str = base64.b64encode(b).decode('ascii')

result = d.decode('',('{ "dev_id": "snsedg-water-0935EB", "payload_raw": "'+b_str+'" }').encode('utf-8'))

print(json.dumps(result,'',4))

