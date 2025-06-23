from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from graph.state import State
from nodes.planner_node import planner_node
from nodes.google_apis_node import google_api_agent_node
from nodes.websearch_agent_node import websearch_agent_node

def decision_function(state: State):
    """
    Decision function that routes to the next agent based on planner's decision
    """
    print(state)
    # Get the next agent from the planner's decision
    next_agent = state.get("next_agent", "websearch_agent")
    
    # Route to the appropriate agent or end
    if next_agent == "google_apis_agent":
        return "google_apis_agent"
    elif next_agent == "websearch_agent":
        return "websearch_agent"
    elif next_agent == "END":
        return END
    else:
        # Default fallback
        return "websearch_agent"

graph_builder = StateGraph(State)
graph_builder.add_node("planner",planner_node)
graph_builder.add_node("google_apis_agent",google_api_agent_node)
graph_builder.add_node("websearch_agent",websearch_agent_node)

graph_builder.add_edge(START, "planner")
graph_builder.add_conditional_edges("planner", 
    decision_function,
    {
    "google_apis_agent": "google_apis_agent",
    "websearch_agent": "websearch_agent",
    END: END
})
graph_builder.add_edge("google_apis_agent", "planner")
graph_builder.add_edge("websearch_agent","planner")
# Note: We don't need the planner -> END edge anymore since it's handled in conditional edges

graph = graph_builder.compile()


# Export the uncompiled graph for visualization
__all__ = [ "graph"]

