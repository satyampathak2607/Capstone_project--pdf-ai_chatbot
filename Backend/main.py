from fastapi import FastAPI
from upload.routes import upload_router
from summarize.routes import summarize_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(summarize_router)
from chat.routes import chat_router
app.include_router(chat_router)