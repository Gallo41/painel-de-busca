import os
import sys
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, purge_simulated_leads, upsert_niches
from app.routers.leads_router import router as leads_router
from app.routers.outreach_router import router as outreach_router
from app.services.niches_catalog import DEFAULT_NICHES


def create_app(db_path: Optional[str] = None) -> FastAPI:
    if db_path:
        os.environ["PAINEL_DB_PATH"] = db_path

    init_db(db_path)
    upsert_niches(DEFAULT_NICHES, db_path=db_path)
    if not db_path:
        # Banco real do usuário: nunca mantém leads de demonstração/gerados misturados com dados reais
        purge_simulated_leads()

    app = FastAPI(
        title="Painel de Busca, Raio-X & Prospecção de Leads",
        description=(
            "Sistema de prospecção de clientes para freelancers (Sites, Reformas e Sistemas Complexos) "
            "integrando a skill google-maps-scraper, as 8 ferramentas de Raio-X e API pré-pronta para automação futura de Outreach."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(leads_router)
    app.include_router(outreach_router)

    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_dashboard():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Painel de Busca API ativa. Acesse /docs para documentação."}

    return app


app = create_app()
