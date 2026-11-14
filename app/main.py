from fastapi import FastAPI  # type: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.conversion import router as conversion_router
from app.core.config import get_settings
from app.exceptions.handlers import register_exception_handlers


app = FastAPI()

app.include_router(conversion_router)
register_exception_handlers(app)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


@app.get("/")
async def root():
    return {"message": "SaveToken API is running!"}

@app.get("/Health")
async def health():
    return {"status": "healthy"}



