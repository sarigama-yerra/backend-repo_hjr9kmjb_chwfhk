import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone

app = FastAPI(title="Energy Management Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Energy Management API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: str | None = None
    message: str = Field(..., min_length=5, max_length=2000)

# Simple in-memory log for demo plus optional DB write if configured
CONTACT_LOG: list[dict] = []

@app.post("/api/contact")
def submit_contact(payload: ContactMessage):
    record = payload.model_dump()
    record["created_at"] = datetime.now(timezone.utc).isoformat()

    # Try to write to database if available
    try:
        from database import db
        if db is not None:
            db["contact"].insert_one(record)
    except Exception:
        # Fallback: keep in memory for current session
        CONTACT_LOG.append(record)

    return {"status": "ok"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
