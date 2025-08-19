#!/usr/bin/env python
# coding: utf-8

import os
import re
import json
import sqlite3
from Levenshtein import distance
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Initialize LLM

llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.environ["OPENAI_API_KEY"]
)


# Prompt for extracting search parameters

extract_prompt = PromptTemplate(
    input_variables=["description"],
    template="""
You are a helpful assistant for a restaurant search. 
Your task: 
1. Understand the user's food description.
2. Extract:
   - include_keywords: important keywords and cuisine names (English only)
   - synonyms: synonyms for each keyword if possible
   - exclude_keywords: items the user explicitly says they don't want
   - guessed_food_names: possible actual food dish names that fit the description, even if the user didn't mention them directly
"synonyms must always be a dictionary mapping each include_keyword to a list of synonyms, even if empty"

From the user request: "{description}"

Return JSON with keys: include_keywords, synonyms, exclude_keywords, guessed_food_names.
Make sure guessed_food_names are in English.
"""
)

def extract_search_params(description):
    prompt = extract_prompt.format(description=description)
    response = llm.invoke(prompt)
    response_text = getattr(response, "content", response)

    # Clean up JSON
    json_text_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if json_text_match:
        json_text = json_text_match.group(1)
    else:
        json_text_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
        json_text = json_text_match.group(1) if json_text_match else response_text

    try:
        params = json.loads(json_text)
    except json.JSONDecodeError:
        print("Failed to parse JSON:")
        print(json_text)
        params = {}

    return params


# Food search function

def enhanced_food_search(params, max_distance=2, db_path="food_orders.db"):
    if isinstance(params, str):
        params = json.loads(params)

    include_keywords = params.get("include_keywords", [])
    synonyms = params.get("synonyms", {})
    guessed_food_names = params.get("guessed_food_names", [])
    exclude_keywords = params.get("exclude_keywords", [])

    # Combine all keywords
    all_keywords = set(include_keywords)
    for syn_list in synonyms.values():
        all_keywords.update(syn_list)
    all_keywords.update(guessed_food_names)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT food_name, food_category, restaurant_name, price FROM foods")
    rows = cursor.fetchall()

    results = []
    for food_name_db, category_db, restaurant_db, price_db in rows:

        # Exclude check
        if any(ex_kw.lower() in field.lower() for ex_kw in exclude_keywords
               for field in (food_name_db, category_db, restaurant_db)):
            continue

        # Match score
        match_found = False
        min_dist = float('inf')
        for field_text in (food_name_db, category_db, restaurant_db):
            for kw in all_keywords:
                if kw.lower() in field_text.lower():
                    match_found = True
                    min_dist = 0
                    break
                else:
                    dist = distance(field_text.lower(), kw.lower())
                    if dist <= max_distance:
                        match_found = True
                        min_dist = min(min_dist, dist)
            if match_found and min_dist == 0:
                break

        if match_found:
            results.append({
                "food_name": food_name_db,
                "category": category_db,
                "restaurant_name": restaurant_db,
                "price": price_db,
                "edit_distance": min_dist
            })

    results.sort(key=lambda x: x["edit_distance"])
    conn.close()
    return results

def combined_food_search(user_input: str) -> str:
    """Search for food items based on the user's natural language input."""
    params = extract_search_params(user_input)
    results = enhanced_food_search(params)
    if not results:
        return "No food items matching your criteria were found."

    output_lines = [
        f"{r['food_name']} ({r['category']}) - {r['restaurant_name']} - {r['price']} "
        for r in results
    ]
    return "\n".join(output_lines)

# Bind the tool
tools = [combined_food_search]
llm_with_tools = llm.bind_tools(tools)

# Assistant prompt

prompt2 = """
You are a helpful assistant specialized in food search.  

When the user message contains any request about food, cuisine, dishes, ingredients, or preferences, you should call the tool by passing the user's message exactly as input.  

If the user message is unrelated to food or food search, respond politely that you can only assist with food search.  

When the tool returns a result, summarize it in natural language. If the result is empty, inform the user politely.

note that you can not order foods directly, you are assistant.
If the user asks about anything else not related to food orders, searching, or comments, respond with:  
**"Sorry, I can only help with food orders and related services."**
"""


# Graph nodes

sys_msg = SystemMessage(content=prompt2)

def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


# Interactive loop

def main():
    print("Interactive Food Search (type 'exit' to quit)")
    thread = {"configurable": {"thread_id": "user_thread"}}

    user_input = ""
    while user_input.lower() != "exit":
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            break

        initial_input = {"messages": user_input}

        # Stream the graph responses
        for event in graph.stream(initial_input, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()
        for event in graph.stream(None, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()
        for event in graph.stream(None, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()

if __name__ == "__main__":
    #main()
    pass
