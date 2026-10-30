import time
from pathlib import Path
import jwt
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

SECRET="test-only-not-deployment-secret-32-chars"

@pytest.fixture
def client(tmp_path):
    app=create_app("sqlite:///"+str(tmp_path/"test.db"),SECRET)
    with TestClient(app) as c:
        yield c

def account(c,email="a@example.test"):
    assert c.post("/api/v1/auth/signup",json={"email":email,"password":"test-password-123"}).status_code==201
    r=c.post("/api/v1/auth/token",data={"username":email,"password":"test-password-123"})
    assert r.status_code==200
    return {"Authorization":"Bearer "+r.json()["access_token"]}

def test_crud_put_patch_query_and_persistence(client):
    h=account(client)
    item=client.post("/api/v1/items",headers=h,json={"name":"cola","description":"350ml","price":2500}).json()
    path="/api/v1/items/"+item["id"]
    assert client.patch(path,headers=h,json={"price":2000}).json()["name"]=="cola"
    assert client.get("/api/v1/items?q=cola",headers=h).json()[0]["price"]==2000
    assert client.put(path,headers=h,json={"name":"cookie","price":1000}).json()["description"]==""
    assert client.get(path,headers=h).json()["name"]=="cookie"
    assert client.delete(path,headers=h).status_code==204
    assert client.get(path,headers=h).status_code==404

def test_owner_isolation_all_verbs(client):
    a,b=account(client),account(client,"b@example.test")
    item=client.post("/api/v1/items",headers=a,json={"name":"private","price":1}).json()
    p="/api/v1/items/"+item["id"]
    assert client.get("/api/v1/items",headers=b).json()==[]
    assert client.get(p,headers=b).status_code==404
    assert client.patch(p,headers=b,json={"name":"stolen"}).status_code==404
    assert client.put(p,headers=b,json={"name":"stolen","price":1}).status_code==404
    assert client.delete(p,headers=b).status_code==404

def test_validation_mass_assignment_null_and_sql(client):
    h=account(client)
    assert client.post("/api/v1/items",headers=h,json={"name":"x","price":-1}).status_code==422
    assert client.post("/api/v1/items",headers=h,json={"name":"x","price":1,"owner":"another"}).status_code==422
    item=client.post("/api/v1/items",headers=h,json={"name":"x'; DROP TABLE items;--","price":1}).json()
    assert client.patch("/api/v1/items/"+item["id"],headers=h,json={"price":None}).status_code==422
    assert len(client.get("/api/v1/items",headers=h).json())==1

def test_auth_errors_expiry_and_signature(client):
    h=account(client)
    assert client.post("/api/v1/auth/signup",json={"email":"a@example.test","password":"test-password-123"}).status_code==409
    assert client.post("/api/v1/auth/token",data={"username":"a@example.test","password":"wrong"}).status_code==401
    assert client.get("/api/v1/auth/me").status_code==401
    assert client.get("/api/v1/auth/me",headers={"Authorization":"Bearer invalid"}).status_code==401
    uid=client.get("/api/v1/auth/me",headers=h).json()["id"]
    claims={"sub":uid,"exp":time.time()-1,"iss":"oct27-learning","aud":"oct27-api"}
    for key,exp in [(SECRET,time.time()-1),("wrong-key-that-is-at-least-32-characters",time.time()+60)]:
        claims["exp"]=exp
        token=jwt.encode(claims,key,algorithm="HS256")
        assert client.get("/api/v1/auth/me",headers={"Authorization":"Bearer "+token}).status_code==401

def test_device_command_ack_auth_and_expiry(client):
    h=account(client)
    b=account(client,"b@example.test")
    d=client.post("/api/v1/devices",headers=h,json={"name":"test-board-fixture"}).json()
    did=d["id"]; dh={"X-Device-Key":d["device_key"]}
    assert client.get("/api/v1/devices",headers=h).json()[0]["status"]=="never_seen"
    assert "device_key" not in client.get("/api/v1/devices",headers=h).json()[0]
    telemetry={"raw":100,"touched":True,"led":False}
    assert client.post(f"/api/v1/device/{did}/telemetry",json=telemetry).status_code==401
    assert client.post(f"/api/v1/device/{did}/telemetry",headers=dh,json=telemetry).status_code==200
    assert client.post(f"/api/v1/devices/{did}/commands",headers=b,json={"led":True}).status_code==404
    cmd=client.post(f"/api/v1/devices/{did}/commands",headers=h,json={"led":True}).json()
    assert cmd["state"]=="pending"
    assert client.get(f"/api/v1/device/{did}/next-command",headers=dh).json()["command"]["id"]==cmd["id"]
    for _ in range(2):
        assert client.post(f"/api/v1/device/{did}/ack/{cmd['id']}",headers=dh).json()["state"]=="applied"
    assert client.get(f"/api/v1/device/{did}/next-command",headers=dh).json()["command"] is None
    client.app.state.db.execute("UPDATE devices SET seen=:t WHERE id=:id",t=time.time()-11,id=did)
    assert client.get("/api/v1/devices",headers=h).json()[0]["status"]=="stale"
    cid=client.post(f"/api/v1/devices/{did}/commands",headers=h,json={"led":False}).json()["id"]
    client.app.state.db.execute("UPDATE commands SET created=:t WHERE id=:id",t=time.time()-31,id=cid)
    assert client.get(f"/api/v1/device/{did}/next-command",headers=dh).json()["command"] is None
    assert client.post(f"/api/v1/device/{did}/ack/{cid}",headers=dh).status_code==409

def test_categories_and_swagger(client):
    h=account(client)
    assert client.post("/api/v1/categories",headers=h,json={"name":"drink"}).status_code==201
    assert client.get("/api/v1/categories",headers=h).json()[0]["name"]=="drink"
    assert client.get("/docs").status_code==200
    assert "/api/v1/items/{item_id}" in client.get("/openapi.json").json()["paths"]
    assert client.get("/web/").status_code==200
    assert client.get("/web/learning.html").status_code==200

def test_database_survives_restart(tmp_path):
    url="sqlite:///"+str(tmp_path/"persistent.db")
    with TestClient(create_app(url,SECRET)) as a:
        h=account(a)
        a.post("/api/v1/items",headers=h,json={"name":"persist","price":2})
    with TestClient(create_app(url,SECRET)) as b:
        assert b.get("/api/v1/items",headers=h).json()[0]["name"]=="persist"

def test_cors_exact_origin(client,monkeypatch,tmp_path):
    monkeypatch.setenv("CORS_ORIGINS","https://frontend.example.test")
    with TestClient(create_app("sqlite:///"+str(tmp_path/"cors.db"),SECRET)) as c:
        good=c.options("/api/v1/items",headers={"Origin":"https://frontend.example.test","Access-Control-Request-Method":"GET"})
        bad=c.options("/api/v1/items",headers={"Origin":"https://other.example.test","Access-Control-Request-Method":"GET"})
        assert good.headers["access-control-allow-origin"]=="https://frontend.example.test"
        assert "access-control-allow-origin" not in bad.headers
