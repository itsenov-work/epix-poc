import json
from form_fields import FormFields
from exceptions import HandledException


def read_body(event):
    try:
        body = event["body"]
        js = json.loads(body)
    except KeyError:
        raise HandledException("No body found in the event")
    except json.JSONDecodeError:
        raise HandledException("Invalid JSON in the body")

    try:
        answers = js["form_response"]["answers"]
        form = js["form_response"]["definition"]["fields"]
    except KeyError as e:
        raise HandledException(f"Invalid form response, missing key:{e}")

    return answers, form


def ensure_mapper_matches_form(mapper, form):
    form_fields = {
        field["ref"]: field for field in form
    }

    issues = []
    for response in mapper:

        num_choices_mapper = len(mapper[response])

        if not any(response == form_field for form_field in FormFields):
            issues.append(f"Response {response} mismatched with enum FormFields")
        if response not in form_fields:
            issues.append(f"Response {response} not found in the form")

        field = form_fields[response]

        # Find the field in the form
        # Ensure the number of choices in the mapper matches the number of choices in the form
        if "choices" in field:
            num_choices_form = len(field["choices"])
            if num_choices_mapper != num_choices_form:
                issues.append(
                    f"{num_choices_mapper} choices in the mapper for {response} does not match {num_choices_form} "
                    f"number of choices in the form")
        else:
            if len(mapper[response]) != 1:
                issues.append(
                    f"Mapper for {response} has {len(mapper[response])} choices but the form has no choices")

        # Find each choice in the form
        for choice in mapper[response]:
            if choice["label"] not in [c["label"] for c in field["choices"]]:
                issues.append(f"Choice {choice['label']} not found in the form for response {response}")

    if issues:
        raise HandledException("\n".join(issues))


def get_responses(answer, mapper):
    responses = {}
    for response in answer:
        ref = response["field"]["ref"]
        if "number" in response:
            responses[ref] = response["number"]
            continue

        if ref not in mapper:
            continue
        mapping = {choice["label"]: choice["value"] for choice in mapper[ref]}
        if "choice" in response:
            responses[ref] = mapping[response["choice"]["label"]]
        elif "choices" in response:
            responses[ref] = sum([mapping[label] for label in response["choices"]["labels"]])

    return responses

