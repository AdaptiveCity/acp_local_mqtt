import asyncio
import os
import signal
import time
from datetime import datetime, timezone
import logging

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

# gmqtt also compatibility with uvloop
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

STOP = asyncio.Event()

def on_connect(client, flags, rc, properties):
    print('{} Connected'.format(ts_string()))
    #client.subscribe('TEST/#', qos=0)

def on_message(client, topic, payload, qos, properties):
    print('{} RECV MSG: {}'.format(ts_string(),payload))

def on_disconnect(client, packet, exc=None):
    print('{} Disconnected'.format(ts_string()))

def on_subscribe(client, mid, qos, properties):
    print('{} SUBSCRIBED'.format(ts_string()))

def ask_exit(*args):
    STOP.set()

def ts_string():
    return '{:.6f}'.format(time.time())

async def publisher(client):
    while True:
        await asyncio.sleep(10)
        ts = ts_string()
        print("{} [test_pub_timeout] publishing".format(ts))
        client.publish('TIME', ts, qos=0)

async def main(broker_host):
    client = MQTTClient("client-id")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    client.set_auth_credentials('mqtt-usr','mqtt-pwd')
    await client.connect(broker_host, keepalive=20, version=MQTTv311)

    client.publish('TIME', str(time.time()), qos=0)

    asyncio.ensure_future(publisher(client))

    await STOP.wait()
    await client.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    host = 'localhost'
    #token = os.environ.get('FLESPI_TOKEN')

    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main(host))

