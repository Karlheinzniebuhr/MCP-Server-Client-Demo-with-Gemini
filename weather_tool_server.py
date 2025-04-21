from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(filename='mcp_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__) # Get a logger for this module

logger.info("Initializing FastMCP server...")
# Initialize FastMCP server
mcp = FastMCP("weather")
logger.info("FastMCP server initialized.")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"



async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""



@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    logger.info(f"MCP Request Received: get_alerts with state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        result = "Unable to fetch alerts or no alerts found."
    elif not data["features"]:
        result = "No active alerts for this state."
    else:
        alerts = [format_alert(feature) for feature in data["features"]]
        result = "\n---\n".join(alerts)

    # ---> Log full result text sent back via MCP <--- 
    logger.info(f"=== MCP Response Sent (get_alerts) ===\n{result}\n======================================")
    return result

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    logger.info(f"MCP Request Received: get_forecast with latitude: {latitude}, longitude: {longitude}")

    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        result = "Unable to fetch forecast data for this location."
    else:
        # Get the forecast URL from the points response
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)

        if not forecast_data:
            result = "Unable to fetch detailed forecast."
        else:
            # Format the periods into a readable forecast
            periods = forecast_data["properties"]["periods"]
            forecasts = []
            for period in periods[:5]:  # Only show next 5 periods
                forecast = f"""
                    {period['name']}:
                    Temperature: {period['temperature']}°{period['temperatureUnit']}
                    Wind: {period['windSpeed']} {period['windDirection']}
                    Forecast: {period['detailedForecast']}
                    """
                forecasts.append(forecast)
            result = "\n---\n".join(forecasts)
    # ---> Log full result text sent back via MCP <--- 
    logger.info(f"=== MCP Response Sent (get_forecast) ===\n{result}\n=======================================")
    return result



if __name__ == "__main__":
    logger.info("MCP Server Script Starting Execution...")
    # Initialize and run the server
    try:
        mcp.run(transport='stdio')
        logger.info("mcp.run() finished gracefully.") # Might not be reached with stdio
    except Exception as e:
        logger.critical(f"MCP Server crashed: {e}", exc_info=True)
        raise