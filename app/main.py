"""API do ATLAS. Rodar com:  uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.data import estado
from app.routers import clientes, executivo, geografia, outras, produtos, sistema


@asynccontextmanager
async def lifespan(_: FastAPI):
    estado.recarregar()  # lê as planilhas uma vez, ao subir
    yield


app = FastAPI(title="ATLAS · Aditive", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGENS_PERMITIDAS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
for modulo in (sistema, executivo, clientes, geografia, produtos, outras):
    app.include_router(modulo.router)
