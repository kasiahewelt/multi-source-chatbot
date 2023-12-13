import os

from dotenv import load_dotenv
from simple_salesforce import Salesforce
load_dotenv()

username = os.getenv('SALESFORCE_USERNAME')
password = os.getenv('SALESFORCE_PASSWORD')
security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')

sf = Salesforce(username=username, password=password, security_token=security_token)


def execute_sosl(search: str):
    """Returns the result of a Salesforce search as a dict decoded from
    the Salesforce response JSON payload.
    Arguments:
    * search -- the fully formatted SOSL search string, e.g.
                `FIND {Waldo}`
    """
    from simple_salesforce import SalesforceError
    try:
        res = sf.search(search)
    except SalesforceError as err:
        return f"Error running SOSL query: {err}"
    return dict(res)


def execute_soql(query: str):
    """Returns the full set of results for the `query`. This is a
    convenience wrapper around `query(...)` and `query_more(...)`.
    The returned dict is the decoded JSON payload from the final call to
    Salesforce, but with the `totalSize` field representing the full
    number of results retrieved and the `records` list representing the
    full list of records retrieved.
    Arguments:
    * query -- the SOQL query to send to Salesforce, e.g.
               SELECT Id FROM Lead WHERE Email = "waldo@somewhere.com"
    """
    from simple_salesforce import SalesforceError
    try:
        res = sf.query_all(query)
    except SalesforceError as err:
        return f"Error running SOQL query: {err}"
    return res
