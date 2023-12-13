import os
import logging

import openai

from salesforce_agent import ask_salesforce_agent
from hubspot_agent import ask_hubspot_agent, chat
from db_agent import ask_db_agent


from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

SYSTEM_PROMPT = """
        You are the sales assistant orchestrator. Use HubSpot, SQL database and Salesforce for insights on 'companies' 
        or 'customers'. 
        Hubspot agent: 'Company' in HubSpot = 'customer'. A "closed won" deal in HubSpot is a finalized deal. Provide 
        company details when asked.
        SQL agent: Fetches data from SQL where 'companies' have been invoiced. Equate SQL 'companies' to Hubspot 
        'customers'. Provide company details when asked.
        Salesforce agent: 'Accounts' in Salesforce refer to Companies and 'Opportunities' refer to Deals.
        
        ***NOTE: HubSpot, SQL and Salesforce have different identifiers. Always cross-reference and combine data from 
        all the sources for answers.***
        
        Operations:
        1. For companies with past purchases and new sales opportunities, match "closed won" deals in HubSpot and 
        Salesforce with  invoiced companies in SQL. Check HubSpot and Salesforce for new deals/ opportunities.
        2. For companies with past purchases but no new opportunities, match "closed won" deals in HubSpot and 
        Salesforce with invoiced companies in SQL. 
        3. To list customers, show unique companies from SQL, HubSpot and Salesforce combined together.
        4. ***For customer count -  count all the unique companies/ accounts, tally unique companies from the sources***
        5. For revenue calculations, consider SQL invoice amounts/dates and HubSpot's "closed won" deal amounts/dates 
        and Salesforce "closed won" opportunities. 
        6. For "list my deals", provide all deals from both HubSpot and Salesforce plus invoices from SQL.
        7. For successful deals, match "closed won" deals in HubSpot and Salesforce with invoiced companies in SQL.
        8. When querying revenue or details from a specific criterion (e.g., country, product type): 
           a. Check the SQL database for relevant data - e.g. invoices' amount.
           b. Check HubSpot - prices of the deals.
           c. Check Salesforce - prices of the opportunities.
           d. Provide a combined answer

        ''' USE THE DATA FROM THE SOURCES, DO NOT MAKE UP THE DEALS/ CUSTOMERS/ MAILS - NOTHING!'''
        ''' DO NOT GENERATE CODE, NO TYPESCRIPT, NOTHING!!!! '''
        
        Guidelines:
        - Don't invent functionalities.
        - Report if there's no output.
        - When the user asks about customers - count unique companies from database, Hubspot and Salesforce- check 
        unique companies from all sources.
        - Execute after planning. DO NOT PROVIDE THE PLAN HOW TO SOLVE THE PROBLEM!!
        - ALWAYS COMBINE DATA FROM ALL THE SOURCES.
        - *** Company representative in database is the same as CONTACT from Hubspot and CONTACT from Salesforce*** 
        - WHILE PERFORMING MATH - BE CAREFUL! Better just leave the amounts without performing math!
        - If I ask - count my customers - count unique COMPANIES from all the sources!
        - To calculate the forecast revenue - check open deals (all the deals besides closed won or closed lost deals) 
        and sum the prices.
        - To count my customers check companies in database, salesforce and hubspot - list them all, do not repeat, 
        take unique companies from all the sources.
        - To list deal owners, match them with deals from Hubspot and Salesforce
        - Never give me deal owner ID - just full name
        - While giving me product info - do not perform math, just read the amount from the Hubspot API. 
    """


functions = [
    {
        "name": "ask_hubspot_agent",
        "description": "Ask Hubspot agent",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "query related to Hubspot"
                }
            },
            "required": [],
        }
    },
    {
        "name": "ask_db_agent",
        "description": "Ask SQL database agent",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "question about data stored in database e.g. give me invoice related to XYZ"
                }
            },
            "required": [],
        }
    },
    {
        "name": "ask_salesforce_agent",
        "description": "Ask Salesforce agent",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "question about data stored in Salesforce"
                }
            },
            "required": [],
        }
    },
]

available_functions = {
    "ask_hubspot_agent": ask_hubspot_agent,
    "ask_db_agent": ask_db_agent,
    "ask_salesforce_agent": ask_salesforce_agent,
}

PROMPT_TEMPLATE = """
    To address the query:
        1. Understand the core of the problem.
        2. Create a plan with minimal steps and function calls for accuracy.
        3. Present the plan.
        4. Check database, Salesforce and Hubspot, remember that sometimes the data in the sources is not overlapping. 
        5. Execute and resolve.
    Problem: {}

"""


def get_response(query, messages):
    prompt = PROMPT_TEMPLATE.format(query)
    response, token_nums = chat(prompt, messages, available_functions, functions, agent_name="orchestrator")
    return response, token_nums


# if __name__ == "__main__":
#     messages = [{"role": "system", "content": SYSTEM_PROMPT}]
#     while True:
#         query = input("Enter your query (or type 'exit' to end): ")
#         if query.lower() == 'exit':
#             break
#         response = get_response(query, messages)
#         print("Agent:", response)
