# FoodChat-AI 🍴🤖

FoodChat-AI is an intelligent chatbot prototype designed as part of a course project. It leverages Large Language Models (LLMs) along with LangChain and LangGraph to handle user queries in different domains of a food-assistant application.  

The project demonstrates modular chatbot design where the main LLM agent dynamically routes user queries to specialized modules (e.g., food info, customer services, food search, and food suggestions).  

⚠️ Note: This chatbot is not a real food-ordering system. It is a virtual assistant prototype focused on answering queries, providing suggestions, and simulating customer support tasks.  

---

## ✨ Features

- Food Information  
  Answers general or specific questions about foods and nutrition using knowledge sources.  

- Customer Services  
  Simulates support interactions such as:  
  - Tracking order status  
  - Canceling an order  
  - Leaving feedback  

- Food Search  
  Allows natural language search for available foods in restaurants.  
  Example queries:  
  - *"Which restaurants have pizza?"*  
  - *"What’s the price of Ghorme Sabzi in Milad restaurant?"*  

- Food Suggestions  
  Provides intelligent meal recommendations based on user preferences using reflection-like reasoning.  

---

## 🏗️ Project Structure
FoodChat-AI/
├── modules/
│   ├── food_info.py         # Handles food & nutrition info
│   ├── food_services.py     # Customer service tasks (order tracking, cancel, feedback)
│   └── food_suggestion.py   # Suggests foods based on user input
├── router/
│   └── module_identifier.py # Decides which module to call for a query
├── db_manager.py            # Simple DB interface for orders & menus
├── main.py                  # Entry point: LLM orchestrates module calls
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── The New Complete Book of Foods.pdf # Reference dataset
└── .gitignore
