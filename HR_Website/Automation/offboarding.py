import boto3
import datetime
import json
from boto3.dynamodb.conditions import Key
import os

AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-central-1"
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "employees")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)
logs = boto3.client("logs")

LOG_GROUP = "/case3/employee_lifecycle"


def log_action(action, employee_id, email, details):
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    stream = f"{employee_id}-lifecycle"

    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=stream)
    except:
        pass  # stream bestaat al

    logs.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=stream,
        logEvents=[
            {
                "timestamp": timestamp,
                "message": json.dumps({
                    "action": action,
                    "employee_id": employee_id,
                    "email": email,
                    "details": details,
                    "timestamp": str(datetime.datetime.now())
                })
            }
        ]
    )


def offboard_employee(email):
    # Veilig en snel — email-index gebruiken
    response = table.query(
        IndexName="email-index",
        KeyConditionExpression=Key("email").eq(email)
    )

    if not response["Items"]:
        return {
            "success": False,
            "message": "Employee not found"
        }

    user = response["Items"][0]
    employee_id = user["id"]

    now = datetime.datetime.utcnow().isoformat()

    # Account terminating updates
    user["status"] = "TERMINATED"
    user["login_enabled"] = False
    user["device_status"] = "BLOCKED"
    user["termination_date"] = now
    user["updated_at"] = now

    table.put_item(Item=user)
    log_action("OFFBOARDING", employee_id, email, "Employee terminated")

    return {
        "success": True,
        "employee_id": employee_id,
        "message": "Employee successfully offboarded"
    }
