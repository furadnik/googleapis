"""Gmail api."""
from __future__ import annotations

import base64
import email
from typing import Collection, Optional

from . import googleapi


def get_body(msg: email.Message, preferred_type: Optional[str] = "text/plain") -> str:
    """Get message body."""
    mime_type = msg.get_content_maintype()
    if mime_type == "multipart":
        return "".join(get_body(x, preferred_type=preferred_type) for x in msg.get_payload())
    elif mime_type == "text" and (preferred_type is None or msg.get_content_type() == preferred_type):
        return base64.b64decode(msg.get_payload()).decode("utf-8")
    return ""


Id = str


class Mail:
    """Mail object."""

    def __init__(self, mail_info: dict) -> None:
        """Save mail info."""
        self._mail_info = mail_info

    def __eq__(self, other: object) -> bool:
        """Compare two mails."""
        if isinstance(other, Mail):
            return self.id == other.id
        elif isinstance(other, Id):
            return self.id == other
        raise NotImplementedError("Not implemented equating to other types than mail.")

    @property
    def id(self) -> Id:
        """Get message id."""
        return self._mail_info["id"]

    @property
    def body(self) -> str:
        """Get email body."""
        gmail_content = gmail_service.users().messages().get(
            userId="me", id=self.id, format="raw"
        ).execute()
        msg_raw = base64.b64decode(gmail_content['raw'])
        msg_str = email.message_from_bytes(msg_raw)
        return get_body(msg_str) or get_body(msg_str, None)

    def _get_headers(self) -> list[dict]:
        """TODO: implement later."""
        return gmail_service.users().messages().get(
            userId="me", id=self.id, format="metadata"
        ).execute()["payload"]["headers"]

    def _get_header(self, header_name: str) -> str:
        """Get header from api."""
        for x in self._get_headers():
            if x["name"] == header_name:
                return x["value"]
        raise ValueError("Header not found.")

    @property
    def subject(self) -> str:
        """Get message subject."""
        return self._get_header("Subject")

    @property
    def from_(self) -> str:
        """Get from."""
        return self._get_header("From")

    @property
    def from_address(self) -> str:
        """Get from address."""
        addr = self.from_
        if "<" in addr:
            addr = addr.split("<")[1].split(">")[0]

        return addr

    def __repr__(self) -> str:
        """Get repr."""
        return f"Mail({self.subject} - {self.from_})"


def get_unread_mail(current_mail: Collection[Mail] | Collection[Id] = []) -> list[Mail]:
    """Get unread mails."""
    current_ids = {x.id if isinstance(x, Mail) else x for x in current_mail}
    resp = gmail_service.users().messages().list(userId="me", q="is:unread").execute()
    if "messages" not in resp.keys():
        return []

    return [Mail(x) for x in resp["messages"] if x["id"] not in current_ids]


def get_unread():
    """Get unread mails ids."""
    resp = gmail_service.users().messages().list(userId="me", q="is:unread").execute()
    if "messages" not in resp.keys():
        return []

    return [x["id"] for x in resp["messages"]]


def get_headers(message_id):
    """Get headers."""
    return {
        x["name"]: x["value"]
        for x in gmail_service.users().messages().get(
            userId="me", id=message_id, format="metadata"
        ).execute()["payload"]["headers"]
    }


def create_draft(fr="filip.uradnik9@gmail.com", to="", subject="", body="", file=""):
    """Create draft mail."""
    from . import send_message
    if fr == "filip.uradnik9@gmail.com":
        service = googleapi.get_service('gmail', "v1", user="fu9")
    else:
        service = gmail_service
    if file:
        message = send_message.create_message_with_attachment(fr, to, subject, body, file)
    else:
        message = send_message.create_message(fr, to, subject, body)

    return send_message.create_draft(service, fr, message)


gmail_service = googleapi.get_service('gmail', "v1")

if __name__ == "__main__":
    print(get_unread_mail()[0].subject)
