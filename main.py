"""
主应用入口：独立 FastAPI 爬虫服务

本文件将 crawler 作为主应用运行，支持直接启动。
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
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

# 静态前端与首页挂载：由后端同端口提供 index.html
# 静态资源（若后续有 js/css/img）可放在 ./static 目录并自动挂载
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html; charset=utf-8")
    return {"message": "index.html 未找到，请将前端文件放在项目根目录。"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
