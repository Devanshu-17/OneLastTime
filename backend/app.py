from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import numpy as np
import pandas as pd
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_groq import ChatGroq
import time
import os

# AI Agent imports
from crewai import Agent, Task, Crew
from crewai_tools.tools import SerperDevTool

app = FastAPI()

# Setup CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500"  # If you are using Live Server in VSCode
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the frontend directory
frontend_directory = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Serve static files
app.mount("/static", StaticFiles(directory=frontend_directory), name="static")

qdrant_uri = "https://14ea86c5-419c-41e5-b82b-18eec7c016e2.us-east4-0.gcp.cloud.qdrant.io:6333"
qdrant_api = "cfhdTR3705TH3iU78F6WY6dQGmjWuO2ofiLzuyr4LR3bF8zf4VZ_Rw"
groq_key = "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"

llm = ChatGroq(groq_api_key=groq_key,
               model='mixtral-8x7b-32768',
               temperature=0.2)  # set temperature by your own

threshold = 0.87

class QdrantVectorStore:
    def __init__(self, qdrant_uri, qdrant_api, threshold):
        self.encoder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.client = QdrantClient()
        self.db_collection_name = "ChatDoctor"
        
        self.db_client = QdrantClient(
            qdrant_uri,
            api_key=qdrant_api
        )
        
        self.euclidean_threshold = threshold
    
    def get_embedding(self, question):
        embedding = list(self.encoder.embed(question))[0]
        return embedding
    
    def query_database(self, query_text):
        result = self.db_client.query(
            query_text=query_text,
            limit=3,
            collection_name=self.db_collection_name
        )
        return result
    
    def query(self, question):
        start_time = time.time()
        
        db_results = self.query_database(question)
        
        if db_results and db_results[0].score > self.euclidean_threshold:
            response_text = db_results[0].document
            print("Response Text from Database", response_text)
            print('Retrieval without cache.')
            elapsed_time = time.time() - start_time
            print(f"Time taken: {elapsed_time:.3f} seconds")
            return response_text
        else:
            print("No answer found in Database")
            elapsed_time = time.time() - start_time
            print(f"Time taken: {elapsed_time:.3f} seconds")
            return "No answer available"

vector_db = QdrantVectorStore(qdrant_uri, qdrant_api, threshold)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_directory, 'index.html'))

@app.post("/query")
async def chat_query(request: QueryRequest):
    question = request.question
    context = vector_db.query(question)
    print("Context from Database", context)
   
    if context == "No answer available":
        # Use the AI agent to search the web for information
        os.environ['SERPER_API_KEY'] = "9e197ad3ca682f2775833b0f274a1f66a6b563e7"
        os.environ['GROQ_API_KEY'] = groq_key

        search_tool = SerperDevTool(n_results=5)
        
        researcher = Agent(
            role="Researcher",
            goal='Find accurate and up-to-date medical information from reputable sources to assist users with their health-related queries, based on this user query: {subject_area}. Also Provide concise and accurate summaries of collected medical information.',
            backstory=(
                "As a dedicated health information searcher, your primary mission is to "
                "scour the web for reliable and precise medical information. With a keen eye for credible sources "
                "and a passion for accuracy, you aim to provide the most relevant data to help users make informed health decisions, along with potential treatment options and medications that may be suitable for their condition."
                "Apart from that, you have a detail-oriented summarizer with a talent for condensing complex medical information "
                "into clear and accessible summaries. Your work ensures that users receive accurate and understandable information."
            ),
            llm=llm,
            max_iter=3,
            tools=[search_tool],
            allow_delegation=True,
            verbose=True
        )

        research_task = Task(
            description=(
                "Find accurate and up-to-date medical information from reputable sources to assist users with their health-related queries, based on this user query: {subject_area}"
                "Set the input parameter as: search_query'"
            ),
            expected_output='A brief summary of the latest advancements in {subject_area}.',
            tools=[search_tool],
            agent=researcher
        )

        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            max_rpm=3,
            cache=False
        )

        # Kickoff the research task
        result = crew.kickoff(inputs={'subject_area': question})
        print("##################")
        print(result)
        print("##################")
        context = result if result else "No relevant information found on the web."

    prompt_template = """Answer the question using the given context. If no relevant context is available, please respond accordingly.

Context: {context}

Question: {question}"""
    prompt = PromptTemplate.from_template(prompt_template)

    chain = prompt | llm | StrOutputParser()

    # Verbose logging
    prompt_input = {"question": question, "context": context}
    print("Prompt Input:", prompt_input)
   
    final_result = chain.invoke(prompt_input)
    print("Final Result:", final_result)
    
    return {"response": final_result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
