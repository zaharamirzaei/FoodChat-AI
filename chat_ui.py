# chat_ui.py
import os
import sys
import uuid
from dotenv import load_dotenv

# Ensure local imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import chainlit as cl
from router.module_identifier import identify_module
from main import (
    run_food_info,
    run_food_suggestion,
    run_food_services_module,
)

load_dotenv()

EXIT_WORDS = {"exit", "quit", "bye", "goodbye"}


@cl.on_chat_start
async def on_start():
    cl.user_session.set("services_thread_id", str(uuid.uuid4()))
    cl.user_session.set(
        "suggestion_thread",
        {"configurable": {"thread_id": str(uuid.uuid4())}}
    )
    cl.user_session.set("current_module", None)

    await cl.Message(
        content=(
            "👋 Hi! I'm **ChatFood**.\n"
            "Ask me anything about food — recipes, ingredients, nutrition, restaurants, or ordering.\n"
            "Type `exit` anytime to release the current module."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    text = (message.content or "").strip()
    if not text:
        await cl.Message(content="⚠️ Please type something.").send()
        return

    # Release sticky module
    if text.lower() in EXIT_WORDS:
        cl.user_session.set("current_module", None)
        await cl.Message(content="✅ Current module released.").send()
        return

    current_module = cl.user_session.get("current_module")
    services_thread_id = cl.user_session.get("services_thread_id")
    suggestion_thread = cl.user_session.get("suggestion_thread")

    # Identify module if none is active
    if current_module is None:
        module_name = identify_module(text)
        if module_name == "irrelevant":
            await cl.Message(
                content="⚠️ I can only answer food-related questions (recipes, ingredients, nutrition, restaurants, ordering)."
            ).send()
            return
        cl.user_session.set("current_module", module_name)
        current_module = module_name
        await cl.Message(content=f"🔎 Module selected: **{module_name}**").send()

    try:
        if current_module == "food_info":
            reply = run_food_info(text)
            await cl.Message(content=reply).send()
            cl.user_session.set("current_module", None)

        elif current_module == "food_suggestion":
            reply = run_food_suggestion(text, suggestion_thread)
            await cl.Message(content=reply).send()
            cl.user_session.set("current_module", None)

        elif current_module == "food_services":
            reply = run_food_services_module(text, services_thread_id)
            await cl.Message(content=reply).send()

        else:
            await cl.Message(content="❓ Could not determine the right module.").send()
            cl.user_session.set("current_module", None)

    except Exception as e:
        await cl.Message(content=f"⚠️ Error: {e}").send()


