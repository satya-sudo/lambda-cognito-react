import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored")) 


import imp
import json
import jwt
from db.db import Event

def getUserIdfromHeader(event):
    """
    This function is called when a user wants to get the user id from the header.
    """
    user  = {}
    try:
        data = jwt.decode(event['headers']['Authorization'].split()[-1],options={"verify_signature": False})
        user["user_id"] = data["cognito:username"]
        user["email"] = data["email"]
    except Exception as e:
        print(e)
        return None
    return user

def get_events(event, context):
    """
    This function is called when a user wants to get all events 
    created by the user.
    """

    # get User details from header
    user  =  getUserIdfromHeader(event)
    # print(user)
    if not user:
        return {"statusCode": 401, "body": json.dumps({"error": "Autherization error"})}
    
    # print(user)
    all_events  = Event.get_all_events_by_owner(user["user_id"])

    return {
        "statusCode": 200,
        "body": json.dumps({"events": all_events,"user":user,"status": "success"})
    }

def post_event(event, context):
    """
    This function is called when a user wants to create an event.
    """
    
    try:
        data = json.loads(event["body"])
    except Exception as e:
        print(e)
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid request"})}
    # get User details from header
    user  =  getUserIdfromHeader(event)
    if not user:
        return {"statusCode": 401, "body": json.dumps({"message": "Autherization error"})}
    
    # get the event data from the body
    data = json.loads(event['body'])
    try:
        name = data["name"]
        location = data["location"]
        date = data["date"]
        event  = Event(location=location, name=name, date=date, user_id=user["user_id"])
        if event.save():
            return {
                "statusCode": 201,
                "body": json.dumps({"message": "Event created successfully","status": "success"})
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Event creation failed","status": "failure"})
            }
    except Exception as e:
        print(e)
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Event creation failed","status": "failure"})
        }



def attend_event(event, context):
    """
    This function is called when a user wants to attend an event.
    need the event code and the user id
    """
    user  =  getUserIdfromHeader(event)
    if not user:
        return {"statusCode": 401, "body": json.dumps({"message": "Autherization error"})}

    try:
        code = event["pathParameters"]["code"]
    except:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid request","status": "failure"})}

    if Event.add_attendee(code, user["user_id"], user["email"]) :
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Added to Attendee listsuccessfully","status": "success"})
        }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Failed to add to Attendee list. Maybe wrong event code.","status": "failure"})
        }

def list_event(event, context):
    """
    This function is called when a user wants to list all events the user is attending.
    """
    user  =  getUserIdfromHeader(event)
    if not user:
        return {"statusCode": 401, "body": json.dumps({"message": "Autherization error"})}

    all_events  = Event.get_attending_events(user["user_id"])

    # print("list_events")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda!"
        ,"events": all_events,"user":user,"status": "success"})
    }