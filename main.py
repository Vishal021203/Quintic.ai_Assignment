import sqlite3
import pandas as pd
import requests
import json

DATABASE_NAME = "students.db"
EXCEL_FILE = "students.xlsx"
OLLAMA_API_URL = "http://172.25.60.20:11434/api/generate"
OLLAMA_MODEL = "llama3"  # You can change based on availability

def load_excel_to_db():
    print("[INFO] Loading Excel data into SQLite database...")
    df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
    conn = sqlite3.connect(DATABASE_NAME)
    df.to_sql('students', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    print("[INFO] Data loaded successfully!")

def call_llm_to_get_sql(natural_query):
    prompt = f"""
    You are an assistant that converts natural language questions into SQL queries.
    The SQLite table is named 'students' with these columns:
    - Name (TEXT)
    - CGPA (REAL)
    - Location (TEXT)
    - Email (TEXT)
    - Phone_Number (TEXT)
    - Preferred_Work_Location (TEXT)
    - Specialization_in_degree (TEXT)

    Convert the following user question into an SQL SELECT query only (no explanation):

    "{natural_query}"
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        generated_text = data.get("response", "").strip()
        # Basic cleanup: remove any explanations or comments accidentally generated
        generated_text = generated_text.split(';')[0] + ';'
        return generated_text
    else:
        print("[ERROR] Failed to get response from LLM:", response.text)
        return None

def execute_sql(sql):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        # Fetch column names for better output formatting
        column_names = [description[0] for description in cursor.description]
        conn.close()
        return column_names, rows
    except Exception as e:
        conn.close()
        print("[ERROR] SQL execution failed:", e)
        return [], []

def chat():
    print("\n📚 Student Query Chat Interface")
    print("Type your query in natural language (or type 'exit' to quit):\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        sql = call_llm_to_get_sql(user_input)
        if sql:
            print(f"\n[Generated SQL]: {sql}\n")
            columns, results = execute_sql(sql)
            if results:
                print("-" * 50)
                print(" | ".join(columns))
                print("-" * 50)
                for row in results:
                    print(" | ".join(str(item) for item in row))
                print("-" * 50)
            else:
                print("[INFO] No results found or error in query execution.")
        else:
            print("[INFO] Could not generate SQL from your input.")

if __name__ == "__main__":
    load_excel_to_db()
    chat()
