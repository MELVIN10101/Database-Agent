
---

## ⚙️ Technologies Used

- [Streamlit](https://streamlit.io) – for web UI
- [Pandas](https://pandas.pydata.org/) – for CSV processing
- [SQLite3](https://www.sqlite.org/index.html) – for database storage
- [LangChain](https://www.langchain.com/) – for agents, tools & LLM orchestration
- [Ollama](https://ollama.com) – for running local LLMs like `mistral`
- Python 3.10+

---

## 🔄 Workflow

### 1. **LLM Setup (Ollama)**
- Loads a local model like `mistral` via `OllamaLLM`.
- This model powers all language interpretation and SQL query generation.

---

### 2. **Load CSV into Pandas**
- Cybercrime data from `cybercrimedata.csv` is loaded into a DataFrame.
- Columns like `Records` are cleaned and converted to numeric.
- Basic shape info and stats are extracted.

---

### 3. **Register Custom Tools (Functions)**
Defined tools:
- `get_total_records_exposed()`
- `most_targeted_organization_type()`
- `records_exposed_by_year()`
- `breach_methods_count()`
- `get_incident_count_per_year()`
- `list_companies_by_org_type()`
- `most_common_breach_method()`

These tools are wrapped and exposed to the LLM using LangChain’s `@tool` decorator.

---

### 4. **Create SQL Database Agent**
- If the SQLite DB doesn't exist, it's created from the DataFrame.
- Connected using `SQLDatabase` and LangChain's SQL toolkit.
- A `ZERO_SHOT_REACT_DESCRIPTION` SQL agent is created to convert questions into SQL queries and return results.

---

### 5. **Create Pandas DataFrame Agent**
- A second agent is created that interacts directly with the Pandas DataFrame.
- Used for calculations, aggregations, and high-speed in-memory data queries.

---

### 6. **Function-Based Agent**
- A function agent using the decorated tools is created to answer analytical or statistical questions.

---

### 7. **Streamlit UI**
- Users can input a natural language question.
- Based on the intent:
  - If it's about totals, counts, or specific patterns → routed to `function_agent`.
  - Otherwise → routed to `sql_agent_executor`.
- All responses are shown in a real-time chat interface.
- Previous chat messages are stored in `st.session_state` for context.

---

### 8. **Loading Animation**
- While the query is being processed, a loading spinner is shown using `st.spinner()`.

---

## 🧪 Example Questions You Can Ask

- "What is the total number of records exposed?"
- "Which year had the most incidents?"
- "How many breaches happened in 2019?"
- "List companies under government organization type."
- "What is the most used breach method?"

---

## 🚀 Running the App

1. *Install dependencies*
```bash
pip install streamlit pandas langchain langchain-community langchain-experimental langchain-core

2. *Install Ollama*
```bash
ollama run mistral

3. *Start the Streamlit app*
```bash
    streamlit run app.py
