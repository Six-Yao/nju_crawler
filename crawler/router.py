"""
爬虫服务 API 路由

本文件负责暴露 /api/crawl 接口，供前端或调度系统触发指定源的抓取。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

# 数据模型：请求体、响应体、错误体
from .models import CrawlRequest, CrawlResponse, ErrorResponse
# 业务逻辑：实际抓取实现
from .services import crawl_source
# 其他 API 路由
from storage.router import router as records_router

# 创建路由器实例
router = APIRouter()

#
# POST /api/crawl
# 说明：
#   - 请求体：{"source": "源ID"}
#   - 用于触发某个官网/公众号的抓取任务
#   - 返回抓取到的数据列表
#   - 未知源返回 404，网络/解析异常返回 502
#
@router.post(
    "/api/crawl",
    response_model=CrawlResponse,
    responses={404: {"model": ErrorResponse}},
)
async def crawl_endpoint(payload: CrawlRequest) -> CrawlResponse:
    """
    触发指定 source 的抓取任务。
    参数：payload.source（字符串，源标识）
    返回：CrawlResponse（抓取结果数据）
    异常：
      - ValueError：源不存在，返回 404
      - RuntimeError：网络或解析失败，返回 502
    """
    try:
        if payload.source == "all":
            # 抓取所有源
            data = []
            for source in [s["id"] for s in crawl_source.TARGET_SOURCES]:
                source_data = await crawl_source(source)
                data.extend(source_data)
        else:
            data = await crawl_source(payload.source)  # 调用服务层异步抓取
        return CrawlResponse(data=data)
    except ValueError as exc:
        # 未知源，返回 404
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        # 网络/解析异常，返回 502
        raise HTTPException(status_code=502, detail=str(exc))

# 挂载统一查询 API 路由
router.include_router(records_router, prefix="/api")