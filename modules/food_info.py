import os
import warnings
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
import lancedb
from llama_parse import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_tavily import TavilySearch
from langchain_community.vectorstores import LanceDB
from dotenv import load_dotenv

load_dotenv()

class RouteQuery(BaseModel):
    datasource: str = Field(..., description="vectorstore, web_search, neither")


class GradeDocuments(BaseModel):
    binary_score: str = Field(description="yes or no")


class GradeHallucinations(BaseModel):
    binary_score: str = Field(description="yes or no")


class GradeAnswer(BaseModel):
    binary_score: str = Field(description="yes or no")


def find_generation(output):
    if not isinstance(output, dict):
        return None
    for key, value in output.items():
        if key == "generation" and isinstance(value, str):
            return value
        elif isinstance(value, dict):
            result = find_generation(value)
            if result:
                return result
    return None


class FoodInfoModule:
    def __init__(self):
        warnings.filterwarnings("ignore", category=FutureWarning)

        LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
		
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

        self.load_data()

        self.web_search_tool = TavilySearch(k=3)

        self.build_router()

        self.build_graders_and_chain()

        self.build_graph()

    def load_data(self):
        self.db = lancedb.connect("lancedb_path")
        self.table_name = "food_knowledge_base"

        if self.table_name in self.db.table_names():
            self.table = self.db.open_table(self.table_name)
        else:
            parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"), result_type="markdown")
            docs = parser.load_data("./The New Complete Book of Foods.pdf")

            raw_text = "\n".join([d.text for d in docs]) if isinstance(docs, list) else docs.text
            doc = Document(page_content=raw_text)
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=200,
                chunk_overlap=25,
                separators=["\n\n", "\n", ".", " "],
            )
            self.doc_splits = text_splitter.split_documents([doc])

            texts = [chunk.page_content for chunk in self.doc_splits]
            embeddings = self.embedding.embed_documents(texts)

            self.table = self.db.create_table(
                self.table_name,
                data=[{"text": chunk.page_content, "vector": vec} for chunk, vec in zip(self.doc_splits, embeddings)]
            )

        self.vectorstore = LanceDB(connection=self.db, table=self.table, embedding=self.embedding)
        self.retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    def build_router(self):
        system = """You are an expert system that decides whether a user question should be answered using a local PDF-based vectorstore or a web search.


The local vectorstore contains information from a book titled 'The New Complete Book of Food' by Carol Ann Rinzler. This book includes:

- Nutritional profiles of individual foods (like apples, garlic, oats, etc.)
- Scientific findings about how foods affect health (e.g., cancer prevention, cholesterol control)
- How to store, prepare, cook, and use foods for maximum benefit
- Adverse effects or drug interactions of foods (e.g., grapefruit and medication)
- Food safety, food science, and dietary guidelines (including DRI, RDA, UL)
- Common myths and updated scientific facts about nutrition
- Use 'vectorstore' for questions about nutritional content, medicinal effects, food science, storage, preparation, or culinary properties that are likely to be found in the book "The New Complete Book of Foods".
Use the vectorstore for any question about a specific food or how to prepare, cook, or serve food, even if the question is about general cooking instructions.


If the question is about something **not found in the book** (like recent food trends, breaking news, or global food shortages), use web search.
Only answer questions **related to food, nutrition, or diet**. If the question is unrelated to food, return 'neither' as the route.

Return one of the following options:
- 'vectorstore'
- 'web_search'
- 'neither'
"""
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{question}"),
            ]
        )
        structured_llm_router = self.llm.with_structured_output(RouteQuery)
        self.question_router = route_prompt | structured_llm_router

    def build_graders_and_chain(self):
        
        system_template = system_template = """
Use the provided context to answer the user's question.
If the context contains partial information, provide it in a complete sentence.
If the context contains no relevant information, respond politely that the information is not available.
"""

        human_template = """
Context:
{context}

Question:
{question}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", human_template)
        ])
        self.rag_chain = prompt | self.llm | StrOutputParser()

    def build_graph(self):
        from typing_extensions import TypedDict

        class GraphState(TypedDict):
            question: str
            generation: str
            documents: List[str]

        self.GraphState = GraphState

        def retrieve(state):
            question = state["question"]
            documents = self.retriever.invoke(question)
            return {"documents": documents, "question": question}

        def generate(state):
            question = state["question"]
            documents = state["documents"]
            if isinstance(documents, list):
                context = "\n".join(d.page_content for d in documents)
            elif hasattr(documents, "page_content"):
                context = documents.page_content
            else:
                context = str(documents)
            generation = self.rag_chain.invoke({"context": context, "question": question})
            return {"documents": documents, "question": question, "generation": generation}

        def grade_documents(state):
            documents = state["documents"]
            return {"documents": documents, "question": state["question"]}

        def route_question(state):
            question = state["question"]
            source = self.question_router.invoke({"question": question})
            route = source.datasource
            print(route)
            if route == "web_search":
                return "web_search"
            elif route == "vectorstore":
                return "retrieve"
            else:
                return "irrelevant"

        def decide_to_generate(state):
            filtered_documents = state["documents"]
            if not filtered_documents:
                return "retrieve"
            else:
                return "generate"

        def handle_irrelevant_question(state):
            return {"generation": "Sorry, this question is not related to food."}

        self.workflow = StateGraph(self.GraphState)

        self.workflow.add_node("web_search", lambda state: {"documents": [], "question": state["question"]})  # simplified
        self.workflow.add_node("retrieve", retrieve)
        self.workflow.add_node("grade_documents", grade_documents)
        self.workflow.add_node("generate", generate)
        self.workflow.add_node("irrelevant", handle_irrelevant_question)

        self.workflow.add_conditional_edges(
            START,
            route_question,
            {
                "web_search": "web_search",
                "retrieve": "retrieve",
                "irrelevant": "irrelevant",
            },
        )
        self.workflow.add_edge("retrieve", "grade_documents")
        self.workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "retrieve": "retrieve",
                "generate": "generate",
            },
        )
        self.workflow.add_conditional_edges(
            "generate",
            lambda state: END,
            {
                END: END,
            },
        )

        self.app = self.workflow.compile()

        system = """You are a question re-writer that converts an input question to a better version optimized for vectorstore retrieval."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Here is the initial question: \n\n {question} \n Formulate an improved question."),
            ]
        )
        self.question_rewriter = re_write_prompt | self.llm | StrOutputParser()

    def answer_question(self, question: str) -> str:
        inputs = {"question": question}
        final_answer = None
        for output in self.app.stream(inputs):
            gen = find_generation(output)
            if gen:
                final_answer = gen
                break  
        return final_answer or "no answer found."


if __name__ == "__main__":
    module = FoodInfoModule()
    #llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    #print(llm("what is pasta?"))

    while True:
        q = input("ask your question about food: ")
        ans = module.answer_question(q)
        print(ans)
