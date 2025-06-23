from typing import TypedDict, List, Optional
from typing_extensions import Annotated


class State(TypedDict):
    main_task: Optional[str]
    messages: List[str]
    current_task: Optional[str]
    plan: Optional[List[str]]
    next_agent: Optional[str]
    task_completed: bool
    final_answer: Optional[str]