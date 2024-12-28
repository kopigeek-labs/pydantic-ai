import os
from typing import cast

import logfire
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')

##################################################################################
#####   Define a Pydantic Model and call it at the Agent with result_type   ######
##################################################################################
class MyModel(BaseModel):
    """
    A pydantic model (BaseModel) to demonstrate a structured result_type returned by the Agent
    """
    city: str
    country: str

model = cast(KnownModelName, os.getenv('PYDANTIC_AI_MODEL', 'openai:gpt-4o-mini'))

print(f'Using Model: {model}')

agent = Agent(
    model,
    result_type=MyModel # the agent returns a structured response
    )

if __name__ == '__main__':
    result = agent.run_sync('The windy city in the US of A')
    # print(result.data)
    print(result.data.country)
    print(result.data.city)
