#!/usr/bin/env python3
"""
Test script to demonstrate the planner's decision-making capabilities
"""

from graph.builder import graph
from graph.state import State
import asyncio

async def test_planner_decisions():
    """Test different scenarios to see how the planner decides which agent to call"""
    
    test_cases = [
        "Check my Gmail for unread emails max of 3",
        # "get me the latest unread email from my gmail max of 3 , dont show me links",
        # "get me the upcomming calendar events from my calendar max of 3",
        # "who is the current president of the united states 2025",
        # "give me details about the conflict between israel and palestine",
        # "why is sachine considered the god of cricket",
        # "Find information about climate change",
        # "Schedule a meeting for tomorrow at 2 PM",
        # "Search for the latest AI research papers",
        # "Send an email to john@example.com",
        # "What's the weather like in New York?"
    ]
    
    for test_case in test_cases:

        # Initialize state with the test case
        initial_state = State(
            messages=[{"role": "user", "content": test_case}],
            current_task=None,
            plan=None,
            next_agent=None,
            task_completed=False,
            final_answer=None
        )
        
        # Run the graph using async API
        try:
            result = await graph.ainvoke(initial_state)
            print(f"User query: {test_case}")
            print(f"Final answer: {result.get('final_answer')}")
        except Exception as e:
            print(f"Error running graph: {e}")

if __name__ == "__main__":
    asyncio.run(test_planner_decisions()) 