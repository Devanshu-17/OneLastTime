import email
from math import e
import re
from urllib import response
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import numpy as np
from fastapi.responses import FileResponse
import pandas as pd
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding # type: ignore
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate # type: ignore
from langchain_core.output_parsers import StrOutputParser # type: ignore
from langchain_core.runnables.passthrough import RunnablePassthrough # type: ignore
from langchain_groq import ChatGroq # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient # type: ignore
import time
import os
import uuid
from bson import ObjectId

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# AI Agent imports
from crewai import Agent, Task, Crew # type: ignore
from crewai_tools.tools import SerperDevTool # type: ignore

app = FastAPI()

# Setup CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "http://localhost:3000",
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

# MongoDB settings
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "OneLastTimeDB"

# Create MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]

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
    
    def get_embedding(self, text):
        embedding = list(self.encoder.embed(text))[0]
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

class StatusUpdateRequest(BaseModel):
    id: str
    status: str
    response: str = None

class SaveToQdrantRequest(BaseModel):
    question: str
    response: str
    email: str = None

class SaveFeedbackRequest(BaseModel):
    question: str
    feedback: str

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
        final_result_web = result+"**Information found on the web."
        print("Final Result:", final_result_web)
        context = final_result_web if final_result_web else "No relevant information found on the web."

        # Save query and result to MongoDB
        await db.user_queries.insert_one({
            "question": question,
            "response": context,
            "timestamp": time.time(),
            "status": "pending"
        })

        return {"response": final_result_web}
    
    else:

        prompt_template = """Answer the question using the given context. If no relevant context is available, please respond accordingly. If the context contains the word '**Information found on the web.**', it means the information was retrieved from the web.
            So remember to mention that in your response and don't remove it.

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

@app.post("/save_to_qdrant")
async def save_to_qdrant(request: SaveToQdrantRequest):
    question = request.question
    response = request.response
    
    data = question + response
    data_embedding = vector_db.get_embedding(data)
    
    point = models.PointStruct(
        id=str(uuid.uuid4()),
        payload={
            "question": question,
            "response": response,
            "email": request.email
        },
        vector=data_embedding.tolist()
    )
    
    try:
        result = vector_db.db_client.upload_points(
            collection_name=vector_db.db_collection_name,
            points=[point],
            parallel=4,
            max_retries=3
        )
        print("Data point uploaded successfully to Qdrant.")
        return {"message": "Data saved successfully to Qdrant."}
    except Exception as e:
        print(f"Error uploading data point to Qdrant: {e}")
        return HTTPException(status_code=500, detail="Failed to save data to Qdrant")

@app.post("/save_feedback")
async def save_feedback(request: SaveFeedbackRequest):
    question = request.question
    feedback = request.feedback

    data = question + feedback
    data_embedding = vector_db.get_embedding(data)

    point = models.PointStruct(
        id=str(uuid.uuid4()),
        payload={
            "question": question,
            "feedback": feedback
        },
        vector=data_embedding.tolist()
    )

    try:
        result = vector_db.db_client.upload_points(
            collection_name=vector_db.db_collection_name,
            points=[point],
            parallel=4,
            max_retries=3
        )
        print("Feedback uploaded successfully to Qdrant.")
        return {"message": "Feedback saved successfully to Qdrant."}
    except Exception as e:
        print(f"Error uploading feedback to Qdrant: {e}")
        return HTTPException(status_code=500, detail="Failed to save feedback to Qdrant")

@app.get("/get_queries")
async def get_queries():
    queries = await db.web_responses.find().to_list(1000)
    for query in queries:
        query["_id"] = str(query["_id"])
    return JSONResponse(content=queries)

@app.post("/update_status")
async def update_status(request: StatusUpdateRequest):
    query = await db.user_queries.find_one({"_id": ObjectId(request.id)})
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    # Fetch the response from the database before updating the status
    response = query.get("response", "No response available")  # Default to "No response available" if not found

    update_data = {"status": request.status}
    
    if request.status == "accepted":
        update_data["response"] = response  # Use the fetched response
    elif request.status == "rejected" and request.response:
        update_data["response"] = request.response

    await db.user_queries.update_one(
        {"_id": ObjectId(request.id)},
        {"$set": update_data}
    )

    if request.status in ["accepted", "rejected"]:
        if query.get("email"):
            # Send email to the user
            subject = "Your Medical Query Response"
            body = f"Dear User,\n\nYour medical query has been reviewed by a doctor. Here's the response:\n\nQuestion: {query['question']}\n\nAnswer: {update_data['response']}\n\nThank you for using our service!"
            send_email(query["email"], subject, body)

        if request.status == "accepted":
            # Save verified data to Qdrant
            save_to_qdrant_request = SaveToQdrantRequest(
                question=query["question"],
                response=update_data["response"],
                email=query.get("email", "")
            )
            await save_to_qdrant(save_to_qdrant_request)

    return {"message": "Status updated"}


# Add this new endpoint to your app.py file

@app.post("/save_query")
async def save_query(request: Request):
    data = await request.json()
    email = data.get('email')
    question = data.get('question')
    
    if not email or not question:
        raise HTTPException(status_code=400, detail="Email and question are required")

    # Retrieve the model response from the database
    model_response_doc = await db.user_queries.find_one({"question": question})
    model_response = model_response_doc["response"] if model_response_doc else "No response available"

    try:
        await db.user_queries.insert_one({
            "email": email,
            "question": question,
            "response": model_response,  # Use the retrieved model response
            "timestamp": time.time(),
            "status": "pending"
        })
        return {"message": "Query saved successfully"}
    except Exception as e:
        print(f"Error saving query to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to save query")

    
def send_email(recipient_email, subject, body):
    sender_email = "pytech.shop@gmail.com"  # Replace with your email
    password = "myvl litr gdnh dwyr"  # Replace with your email password or app-specific password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.get("/get_user_queries")
async def get_user_queries():
    queries = await db.user_queries.find().to_list(1000)
    for query in queries:
        query["_id"] = str(query["_id"])
    return JSONResponse(content=queries)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
