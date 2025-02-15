from __future__ import annotations as _annotations

# import asyncio
import os
from dataclasses import dataclass
from typing import Any, List, Dict
# from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# import time
# import re
# import json

# import shuutil

# import httpx
# from git import Repo

# import logfire
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import OpenAI

from devtools import debug

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
# logfire.configure(send_to_logfire='if-token-present')

deepseekv3="deepseek/deepseek-chat:free"
gemini_flash="google-gla:gemini-1.5-flash"

# Setup OpenRouter Model
openrouter_model = OpenAIModel(
    model_name=deepseekv3,
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Setup a PydanticAI Agent
agent = Agent(
    model=openrouter_model,
    system_prompt="Keep responses under 20 words."
)

if __name__ == '__main__':
    result = agent.run_sync("Which model are you")
    print(result.data)
    print(result.usage())