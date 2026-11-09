from fastapi import APIRouter, Depends, HTTPException, Query

from app.database.dependencies.auth import get_current_user
from app.schemas.education_resource import ProviderName, ResourceSearch
from app.services.education_resources import search_resources

router = APIRouter(prefix="/resources", tags=["Resource discovery"])


@router.get("/search", response_model=ResourceSearch, dependencies=[Depends(get_current_user)])
def search(q: str = Query(..., min_length=2, max_length=200),
           provider: ProviderName | None = None, limit: int = Query(8, ge=1, le=12)):
    query = " ".join(q.split())
    if len(query) < 2:
        raise HTTPException(422, "Enter at least two characters to search")
    return search_resources(query, provider, limit)

