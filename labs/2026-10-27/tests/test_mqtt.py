"""Actual local MQTT wire exchange with AMQTT broker, not real ESP32."""
import asyncio
import json
import socket
import threading
import time
import paho.mqtt.client as mqtt
import pytest
from mqtt.bridge import Bridge

def test_mqtt_publish_subscribe_roundtrip():
    Broker=pytest.importorskip("amqtt.broker").Broker
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]
    async def scenario():
        broker=Broker({"listeners":{"default":{"type":"tcp","bind":f"127.0.0.1:{port}"}},
                       "plugins":{"amqtt.plugins.authentication.AnonymousAuthPlugin":{"allow_anonymous":True}}})
        await broker.start()
        try:
            await asyncio.to_thread(exchange,port)
        finally:
            await broker.shutdown()
    def exchange(port):
        bridge=Bridge(port=port)
        peer=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id="fixture-device")
        subscribed=threading.Event(); received=threading.Event(); commands=[]
        def on_connect(client,userdata,flags,reason,properties):
            client.subscribe("physicalai/fixture/command",qos=1)
        def on_subscribe(*args):
            subscribed.set()
        def on_message(client,userdata,message):
            commands.append(json.loads(message.payload));received.set()
        peer.on_connect=on_connect;peer.on_subscribe=on_subscribe;peer.on_message=on_message
        bridge.start();peer.connect("127.0.0.1",port);peer.loop_start()
        try:
            assert subscribed.wait(5)
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                peer.publish("physicalai/fixture/state",json.dumps({"raw":123,"touched":True,"led":False}),qos=1).wait_for_publish()
                if "fixture" in bridge.snapshot():break
                time.sleep(.02)
            assert bridge.snapshot()["fixture"]["raw"]==123
            command=bridge.led("fixture",True)
            assert received.wait(5)
            assert commands[0]=={"id":command["id"],"led":True}
            peer.publish("physicalai/fixture/state",json.dumps({"raw":124,"touched":True,"led":True,"last_command_id":command["id"]}),qos=1).wait_for_publish()
            deadline=time.monotonic()+5
            while time.monotonic()<deadline and bridge.snapshot()["fixture"].get("last_command_id")!=command["id"]:
                time.sleep(.02)
            assert bridge.snapshot()["fixture"]["last_command_id"]==command["id"]
            assert command["state"]=="published_not_hardware_confirmed"
        finally:
            peer.disconnect();peer.loop_stop();bridge.stop()
    asyncio.run(scenario())

def test_malformed_state_is_ignored():
    bridge=Bridge()
    class Message:
        topic="physicalai/fixture/state"
        payload=b'{"raw":1,"touched":"yes","led":false}'
        retain=False
    bridge.message(None,None,Message())
    assert bridge.snapshot()=={}
