# NexusData AI Studio 🚀

NexusData AI is a smart analytics dashboard that lets you "talk" to your Excel data. Instead of writing complex formulas, you simply upload a file and ask questions in plain English to get instant charts ,pandas code and summaries.

---

## ✨ Key Features
- **AI-Powered Analytics:** Uses Llama 3.3 to turn your questions into data insights.
- **Instant Visualization:** Automatically generates Bar, Line, or Pie charts.
- **Secure & Private:** Your data is processed in real-time and never stored permanently.
- **Premium Design:** A modern, tech-focused "Glassmorphism" interface.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Cloud / Infrastructure** | Render (Deployment), GitHub (CI/CD) |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI / ML** | LangChain, Groq Cloud (Llama 3.3 70B), ChatGroq |
| **Data Processing** | Pandas, Openpyxl, NumPy |
| **Security** | OAuth2, JWT (Jose), Passlib |
| **Frontend** | Vanilla JS, TailwindCSS, Chart.js |

---

## 🚀 How to Run It Locally

### 1. Clone & Install
```bash
git clone [https://github.com/yourusername/nexusdata-ai.git](https://github.com/yourusername/nexusdata-ai.git)
cd nexusdata-ai
pip install -r requirements.txt
```
###2. Environment Configuration
Create a .env file in the root directory and add your keys:

Code snippet
```bash
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=supabase_url
SUPABASE_ANON_KEY=your_super_secret_anon_key
```
###3. Install Dependencies
```Bash
pip install -r requirements.txt
```
###4. Start the Microservices
Open two terminals and run the following:

Terminal 1 (Auth Service):

```Bash
uvicorn auth_service.main:app --port 8001 --reload
```
Terminal 2 (Compute Engine):
```Bash
uvicorn compute_service.main:app --port 8002 --reload
```
