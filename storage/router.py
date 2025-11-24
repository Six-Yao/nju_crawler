from fastapi import APIRouter, Query
from typing import List, Optional
from storage import database

router = APIRouter()

@router.get("/records", summary="查询指定源和时间范围的数据")
def query_records(
    source_id: Optional[str] = Query(None, description="来源ID，可选"),
    start_time: Optional[str] = Query(None, description="开始时间，格式如2024-01-01"),
    end_time: Optional[str] = Query(None, description="结束时间，格式如2024-01-31")
):
    return database.query_records(source_id, start_time, end_time)
