#!/usr/bin/env python
# coding: utf-8

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from db_manager import cancel_order, comment_order, check_order_status, food_search


llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)

TOOLS = [cancel_order, check_order_status, comment_order, food_search]
llm_with_tools = llm.bind_tools(TOOLS)

ASSISTANT_PROMPT = (
    """
You are a helpful food ordering assistant for a CLI/terminal experience. You can NOT place orders yourself, but you help via these tools:

1) food_search(food_name, restaurant_name)
2) cancel_order(order_id, phone_number)
3) comment_order(order_id, person_name, comment)
4) check_order_status(order_id)

Rules for multi-turn chat in terminal:
- Use conversation memory (previous turns) to resolve short replies. If the user previously indicated an intent (e.g., "check status") and then provides just a number like "87", assume it's the missing order_id and proceed.
- If information is still ambiguous, ask a concise follow-up question. DO NOT repeat questions already answered (e.g., if the user said "any restaurant", don't ask again).
- Never guess required fields; collect them. But do interpret terse follow-ups in context.
- After each tool call, summarize the result briefly and clearly.
- Only say: "Sorry, I can only help with food orders and related services." when the message is truly unrelated. Do NOT say this for numeric-only messages—those are likely IDs.
"""
).strip()


def _assistant_node(state: MessagesState):
    # System message is injected every turn; memory comes from checkpointer+thread_id
    output = llm_with_tools.invoke([SystemMessage(content=ASSISTANT_PROMPT)] + state["messages"])
    return {"messages": [output]}


# Build the graph ONCE at import time, with a memory checkpointer 
_builder = StateGraph(MessagesState)
_builder.add_node("assistant", _assistant_node)
_builder.add_node("tools", ToolNode(TOOLS))

_builder.add_edge(START, "assistant")
_builder.add_conditional_edges("assistant", tools_condition)
_builder.add_edge("tools", "assistant")

_memory = MemorySaver()
GRAPH = _builder.compile(checkpointer=_memory)


def run_turn(user_text: str, thread_id: str) -> str:
    """Run a single user turn through the graph and return the assistant's latest text.

    Keep the SAME thread_id across the whole CLI session to preserve memory.
    """
    initial_input = {"messages": [HumanMessage(content=user_text)]}
    cfg = {"configurable": {"thread_id": thread_id}}

    last_text: Optional[str] = None
    for event in GRAPH.stream(initial_input, cfg, stream_mode="values"):
        msgs = event.get("messages", [])
        if msgs:
            last = msgs[-1]
            # We only print assistant/tool messages that actually have text
            content = getattr(last, "content", None)
            if isinstance(content, str):
                last_text = content

    return last_text or ""