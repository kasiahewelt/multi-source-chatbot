import os

from langchain import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
hub_api = os.getenv("HUB_API")


db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}",
    engine_args={"pool_pre_ping": True},
)
llm = ChatOpenAI(temperature=0.00000001, openai_api_key=API_KEY, model_name='gpt-3.5-turbo-16k')
db_chain = SQLDatabaseChain.from_llm(llm, db, top_k=100, verbose=True)


def ask_db_agent(question):
    print("querying sql chain")
    print(question)
    sql_agent_prompt = """
    For any given input question, perform the following tasks:
    1. Construct a syntactically correct PostgreSQL query to address the question.
    2. Run the query and observe its results. Do not make up the results! If SQL query gives empty results - keep it empty!!
    3. Return the results in a clear and concise manner. Include all the examples from the SQLResult.
    4. Note that in SQL Database you have invoices, not the deals!!! 

    Question: {question}

    SQLQuery: SQL Query to run
    SQLResult: Result of the SQLQuery
    Answer: Result of the SQLQuery  
    """
    return db_chain.run(sql_agent_prompt.format(question=question))


# if __name__ == "__main__":
#     while True:
#         query = input("Enter your query (or type 'exit' to end): ")
#         if query.lower() == "exit":
#             break
#         response = ask_db_agent(query)
#         print("Agent:", response)
