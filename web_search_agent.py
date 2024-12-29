# Source: https://www.youtube.com/watch?v=pC17ge_2n0Q
# https://github.com/coleam00/ai-agents-masterclass/blob/main/pydantic-ai/web_search_agent.py

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
# from typing import Any

import logfire
from devtools import debug
from httpx import AsyncClient
from dotenv import load_dotenv

from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext 

load_dotenv()
llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')

# If using OpenAI compatible URL
client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='' # notneeded for ollama
)

# model picker between OpenAI or Ollama
model = OpenAIModel(llm) if llm.lower().startswith("gpt") else OpenAIModel(llm, openai_client=client)

# configure logfire
logfire.configure(send_to_logfire='if-token-present')

# define dependency for the agent
@dataclass
class Deps:
    client: AsyncClient
    brave_api_key: str | None  # doesnt pass API key to LLM model

# create the pydantic Search Agent
web_search_agent = Agent (
    model,
    system_prompt=f'You are an expert at researching the web to answer user questions. The current date is: {datetime.now().strftime("%Y-%m-%d")}',
    deps_type=Deps,
    retries=2
)

@web_search_agent.tool
async def search_web(
    ctx: RunContext[Deps], web_query: str
) -> str:
    """ Search the web given a query defined to answer the user's question.

    Args:
        ctx: The context.
        web_query: The query from the web search.

    Returns:
        str: The search results as a formatted sting.

    """
    if ctx.deps.brave_api_key is None:
        return "This is a test web search result. Please provide a valid Brave API key to get real search results."
    
    await asyncio.sleep(2)

    # headers = {
    #     'X-Subscription-Token': ctx.deps.brave_api_key,
    #     'Accept': 'application/json',
    # }

    #dynamic logging in logfire
    with logfire.span('calling Brave search API', query=web_query) as span:
        r = await ctx.deps.client.get(
            'https://api.search.brave.com/res/v1/web/search',
            params={
                'q': web_query,
                'count': 1,
                'text_decorations': True,
                'search_lang': 'en'
            },
            # headers=headers
            headers = {
                'X-Subscription-Token': ctx.deps.brave_api_key,
                'Accept': 'application/json',
            }
        )
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    # Add web results in a nicely formatted way
    results = []

    web_result = data.get('web',{}).get('results',[])
    for item in web_result[:3]:
        title = item.get('title','')
        description = item.get('description','')
        url = item.get('url','')
        if title and description:
            results.append(f"Title: {title}\nSummary: {description}\n Source: {url}\n")

    return "\n".join(results) if results else "No results found for the query"

async def main():
    prompt = 'Give me some articles talking about Acra and Singapore'

    async with AsyncClient() as client:
        brave_api_key = os.getenv('BRAVE_API_KEY', None)
        deps = Deps(client=client, brave_api_key=brave_api_key)

        result = await web_search_agent.run(
            prompt, deps=deps
        )

        debug(result)
        print('Response', result.data)

if __name__ == "__main__":
    asyncio.run(main())