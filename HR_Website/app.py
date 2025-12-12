from flask import Flask, redirect, request, session, url_for, render_template
import requests
import jwt
import urllib.parse
import os
import uuid
import datetime
import boto3
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)
app.secret_key = "supersecretkey"

AUTH_ENABLED = True

KEYCLOAK_BASE = os.environ.get("KEYCLOAK_BASE")
REALM = "Innovatech"
CLIENT_ID = "HR-portal"
CLIENT_SECRET = "XOSAQ9tVYzYCUO1m1c8APMFoZkmXUKTl"

ALB_BASE = os.environ.get(
    "ALB_BASE",
    "http://hr-portal-alb-41585817.eu-central-1.elb.amazonaws.com"
)

REDIRECT_URI = os.environ.get("REDIRECT_URI", f"{ALB_BASE}/callback")

AUTH_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
LOGOUT_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/logout"

AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "employees")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
employees_table = dynamodb.Table(DYNAMODB_TABLE)

from Automation.onboarding import create_employee
from Automation.offboarding import offboard_employee
from Automation.deviceenroll import mark_device_compliant


def extract_hr_roles(roles):
    hr = [r for r in roles if r in ("HR-Employee", "HR-Manager", "HR-Admin")]
    return ", ".join(hr) if hr else "Geen HR-rol"


def get_device_status_for_email(email):
    if not email:
        return "UNKNOWN", None

    result = employees_table.scan(
        FilterExpression=Attr("email").eq(email)
    )

    items = result.get("Items", [])
    if not items:
        return "UNKNOWN", None

    return items[0].get("device_status", "PENDING_ENROLL"), items[0].get("id")


def require_role_and_compliance(*allowed_roles):
    def decorator(f):
        def wrapper(*args, **kwargs):

            if "user" not in session:
                return redirect(url_for("login"))

            user = session["user"]
            roles = user["roles"]
            email = user["email"]
            employee_id = user.get("employee_id")

            if not any(r in roles for r in allowed_roles):
                return render_template("403.html", user=user), 403

            if "HR-Admin" in roles or "HR-Manager" in roles:
                return f(*args, **kwargs)

            if request.endpoint == "onboard" and "HR-Employee" in roles:
                return f(*args, **kwargs)

            status, empID = get_device_status_for_email(email)
            if empID and not employee_id:
                user["employee_id"] = empID
                session["user"] = user

            if status != "COMPLIANT":
                return render_template(
                    "403_device.html",
                    user=user,
                    device_status=status,
                    display_roles=extract_hr_roles(roles),
                ), 403

            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


@app.route("/login")
def login():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
    }
    return redirect(AUTH_URL + "?" + urllib.parse.urlencode(params))


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    token_resp = requests.post(TOKEN_URL, data=data)
    tokens = token_resp.json()

    if "access_token" not in tokens:
        return f"Keycloak error: {tokens}", 400

    decoded = jwt.decode(tokens["access_token"], options={"verify_signature": False})

    username = decoded.get("preferred_username")
    email = decoded.get("email")
    roles = decoded.get("realm_access", {}).get("roles", [])

    device_status, employee_id = get_device_status_for_email(email)

    if "HR-Admin" in roles or "HR-Manager" in roles:
        device_status = "COMPLIANT"

    if "HR-Employee" in roles and employee_id is None:
        existing = employees_table.scan(
            FilterExpression=Attr("email").eq(email)
        )

        if not existing.get("Items"):
            now = datetime.datetime.utcnow().isoformat()
            new_user = {
                "id": str(uuid.uuid4()),
                "name": username,
                "email": email,
                "department": "Unknown",
                "role": "HR-EMPLOYEE",
                "status": "ACTIVE",
                "login_enabled": True,
                "device_status": "PENDING_ENROLL",
                "created_at": now,
                "updated_at": now
            }
            employees_table.put_item(Item=new_user)
            employee_id = new_user["id"]
            device_status = "PENDING_ENROLL"

    session["user"] = {
        "username": username,
        "email": email,
        "roles": roles,
        "employee_id": employee_id,
        "device_status": device_status,
    }

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        LOGOUT_URL
        + f"?client_id={CLIENT_ID}&post_logout_redirect_uri={ALB_BASE}/login"
    )


@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    roles = user["roles"]
    email = user["email"]

    if "HR-Admin" in roles or "HR-Manager" in roles:
        device_status = "COMPLIANT"
    else:
        device_status, _ = get_device_status_for_email(email)

    display_roles = extract_hr_roles(roles)

    return render_template(
        "home.html",
        user=user,
        device_status=device_status,
        display_roles=display_roles,
    )


@app.route("/onboard", methods=["GET", "POST"])
@require_role_and_compliance("HR-Employee", "HR-Manager", "HR-Admin")
def onboard():
    user = session["user"]

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        department = request.form["department"].strip()
        role = request.form["role"].strip()

        if not name or not email:
            return render_template(
                "onboard.html",
                user=user,
                error="Naam en email zijn verplicht.",
                success=False
            )

        user_roles = session["user"]["roles"]

        if "HR-Employee" in user_roles and role != "HR-Employee":
            return render_template(
                "403.html",
                user=session["user"],
                message="Je mag geen hogere rollen aanmaken."
            ), 403

        if "HR-Manager" in user_roles and role == "HR-Admin":
            return render_template(
                "403.html",
                user=session["user"],
                message="Je mag geen HR-Admin accounts aanmaken."
            ), 403

        result = create_employee(name, email, department, role)

        return render_template("onboard.html", user=user, result=result, success=True)

    return render_template("onboard.html", user=user, success=False)

@app.route("/device", methods=["GET", "POST"])
@require_role_and_compliance("HR-Manager", "HR-Admin")
def device():
    user = session["user"]

    if request.method == "POST":
        employee_id = request.form["employee_id"].strip()

        if not employee_id:
            return render_template(
                "device.html",
                user=user,
                error="Je moet een geldig Employee ID invullen."
            )

        mark_device_compliant(employee_id)
        return redirect(url_for("home"))

    return render_template("device.html", user=user)

@app.route("/offboard", methods=["GET", "POST"])
@require_role_and_compliance("HR-Manager", "HR-Admin")
def offboard():
    user = session["user"]
    error = None
    success = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            return render_template(
                "offboard.html",
                user=user,
                error="Vul een geldig e-mailadres in."
            )
        try:
            offboard_employee(email)
            success = "Medewerker is succesvol offboard."

        except Exception as e:
            error = str(e)

        return render_template(
            "offboard.html",
            user=user,
            error=error,
            success=success
        )

    return render_template("offboard.html", user=user)


@app.route("/appA", methods=["GET", "POST"])
@require_role_and_compliance("HR-Employee")
def appA():
    user = session["user"]
    email = user["email"]

    result = employees_table.scan(
        FilterExpression=Attr("email").eq(email)
    )

    if not result["Items"]:
        item = {"id": "unknown", "email": email}
    else:
        item = result["Items"][0]

    if request.method == "POST":
        notes = request.form.get("notes", "")
        item["notes"] = notes

        if item["id"] != "unknown":
            employees_table.put_item(Item=item)

    saved_notes = item.get("notes", "")

    return render_template("appA.html", user=user, notes=saved_notes)


@app.route("/appB")
@require_role_and_compliance("HR-Manager")
def appB():
    scan = employees_table.scan()
    employees = scan.get("Items", [])

    return render_template("appB.html", user=session["user"], employees=employees)


@app.route("/appC", methods=["GET", "POST"])
@require_role_and_compliance("HR-Admin")
def appC():
    message = None
    message_type = None  

    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip()
        action = request.form.get("action")

        if not employee_id:
            message = "Je moet een Employee ID invullen."
            message_type = "error"
        else:
            response = employees_table.get_item(Key={"id": employee_id})
            item = response.get("Item")

            if not item:
                message = f"Medewerker met ID '{employee_id}' bestaat niet."
                message_type = "error"
            else:
                if action == "enable_login":
                    item["login_enabled"] = True
                    message = f"Login ingeschakeld voor {employee_id}"
                elif action == "disable_login":
                    item["login_enabled"] = False
                    message = f"Login uitgeschakeld voor {employee_id}"
                elif action == "block_device":
                    item["device_status"] = "BLOCKED"
                    message = f"Device geblokkeerd voor {employee_id}"

                employees_table.put_item(Item=item)
                message_type = "success"

    employees = employees_table.scan().get("Items", [])

    return render_template(
        "appC.html",
        user=session["user"],
        employees=employees,
        message=message,
        message_type=message_type
    )

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
