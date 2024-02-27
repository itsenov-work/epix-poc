import json
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from form_fields import FormFields, FIELD_NORMALIZED_WEIGHTS
from exceptions import HandledException
from read import ensure_mapper_matches_form, read_body, get_responses
from calculate import calculate_score, calculate_bmi
import boto3
from pdf_builder.generator import edit_fields
import uuid

BUCKET_NAME = "epix-aging-form"


def upload_event(event, _uuid):
    s3 = boto3.client("s3")
    s3.put_object(Bucket=BUCKET_NAME, Key=f"events/{_uuid}.json", Body=json.dumps(event))


def upload_pdf(_uuid):
    s3 = boto3.client("s3")
    s3.upload_file("/tmp/generated.pdf", BUCKET_NAME, f"pdfs/{_uuid}.pdf")

def get_message(score):
    if score < 9:
        return "Very slow aging"
    elif 9 <= score < 18:
        return "Slow aging"
    elif 18 <= score < 30:
        return "Normal aging"
    elif 30 <= score < 39:
        return "Fast aging"
    elif score >= 39:
        return "Very fast aging"


def get_score(responses, mapper):
    responses[FormFields.BMI] = calculate_bmi(responses[FormFields.WEIGHT], responses[FormFields.HEIGHT])
    factors = [responses[response] for response in mapper]
    weights = [FIELD_NORMALIZED_WEIGHTS[response] for response in mapper]
    score = calculate_score(factors, weights)
    return score


def get_pdf_config(responses, score):
    config = {
        "physical_activity": responses[FormFields.PHYSICAL_ACTIVITY] +,
        "dietary_habits": responses[FormFields.FRUIT_AND_VEGETABLES] + responses[FormFields.DAILY_DIET],
        "lifestyle_habits": responses[FormFields.CIGARETTES] + responses[FormFields.ALCOHOL]
                            + responses[FormFields.HOURS_OF_SLEEP],
        "medical_history": responses[FormFields.DIAGNOSED] + responses[FormFields.BLOOD_PRESSURE],
        "stress_management": responses[FormFields.STRESS_LEVEL] + responses[FormFields.MEDITATION],
        "genetic_awareness": responses[FormFields.DIAGNOSED] + responses[FormFields.MENTAL_HEALTH_CONDITION],
        "wellness_activities": responses[FormFields.WELLNESS_PROGRAMS],
    }

    config = {
        k: "good" if v > 1 else "bad" if v < -1 else "neutral"
        for k, v in config.items()
    }

    if config["genetic_awareness"] == "neutral":
        config["genetic_awareness"] = "good"

    config["overall"] = "good" if score < 18 else "neutral" if 18 <= score < 30 else "bad"
    config["healthy_lifestyle_encouragement"] = config["overall"]
    if config["healthy_lifestyle_encouragement"] == "bad":
        config["healthy_lifestyle_encouragement"] = "neutral"

    return config


def send_email_smtp(email, pdf_path):
    mail_server = "mail.s809.sureserver.com"
    mail_server_port = 587
    mail_username = "healthscore@epix.ai"
    mail_password = "BX50vzh[)AJj"

    import smtplib
    server = smtplib.SMTP(mail_server, mail_server_port)
    server.starttls()

    # Create the email message
    message = MIMEMultipart()
    message["From"] = "healthscore@epix.ai"
    message["To"] = email
    message["Subject"] = "Your EPIX Health Score and Recommendations"
    message.attach(MIMEText("Your health score and recommendations are attached to this email."))
    # Attach the PDF
    with open(pdf_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header("Content-Disposition", "attachment", filename="EPIX Health Score.pdf")
        message.attach(attach)
    # Send the email
    server.login(mail_username, mail_password)
    server.send_message(message)
    server.quit()


def main(event):
    # upload_event(event, event["uuid"])
    from logger import setup_logger
    setup_logger(event["uuid"])
    answers, form = read_body(event)
    with open("form_mapper.json") as f:
        mapper = json.load(f)
    ensure_mapper_matches_form(mapper, form)
    responses = get_responses(answers, mapper)
    score = get_score(responses, mapper)
    pdf_config = get_pdf_config(responses, score)

    event_uuid = event["uuid"]
    filepath = f"/tmp/generated_{event_uuid}.pdf"
    edit_fields(pdf_config, filepath)
    # upload_pdf(event["uuid"])
    email = [
        answer for answer in answers if answer["field"]["type"] == "email"
    ][0]["email"]
    send_email_smtp(email, filepath)
    return score


def lambda_handler(event, context):
    event_uuid = str(uuid.uuid4())
    event["uuid"] = event_uuid
    try:
        score = main(event)
    except HandledException as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": str(e)
            }),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": get_message(score),
            "score": score
        }),
    }


# Test the lambda_handler

if __name__ == "__main__":
    event = {}
    with open("example.json") as f:
        event["body"] = json.load(f)
        event["body"] = json.dumps(event["body"])
    print(lambda_handler(event, None))
