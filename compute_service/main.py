import os
import io
import re
import httpx
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from jose import jwt, JWTError


app = FastAPI(title="Stateless Compute Engine Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "SUPER_SECRET_PIZZA_KEY_CHANGE_THIS_IN_PRODUCTION"
ALGORITHM = "HS256"

# 🔑 OAuth2 Spec: Automatically scans arriving HTTP post packages for the 'Authorization: Bearer <token>' string header matrix
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/token")

def verify_oauth2_token(token: str = Depends(oauth2_scheme)):
    """OAuth2 Security Guard Dependency validating cryptographically signed sessions."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token parameters.")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid verification footprint.")

# --- GenAI Groq Data Science Execution Chain Configuration Engine ---
# TEMPORARY TEST: Hardcode the key to see if the 401 goes away
# --- GenAI Groq Data Science Execution Chain Configuration Engine ---

# 1. THE KEY: Paste your real key here. 
# Ensure it starts with 'gsk_' and has no extra spaces.
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. FIND THE PROJECT ROOT
# This looks for the directory containing your .env file
# Assuming your structure is: ai-project/.env and ai-project/compute_service/main.py
base_dir = Path(__file__).resolve().parent.parent 
env_path = base_dir / ".env"

# 2. LOAD IT WITH OVERRIDE
# 'override=True' ensures that if Windows cached an old key, the .env version wins
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Environment loaded from: {env_path}")
else:
    print("⚠️ Warning: .env file not found at the root. Falling back to system env.")

# 3. EXTRACT THE KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 4. INITIALIZE THE LLM
custom_client = httpx.Client(verify=False)
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY, 
    model_name="llama-3.3-70b-versatile", 
    temperature=0, 
    http_client=custom_client
)

if not GROQ_API_KEY:
    print("🔴 ERROR: GROQ_API_KEY is still missing. Check your .env file spelling!")
else:
    print("🟢 LLM initialized successfully from .env!")
# 🛠️ UPGRADED PROMPT TEMPLATE: Forces clean code formatting and prevents clipped strings
code_template = """You are an expert data scientist. You have a pandas DataFrame named 'df'.
DataFrame Schema (column types): {schema}
User Question: {question}

Task: Write a clean, valid Python script using pandas to answer the question.

STRICT INSTRUCTIONS:
1. Write ONLY raw Python code. Do NOT wrap your code in markdown code blocks like ```python.
2. Ensure all strings, brackets, and quotes are closed completely. Do not leave anything unfinished.
3. Your code MUST assign the final answer to a local variable named 'result'.
4. If the question involves numbers, charts, lists, or breakdowns, ensure 'result' is assigned to a DataFrame or a Series (e.g., result = df.groupby('size')['revenue'].sum()).

Write your executable Python code below:"""

code_prompt = PromptTemplate(template=code_template, input_variables=["schema", "question"])
code_chain = code_prompt | llm | StrOutputParser()
@app.post("/query")
async def process_data_query(
    question: str = Form(...), 
    file: UploadFile = File(...),
    current_user: str = Depends(verify_oauth2_token)
):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Spreadsheet structure mismatch.")
        
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        columns_schema = str(df.dtypes.to_dict())
        
        generated_code = code_chain.invoke({"schema": columns_schema, "question": question}).strip()
        generated_code = re.sub(r'^```python\s*|^```\s*', '', generated_code, flags=re.MULTILINE)
        generated_code = re.sub(r'\s*```$', '', generated_code, flags=re.MULTILINE).strip()
        
        local_vars = {'df': df, 'pd': pd}
        exec(generated_code, globals(), local_vars)
        
        raw_result = local_vars['result']
        is_table = isinstance(raw_result, (pd.DataFrame, pd.Series))
        
        # 📊 NEW: Smart Chart Classification Engine
        chart_type = "bar" # Default
        question_lower = question.lower()
        
        if any(w in question_lower for w in ["trend", "over time", "month", "date", "daily", "weekly"]):
            chart_type = "line"
        elif any(w in question_lower for w in ["percentage", "share", "proportion", "distribution", "pie"]):
            chart_type = "pie"
        
        if is_table:
            chart_df = raw_result.reset_index() if isinstance(raw_result, pd.Series) else raw_result.copy()
            serialized_data = chart_df.to_dict(orient="records")
            answer_text = chart_df.to_string(index=False)
        else:
            serialized_data = str(raw_result)
            answer_text = str(raw_result)
            
        return {
            "generated_code": generated_code,
            "is_chart_eligible": is_table and len(chart_df) > 1,
            "chart_type": chart_type,             # 🚀 Sends 'bar', 'line', or 'pie' to frontend
            "data": serialized_data,
            "answer_text": answer_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
