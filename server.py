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

@mcp_server.tool(description="可以将数据库中所有的表格都列举出来，并且能获取所有表格的大致信息。")
async def list_tables() -> list[dict]:
    # 显式指定数据库，避免默认库不一致
    meta_rows = await sql_query("SHOW TABLE STATUS", as_dict=True)
    return [
        {
            "table_name": row["Name"],
            "row_estimate": int(row["Rows"]),
            "size_mb": round((row["Data_length"] + row["Index_length"]) / 1024 / 1024, 2),
        }
        for row in meta_rows
    ]


@mcp_server.tool(description="可以将表格的所有column值都解析出来。请注意：该表格所需参数名为'table'。")
async def describe_table(table: str) -> dict:
    rows = await sql_query(f"SHOW COLUMNS FROM `{table}`", as_dict=True)
    return {
        "columns": [
            {"name": c["Field"], "type": c["Type"], "null": c["Null"], "key": c["Key"]}
            for c in rows
        ]
    }

select_regex = re.compile(r"^select\s.+\sfrom\s.+", re.I | re.S)

@mcp_server.tool(description="可以执行一个安全的SELECT query以确保能够从数据库中调取合理的数据。请注意：该表可所需参数名为'query'。")
async def query_mysql(query: str) -> dict:
    if not select_regex.match(query.strip()):
        raise ValueError("Only SELECT queries are allowed.")
    rows = await sql_query(query, as_dict=True)
    return {"payload": {"query": query, "rows": rows}}

# ========== Main Entrypoint ==========
    

# ========== Ivanti API Tools ==========

@mcp_server.tool(description="可以登录Ivanti系统并获取Session Key。成功登录后会缓存Session Key供后续接口使用。参数需要提供tenant、username、password、role。")
async def login_ivanti(tenant: str, username: str, password: str, role: str) -> str:
    global ivanti_session_key, ivanti_tenant
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://{tenant}/api/rest/authentication/login"
            payload = {"tenant": tenant, "username": username, "password": password, "role": role}
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            # Parse session key from response
            session_val = None
            try:
                session_val = response.json()
            except Exception:
                session_val = response.text.strip()
            if isinstance(session_val, dict):
                key = None
                if "sessionId" in session_val:
                    key = session_val["sessionId"]
                elif "SessionId" in session_val:
                    key = session_val["SessionId"]
                elif "token" in session_val:
                    key = session_val["token"]
                else:
                    return f"登录成功，但无法解析Session Key: {session_val}"
                session_val = key
            if not isinstance(session_val, str) or session_val == "":
                return "登录失败: 未获取到Session Key"
            # Store session key and tenant globally
            if tenant in session_val:
                ivanti_session_key = session_val
            else:
                ivanti_session_key = f"{tenant}#{session_val}#2"
            ivanti_tenant = tenant
            return "登录成功，Session Key 已缓存。"
        except httpx.HTTPStatusError as e:
            error_msg = ""
            try:
                err_json = e.response.json()
                if isinstance(err_json, dict):
                    if "error" in err_json:
                        error_msg = err_json.get("error")
                    elif "message" in err_json:
                        error_msg = err_json.get("message")
                    else:
                        error_msg = str(err_json)
                else:
                    error_msg = str(err_json)
            except Exception:
                error_msg = e.response.text
            return f"登录失败: HTTP {e.response.status_code} - {error_msg}"
        except Exception as e:
            return f"登录请求异常: {str(e)}"

@mcp_server.tool(description="可以根据工单单号获取Ivanti工单的详细信息。请确保已登录后再调用此工具，参数名为ticket_number。")
async def get_ticket_detail(ticket_number: int) -> dict:
    if not ivanti_session_key:
        return {"error": "未登录Ivanti，请先调用login_ivanti进行登录。"}
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://{ivanti_tenant}/api/odata/businessobject/incidents"
            params = {"$filter": f"incidentnumber eq {ticket_number}"}
            headers = {"Authorization": ivanti_session_key}
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                err_json = e.response.json()
                error_msg = err_json.get("error") if isinstance(err_json, dict) else str(err_json)
            except Exception:
                error_msg = e.response.text
            return {"error": f"HTTP {e.response.status_code} - {error_msg}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

@mcp_server.tool(description="可以根据用户登录ID获取Ivanti用户的详细信息。请确保已登录后再调用此工具，参数名为login_id。")
async def get_user_detail(login_id: str) -> dict:
    if not ivanti_session_key:
        return {"error": "未登录Ivanti，请先调用login_ivanti进行登录。"}
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://{ivanti_tenant}/api/odata/businessobject/employees"
            params = {"$filter": f"LoginID eq '{login_id}'"}
            headers = {"Authorization": ivanti_session_key}
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                err_json = e.response.json()
                error_msg = err_json.get("error") if isinstance(err_json, dict) else str(err_json)
            except Exception:
                error_msg = e.response.text
            return {"error": f"HTTP {e.response.status_code} - {error_msg}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

# ========== Main Entrypoint ==========
    

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
