from fastapi import FastAPI

from app.transporte import router          # ← nuevo

app = FastAPI(title="Examen Ruilova", version="1.0.0")
app.include_router(router)               # ← nuevo


@app.get("/")
def raiz() -> dict:
    return {"api": "rutas", "docs": "/docs"}
