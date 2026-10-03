"""
ContentGremlin - API Routes

Production engine routes are always mounted.
Legacy pipeline routes are loaded from api._routes_core when present.

On this feature branch, if _routes_core is incomplete, restore with:
  git checkout main -- api/routes.py
  # then re-add: from api.production_routes import router as production_router
  #              router.include_router(production_router)
Or merge this branch and resolve routes.py by keeping main body + production include.
"""
from fastapi import APIRouter

router = APIRouter()

# Production engine (publish-ready): /produce /qa /production /broll /music
from api.production_routes import router as production_router

router.include_router(production_router)

# Legacy pipeline routes (analyze, ideas, script, super_pipeline, …)
try:
    from api._routes_core import router as core_router

    router.include_router(core_router)
except Exception as _exc:  # pragma: no cover - branch bootstrap
    import warnings

    warnings.warn(
        f"Legacy api._routes_core not loaded ({_exc}). "
        "Production endpoints work; restore core routes from main if needed."
    )
