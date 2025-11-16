import uuid, time, hashlib, logging
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, HelpRequest, Supervisor, KnowledgeEntry
from notifier import notify_agent_of_supervisor_reply
from fastapi.responses import JSONResponse
from livekit import api
import os
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://ai-frontdesk-rzszy9ba.livekit.cloud")

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Frontdesk — Human-in-the-Loop")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin"
def hash_pw(pw: str): return hashlib.sha256(pw.encode()).hexdigest()
db = SessionLocal()
if not db.query(Supervisor).filter_by(username=DEFAULT_USER).first():
    sup = Supervisor(id=str(uuid.uuid4()), username=DEFAULT_USER, password=hash_pw(DEFAULT_PASS))
    db.add(sup); db.commit()
db.close()

@app.get("/", response_class=RedirectResponse)
async def index():
    return "/supervisor"

@app.get("/supervisor")
async def supervisor_panel(request: Request, db: Session = Depends(get_db)):
    requests = db.query(HelpRequest).order_by(HelpRequest.created_at.desc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "requests": requests})

@app.get("/api/data")
async def get_dashboard_data(db: Session = Depends(get_db)):
    pending = db.query(HelpRequest).filter(HelpRequest.status == "pending").all()
    history = db.query(HelpRequest).filter(HelpRequest.status != "pending").all()
    knowledge = db.query(KnowledgeEntry).all()

    def serialize_request(req):
        return {
            "id": req.id,
            "question": req.question,
            "answer": req.answer,
            "status": req.status,
            "created_at": req.created_at,
        }

    def serialize_kb(kb):
        return {
            "topic_key": kb.topic_key,
            "answer": kb.answer,
        }

    data = {
        "pending": [serialize_request(r) for r in pending],
        "history": [serialize_request(r) for r in history],
        "knowledge": [serialize_kb(k) for k in knowledge],
    }

    return JSONResponse(content=data)

@app.post("/api/respond")
async def api_respond(
    request_id: str = Form(...),
    answer: str = Form(...),
    db: Session = Depends(get_db)
):
    """Supervisor reply from dashboard form."""
    help_request = db.query(HelpRequest).filter_by(id=request_id).first()
    if not help_request:
        return {"error": "Request not found"}

    help_request.answer = answer
    help_request.status = "resolved"
    help_request.resolved_at = time.time()
    db.commit()
    await notify_agent_of_supervisor_reply("supervisor_room", answer)

    return {"status": "ok"}


@app.post("/api/transfer")
async def api_transfer(
    customer_id: str = Form(...),
    question: str = Form(...),
    db: Session = Depends(get_db)
):
    """Simulate AI escalation — manually create a help request."""
    new_request = HelpRequest(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        question=question,
        status="pending",
        created_at=time.time()
    )
    db.add(new_request)
    db.commit()
    return {"status": "created", "id": new_request.id}



@app.get("/api/token")
async def get_token(identity: str):
    api_key = os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LIVEKIT_API_SECRET')

    token = api.AccessToken(api_key, api_secret) \
        .with_identity(identity) \
        .with_name("test_user") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="supervisor_room",
            can_publish=True,
            can_subscribe=True
        ))
    return {"token": token.to_jwt()}
