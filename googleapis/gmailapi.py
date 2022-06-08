from . import googleapi
import base64

def get_unread():
    return [x["id"] for x in gmail_service.users().messages().list(userId="me", q="is:unread").execute()["messages"]]

def get_headers(message_id):
    return {x["name"]: x["value"] for x in gmail_service.users().messages().get(userId="me", id=message_id, format="metadata").execute()["payload"]["headers"]}

def create_draft(fr="filip.uradnik9@gmail.com", to="", subject="", body="", file=""):
    from . import send_message
    if fr == "filip.uradnik9@gmail.com": service = googleapi.get_service('gmail', "v1", user="fu9")
    else: service = gmail_service
    if file:message = send_message.create_message_with_attachment(fr, to, subject, body, file)
    else:message = send_message.create_message(fr, to, subject, body)
    return send_message.create_draft(service, fr, message)


gmail_service = googleapi.get_service('gmail', "v1")
