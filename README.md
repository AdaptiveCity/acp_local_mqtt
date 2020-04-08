# ACP local mosquitto MQTT broker configuration

These instructions explain the installation of a local MQTT broker (mosquitto) on the
server receiving data from sensors publishing to the broker directly and also messages
received over a bridge from TTN.

In addition, the instructions install `acp_decoders` which is a Python plugin framework
to normalize / decode the data in the incoming messages, re-publishing the data on the
`acp/...` topic.

![acp_local_mqtt architecture diagram](images/acp_local_mqtt.png)

##

Install `mosquitto` server and clients
```
sudo apt install mosquitto mosquitto-clients
```

## Test basic mosquitto install

Installation can immediately be tested with `mosquitto_sub -v -t '#'` and `mosquitto_pub -t foo -m bah`
issued in that order in two open terminals.

Note the MQTT broker is *open to anyone* at this point.

## Require passwords

```
sudo cp ~acp_prod/acp_prod/secrets/mosquitto_passwd /etc/mosquitto/passwd

sudo cp ~acp_prod/acp_prod/mosquitto/default.conf /etc/mosquitto/conf.d/

sudo systemctl stop mosquitto

service mosquitto status

sudo systemctl start mosquitto
```

View the usernames with
```
cat /etc/mosquitto/passwd
```
For the passwords see the `secrets` configs e.g. `~acp_prod/acp_prod/secrets/feedmqtt.local.json` 
which connects to this local mosquitto broker.

## Test the username / password protection

Trying the earlier 'no username' subscription `mosquitto_sub -v -t '#'` should fail
with a connection error.

Giving the username password should work: `mosquitto_sub -v -t '#' -u <username> -P <password>`.

(The usernames are in the `/etc/mosquitto/passwd` file, passwords in the `secrets` configs.)

## Limit MQTT to port 8883 encrypted connections

We will overwrite the non-encrypting `/etc/mosquitto/conf.d/default.conf`:

First, copy and edit the `acp_prod/mosquitto/default_ssl.conf` to INCLUDE THE CORRECT HOSTNAME from the
certificate.

```
sudo cp ~acp_prod/acp_prod/mosquitto/default_ssl.conf /etc/mosquitto/conf.d/default.conf
```

Note this file will allow connections to BOTH port 1883 (plaintext) and 8883 (SSL).

Mosquitto can be restarted with:
```
sudo systemctl stop mosquitto
sudo systemctl status mosquitto
sudo systemctl start mosquitto
```

## Test a plaintext subscribe via a local console with 

```
mosquitto_sub -v -h localhost -t '#' -u <username> -P <password>
```

## Test SSL access via port 8883

For SSL access the hostname given in the server certificate must be used, e.g.:

```
mosquitto_pub -t 'hello' -m 'world' -u <username> -P <password> -p 8883 -h <hostname> --capath /etc/ssl/certs
```

## Create a bridge to The Things Network

Add the mosquitto bridge config:
```
sudo cp ~acp_prod/acp_prod/secrets/mosquitto_ttn.conf /etc/mosquitto/conf.d/
```

Restart mosquitto as before.

## Test the TTN connection

Locally subscribe to TTN uplink data which should now appear on topic `+/devices/+/up`.
```
mosquitto_sub -t '+/devices/+/up' -u <username> -P <password>
```

## Install `acp_decoders`

See `acp_decoders/README.md`

