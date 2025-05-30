from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/")
async def list_projects():
    """List projects - placeholder endpoint."""
    return {"message": "Projects endpoint - coming soon"}
