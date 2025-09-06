
def browser_use_agent_gen():
    ...

class BrowserUseAgentBase:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.browser_use_agent = browser_use_agent_gen()
