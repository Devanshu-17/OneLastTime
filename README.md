# OneLastTime
Team OneLastTime project for the KLEOS 2.0 2024 hackathon

<p align="center">
  <br />
  <a href="https://github.com/Devanshu-17/OneLastTime/blob/main/frontend/README.md"><b>Checkout the Demo here »</b></a>
  <br />
  <br />
</p>

## Problem Statement:

<img width="793" alt="New Screen Shot Name 2024-06-22 at 3 52 16 AM" src="https://github.com/Devanshu-17/OneLastTime/assets/93381397/902587fd-c7ee-4b2d-ace9-066aedee7670">

## Tentative System Architecture:

<img width="1229" alt="New Screen Shot Name 2024-06-23 at 8 15 23 AM" src="https://github.com/Devanshu-17/OneLastTime/assets/93381397/797878ea-4307-4447-af85-80054152f958">

<br />

* The User first sends a query to the LLM.
* The LLM takes the user's query and checks it against the vector database (Qdrant) - This database will contain verified and trusted health information
* If the data is present in database, then send the response back to the user.
* If the data is not present, then using AI Agent, we will do a web search on the user's query (we will use CrewAI and SerperAPI).
* This web scraped data will be then sent to a panel of Medical experts, who will verify the data.
* This result will also be shown to the user, with a warning saying

    > :warning: **This data was taken from the web with these sources [....]**: Please wait for our Medical experts to verify the data.

* When the Medical experts verify the data, the user will be informed.
* In case, the results from the web is wrong, the the Medical Expert can send their own trusted opinion to the user.
* This final trusted and verified source will also be added to the vector database, making an ever growing set of perfect data. 🤗

## Tasks:

### PART 1: Backend Pipeline

* [x] Create a Notebook in which we will experiment AI Agents
* [x] Create a AI Agent for searching the web and summarising the scraped results
* [x] Test different prompts to verify which gives the best results
* [x] Create a Notebook to push the dataset into the database (Qdrant)
* [x] Check the threshold and FAITHFUL score of the database to ensure that the LLM can retrieve the data correctly (RAG)

### PART 2: Backend

* [x] Integrate the various pipeline into a single backend file (We will use FastAPI)
* [x] Create a MongoDB database for storing logs and Medical Expert's details.
* [x] Develop the workflow for connecting the API calls between the Medical Experts, the LLM and the users.

* [x] Email Notification Service 

### PART 3: Frontend

* [x] Create a demo frontend to show working of backend.
* [x] Create a landing page.
* [x] Create a Chat Page for user to interact with.
* [x] Create a Medical Expert page where they can validate and verify the user's query.

## Sources:

* Dataset Used: https://www.huggingface.co/datasets/lavita/ChatDoctor-HealthCareMagic-100k?row=36
* CrewAI: https://docs.crewai.com/
* Serper API: https://www.serper.dev
* Qdrant: https://cloud.qdrant.io
* https://arxiv.org/html/2402.04620v1
* https://www.analyticsvidhya.com/blog/2024/06/agentic-workflow-with-crewai-and-groq/
