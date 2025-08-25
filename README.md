# FoodChat-AI 🍴🤖

**FoodChat-AI** is an intelligent chatbot prototype designed as part of a course project. It leverages **Large Language Models (LLMs)** along with **LangChain**, **LangGraph**, and now **Chainlit** to handle user queries in different domains of a food-assistant application.  

The project demonstrates modular chatbot design where the **main LLM agent** dynamically routes user queries to specialized modules (e.g., food info, customer services, food search, and food suggestions).  

⚠️ Note: This chatbot is **not** a real food-ordering system. It is a **virtual assistant** prototype focused on answering queries, providing suggestions, and simulating customer support tasks.  

---

## ✨ Features

- **Food Information**  
  Answers general or specific questions about foods and nutrition using knowledge sources.  

- **Customer Services**  
  Simulates support interactions such as:  
  - Tracking order status  
  - Canceling an order  
  - Leaving feedback  

- **Food Search**  
  Allows natural language search for available foods in restaurants.  
  Example queries:  
  - *"Which restaurants have pizza?"*  
  - *"What’s the price of Ghorme Sabzi in Milad restaurant?"*  

- **Food Suggestions**  
  Provides intelligent meal recommendations based on user preferences using reflection-like reasoning.  

- **Interactive Chat UI (via Chainlit)**  
  A modern chat interface where:  
  - Modules are dynamically selected  
  - Customer services can handle multi-turn conversations  
  - Users can exit modules manually with commands like `exit`, `quit`, `bye`, etc.  

---

## 🏗 Project Structure

```
FoodChat-AI/
├── modules/
│   ├── food_info.py         # Handles food & nutrition info
│   ├── food_services.py     # Customer service tasks (order tracking, cancel, feedback)
│   └── food_suggestion.py   # Suggests foods based on user input
├── router/
│   └── module_identifier.py # Decides which module to call for a query
├── db_manager.py            # Simple DB interface for orders & menus
├── main.py                  # Entry point: LLM orchestrates module calls
├── chat_ui.py               # Chainlit interface for interactive chat UI
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── The New Complete Book of Foods.pdf # Reference dataset
└── .gitignore
```

---

## ⚙️ Installation & Setup

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/FoodChat-AI.git
   cd FoodChat-AI
   ```

2. **Create & activate a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## 🔑 Environment Variables

Before running the chatbot, configure your environment variables.  

1. Copy the example file:  
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your API keys:  
   ```ini
   # Example .env file
   OPENAI_API_KEY=your_openai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

Depending on which LLM provider you use (e.g., **OpenAI**, **Gemini**, or others supported by LangChain), add the corresponding keys.  

The chatbot won’t run without valid API keys.  

---

## ▶️ Running the Project

### 🔹 CLI Mode (original)
```bash
python main.py
```

### 🔹 Chat UI Mode (new)
Run with Chainlit:
```bash
chainlit run chat_ui.py -w
```
This will start a local web interface at [http://localhost:8000](http://localhost:8000).  

---

## 🖼 Chat UI Preview

Here’s a screenshot of the new Chainlit-based chat interface:  


![Chat UI Preview](https://raw.githubusercontent.com/zaharamirzaei/FoodChat-AI/main/assets/chainlit2.png)


---

## 🔍 How It Works

1. The user sends a query.  
2. `module_identifier.py` analyzes the query and decides which module should handle it.  
3. The chosen module (`food_info`, `food_services`, or `food_suggestion`) processes the request.  
4. The result is passed back to the main agent (or UI) and returned to the user.  

---

## 🚀 Technologies Used

- **Python 3.10+**
- **LangChain / LangGraph**
- **Chainlit** (for chat UI)
- **LLM APIs** (e.g., Gemini 1.5 Flash, GPT models)
- **SQLite** (for simple DB management)

---

## 📌 Notes

- No model fine-tuning is required.  
- The project focuses on **modular chatbot architecture** and **agent-based reasoning**.  
- Food data is partially sourced from `The New Complete Book of Foods.pdf`.  

---

## 📜 License

This project is for **educational purposes only**.  
Feel free to fork and experiment with it.  
