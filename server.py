import asyncio
import httpx
import json
from typing import Any
from mcp.server.fastmcp import FastMCP

#Initialize the MCP Server

mcp_server = FastMCP("WeatherServer")

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

@mcp_server.tool()
async def query_weather(city: str) -> str:
    data = await fetch_weather(city)
    return format_weather(data)

# async def test():
#     try: 
#         data = await fetch_weather(Beijing)
#         return format_weather(data)
    
#     except Exception as e:
#         return f"Error message (from server.py): {str(e)}"

if __name__ == "__main__":
    mcp_server.run(transport='stdio')
    # asyncio.run(test())