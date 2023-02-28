from . import googleapi
import requests


class Book:

    def __init__(self, j):
        self._j = j

    @property
    def link(self) -> str:
        """Get link to book."""
        return self._j["accessInfo"]["webReaderLink"]

    @property
    def title(self) -> str:
        """Get link to book."""
        return self._j["volumeInfo"]["title"]

    @property
    def pages(self) -> int:
        """Get number of pages."""
        return self._j["volumeInfo"]["pageCount"]

    @property
    def current_page(self) -> int:
        """Get current page."""
        try:
            return int(self._j["userInfo"]["readingPosition"]["pdfPosition"].split(",")[1][:-1])
        except KeyError:
            return 0

    @property
    def portion_read(self) -> float:
        """Return what portion of the book is read."""
        return self.current_page / self.pages

    def __repr__(self):
        """Return representation."""
        return f"Book({self.title}, {self.portion_read})"


def get_books(id=7):
    r = _access_api(f"mylibrary/bookshelves/{id}/volumes").json()
    if not "items" in r.keys():
        return []
    return [Book(x) for x in r["items"]]


def _access_api(url):
    creds.refresh_token
    return requests.get(
        'https://www.googleapis.com/books/v1/' + url,
        headers={'Authorization': 'Bearer %s' % creds.token})


creds = googleapi.get_service('books', "v1", True)

if __name__ == '__main__':
    for x in _access_api('mylibrary/bookshelves').json()["items"]:
        print(x["title"], x["id"], (x["volumeCount"] if "volumeCount" in x.keys() else ""), get_books(x["id"]))
