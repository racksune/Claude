import os
import uvicorn
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

client = OpenAI(
    base_url=os.environ["UPSTREAM_BASE_URL"],
    api_key=os.environ["UPSTREAM_API_KEY"]
)

MODEL = os.getenv("MODEL", "claude-opus-4-6")
ACCESS_TOKEN = os.environ["MCP_ACCESS_TOKEN"]

mcp = FastMCP("Claude Opus Bridge")

@mcp.tool()
def ask_opus(prompt: str) -> str:
    """Send a prompt to the configured AI model."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or "No response"

app = mcp.streamable_http_app()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/mcp"):
            expected = "Bearer " + ACCESS_TOKEN
            if request.headers.get("authorization") != expected:
                return Response("Unauthorized", status_code=401)
        return await call_next(request)

app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000"))
    )
