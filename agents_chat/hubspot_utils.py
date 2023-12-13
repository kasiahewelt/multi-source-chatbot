import os

from dotenv import load_dotenv
from hubspot import HubSpot

SUPPORTED_ASSOCIATIONS = [
    "deal_to_company",
    "deal_to_contact",
    "deal_to_line_item",
    "company_to_contact",
    "company_to_deal",
    "contact_to_company",
    "contact_to_deal",
    "meeting_event_to_deal",
    "deal_to_task",
    "deal_to_meeting_event",
    "deal_to_note",
    "deal_to_call",
    "call_to_deal",
    "note_to_deal",
    "task_to_deal",
]

load_dotenv()
hub_api = os.getenv("HUB_API")
hs_client = HubSpot(access_token=hub_api)


def extract_associations(raw_associations):
    associations = {}
    for entity_type in raw_associations:
        associations[entity_type] = []
        for association_data in raw_associations[entity_type].results:
            if association_data.type not in SUPPORTED_ASSOCIATIONS:
                continue
            associations[entity_type].append(association_data.id)
    return associations


def flatten_contact(raw_response):
    return {
        "id": raw_response.id,
        "email": raw_response.properties["email"],
        "firstname": raw_response.properties["firstname"],
        "lastname": raw_response.properties["lastname"],
        "associations": extract_associations(raw_response.associations),
    }


def flatten_company(raw_response):
    return {
        "id": raw_response.id,
        "domain": raw_response.properties["domain"],
        "name": raw_response.properties["name"],
        "associations": extract_associations(raw_response.associations),
    }


def flatten_deal(raw_response):
    return {
        "id": raw_response.id,
        "dealname": raw_response.properties["dealname"],
        "dealstage": raw_response.properties["dealstage"],
        "amount": raw_response.properties["amount"],
        "closedate": raw_response.properties["closedate"],
        "createdate": raw_response.properties["createdate"],
        "lastmodifeddate": raw_response.properties["hs_lastmodifieddate"],
        "hubspot_owner_id": raw_response.properties["hubspot_owner_id"],
        "associations": extract_associations(raw_response.associations),
    }


def flatten_owner(raw_response):
    return {
        "id": raw_response.id,
        "first_name": raw_response.first_name,
        "last_name": raw_response.last_name,
        "email": raw_response.email,
    }


def flatten_products(raw_response):
    return {
        "id": raw_response.id,
        "name": raw_response.properties["name"],
        "quantity": raw_response.properties["quantity"],
        "amount": raw_response.properties["amount"],
    }


def flatten_task(raw_task):
    # Assuming a task has properties like a title, status, body, etc.
    # You can modify this as per the actual structure of a task object
    return {
        "id": raw_task.id,
        "owner_id": raw_task.properties["hubspot_owner_id"],
        "subject": raw_task.properties["hs_task_subject"],
        "status": raw_task.properties["hs_task_status"],
        "priority": raw_task.properties["hs_task_priority"],
        "type": raw_task.properties["hs_task_type"],
        "body": raw_task.properties["hs_task_body"]
    }


def flatten_note(raw_note):
    # Modify based on actual structure of a note object
    return {
        "id": raw_note.id,
        "body": raw_note.properties["hs_note_body"],
        "owner_id": raw_note.properties["hubspot_owner_id"]
    }


def flatten_call(raw_call):
    # Modify based on actual structure of a call object
    return {
        "id": raw_call.id,
        "body": raw_call.properties["hs_call_body"],
        "direction": raw_call.properties["hs_call_direction"],
        "disposition": raw_call.properties["hs_call_disposition"],
        "duration": raw_call.properties["hs_call_duration"],
        "status": raw_call.properties["hs_call_status"],
        "title": raw_call.properties["hs_call_title"]
    }


def flatten_meeting(raw_meeting):
    # Modify based on actual structure of a meeting object
    return {
        "id": raw_meeting.id,
        "title": raw_meeting.properties["hs_meeting_title"],
        "body": raw_meeting.properties["hs_meeting_body"],
        "location": raw_meeting.properties["hs_meeting_location"]
    }


def get_activities():
    # print("listing activities")

    tasks = [
        flatten_task(task)
        for task in hs_client.crm.objects.get_all(
            object_type="tasks",
            associations=["deals"],
            properties=[
                "hubspot_owner_id",
                "hs_task_subject",
                "hs_task_status",
                "hs_task_priority",
                "hs_task_type",
                "hs_task_body",
            ],
        )
    ]

    notes = [
        flatten_note(note)
        for note in hs_client.crm.objects.get_all(
            object_type="notes",
            associations=["deals"],
            properties=["hs_note_body", "hubspot_owner_id"],
        )
    ]

    calls = [
        flatten_call(call)
        for call in hs_client.crm.objects.get_all(
            object_type="calls",
            associations=["deals"],
            properties=[
                "hs_call_body",
                "hs_call_direction",
                "hs_call_disposition",
                "hs_call_duration",
                "hs_call_status",
                "hs_call_title",
            ],
        )
    ]

    meetings = [
        flatten_meeting(meeting)
        for meeting in hs_client.crm.objects.get_all(
            object_type="meetings",
            associations=["deals"],
            properties=["hs_meeting_title", "hs_meeting_body", "hs_meeting_location"],
        )
    ]

    return {"tasks": tasks, "notes": notes, "calls": calls, "meetings": meetings}


def get_all_contacts():
    # print("listing contacts")
    response = []
    for raw_response in hs_client.crm.contacts.get_all(
            associations=["companies", "deals"]
    ):
        response.append(flatten_contact(raw_response))
    return response


def get_all_companies():
    # print("listing companies")
    response = []
    for raw_response in hs_client.crm.companies.get_all(
            associations=["contacts", "deals"]
    ):
        response.append(flatten_company(raw_response))
    return response


def get_products():
    response = []
    for raw_response in hs_client.crm.line_items.get_all(
            properties=["name", "quantity", "amount"]
    ):
        response.append(flatten_products(raw_response))
    return response


def get_deal_owner():
    # print("listing owners")
    response = []
    for raw_response in hs_client.crm.owners.get_all():
        response.append(flatten_owner(raw_response))
    return response


def get_all_deals():
    # print("listing deals")
    response = []
    for raw_response in hs_client.crm.deals.get_all(
            associations=[
                "companies",
                "contacts",
                "line_items",
                "calls",
                "meetings",
                "tasks",
                "notes",
                "tickets",
            ],
            properties=["hubspot_owner_id", "amount", "dealname", "dealstage", "closedate"],
    ):
        response.append(flatten_deal(raw_response))
    return response


def match_activities_to_deals():
    deals = get_all_deals()
    activities = get_activities()

    activity_map = {}
    for activity_type, activity_list in activities.items():
        for activity in activity_list:
            activity_map[activity['id']] = (activity_type, activity)

    deal_activities = {}

    for deal in deals:
        if not isinstance(deal, dict):
            print(f"Unexpected item in deals: {deal}")
            continue

        deal_id = deal.get('id')
        dealname = deal.get('dealname')
        associations = deal.get('associations', {})

        matched_activities = {
            'tasks': [],
            'notes': [],
            'calls': [],
            'meetings': []
        }

        for associated_type, associated_ids in associations.items():
            for associated_id in associated_ids:
                if associated_id in activity_map:
                    activity_type, activity_data = activity_map[associated_id]
                    matched_activities[activity_type].append(activity_data)

        deal_activities[dealname] = matched_activities

    return deal_activities
