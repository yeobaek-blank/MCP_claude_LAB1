from mcp.server.fastmcp import FastMCP
import requests
import os

# OpenWeather API Key (환경변수 또는 직접 입력)
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY") or "8ba4da2fcca28e93dd7087c0cb6414e1"

def fetch_weather(city: str) -> str:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
    )
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            
            return f"{city}의 현재 날씨: {weather}, 온도: {temp}°C"
        else:
            return f"{city}의 날씨 정보를 가져오지 못했습니다: {data.get('message', '오류')}"
    except Exception as e:
        return f"날씨 정보 조회 중 오류 발생: {e}"

mcp = FastMCP()

@mcp.tool()
def get_weather(city: str) -> str:
    """
    Returns weather of the city using OpenWeather API

    :param city: The city to get the weather for
    """
    return fetch_weather(city)

if __name__ == "__main__":
    mcp.run(transport="stdio")
