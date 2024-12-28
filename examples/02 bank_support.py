from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bankdatabase import DatabaseConn

import logfire
logfire.configure()
# logfire.instrument_asyncpg() #postgresdb sync

@dataclass
class SupportDependencies:
    """Dependencies (deps_type) are used to pass data (e.g. search API keys, customer IDs), connections, \n
    and logic into the model that will be needed when running system prompt and tool functions. 

    Attributes:
        customer_id: Unique identifier for the customer
        db: Database connection instance
    """
    customer_id: int
    db: DatabaseConn


class SupportResult(BaseModel):
    """Pydantic model to constrain the structured data returned by agent. \n
    Pydantic can build tje JSON schema that tells the LLM how to return the data \n
    and performs validation to guarantee the data is correct at the end of the run
    """
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description='Whether to block their')
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type=SupportDependencies,
    result_type=SupportResult, # response from the agent will, be guaranteed to be a SupportResult
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query. '
        "Reply using the customer's name."
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    """Add customer name to the system prompt.

    Args:
        ctx: Runtime context containing customer dependencies

    Returns:
        str: System prompt addition with customer's name
    """
    customer_name = await ctx.deps.db.customer_name(customer_id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool
async def customer_balance(ctx: RunContext[SupportDependencies], include_pending: bool) -> str:
    """Returns the customer's current account balance."""
    balance = await ctx.deps.db.customer_balance(
        customer_id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return f'${balance:.2f}'


if __name__ == '__main__':
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = support_agent.run_sync('What is my balance?', deps=deps)
    print(result.data)
    # """
    # support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    # """

    result = support_agent.run_sync('I just lost my card!', deps=deps)
    print(result.data)
    # """
    # support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    # """

    logfire.info('Hello, {name}!', name='world')

