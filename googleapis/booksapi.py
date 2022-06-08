from . import googleapi
import requests

class Book:

    def __init__(self, j):
        self.link = j["accessInfo"]["webReaderLink"]
        self.title = j["volumeInfo"]["title"]

    def __repr__(self):
        return f"Book({self.title})"

def get_books(id=7):
    r = _access_api(f"mylibrary/bookshelves/{id}/volumes").json()
    if not "items" in r.keys():return []
    return [Book(x) for x in r["items"]]

def _access_api(url):
    creds.refresh_token
    return requests.get(
        'https://www.googleapis.com/books/v1/' + url,
        headers={'Authorization': 'Bearer %s' % creds.token})

creds = googleapi.get_service('books', "v1", True)

if __name__ == '__main__':
    for x in _access_api('mylibrary/bookshelves').json()["items"]:print(x["title"], x["id"], (x["volumeCount"] if "volumeCount" in x.keys() else ""), get_books(x["id"]))
