from fastapi import APIRouter
from ..services.ml_service import train_and_evaluate_ml

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


@router.get("/benchmark")
def get_benchmark_results():
    """Runs evaluation benchmark across 50+ labeled dataset samples comparing ML vs Heuristics."""
    return train_and_evaluate_ml()
