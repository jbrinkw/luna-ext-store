# GeneralByte Extension

Minimal utilities extension providing essential assistant capabilities.

## Features

- **Phone Notifications**: Send push notifications via Home Assistant's notify service
- **Web Search**: Perform general web searches using Tavily API
- **Weather**: Get current weather information for any location (defaults to Charlotte, NC)

## Tools

### GENERAL_ACTION_send_phone_notification
Send a phone notification via Home Assistant.

**Example**: "Notify me: Garage door is open"

**Required Environment Variables**:
- `HA_URL`: Home Assistant instance URL
- `HA_TOKEN`: Home Assistant long-lived access token
- `DEFAULT_NOTIFY_SERVICE`: Target notify service (optional, defaults to mobile_app_jeremys_iphone)

### GENERAL_GET_web_search
Search the web and return top results with titles, URLs, and content snippets.

**Example**: "search for langchain tavily integration"

**Required Environment Variables**:
- `TAVILY_API_KEY`: Tavily API key for web search

### GENERAL_GET_weather
Get current weather conditions for any location using Open-Meteo API.

**Example**: "weather in Paris" or just "weather" (defaults to Charlotte, NC)

**Required Environment Variables**: None (uses free Open-Meteo API)

## Installation

Required secrets in `.env`:
```
HA_URL=http://your-homeassistant:8123
HA_TOKEN=your-long-lived-access-token
TAVILY_API_KEY=tvly-your-api-key
DEFAULT_NOTIFY_SERVICE=mobile_app_your_device
```

## Dependencies

- `requests`
- `pydantic`
- `python-dotenv`
- `langchain-tavily`

Install via: `pip install requests pydantic python-dotenv langchain-tavily`

