import json
import logging
import os
import copy

import openai

from hubspot_utils import (
    get_all_companies,
    get_all_deals,
    get_all_contacts,
    get_deal_owner,
    get_products,
    get_activities,
    match_activities_to_deals,
)

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


def call_function(available_functions, response_message, messages):
    function_name = response_message["function_call"]["name"]
    arguments = response_message["function_call"]["arguments"]
    logger.info(
        f"LLM wants to call {function_name} function with arguments: {arguments}"
    )
    function_to_call = available_functions.get(function_name)
    if function_to_call is None:
        logger.error(
            f"LLM wanted to call function {function_name} that is not available"
        )
        messages.append(
            {
                "role": "user",
                "content": f"There is no function such: {function_name}. Available functions are: {','.join(available_functions.keys())}",
            }
        )
        return
    function_args = json.loads(response_message["function_call"]["arguments"])
    function_response = function_to_call(**function_args)
    function_response = json.dumps(function_response)
    messages.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        }
    )
    logger.info(
        f"{function_name} for arguments {arguments} returned {function_response}"
    )


def chat(
    prompt, messages, available_functions, functions, max_turns=15, agent_name="agent"
):
    logger.info(f"Entering chat function for {agent_name} and prompt:\n {prompt}")
    messages_new = copy.deepcopy(messages)
    messages_new.append({"role": "user", "content": prompt})
    turns = 0
    while True:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=messages_new,
            functions=functions,
            function_call="auto",
            temperature=0.00000001,
        )
        response_message = response["choices"][0]["message"]
        message_content = response["choices"][0]["message"]["content"]
        if message_content:
            logger.info(f"LLM responded with message: {message_content}\n")
        messages_new.append(response_message)
        if response_message.get("function_call"):
            call_function(available_functions, response_message, messages_new)
        else:
            logger.info(f"chat function for {agent_name} returned:\n {message_content}")
            break
        turns += 1
        if turns > max_turns:
            raise Exception("Reached max number of turns to LLM for single user query")
    messages[:] = messages_new
    return (
        response["choices"][0]["message"]["content"],
        response["usage"]["total_tokens"],
    )


class HubspotAgent:
    SYSTEM_PROMPT = """
    You are a virtual sales team assistant specializing in Hubspot-related queries.
    Your expertise lies in leveraging the Hubspot API to fetch data.
    Hubspot contains various entities, interconnected through associations.
    Your primary role is to exploit these associations for precise data filtration and aggregation.
    Avoid generating new code; instead, utilize pre-existing functions.
    When tasked with filtering data from Hubspot, first retrieve the complete dataset and then extract the specific 
    segments as instructed by the user.
    Please note that, closewon to the deal stage is the only closed and successful deal, the others remain open and 
    should not be taken into final consideration in regards revenue. 
    ALL OPEN DEALS are important to predict forecast revenue!!! 
    When I am asking about the forecast - take under consideration open deals and the price (not closed won!)
    Remember to match the deals with appropriate deal owner and its activities!
    *** If Hubspot function is not available - just list the information. DO NOT INVENT FUNCTIONS ***
    *** DO NOT GENERATE ANY CODE! JUST PROVIDE ANSWER TO THE QUESTION! ***
    *** Answer the question DIRECTLY. DO NOT provide or mention any plan or steps on how to solve the problem. ***
    ACTIVITIES include tasks, meetings, calls, notes and tickets!!
    *** ALWAYS MATCH ACTIVITIES WITH SPECIFIC DEAL!!! NEVER PRINT ALL THE ACTIVITIES FOR ALL THE DEALS!!***
    """

    PROMPT_TEMPLATE = """
        Please follow the approach below during solving the problem:
            1. Let’s first understand the problem and devise a plan to solve the problem.
               Please make the plan the minimum number of steps and the minimum number of functions calls required
               to accurately complete the task.
            2. Output the plan to the user and carry out the plan and solve the problem step by step
            ''' DO NOT PROVIDE THE PLAN - JUST EXECUTE AND GIVE ME FINAL OUTPUT '''
            Problem: {}
    """

    def __init__(self):
        self.available_functions = {
            "get_all_companies": get_all_companies,
            "get_all_deals": get_all_deals,
            "get_all_contacts": get_all_contacts,
            "get_deal_owner": get_deal_owner,
            "get_products": get_products,
            "get_activities": get_activities,
            "match_activities_to_deals": match_activities_to_deals,
        }
        self.functions = [
            {
                "name": "get_all_companies",
                "description": "Returns all companies available in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "get_all_contacts",
                "description": "Returns all contacts available in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "get_all_deals",
                "description": "Returns all deals available in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "get_deal_owner",
                "description": "Returns all owners available in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "get_products",
                "description": "Returns products associated with a deal in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "get_activities",
                "description": "Returns products activities with a deal in Hubspot.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "match_activities_to_deals",
                "description": "Matches activities to specific deals and returns the mapped results.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    def chat(self, query):
        prompt = self.PROMPT_TEMPLATE.format(query)
        response, _ = chat(
            prompt,
            self.messages,
            self.available_functions,
            self.functions,
            agent_name="hubspot_agent",
        )
        return response


def ask_hubspot_agent(query):
    print("asking Hubspot Agent")
    return HubspotAgent().chat(query)


# if __name__ == "__main__":
#     while True:
#         query = input("Enter your query (or type 'exit' to end): ")
#         if query.lower() == "exit":
#             break
#         response = ask_hubspot_agent(query)
#         print("Agent:", response)
