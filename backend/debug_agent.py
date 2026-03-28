from google.adk.agents import Agent
import inspect

agent = Agent(name="test", model="gemini-1.5-flash")
print(f"Agent class: {type(agent)}")
methods = [m for m, _ in inspect.getmembers(agent, predicate=inspect.ismethod)]
print(f"Methods: {methods}")
dir_members = dir(agent)
print(f"All members: {dir_members}")
