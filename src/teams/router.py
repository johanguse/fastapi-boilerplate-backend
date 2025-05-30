from fastapi import APIRouter

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/")
async def list_teams():
    """List teams - placeholder endpoint."""
    return {"message": "Teams endpoint - coming soon"}
