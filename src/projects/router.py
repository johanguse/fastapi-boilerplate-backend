from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/")
async def list_projects() -> dict[str, str]:
    """List projects - placeholder endpoint."""
    return {"message": "Projects endpoint - coming soon"}
