from __future__ import annotations as _annotations

import asyncio
import os
from dotenv import load_dotenv
_ = load_dotenv()

from dataclasses import dataclass
from typing import Any

import logfire
from devtools import debug
from httpx import AsyncClient

from pydantic_ai import Agent, ModelRetry, RunContext

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')

@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None

weather_agent = Agent(
    model='openai:gpt-4o-mini',
    system_prompt=(
        'Be concise. Reply with one setence'
        'Use the `get_lat_lng` tool to get the latitude and longtitude of the locations,'
        'then use the `get_weather` tool to get the weather'
    ),
    deps_type=Deps,
    retries=2,
)

# Define the function-call tools for the agent
@weather_agent.tool
async def get_lat_lng(ctx: RunContext[Deps], location_description: str) -> dict[str, float]:
    """ Get the lat, long of a location.

    Args:
        ctx: Context and Dependencies
        location_description: descrption of a location
    """ 
    if ctx.deps.geo_api_key is None:
        return {'lat':51.1, 'lng':-0.1} # if no API key provided, return dummy location of London
    
    params = {
        'q': location_description,
        'api_key': ctx.deps.geo_api_key
    }

    with logfire.span('calling geocode API', params=params) as span:
        r = await ctx.deps.client.get('https://geocode.maps.co/search', params=params)
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

        if data: 
            return {'lat': data[0]['lat'], 'lng': data[0]['lon']}
        else:
            raise ModelRetry('Could not find the location')
        
@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    if ctx.deps.weather_api_key is None:
        return {'temperature':'99.9°C', 'decription':'Scorching hot'}
    
    params = {
        'apikey': ctx.deps.weather_api_key,
        'location': f'{lat},{lng}',
        'units': 'metric',
    }

    with logfire.span('calling weather API', params=params) as span:
        r = await ctx.deps.client.get(
            'https://api.tomorrow.io/v4/weather/realtime', params=params
        )
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    values = data['data']['values']
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    return {
        'temperature': f'{values["temperatureApparent"]:0.0f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
    }

async def main():
    async with AsyncClient() as client:
        # create a free API key at https://www.tomorrow.io/weather-api/
        weather_api_key = os.getenv('WEATHER_API_KEY')
        # create a free API key at https://geocode.maps.co/
        geo_api_key = os.getenv('GEO_API_KEY')
        deps = Deps(
            client=client, weather_api_key=weather_api_key, geo_api_key=geo_api_key
        )
        result = await weather_agent.run(
            'What is the weather like in Singapore?', deps=deps
        )
        debug(result)
        print('Response:', result.data)


if __name__ == '__main__':
    asyncio.run(main())