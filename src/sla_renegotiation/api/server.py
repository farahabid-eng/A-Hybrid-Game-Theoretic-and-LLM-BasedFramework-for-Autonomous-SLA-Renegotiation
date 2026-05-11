from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sla_renegotiation.api.routes import context, negotiation, sla, validation, workflow


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(title="SLA Renegotiation API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sla.router)
app.include_router(workflow.router)
app.include_router(context.router)
app.include_router(negotiation.router)
app.include_router(validation.router)


@app.get("/health")
def health():
    return {"status": "ok"}
