from fastapi import FastAPI, Query
from src.engine import SearchEngine

app = FastAPI(title="SearchMO API")
engine = SearchEngine()

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    results = engine.search(q)
    return {"query": q, "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
