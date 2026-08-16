from fastapi import APIRouter

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("/")
async def search_knowledge(query: str):
    return {
        "message": "Search academic knowledge",
        "query": query,
        "results": [],
    }