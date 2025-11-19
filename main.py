import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import User, Company, Period, Placement, Log, Attendance, Evaluation, Notification

app = FastAPI(title="PKL Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "PKL Management Backend is running"}

# ------------------------------------------------------
# Helper
# ------------------------------------------------------

def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()

# ------------------------------------------------------
# Schema endpoint (for viewer)
# ------------------------------------------------------
@app.get("/schema")
def get_schema():
    return {
        "collections": [
            "user", "company", "period", "placement", "log", "attendance", "evaluation", "notification"
        ]
    }

# ------------------------------------------------------
# Users (minimal manual login: email + password_hash)
# ------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/register")
def register(user: User):
    # naive check existing email
    existing = get_documents(collection_name(User), {"email": user.email}, limit=1)
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    user_dict = user.model_dump()
    return {"id": create_document(collection_name(User), user_dict)}

@app.post("/auth/login")
def login(req: LoginRequest):
    users = get_documents(collection_name(User), {"email": req.email}, limit=1)
    if not users:
        raise HTTPException(status_code=401, detail="Akun tidak ditemukan")
    # For demo: accept any password, in real use hash check
    user = users[0]
    return {"message": "Login berhasil", "user": {"id": str(user.get("_id")), "name": user.get("name"), "role": user.get("role")}}

# ------------------------------------------------------
# Generic CRUD creators
# ------------------------------------------------------
class IdResponse(BaseModel):
    id: str

@app.post("/companies", response_model=IdResponse)
def create_company(company: Company):
    new_id = create_document(collection_name(Company), company)
    return {"id": new_id}

@app.get("/companies")
def list_companies():
    return get_documents(collection_name(Company))

@app.post("/periods", response_model=IdResponse)
def create_period(period: Period):
    new_id = create_document(collection_name(Period), period)
    return {"id": new_id}

@app.get("/periods")
def list_periods():
    return get_documents(collection_name(Period))

@app.post("/placements", response_model=IdResponse)
def create_placement(placement: Placement):
    new_id = create_document(collection_name(Placement), placement)
    return {"id": new_id}

@app.get("/placements")
def list_placements(student_id: Optional[str] = None, status: Optional[str] = None):
    filt = {}
    if student_id:
        filt["student_id"] = student_id
    if status:
        filt["status"] = status
    return get_documents(collection_name(Placement), filt)

# Update placement: status change, assign supervisors, notes
class PlacementUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    supervisor_dosen_id: Optional[str] = None
    supervisor_industri_id: Optional[str] = None

@app.patch("/placements/{placement_id}")
def update_placement(placement_id: str, payload: PlacementUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    from bson import ObjectId
    try:
        oid = ObjectId(placement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID tidak valid")
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        return {"updated": 0}
    res = db[collection_name(Placement)].update_one({"_id": oid}, {"$set": data, "$currentDate": {"updated_at": True}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Penempatan tidak ditemukan")
    return {"updated": res.modified_count}

@app.post("/logs", response_model=IdResponse)
def create_log(log: Log):
    log_dict = log.model_dump()
    if not log_dict.get("uploaded_at"):
        log_dict["uploaded_at"] = datetime.utcnow()
    new_id = create_document(collection_name(Log), log_dict)
    return {"id": new_id}

@app.get("/logs")
def list_logs(placement_id: Optional[str] = None):
    filt = {"placement_id": placement_id} if placement_id else {}
    return get_documents(collection_name(Log), filt)

@app.post("/attendance", response_model=IdResponse)
def create_attendance(att: Attendance):
    att_dict = att.model_dump()
    if not att_dict.get("uploaded_at"):
        att_dict["uploaded_at"] = datetime.utcnow()
    new_id = create_document(collection_name(Attendance), att_dict)
    return {"id": new_id}

@app.get("/attendance")
def list_attendance(placement_id: Optional[str] = None):
    filt = {"placement_id": placement_id} if placement_id else {}
    return get_documents(collection_name(Attendance), filt)

@app.post("/evaluations", response_model=IdResponse)
def create_evaluation(ev: Evaluation):
    # hitung total sesuai bobot: 40/20/20/20
    total = 0.4 * ev.teknis + 0.2 * ev.disiplin + 0.2 * ev.soft_skills + 0.2 * ev.laporan
    data = ev.model_dump()
    data["total"] = round(total, 2)
    new_id = create_document(collection_name(Evaluation), data)
    return {"id": new_id, "total": data["total"]}

@app.get("/evaluations")
def list_evaluations(placement_id: Optional[str] = None):
    filt = {"placement_id": placement_id} if placement_id else {}
    return get_documents(collection_name(Evaluation), filt)

@app.post("/notifications", response_model=IdResponse)
def create_notification(n: Notification):
    new_id = create_document(collection_name(Notification), n)
    return {"id": new_id}

@app.get("/notifications")
def list_notifications(user_id: Optional[str] = None, unread_only: bool = False):
    filt = {"user_id": user_id} if user_id else {}
    if unread_only:
        filt["is_read"] = False
    return get_documents(collection_name(Notification), filt)

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
