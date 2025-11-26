"""
主应用入口：独立 FastAPI 爬虫服务

本文件将 crawler 作为主应用运行，支持直接启动。
"""
from fastapi import FastAPI
from crawler.router import router as crawler_router
from crawler.lifecycle import crawler_lifespan
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=crawler_lifespan)
app.include_router(crawler_router)

origins = [
    "*" 
    # 将来部署时, 您应该只允许您的前端网址
    # "http://your-frontend-domain.com", 
]

# 3. 添加中间件 (Middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 允许访问的来源
    allow_credentials=True,    # 允许 cookie
    allow_methods=["*"],       # 允许所有 HTTP 方法 (GET, POST, OPTIONS 等)
    allow_headers=["*"],       # 允许所有请求头
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
