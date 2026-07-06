from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0
)

llm2 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY_2,
    temperature=0
)

llms = [llm,llm2]

def call_llm(prompt: str) -> str:
    response = None
    
    for i,llm in enumerate(llms):
        try:
            response = llm.invoke(prompt)
        except Exception as e:
            print(f" llm{i+1} failed.. trying llm{i+2}..")
            continue
        else:
            break
          
    if isinstance(response.content, str):
        return response.content.strip()

    return str(response.content).strip()