import json
import os
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
        "physical_activity": responses[FormFields.PHYSICAL_ACTIVITY] + responses[FormFields.SPORTS_OR_EXERCISE],
        "dietary_habits": responses[FormFields.FRUIT_AND_VEGETABLES] + responses[FormFields.DAILY_DIET],
        "lifestyle_habits": responses[FormFields.CIGARETTES] + responses[FormFields.ALCOHOL]
                            + responses[FormFields.HOURS_OF_SLEEP],
        "medical_history": responses[FormFields.DIAGNOSED],
        "stress_management": responses[FormFields.STRESS_LEVEL] + responses[FormFields.MEDITATION] + responses[
            FormFields.BLOOD_PRESSURE],
        "genetic_awareness": responses[FormFields.DIAGNOSED] + responses[FormFields.MENTAL_HEALTH_CONDITION],
        "wellness_activities": responses[FormFields.WELLNESS_PROGRAMS],
    }

    config = {
        k: "good" if v < -1 else "bad" if v > 1 else "neutral"
        for k, v in config.items()
    }

    if config["genetic_awareness"] == "neutral":
        config["genetic_awareness"] = "good"

    config["overall"] = "good" if score < 18 else "neutral" if 18 <= score < 30 else "bad"
    config["healthy_lifestyle_encouragement"] = config["overall"]
    if config["healthy_lifestyle_encouragement"] == "bad":
        config["healthy_lifestyle_encouragement"] = "neutral"

    return config


email_subject = """Your EPIX.AI Health Score is Here"""
email_body = """
<pre>Hello,

Thank you for completing the EPIX.AI Healthspan Assessment. We're excited to share your personalized results, which you'll find attached to this email.

Next Steps:

Review Your Results: Take some time to go through the findings and suggestions.
Implement Changes: Consider our recommendations to improve your healthspan.
<a href="https://www.epix.ai/waiting-list">Stay Tuned</a>: Our app will offer more precise insights by monitoring your daily activities.

Disclaimer: 
The biological aging rate provided is an estimate based on your responses. This assessment doesn't collect biological samples, and many factors can influence your actual aging rate. For a comprehensive analysis, keep an eye out for our app that tracks your physical activity and geolocation around the clock.

We're here to support your journey to a healthier life. If you have questions or need further assistance, feel free to contact us at healthscore@epix.ai 

Your journey to a timeless vitality begins with EPIX.AI. Thank you for exploring your healthspan with us.

Best,
The EPIX.AI Team</pre>"""


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
    message["Subject"] = email_subject
    message.attach(MIMEText(email_body, 'html'))
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
    form_mapper_path = os.path.join(os.path.dirname(__file__), "form_mapper.json")
    print(form_mapper_path)
    print(os.listdir(os.path.dirname(__file__)))
    with open(form_mapper_path) as f:
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
    except Exception as e:

        # Get the queue URL
        queue_url = os.environ['DEAD_LETTER_QUEUE_URL']
        print(queue_url)
        # Send the message
        sqs = boto3.client('sqs')
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event)
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": str(e),
                "uuid": event_uuid,
                "response": response,
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
