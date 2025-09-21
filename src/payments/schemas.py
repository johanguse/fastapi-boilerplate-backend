from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: str
    name: str
    price: int
    currency: str = 'usd'
    interval: str  # month/year
    interval_count: int = 1
    max_projects: int
    features: list[str]
