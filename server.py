import os
import re
import json
import httpx
import asyncio
import aiomysql
from aiomysql import DictCursor
from typing import Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the MCP Server
mcp_server = FastMCP("UnifiedTools")

OPENWEATHER_API_BASE = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")  # 可以改成放.env里
USER_AGENT = "weather-app/1.0"

# Global variable for DB connection pool
db_pool = None

# ========== Database Connection Initialization ==========
async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            minsize=1, maxsize=10, autocommit=True,
        )
    return db_pool

# asyncio.get_event_loop().run_until_complete(init_db())

# @mcp_server.on_startup
# async def on_startup():
#     await init_db()

# ========== General SQL Execution ==========
async def sql_query(query: str, params: tuple = (), *, as_dict: bool = False):
    db_pool = await get_db_pool()
    if not re.match(r"^\s*(select|show|describe|desc|explain)\b", query, re.I):
        raise ValueError("Only read-only queries are permitted.")

    async with db_pool.acquire() as conn:
        cursor_cls = DictCursor if as_dict else aiomysql.Cursor
        async with conn.cursor(cursor_cls) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

# ========== Weather Fetch ==========
async def fetch_weather(city: str) -> dict[str, Any] | None:
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "zh_cn",
    }
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPENWEATHER_API_BASE, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {f"HTTP Error {e.response.status_code}: {e}"}
        except Exception as e:
            return {f"Request failed: {str(e)}"}

def format_weather(data: dict[str, Any] | str) -> str:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            return f"无法解析天气数据: {e}"
        
    if "error" in data:
        return f"{data['error']}"

    city = data.get("name", "N/A")
    country = data.get("sys", {}).get("country", "N/A")
    temp = data.get("main", {}).get("temp", "N/A")
    pressure = data.get("main", {}).get("pressure", "N/A")
    humidity = data.get("main", {}).get("humidity", "N/A")
    wind_speed = data.get("wind", {}).get("speed", "N/A")
    weather_list = data.get("weather", [{}])
    description = weather_list[0].get("description", "N/A") if weather_list else "N/A"

    return (
        f"{country}, {city}\n"
        f"Temperature: {temp}°C\n"
        f"Pressure: {pressure} hPa\n"
        f"Humidity: {humidity}%\n"
        f"Wind Speed: {wind_speed} m/s\n"
        f"Weather: {description}"
    )

# ========== MCP Tool Definitions ==========

@mcp_server.tool(description="Get the weather information of a specific city.")
async def query_weather(city: str) -> str:
    data = await fetch_weather(city)
    return format_weather(data)

@mcp_server.tool(description="List every table in the current database with estimated row count and size (MB).")
async def list_tables() -> list[dict]:
    meta_rows = await sql_query("SHOW TABLE STATUS", as_dict=True)
    return [
        {
            "table_name": row["Name"],
            "row_estimate": int(row["Rows"]),
            "size_mb": round((row["Data_length"] + row["Index_length"]) / 1024 / 1024, 2),
        }
        for row in meta_rows
    ]

@mcp_server.tool(description="Describe the structure of a specific table, including column names, types, and keys.")
async def describe_table(table: str) -> dict:
    rows = await sql_query(f"SHOW COLUMNS FROM `{table}`")
    return {
        "columns": [
            {"name": c[0], "type": c[1], "null": c[2], "key": c[3]}
            for c in rows
        ]
    }

select_regex = re.compile(r"^select\s.+\sfrom\s.+", re.I | re.S)

@mcp_server.tool(description="Execute a safe SELECT query against the MySQL database.")
async def query_mysql(query: str) -> dict:
    if not select_regex.match(query.strip()):
        raise ValueError("Only SELECT queries are allowed.")
    rows = await sql_query(query)
    return {"query": query, "rows": rows}

# ========== Main Entrypoint ==========
    

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
