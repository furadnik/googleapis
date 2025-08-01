"""Gmail api."""
from __future__ import annotations

import base64
import email
from email.policy import default
from functools import cached_property
from typing import Collection, Optional

from . import googleapi


def get_body_with_fallback(msg: email.message.EmailMessage) -> str | None:
    """Extract the body of the message, preferring plain text."""
    text = None
    html = None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()

            if ctype == 'text/plain' and disp != 'attachment':
                text = part.get_content()
            elif ctype == 'text/html' and disp != 'attachment':
                html = part.get_content()
        return text or html
    else:
        return msg.get_content()


Id = str

SERVICE = googleapi.Service('gmail', "v1")
SERVICE_FU = googleapi.Service('gmail', "v1", user="fu9")


class Mail:
    """Mail object."""

    def __init__(self, mail_info: dict, service: googleapi.Service) -> None:
        """Save mail info."""
        self._mail_info = mail_info
        self.service = service

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

    @cached_property
    def body(self) -> str | None:
        """Get email body."""
        gmail_content = self.service().users().messages().get(
            userId="me", id=self.id, format="raw"
        ).execute()

        msg_raw = base64.urlsafe_b64decode(gmail_content['raw'])
        msg = email.message_from_bytes(msg_raw, policy=default)

        return get_body_with_fallback(msg)

    def _get_headers(self) -> list[dict]:
        """TODO: implement later."""
        return self.service().users().messages().get(
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
        return email.utils.parseaddr(self.from_)[1]

    def __repr__(self) -> str:
        """Get repr."""
        return f"Mail({self.subject} - {self.from_})"


def get_unread_mail(current_mail: Collection[Mail] | Collection[Id] = [],
                    service: googleapi.Service = SERVICE) -> list[Mail]:
    """Get unread mails."""
    current_ids = {x.id if isinstance(x, Mail) else x for x in current_mail}
    resp = service().users().messages().list(userId="me", q="is:unread").execute()
    if "messages" not in resp.keys():
        return []

    return [Mail(x, service) for x in resp["messages"] if x["id"] not in current_ids]


def get_unread(service: googleapi.Service = SERVICE):
    """Get unread mails ids."""
    resp = service().users().messages().list(userId="me", q="is:unread").execute()
    if "messages" not in resp.keys():
        return []

    return [x["id"] for x in resp["messages"]]


def get_headers(message_id, service: googleapi.Service = SERVICE):
    """Get headers."""
    return {
        x["name"]: x["value"]
        for x in service().users().messages().get(
            userId="me", id=message_id, format="metadata"
        ).execute()["payload"]["headers"]
    }


def create_draft(fr="filip.uradnik9@gmail.com", to="", subject="", body="", file="",
                 service: googleapi.Service = SERVICE):
    """Create draft mail."""
    from . import send_message
    if file:
        message = send_message.create_message_with_attachment(fr, to, subject, body, file)
    else:
        message = send_message.create_message(fr, to, subject, body)

    return send_message.create_draft(service(), fr, message)


if __name__ == "__main__":
    print(get_unread_mail()[0].body)
