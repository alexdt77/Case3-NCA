import boto3
import uuid
import datetime
import json
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
        pass  

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


def create_employee(name, email, department, role):
    employee_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()

    item = {
        "id": employee_id,
        "name": name,
        "email": email,
        "department": department,
        "role": role.upper(),
        "status": "ACTIVE",
        "login_enabled": True,
        "device_status": "PENDING_ENROLL",
        "created_at": now,
        "updated_at": now
    }

    table.put_item(Item=item)

    log_action("ONBOARDING", employee_id, email, "Employee created")

    return {
        "employee_id": employee_id,
        "message": "Employee created successfully. No password generated (Keycloak handles authentication)."
    }
