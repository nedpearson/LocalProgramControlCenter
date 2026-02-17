from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Forensic CPA AI")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Forensic CPA AI API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/analyze")
async def analyze():
    return {
        "analysis": "Sample forensic analysis endpoint",
        "capabilities": [
            "Financial fraud detection",
            "Transaction anomaly detection",
            "Compliance monitoring"
        ]
    }
