from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from ..deps import current_user, database
from ..schemas import ItemInput, ItemPatch, Named

router = APIRouter(tags=["items"])

def owned(db, table, item_id, owner):
    # table only comes from these module constants, never request input.
    item = db.one(f"SELECT * FROM {table} WHERE id=:id AND owner=:owner", id=item_id, owner=owner)
    if not item:
        raise HTTPException(404, "Not found")
    return item

@router.post("/items", status_code=201)
def create(data: ItemInput, user=Depends(current_user), db=Depends(database)):
    uid = uuid4().hex
    db.execute("INSERT INTO items(id,owner,name,description,price) VALUES(:id,:owner,:name,:description,:price)",
               id=uid, owner=user["id"], **data.model_dump())
    return owned(db, "items", uid, user["id"])

@router.get("/items")
def list_items(q: str = Query(default="", max_length=100), user=Depends(current_user), db=Depends(database)):
    return db.all("SELECT * FROM items WHERE owner=:owner AND name LIKE :q ORDER BY id", owner=user["id"], q=f"%{q}%")

@router.get("/items/{item_id}")
def get(item_id: str, user=Depends(current_user), db=Depends(database)):
    return owned(db, "items", item_id, user["id"])

def update(item_id, values, user, db):
    owned(db, "items", item_id, user["id"])
    if values:
        fields = ",".join(f"{k}=:{k}" for k in values)
        db.execute(f"UPDATE items SET {fields} WHERE id=:id AND owner=:owner", id=item_id, owner=user["id"], **values)
    return owned(db, "items", item_id, user["id"])

@router.put("/items/{item_id}")
def put(item_id: str, data: ItemInput, user=Depends(current_user), db=Depends(database)):
    return update(item_id, data.model_dump(), user, db)

@router.patch("/items/{item_id}")
def patch(item_id: str, data: ItemPatch, user=Depends(current_user), db=Depends(database)):
    return update(item_id, data.model_dump(exclude_unset=True), user, db)

@router.delete("/items/{item_id}", status_code=204)
def delete(item_id: str, user=Depends(current_user), db=Depends(database)):
    owned(db, "items", item_id, user["id"])
    db.execute("DELETE FROM items WHERE id=:id AND owner=:owner", id=item_id, owner=user["id"])
    return Response(status_code=204)

@router.post("/categories", status_code=201, tags=["categories"])
def category(data: Named, user=Depends(current_user), db=Depends(database)):
    uid = uuid4().hex
    db.execute("INSERT INTO categories(id,owner,name) VALUES(:id,:owner,:name)", id=uid, owner=user["id"], name=data.name)
    return owned(db, "categories", uid, user["id"])

@router.get("/categories", tags=["categories"])
def categories(user=Depends(current_user), db=Depends(database)):
    return db.all("SELECT id,name FROM categories WHERE owner=:owner ORDER BY name", owner=user["id"])
