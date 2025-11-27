from google.adk.agents import Agent

from adk_short_bot.prompt import ROOT_AGENT_INSTRUCTION
from adk_short_bot.tools import count_characters

root_agent = Agent(
    name="adk_short_bot",
    model="gemini-2.0-flash",
    description="An agent that summerize messages while maintaining their core meaning",
    instruction=ROOT_AGENT_INSTRUCTION,
    # The current ADK runtime expects `static_instruction`; set it explicitly to avoid
    # missing attribute errors in the remote Agent Engine environment.
    global_instruction=ROOT_AGENT_INSTRUCTION,
    tools=[count_characters],
)
# Patch the instance for compatibility with runtimes that access `static_instruction`.
# This attribute is not present on the pydantic model in google-adk 0.1.0.
object.__setattr__(root_agent, "static_instruction", ROOT_AGENT_INSTRUCTION)
