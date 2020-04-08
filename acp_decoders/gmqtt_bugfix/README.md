# Bugfix for `gmqtt`

## Issue

Currently (2020-04-04), gmqtt incorrectly resets a 'timeout' timer while connected with an open subscription to a 
mosquitto broker. This results in the broker disconnecting a gmqtt client after sending a message due to that
open subscription (unless the client coincidentally publishes a message within the timeout period, which will be
treated as a keepalive by the broker and the client will not be dropped).

## Fix

Overwrite the files in your local gmqtt install with the `gmqtt` files in this patch. E.g.

```
cp -r gmqtt ../venv/lib/python3.6/site-packages/
```
