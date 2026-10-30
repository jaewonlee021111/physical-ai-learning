"""Loopback-only MQTT observation API. Start with uvicorn mqtt.bridge:app."""
import json
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from uuid import uuid4
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

class Bridge:
    def __init__(self, host="127.0.0.1", port=1883):
        self.nodes, self.lock = {}, threading.Lock()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="web-"+uuid4().hex[:12])
        self.client.on_connect = self.connect
        self.client.on_message = self.message
        self.host, self.port = host, port
    def connect(self, client, userdata, flags, reason, properties):
        if reason == 0:
            client.subscribe("physicalai/+/state", qos=1)
    def message(self, client, userdata, message):
        try:
            if len(message.payload)>4096:
                return
            parts=message.topic.split("/")
            if len(parts)!=3 or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",parts[1]):
                return
            data=json.loads(message.payload)
            if type(data.get("touched")) is not bool or type(data.get("led")) is not bool or type(data.get("raw")) is not int:
                return
            with self.lock:
                self.nodes[parts[1]]={"raw":data["raw"],"led":data["led"],"touched":data["touched"],"last_command_id":data.get("last_command_id"),"received_at":time.time(),"retained":message.retain}
        except (ValueError, TypeError, AttributeError):
            return
    def start(self):
        self.client.connect(self.host,self.port)
        self.client.loop_start()
    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()
    def snapshot(self):
        with self.lock:
            return {k:{**v,"status":"stale" if v["retained"] or time.time()-v["received_at"]>10 else "online"} for k,v in self.nodes.items()}
    def led(self, node, led):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",node):
            raise ValueError("invalid node")
        cid=uuid4().hex
        result=self.client.publish(f"physicalai/{node}/command",json.dumps({"id":cid,"led":led}),qos=1,retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError("broker not connected")
        return {"id":cid,"state":"published_not_hardware_confirmed"}

bridge=Bridge(os.getenv("MQTT_HOST","127.0.0.1"),int(os.getenv("MQTT_PORT","1883")))
@asynccontextmanager
async def lifespan(app):
    bridge.start()
    yield
    bridge.stop()
app=FastAPI(title="Local MQTT practice",lifespan=lifespan)
@app.get("/",response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang='ko'><meta charset='utf-8'><title>MQTT 대시보드</title><style>body{font:18px system-ui;max-width:850px;margin:auto;padding:25px}button,input{font:inherit;padding:10px}pre{white-space:pre-wrap}</style><h1>로컬 MQTT 대시보드</h1><p>브로커 수신과 보드 적용은 다르다. 상태의 last_command_id로 ACK를 확인한다.</p><label>노드 ID <input id='node' value='xiao'></label><button onclick='send(true)'>LED 켜기 요청</button><button onclick='send(false)'>끄기 요청</button><pre id='command'></pre><pre id='nodes'></pre><script>async function send(led){try{const r=await fetch('/nodes/'+encodeURIComponent(document.querySelector('#node').value)+'/led',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({led})});document.querySelector('#command').textContent=JSON.stringify(await r.json(),null,2);}catch{document.querySelector('#command').textContent='전송 실패';}}async function refresh(){try{const r=await fetch('/nodes');document.querySelector('#nodes').textContent=JSON.stringify(await r.json(),null,2);}catch{document.querySelector('#nodes').textContent='서버 연결 미확인';}}refresh();setInterval(refresh,1500);</script></html>"""
class Command(BaseModel):
    led: bool
@app.get("/nodes")
def nodes():
    return bridge.snapshot()
@app.post("/nodes/{node}/led",status_code=202)
def command(node:str,data:Command):
    try:
        return bridge.led(node,data.led)
    except ValueError:
        raise HTTPException(422,"Invalid node")
    except RuntimeError:
        raise HTTPException(503,"Broker disconnected")
