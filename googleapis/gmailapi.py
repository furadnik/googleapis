"""Gmail api."""
from __future__ import annotations
from . import googleapi


class Mail:
    """Mail object."""

    def __init__(self, mail_info: dict) -> None:
        """Save mail info."""
        self._mail_info = mail_info

    def __eq__(self, other: Mail) -> None:
        """Compare two mails."""
        return self.id == other.id

    @property
    def id(self) -> str:
        """Get message id."""
        return self._mail_info["id"]

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

    @property
    def subject(self) -> str:
        """Get message subject."""
        return self._get_header("Subject")

    @property
    def from_(self) -> str:
        """Get from."""
        return self._get_header("From")

    def __repr__(self) -> str:
        """Get repr."""
        return f"Mail({self.subject} - {self.from_})"


def get_unread_mail(current_mail: list[Mail] = []) -> list[Mail]:
    """Get unread mails."""
    current_ids = [x.id for x in current_mail]
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
    print(get_unread_mail())
