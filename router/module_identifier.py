# module_identifier.py
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)
IDENTIFIER_PROMPT = PromptTemplate.from_template(
"""You are a strict router for a food assistant. 
Pick exactly ONE module name from this list and output ONLY that token:
- food_info        : factual info about foods, ingredients, nutrition, benefits/risks, definitions, recipes, preparation, and cooking methods.
- food_suggestion  : recommending or finding dishes or cuisines based on preferences or constraints, WITHOUT explicitly naming a specific food or restaurant.
- food_services    : any request that explicitly names a specific food or restaurant, including when asking for restaurants, menus, prices, deals, locations, or services like ordering, canceling, tracking orders, delivery, or payment.
- irrelevant       : the request is NOT about food, cooking, recipes, cuisines, restaurants, nutrition, or food services.

Rules:
- Output MUST be exactly one of: food_info | food_suggestion | food_services | irrelevant
- If the request is about how to prepare or cook a dish, always choose food_info.
- If the request explicitly names a food or restaurant (e.g., “pizza”, “McDonald’s”) → choose food_services, unless the intent is clearly to learn how to prepare it (then choose food_info).
- If the request describes food preferences or constraints without naming a specific food or restaurant → choose food_suggestion.
- If unrelated to food → choose irrelevant.

User request: {input}
Answer:"""

)
last_prmpt="""
You are a strict router for a food assistant. 
Pick exactly ONE module name from this list and output ONLY that token:
- food_info        : factual info about foods, ingredients, nutrition, benefits/risks, definitions.
- food_suggestion  : recommending or finding dishes/menus based on preferences, constraints, cuisines.
- food_services    : actions and services like ordering, canceling, tracking orders, delivery, restaurant services.
- irrelevant       : the request is NOT about food, cooking, recipes, cuisines, restaurants, nutrition, or food services.

Rules:
- Output MUST be exactly one of: food_info | food_suggestion | food_services | irrelevant
- No extra text, no punctuation, no code fences.
- If the request is partially about food (ingredients, recipes, nutrition, menus, cuisines, ordering), consider it food-related.

User request: {input}
Answer:
"""

def identify_module(user_input: str) -> str:
    """Return one of: food_info | food_suggestion | food_services | irrelevant"""
    resp = llm.invoke(IDENTIFIER_PROMPT.format(input=user_input))
    name = resp.content.strip().lower()
    allowed = {"food_info", "food_suggestion", "food_services", "irrelevant"}
    
    for tok in allowed:
        if tok == name or tok in name:
            return tok
    return "irrelevant"
