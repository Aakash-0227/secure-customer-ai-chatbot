
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.invoices import router as invoices_router
from app.routes.conversations import router as conversations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic manages database schema migrations.
    yield


app = FastAPI(
    title="Secure Customer AI Chatbot",
    description="An authenticated AI customer assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(auth_router)
app.include_router(invoices_router)
app.include_router(conversations_router)


@app.get("/", tags=["General"])
def home():
    return {"message": "Secure Customer AI Chatbot API is running"}


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}
