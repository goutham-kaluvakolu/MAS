import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from graph.state import State
import prompts.websearch_agent_system_prompt
from models.llm import get_llm
from langchain_community.tools import DuckDuckGoSearchResults

async def websearch_agent_node(state: State) -> dict:
    """
    A more robust web search agent that ensures a summary is generated.
    """
    print("---EXECUTING WEB SEARCH AGENT---")
    try:
        llm = get_llm()
        system_prompt = prompts.websearch_agent_system_prompt.system_prompt
        current_task = state.get("current_task", "No task specified")

        search_tool = DuckDuckGoSearchResults(name="duckduckgo_search")
        llm_with_tools = llm.bind_tools([search_tool])

        # Initial messages to generate the tool call
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=current_task)
        ]
        response_with_tool_call = llm_with_tools.invoke(messages)
        messages.append(response_with_tool_call)

        summary = ""
        if not response_with_tool_call.tool_calls:
            print("LLM decided no search was needed. Using its response directly.")
            summary = response_with_tool_call.content
        else:
            print(f"LLM generated tool calls: {response_with_tool_call.tool_calls}")
            for tool_call in response_with_tool_call.tool_calls:
                try:
                    search_query = tool_call.get("args", {}).get("query")
                    if not search_query:
                        raise ValueError("Search query argument is missing.")
                    print(f"Executing search for query: '{search_query}'")
                    search_result = search_tool.invoke(search_query)
                    print("Raw DuckDuckGo Search Result received.")
                    messages.append(ToolMessage(content=str(search_result), tool_call_id=tool_call['id']))
                except Exception as e:
                    print(f"Error executing tool call {tool_call['id']}: {e}")
                    messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call['id']))

            # --- KEY IMPROVEMENT: A more forceful and clear prompt for summarization ---
            synthesis_prompt = (
                "You are a research summarizer. Based ONLY on the provided search results from the `ToolMessage`,"
                f"provide a comprehensive and detailed answer to the original user task: '{current_task}'."
                "Do not mention the search process itself. Directly answer the question with the information found."
            )
            messages.append(HumanMessage(content=synthesis_prompt))

            print("Synthesizing final answer based on search results...")
            final_response = llm.invoke(messages) # Use the base LLM without tools for the final answer
            summary = final_response.content

        # --- KEY IMPROVEMENT: Check if the summary is empty ---
        if not summary or len(summary) < 20:
             print("Warning: LLM generated an empty or insufficient summary. Reporting failure.")
             output_json = {
                "status": "FAILURE",
                "summary": "Failed to generate a meaningful summary from the web search results."
             }
        else:
            print(f"LLM Summary:\n{summary}\n")
            output_json = {
                "status": "SUCCESS",
                "summary": summary
            }

        return {"messages": [AIMessage(content=json.dumps(output_json))]}

    except Exception as e:
        print(f"Error in websearch_agent_node: {e}")
        error_output = {"status": "FAILURE", "summary": f"An error occurred: {str(e)}"}
        return {"messages": [AIMessage(content=json.dumps(error_output))]}