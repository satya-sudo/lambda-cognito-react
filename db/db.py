from msilib.schema import tables
import boto3

from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

import random


# create or retrieve table events_table
def retrive_or_create_table():
    try:
        table = dynamodb.Table('events_table')
        return table
    except Exception as e:
        print(e)
    if not table:
        table = dynamodb.create_table(
            TableName='events_table',
            KeySchema=[
                {
                    'AttributeName': 'event_code',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'type',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'event_code',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'type',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        print(table.item_count)
        return table


class Event:
    def __init__(self,name, location,date,user_id):
        self.event_code = "event#" + random.randint(10000, 100000).__str__()
        self.location = location
        self.date = date
        self.name = name
        self.type = "owner#" + user_id
        self.table = retrive_or_create_table()
  
    
        
    def save(self):
        try:
            response = self.table.put_item(
                Item={
                    'event_code': self.event_code,
                    'name': self.name,
                    'type': self.type,
                    'location': self.location,
                    'date': self.date
                }
            )
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(e)
        return False


    @staticmethod
    def get_event(event_code):
        event_code = "event#" + event_code
        table = retrive_or_create_table()
        try:
            data = {}
            response = table.query(
                KeyConditionExpression=Key('event_code').eq(event_code) & Key('type').begins_with('owner#')
            )
            if not response['Items']:
                return None
            data["event_code"] = response['Items'][0]['event_code']
            data["type"] = response['Items'][0]['type']
            data["location"] = response['Items'][0]['location']
            data["date"] = response['Items'][0]['date']
            data["name"] = response['Items'][0]['name']
            response = table.query(
                KeyConditionExpression=Key('event_code').eq(event_code) & Key('type').begins_with("attendee#")
            )
            list = []
            for attent in response['Items']:
                attendee = {}
                attendee["email"] = attent['email']
                list.append(attendee)
            data["attendees"] = list

            return data
        except Exception as e:
            print(e)
        return None

    def check_event_code(event_code):
        event_code = "event#" + event_code
        table = retrive_or_create_table()
        try:
            response = table.query(
                KeyConditionExpression=Key('event_code').eq(event_code) & Key('type').begins_with('owner#')
            )
            return response['Items'] != []
        except Exception as e:
            print(e)
        return False
        
    @staticmethod
    def get_all_events_by_owner(owner_id):

        table = retrive_or_create_table()
        try:
           
            response = table.scan(
                FilterExpression=Key('type').eq("owner#" + owner_id)
            )
            list = []
            for event in response['Items']:
                data = {}
                data["event_code"] = event.get('event_code')
                data["type"] = event.get('type',None)
                data["location"] = event.get('location',None)
                data["date"] = event.get('date',None)
                data["name"] = event.get('name',"random")
                data["attendees"] = Event.get_attendies(event['event_code'])
                list.append(data)
            return list

        except Exception as e:
            print(e)
        return []


    def delete_event( event_code):
        event_code = "event#" + event_code
        table =  retrive_or_create_table()
        try:
            response = table.delete_item(
                Key={
                    'event_code': event_code,
                }
            )
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(e)
        return False
    @staticmethod
    def get_attendies(event_code):
        # event_code = "event#" + event_code
        print(event_code)
        table = retrive_or_create_table()
        try:
            response = table.query(
                KeyConditionExpression=Key('event_code').eq(event_code) & Key('type').begins_with('attendee#')
            )
            
            return [{"email":i["email"]}  for i in response['Items']]
        except Exception as e:
            print(e)
        return []

    def attendence_status(event_code, user_id):
        event_code = "event#" + event_code
        table = retrive_or_create_table()
        try:
            response = table.query(
                KeyConditionExpression=Key('event_code').eq(event_code) & Key('type').eq('attendee#' + user_id)
            )
            return response['Items'] != []
        except Exception as e:
            print(e)
        return False

    def add_attendee(event_code, user_id, email):
        table = retrive_or_create_table()
        if not Event.check_event_code(event_code):
            print("event not found")
            return False

        if  Event.attendence_status(event_code, user_id):
            return True
        event_code = "event#" + event_code
        try:
            response = table.put_item(
                Item={
                    'event_code':  event_code,
                    'type': "attendee#" + user_id,
                    'email': email
                }
            )
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(e)
        return False
    
    @staticmethod
    def get_attending_events(user_id):
        user_id  = "attendee#" + user_id
        table = retrive_or_create_table()
        try:
            response = table.scan(
                FilterExpression=Key('type').eq(user_id)
            )
            res = []
            for i in response['Items']:
                code =  i.get('event_code',None)
                if code:
                    ret = Event.get_event(code.split('#')[1])
                    if ret:
                        res.append(ret)
            return res


        except:
            print("error")
        return []

