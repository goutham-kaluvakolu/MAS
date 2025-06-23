import json
from langchain_core.messages import SystemMessage, BaseMessage, AIMessage, HumanMessage
from models.llm import get_llm
from graph.state import State
import prompts.planner_system_prompt

def planner_node(state: State) -> dict:
    """
    The central planner node. It analyzes the full conversation history
    and decides the next step, outputting a JSON object to update the state.

    Args:
        state: The current state of the graph.

    Returns:
        dict: A dictionary of state keys to update.
    """
    print("---EXECUTING PLANNER---")
    llm = get_llm()
    system_prompt = prompts.planner_system_prompt.system_prompt

    # 1. Correctly initialize main_task only on the first run.
    # The first message is always the user's initial request.
    if state.get("main_task") is None:
        # Check if messages exist and are not empty
        if state.get("messages") and isinstance(state["messages"][0], BaseMessage):
             main_task = state["messages"][0].content
        else:
             main_task = "" # Fallback if messages are not in the expected format
        state["main_task"] = main_task


    # 2. Provide the LLM with the FULL conversation history.
    # This is the most critical change. The planner must see what the other agents did.
    messages_for_llm = [SystemMessage(content=system_prompt)]
    # We construct a serializable representation of the state for the LLM
    current_state_str = json.dumps(
        {
            "main_task": state.get("main_task"),
            "plan": state.get("plan"),
            "messages": [msg.content if isinstance(msg, BaseMessage) else str(msg) for msg in state.get("messages", [])]
        },
        indent=2
    )
    
    prompt_with_state = f"Here is the current state of our task. Your job is to analyze it and decide the next step by outputting the required JSON object.\n\nCURRENT STATE:\n{current_state_str}"
    messages_for_llm.append(HumanMessage(content=prompt_with_state))

    print(f"Passing the following context to Planner LLM:\n{prompt_with_state}")

    # 3. Get response from LLM
    # We add .dict() to ensure the model knows to output JSON
    response = llm.with_structured_output(State).invoke(messages_for_llm)

    # 4. Update state with the parsed response
    # The response object is now a Pydantic model that matches our State TypedDict
    print(f"Planner LLM generated response:\n{response}")

    # The 'response' is now an object with attributes, not a dictionary
    next_agent = response.get("next_agent", "END")
    task_completed = next_agent == "END" or response.get("task_completed", False)
    final_answer = response.get("final_answer") if task_completed else None

    # We return a dictionary of the fields we want to update in the state.
    # LangGraph will merge these updates into the main state.
    update_dict = {
        "plan": response.get("plan", []),
        "current_task": response.get("current_task"),
        "next_agent": next_agent,
        "task_completed": task_completed,
        # Append the planner's decision to the message history for logging
        "messages": [AIMessage(content=json.dumps(response))],
        "final_answer": final_answer,
    }
    
    # We are returning a dictionary that LangGraph will use to update the state
    return update_dict