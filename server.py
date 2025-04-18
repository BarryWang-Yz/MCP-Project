import aiomysql
import httpx
import json
from typing import Any
from mcp.server.fastmcp import FastMCP

#Initialize the MCP Server

mcp_server = FastMCP("UnifiedTools")
# mcp_sql_server = FastMCP("SQLServer")

OPENWEATHER_API_BASE = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "c46233933d733988b30f541e698f6c3f"
USER_AGENT = "weather-app/1.0"

async def fetch_weather(city : str) -> dict[str, Any] | None:
    params = {
        "q": city,
        'appid': API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPENWEATHER_API_BASE, params=params, headers=headers, timeout=30.0)
            print(f"[Debug] Request URL: {response.url}")
            print(f"[Debug] Response: {response.text}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            return {f"HTTP Error {e.response.status_code}: {e}"}
        
        except Exception as e:
            return {f"request fail: {str(e)}"}
        

def format_weather (data : dict [str, Any] | str) -> str:
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

    return {
        f"{country}, {city}\n"
        f"Temperature: {temp}°C\n"
        f"Pressure: {pressure} hPa\n"
        f"Humidity: {humidity}%\n"
        f"Wind Speed: {wind_speed} m/s\n"
        f"Weather: {description}"
    }

# Define an asynchronous function to execute a SQL query and return the results
async def sql_query(query: str) -> list[tuple]:
    # Create an asynchronous connection pool to the MySQL database
    pool = await aiomysql.create_pool(
        host='127.0.0.1',       # MySQL server host (localhost)
        port=3306,              # Default MySQL port
        user='root',            # Database username
        password='rootpw',      # Database password
        db='mcp_demo'           # Database name to connect to
    )
    
    # Acquire a connection from the pool
    async with pool.acquire() as conn:
        # Open a new cursor (used to execute queries)
        async with conn.cursor() as cursor:
            # Execute the SQL query passed to the function
            await cursor.execute(query)
            # Fetch all resulting rows as a list of tuples
            result = await cursor.fetchall()
            print(f"\n [SQL Debug] result: {result}")
    
    # Close the connection pool
    pool.close()
    
    # Return the fetched result to the caller
    return result
    

@mcp_server.tool()
async def query_weather(city: str) -> str:
    data = await fetch_weather(city)
    return format_weather(data)


@mcp_server.tool()
async def query_mysql(query: str) -> dict:
    """
        Generate a Select Query to retrive data from mySQL DB
    """
    # cols = cols.join(column)
    # query = f"SELECT {cols} FROM {table}"
    # if condition:
    #     query += f" WHERE {condition}"
    row = await sql_query(query)
    return {"query": query, "rows": row}


if __name__ == "__main__":
    mcp_server.run(transport='stdio')
    mcp_server.run(transport='stdio')
    # asyncio.run(test())