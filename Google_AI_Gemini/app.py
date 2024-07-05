import streamlit as st
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import os
from api_key import api_key
import google.generativeai as genai


load_dotenv()
api_key = os.getenv('api_key')
# Configure Generative AI API
genai.configure(api_key=api_key)

# Function to fetch schema names from MySQL server
def get_schema_names():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='California@12',
            database='information_schema'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata")
        schemas = cursor.fetchall()
        cursor.close()
        conn.close()
        return [schema[0] for schema in schemas]
    except mysql.connector.Error as err:
        st.error(f"Error fetching schema names: {err}")

# Function to fetch table names for a given schema from MySQL server
def get_table_names(schema):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='California@12',
            database='information_schema'
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}'")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return [table[0] for table in tables]
    except mysql.connector.Error as err:
        st.error(f"Error fetching table names: {err}")

# Function to fetch column names for a given schema and table from MySQL server
def get_column_names(schema, table):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='California@12',
            database='information_schema'
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'")
        columns = cursor.fetchall()
        cursor.close()
        conn.close()
        return [column[0] for column in columns]
    except mysql.connector.Error as err:
        st.error(f"Error fetching column names: {err}")

# Generation configuration settings
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize Generative Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Function to generate SQL query using Google Gemini API
def generate_sql_query(natural_language_query, schema, table):
    full_query = f"USE {schema}; SELECT * FROM {table} WHERE {natural_language_query}"
    
    chat_session = model.start_chat(
        history=[
            {"role": "user", "parts": [full_query]},
        ]
    )
    response = chat_session.send_message("Generate an SQL query for the above request.")
    return response.text

# Function to clean the SQL query
def clean_sql_query(sql_query):
    return sql_query.replace('```sql', '').replace('```', '').strip()

# Function to execute the SQL query on the MySQL database
def execute_sql_query(sql_query):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='California@12',
            database='class'
        )
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        cursor.close()
        conn.close()
        return pd.DataFrame(rows, columns=column_names)
    except mysql.connector.Error as err:
        return str(err)

# Streamlit app configuration
st.set_page_config(page_title="SQL Query Generator", page_icon="🔍")
st.title("SQL Query Generator")

# Sidebar section for schema and table selection
st.sidebar.subheader("Database Configuration")

# Fetch and display schema names in dropdown
schema_names = get_schema_names()
selected_schema = st.sidebar.selectbox("Select Schema", schema_names)

# Fetch and display table names in dropdown based on selected schema
if selected_schema:
    table_names = get_table_names(selected_schema)
    selected_table = st.sidebar.selectbox("Select Table", table_names)

    # Fetch and display column names in dropdown based on selected schema and table
    if selected_table:
        column_names = get_column_names(selected_schema, selected_table)
        selected_columns = st.sidebar.multiselect("Select Columns", column_names, default=column_names)

st.sidebar.markdown("---")

# Display schema and table information
if selected_schema and selected_table:
    st.write(f"Selected Schema: {selected_schema}")
    st.write(f"Selected Table: {selected_table}")
    if selected_columns:
        st.write(f"Selected Columns: {selected_columns}")

st.subheader("Enter a natural language query to generate and execute an SQL query")

# Input text for the query
user_input = st.text_area("Enter your query:", "")

# Button to generate the SQL query
generate_button = st.button("Generate and Execute Query")

if generate_button and user_input and selected_schema and selected_table:
    # Generate the SQL query, passing schema and table
    sql_query = generate_sql_query(user_input, selected_schema, selected_table)
    
    st.write("Generated SQL Query:")
    st.code(sql_query)
    
    # Clean the SQL query
    cleaned_sql_query = clean_sql_query(sql_query)
    
    st.write("Cleaned SQL Query:")
    st.code(cleaned_sql_query)
    
    # Execute the SQL query
    query_results = execute_sql_query(cleaned_sql_query)
    
    st.write("Query Results:")
    if isinstance(query_results, pd.DataFrame):
        st.dataframe(query_results)
    else:
        st.write(query_results)
elif generate_button:
    st.write("Please enter a query and make sure to select both schema and table.")
