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
os.environ["GROQ_API_KEY"] =os.environ.get("GROQ_API_KEY", "YOUR_KEY")
custom_client = httpx.Client(verify=False)
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, http_client=custom_client)

custom_client = httpx.Client(verify=False)
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0, 
    http_client=custom_client
)

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
