import os
import sqlite3
import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_ollama import OllamaLLM
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentExecutor
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.tools import tool
from langchain_core.tools import tool


st.set_page_config(page_title="Cybercrime Chatbot", layout="centered")

st.markdown("<h1 style='text-align: center; color: #00bfff;'>Cybercrime AI Assistant</h1>", unsafe_allow_html=True)
st.markdown("wait I'm loading the data...")

llm = OllamaLLM(model = "mistral")

df = pd.read_csv("cybercrimedata.csv",encoding="ISO-8859-1").fillna(value=0)
df['Records'] = df['Records'].astype(str).str.replace(',', '')
df['Records'] = pd.to_numeric(df['Records'], errors='coerce')
shape = df.shape

@tool
def get_total_records_exposed(input: str) -> str:
    """Returns the total number of records exposed in all years."""
    total = df['Records'].sum()
    return f"Total records exposed: {int(total)}"

@tool
def most_targeted_organization_type(input : str) -> str:
    """Returns the organization type with the highest number of breaches."""
    org_type = df['Organization_type'].value_counts().idxmax()
    count = df['Organization_type'].value_counts().max()
    return f"Most targeted organization type: {org_type} with {count} incidents"

@tool
def records_exposed_by_year(year: int) -> str:
    """Returns the number of records exposed in a given year."""
    total = df[df['Year'] == year]['Records'].sum()
    return f"Records exposed in {year}: {int(total)}"

@tool
def breach_methods_count(input: str) -> str:
    """Returns the number of times each breach method was used."""
    methods = df['Method'].value_counts()
    return methods.to_string()

@tool
def get_incident_count_per_year(year: int) -> str:
    """Returns the number of breach incidents reported each year."""
    counts = df['Year'].value_counts().sort_index()
    return counts.to_string()

@tool
def list_companies_by_org_type(org_type: str) -> str:
    """Lists companies targeted under a specific organization type."""
    companies = df[df['Organization_type'].str.lower() == org_type.lower()]['Company'].unique()
    return '\n'.join(companies[:20]) if len(companies) > 0 else "No companies found for this organization type."

@tool
def most_common_breach_method(input: str) -> str:
    """Returns the most frequently used breach method."""
    method = df['Method'].value_counts().idxmax()
    count = df['Method'].value_counts().max()
    return f"The most common breach method is '{method}' used {count} times."

tools = [
    get_total_records_exposed,
    most_targeted_organization_type,
    records_exposed_by_year,
    breach_methods_count,
    get_incident_count_per_year,
    list_companies_by_org_type,
    most_common_breach_method

]

# print("Dataframe shape:", df.shape)
# print("Columns:", df.columns.tolist())
# print("Total records:", len(df[df['Organization_type'] == 'Web']))
# print("Sum of 'Records':", df[df['Organization_type'] == 'Web']['Records'].sum())

agent = create_pandas_dataframe_agent(
    llm = llm,
    df = df,
    verbose = True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    allow_dangerous_code=True,
    max_execution_time=60,
    max_iterations=3,
)
agent_executor = AgentExecutor(
    agent=agent.agent,
    tools=agent.tools,
    handle_parsing_errors=True,
    )

agent_response = agent_executor.invoke({
    "input": "total number of rows and columns {shape}", 
    "return_intermediate_steps": True
})

# print(agent_response)


#creating a sqlite database
db_file = 'cybercrime_data.db'
if not os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    df.to_sql('cybercrime_data', conn , if_exists = 'replace' , index = False)
    conn.commit()
    print("Database created and data inserted successfully.")
else:
    conn = sqlite3.connect(db_file)
    conn.commit()
    print("Database already exists.")
    print({db_file: "Database already exists."})

db = SQLDatabase.from_uri(f"sqlite:///{db_file}") #connecting sqlite to langchain


toolkit = SQLDatabaseToolkit(db=db, llm=llm)

prefix = """You are a helpful assistant working with a cybersecurity incidents database."""
prefix = """You are a helpful assistant working with a cybersecurity incidents database.
You will be given questions in natural language and need to convert them into correct SQL queries.
Return the final answers based on query results."""

suffix = """
Begin!

Question: {input}
{agent_scratchpad}
"""



sql_agent =  create_sql_agent(
    llm = llm,
    database = db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    allow_dangerous_code=True,
    max_execution_time=60,
    max_iterations=3,
    prefix=prefix,
    suffix=suffix,
    toolkit=toolkit,
)

sql_agent_executor = AgentExecutor(
    agent=sql_agent.agent,
    tools=sql_agent.tools,
    handle_parsing_errors=True,
    verbose=True, #remove this if you want to disable verbose output and only see the final answer
    max_execution_time=60,
    max_iterations=3,
    return_intermediate_steps=True,
)

# response = sql_agent_executor.invoke({
#     "input": "Which year had the highest number of incidents?",
#     "return_intermediate_steps": True
# })
# print(response)


# Initialize the function agent with the tools and LLM
function_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    max_execution_time=60,
    max_iterations=3,
    handle_parsing_errors=True,
)

# query = "what is the most targeted record type?"
# response = function_agent.run(query)
# print(response)


st.title("Database-Agent with Cybercrime Dataset]")
st.markdown("Ask me anything about cyber attacks, breach stats, methods, or trends.")
chat_history = st.session_state.get("chat_history", [])
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Your Question:", key="user_input")

if st.button("Ask"):
    if user_input.strip() == "":
        st.warning("Please enter a valid question.")
    else:
        with st.spinner("Analyzing and querying the database..."):
            try:
                if "how many" in user_input or "total" in user_input or "records" in user_input:
                    response = function_agent.run(user_input)
                else:
                    response = sql_agent_executor.invoke({"input": user_input})
            except Exception as e:
                response = f"Error: {str(e)}"
            
            chat_history.append({"user": user_input, "bot": response})
            st.session_state.chat_history = chat_history


for speaker, message in chat_history[::-1]:
    st.markdown(f"**{speaker}:** {message}")

