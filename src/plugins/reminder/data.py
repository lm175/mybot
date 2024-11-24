from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    user_id: int = 0
    task_id: str = ''
    group_id: int = 0
    run_date: str = ''
    event_description: str = ''


@dataclass
class FunctionToll:
    name: str = ''
    arguments: str = ''

@dataclass
class ToolCall:
    id: str = ''
    index: int = 0
    type: str = 'function'
    function: FunctionToll = field(default_factory=FunctionToll)

    def __post_init__(self):
        if isinstance(self.function, dict):
            self.function = FunctionToll(**self.function)

@dataclass
class RespMessage:
    role: str = 'assistant'
    content: str = ''
    tool_calls: List[ToolCall] = field(default_factory=lambda: [ToolCall()])

    def __post_init__(self):
        if isinstance(self.tool_calls, list) and all(isinstance(p, dict) for p in self.tool_calls):
            self.tool_calls = [ToolCall(**p) for p in self.tool_calls] # type: ignore

@dataclass
class Choice:
    finish_reason: str = ''
    index: int = 0
    message: RespMessage = field(default_factory=RespMessage)

    def __post_init__(self):
        if isinstance(self.message, dict):
            self.message = RespMessage(**self.message)


class Response:
    def __init__(self, **kwargs) -> None:
        self.choice: Choice = Choice(**kwargs['choices'][0])
        self.model: str = kwargs.get('model', '')

        self.message = self.choice.message