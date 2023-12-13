import os
from salesforce_utils import execute_soql, execute_sosl
import openai
from dotenv import load_dotenv
from hubspot_agent import chat
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class SalesforceAgent:
    SYSTEM_PROMPT = """
        You are SalesforceAgent, an AI specialized in managing Salesforce CRM data. Within Salesforce terminology, 
        'Accounts' refer to Companies and 'Opportunities' refer to Deals.
        Remember, a 'Closed Won' opportunity means the company has made a purchase, and an open opportunity is one that 
        is not 'Closed Won' or 'Closed Lost'.
        """

    PROMPT_TEMPLATE = """
        To address your request efficiently, please follow the streamlined process below:
        1. Understand the issue at hand and outline the essential steps and functions necessary for an accurate solution, aiming for minimalism in both.
        2. Implement the solution meticulously, focusing only on execution without the need to detail the plan to the user.
        
        Guidelines:
        - Refrain from creating non-existent functionalities.
        - Notify if the expected output cannot be generated.
        - When predicting forecast revenue, consider only open Opportunities, excluding those with a 'Closed Won' and 'Closed Lost' status.
        - If I ask about activities related to the deals/ opportunities - check tasks, events, calls.
        
        Problem: {}
        """

    def __init__(self):
        self.available_functions = {
            "execute_sosl": execute_sosl,
            "execute_soql": execute_soql,
        }
        self.functions = [
            {
                "name": "execute_sosl",
                "description": "Executes a SOSL search with the given search string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "The SOSL search string to be executed."
                        }
                    },
                    "required": ["search"]
                },
            },

            {
                "name": "execute_soql",
                "description": "Executes a SOQL query with the given query string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SOQL query string to be executed."
                        }
                    },
                    "required": ["query"]
                },
            }

        ]
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    def chat(self, query):
        prompt = self.PROMPT_TEMPLATE.format(query)
        response, _ = chat(
            prompt,
            self.messages,
            self.available_functions,
            self.functions,
            agent_name="salesforce_agent",
        )
        return response


def ask_salesforce_agent(query):
    print("asking Salesforce Agent")
    return SalesforceAgent().chat(query)


# if __name__ == "__main__":
#     while True:
#         query = input("Enter your query (or type 'exit' to end): ")
#         if query.lower() == "exit":
#             break
#         response = ask_salesforce_agent(query)
#         print("Agent:", response)
