from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Financial Advisor")

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
    return {"message": "AI Financial Advisor API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/advice")
async def get_advice():
    return {
        "advice": "Sample financial advice endpoint",
        "tips": [
            "Diversify your portfolio",
            "Save for emergencies",
            "Invest for the long term"
        ]
    }
