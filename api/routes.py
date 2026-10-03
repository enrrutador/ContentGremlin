"""ContentGremlin API routes — legacy core + production engine."""
from api._routes_core import router as _core_router
from api.production_routes import router as production_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(_core_router)
router.include_router(production_router)
