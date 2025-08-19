# main.py
import uuid
import io
import sys
from router.module_identifier import identify_module
from langchain.schema import AIMessage
from modules.food_info import FoodInfoModule
from modules.food_suggestion import graph
from modules.food_services import run_turn  # (user_input, thread_id)
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage, AIMessage

def run_food_info(user_input: str) -> str:
    food_module = FoodInfoModule()
    return food_module.answer_question(user_input)


def run_food_suggestion(user_input: str, thread) -> str:
    
    state = {"messages": [HumanMessage(content=user_input)]}
    final_reply = ""

    
    for event in graph.stream(state, thread, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            content = getattr(last_msg, "content", "")
            if content:
                final_reply = content

    return final_reply.strip() if final_reply else "(No response)"


def run_food_services_module(user_input: str, thread_id: str) -> str:
    return run_turn(user_input, thread_id) or "(No response)"

def main():
    print("Unified Food Assistant (type 'exit' or 'quit' to leave)")

    services_thread_id = str(uuid.uuid4())  # Keep session for food_services
    suggestion_thread = {"configurable": {"thread_id": str(uuid.uuid4())}}  # session for food_suggestion

    current_module = None  # Current active module

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Use module_identifier only if no module is active
        if current_module is None:
            module_name = identify_module(user_input)
            print(module_name)
            if module_name == "irrelevant":
                print("I can only answer food-related questions (recipes, ingredients, nutrition, restaurants, ordering).")
                continue
            current_module = module_name
        else:
            module_name = current_module

        # Run the active module
        if module_name == "food_info":
            reply = run_food_info(user_input)
            # After one response, release the module
            current_module = None

        elif module_name == "food_suggestion":
            reply = run_food_suggestion(user_input, suggestion_thread)
            current_module = None

        elif module_name == "food_services":
            reply = run_food_services_module(user_input, services_thread_id)

        else:
            reply = "Could not determine the right module."
            current_module = None

        print(reply)

if __name__ == "__main__":
    main()
