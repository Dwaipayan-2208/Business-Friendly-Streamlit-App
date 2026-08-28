import os
from pathlib import Path
import mysql.connector
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Search and load .env from root OR subfolder automatically
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "Business friendly Streamlit app" / ".env"
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

# Helper function to read from st.secrets (Cloud) or .env (Local)
def get_secret(key_name, default=None):
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, default)

# 1. Page Configuration
st.set_page_config(page_title="Academic Performance AI Agent", page_icon="📊", layout="wide")

# Database Schema Definition
SCHEMA = """The schema of the database is as follows:
TABLE_NAME  COLUMN_NAME DATA_TYPE   COLUMN_TYPE
bridge      ID          int         int
bridge      FullName    text        text
bridge      Sex         text        text
bridge      Class       text        text
chess       ID          int         int
chess       FullName    text        text
chess       Sex         text        text
chess       Class       text        text
music       ID          int         int
music       Type        text        text
student     ID          int         int
student     FullName    varchar     varchar(100)
student     DOB         varchar     varchar(20)
student     Sex         varchar     varchar(10)
student     Class       varchar     varchar(10)
student     HCode       varchar     varchar(10)
student     DCode       varchar     varchar(10)
student     Remission   binary      binary(1)
student     MTest       int         int
student     PTest       int         int
"""

# Initialize Session State for Question History
if "history" not in st.session_state:
    st.session_state.history = []

# 2. NVIDIA API Client Helper (st.secrets)
def get_nvidia_client():
    api_key = get_secret("NVIDIA_API_KEY")
    if not api_key:
        st.error("NVIDIA_API_KEY is missing!")
        st.stop()
    return OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")

# 3. Clever Cloud MySQL Connection Helper (st.secrets)
def connect_to_sql():
    return mysql.connector.connect(
        host=get_secret("MYSQL_HOST", os.getenv("MYSQL_HOST")),
        port=int(get_secret("MYSQL_PORT", os.getenv("MYSQL_PORT", 3306))),
        user=get_secret("MYSQL_USER", os.getenv("MYSQL_USER")),
        password=get_secret("MYSQL_PASSWORD", os.getenv("MYSQL_PASSWORD")),
        database=get_secret("MYSQL_DATABASE", os.getenv("MYSQL_DATABASE"))
    )

# 4. Generate SQL from English
def generate_sql_query(user_question):
    client = get_nvidia_client()
    prompt = (
        f"Given the following database schema:\n{SCHEMA}\n"
        f"Convert this question into a SQL query. Return ONLY the raw SQL query without explanations or markdown formatting:\n{user_question}"
    )
    response = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
    )
    sql = response.choices[0].message.content.strip()
    return sql.replace("```sql", "").replace("```", "").strip()

# 5. UI Layout Setup
with st.sidebar:
    st.title("🏫 Admin Control Panel")
    st.info("Target User: School Administrators & Teachers")
    st.markdown("Use this agent to analyze student performance across sports and academics.")

st.title("📊 Student Performance & Data Analytics Agent")
col1, col2, col3 = st.columns(3)
col1.metric("Total Students", "18")
col2.metric("Avg Math Score (MTest)", "86.5")
col3.metric("Avg Physics Score (PTest)", "84.1")

st.divider()

tab1, tab2 = st.tabs(["🤖 Natural Language Query", "📋 Schema & Guidelines"])

with tab1:
    st.subheader("Ask a Personal Question")
    
    # Pure text input without any dropdowns or preset questions
    user_question = st.text_input("Enter your question:", placeholder="Type your personal question here...")
    
    if st.button("Run Analysis", type="primary"):
        if user_question.strip():
            with st.spinner("Translating question to SQL..."):
                try:
                    # Generate SQL query
                    sql_query = generate_sql_query(user_question)
                    
                    st.divider()
                    st.subheader("Generated SQL Query")
                    st.code(sql_query, language="sql")

                    # Execute query against Clever Cloud MySQL
                    with st.spinner("Connecting to Clever Cloud database..."):
                        conn = connect_to_sql()
                        df = pd.read_sql_query(sql_query, conn)
                        conn.close()

                        for col in df.columns:
                            df[col] = df[col].apply(lambda x: "BLOB" if isinstance(x, (bytes, bytearray)) else x)

                    st.subheader("Database Results")
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Query executed successfully, but returned no matching records.")

                except Exception as e:
                    st.error(f"Error executing query: {e}")
        else:
            st.warning("Please type a question into the text box first.")

with tab2:
    with st.expander("Click to view database schema details", expanded=True):
        st.code(SCHEMA, language="text")
