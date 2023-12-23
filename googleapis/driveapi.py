from __future__ import annotations, print_function

import hashlib
import io
import os
import pathlib
import shutil

from googleapiclient.http import (MediaFileUpload, MediaInMemoryUpload,
                                  MediaIoBaseDownload)

from . import googleapi

FIELDS = 'id,name,mimeType,md5Checksum,parents,size'


class File:

    def push(self, path, remove_nonexisting=True, subfolders=None, hidden=True):
        if not self.is_dir:
            raise Exception("You can push or pull only from/to a dir")
        path = pathlib.Path(path)
        local, drive = os.listdir(path), self.get_folder_content(folders=True)

        if not subfolders is None:
            local = [x for x in local if x in subfolders]
        if not hidden:
            local = [x for x in local if not x.startswith(".")]
        for x in local:
            file_path = path / x
            corresponding_drive = [y for y in drive if y.name == x and y.is_dir == file_path.is_dir()]
            if file_path.is_dir():
                if len(corresponding_drive) == 1:
                    corresponding_drive[0].push(file_path, remove_nonexisting, hidden=hidden)
                elif remove_nonexisting or len(corresponding_drive) == 0:
                    for d in corresponding_drive:
                        d.remove()
                    self.upload(file_path, hidden=hidden)

            elif len(corresponding_drive) > 1:
                pass
            elif len(corresponding_drive) == 0:
                self.upload(file_path)
            else:
                drive_file = corresponding_drive[0]
                if drive_file.md5_check_sum != _md5_from_local_file(file_path):
                    drive_file.set_content_from_file(file_path)

        if remove_nonexisting and subfolders is None:
            for x in drive:
                if not x.name in local:
                    x.remove()

    def pull(self, path, remove_nonexisting=True, subfolders=None, hidden=True):
        if not self.is_dir:
            raise Exception("You can push or pull only from/to a dir")
        path = pathlib.Path(path)
        if not path.exists():
            os.makedirs(path)
        if not path.is_dir():
            raise Exception("Local path isn't dir")
        local, drive = os.listdir(path), self.get_folder_content(folders=True)
        checked = []

        if not subfolders is None:
            drive = [x for x in drive if x.name in subfolders]
        if not hidden:
            drive = [x for x in drive if not x.name.startswith('.')]
        for x in drive:
            checked.append(x.name)
            if x.is_dir and x.name in local:
                x.pull(path / x.name, remove_nonexisting)
            elif (x.is_gdoc):
                x.download(path)
            elif ((x.name in local) and (x.md5_check_sum != _md5_from_local_file(path / x.name))) or (not x.name in local):
                x.download(path)

        if remove_nonexisting:
            for x in local:
                if not x in checked:
                    if (path / x).is_dir():
                        shutil.rmtree(path / x)
                    else:
                        os.remove(path / x)

    def set_share(self, share: bool) -> None:
        """Set public sharing to `share`."""
        body = {"role": "reader", "type": "anyone"}
        drive_service().permissions().create(
            fileId=self.id,
            body=body
        ).execute()

    def __repr__(self):
        return f"File({self.name}, {self.id})"

    def __init__(self, ds_stuff):
        self.id = ds_stuff["id"]
        self.name = ds_stuff["name"]
        self.mime_type = ds_stuff["mimeType"]
        self.is_dir = self.mime_type == "application/vnd.google-apps.folder"
        self.is_gdoc = "application/vnd.google-apps" in self.mime_type and self.mime_type != "application/vnd.google-apps.folder"
        if not self.is_dir:
            self.md5_check_sum = ds_stuff["md5Checksum"] if "md5Checksum" in ds_stuff.keys() else ""
            self.size = int(ds_stuff["size"]) if "size" in ds_stuff.keys() else 0

        self.parents = ds_stuff["parents"]

    def remove(self):
        drive_service().files().delete(fileId=self.id).execute()

    def set_content(self, content, mt='application/octet-stream'):
        if isinstance(content, str):
            content = content.encode()
            mt = "text/plain"
        if len(content) == 0:
            media = None
        else:
            media = MediaInMemoryUpload(content, resumable=True, mimetype=mt)
        return drive_service().files().update(media_body=media,
                                              fileId=self.id,
                                              fields='id').execute()

    def upload(self, path, name=None, exclude_partial=False, hidden=True) -> File:
        if not self.is_dir:
            return None
        if name is None:
            name = pathlib.Path(path).name

        if os.path.exists(path) and os.path.isfile(path):
            if exclude_partial and (name.endswith(".crdownload") or name.endswith(".part") or name + ".part" in os.listdir(path.parent)):
                return
            if hidden and (name.startswith(".")):
                return

            with open(path, "rb") as f:
                empty = len(f.read(3)) == 0

            file_metadata = {'name': name,
                             'parents': [self.id]}
            if empty:
                media = None
            else:
                media = MediaFileUpload(path, resumable=True)

            x = drive_service().files().create(body=file_metadata,
                                                media_body=media,
                                                fields=FIELDS).execute()
            return File(x)

        elif os.path.exists(path) and os.path.isdir(path):
            f = self.create_folder(name)
            for x in os.listdir(path):
                if not x.startswith("."):
                    f.upload(str(pathlib.Path(path) / x), hidden=hidden)

            return f

    def download(self, folder_path):
        path = pathlib.Path(folder_path)
        if self.is_dir:
            path /= self.name
            if not path.exists():
                os.makedirs(path)
            for x in self.get_folder_content(folders=True):
                x.download(path)
        else:
            if self.mime_type == "application/vnd.google-apps.script":
                return False
            if self.is_gdoc:
                request = drive_service().files().export_media(fileId=self.id, mimeType='application/pdf')
            else:
                request = drive_service().files().get_media(fileId=self.id)

            if self.size == 0:
                with open(path / self.name, "w") as f:
                    f.write("")
                return True
            fh = io.FileIO(path / self.name, "wb")
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                _, done = downloader.next_chunk()

    def set_content_from_file(self, path):
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "rb") as f:
                empty = len(f.read(3)) == 0
            if empty:
                media = None
            else:
                media = MediaFileUpload(path, resumable=True)
            drive_service().files().update(media_body=media,
                                            fileId=self.id,
                                            fields='id').execute()

    def get_file_content(self, bts=False):
        b = drive_service().files().get_media(fileId=self.id).execute()
        if bts:
            return b
        try:
            return b.decode("utf-8")
        except:
            return b

    def rename(self, name):
        body = {"name": name}
        return drive_service().files().update(fileId=self.id, body=body).execute()

    def search_for_files(self, name):
        if not self.is_dir:
            return []
        page_token = None
        r = []
        while True:
            response = drive_service().files().list(q=f"name contains '{name}' and trashed = false and '{self.id}' in parents",
                                                    spaces='drive',
                                                    fields='nextPageToken, files(' + FIELDS + ')',
                                                    pageToken=page_token).execute()
            for file in response.get('files', []):
                r.append(File(file))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return r

    def get_folder_content(self, folders=False):
        if not folders:
            mt = " and mimeType != 'application/vnd.google-apps.folder'"
        else:
            mt = ""
        q = f"'{self.id}' in parents and trashed = false" + mt

        page_token = None
        r = []
        while True:
            response = drive_service().files().list(q=q,
                                                    spaces='drive',
                                                    fields='nextPageToken, files(' + FIELDS + ')',
                                                    pageToken=page_token).execute()
            for file in response.get('files', []):
                r.append(File(file))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return r

    def clear_folder(self):
        for x in self.get_folder_content(True):
            x.remove()

    def get_or_create(self, name, folder=False):
        files = self.search_for_files(name)
        if len(files) and (files[0].is_dir or folder == False):
            return files[0]
        if folder:
            return self.create_folder(name)
        return self.create_file(name)

    def move_to(self, folder, from_id=None):
        if from_id is None:
            from_id = self.parent.id
        drive_service().files().update(fileId=self.id, addParents=folder.id, removeParents=from_id).execute()

    def move_contents_to(self, folder, folders=False):
        for file in self.get_folder_content(folders=folders):
            file.move_to(folder, self.id)

    def create_file(self, name, mime_type="text/plain"):
        file_metadata = {
            'name': name,
            'mimeType': mime_type,
            'parents': [self.id]
        }
        return File(drive_service().files().create(body=file_metadata, fields=FIELDS).execute())

    def create_folder(self, name):
        return self.create_file(name, "application/vnd.google-apps.folder")

    @property
    def parent(self):
        return get_file(self.parents[0])

    @property
    def link(self):
        return "https://drive.google.com/open?id=" + self.id


def search_for_files(name):
    page_token = None
    r = []
    while True:
        response = drive_service().files().list(q=f"name contains '{name}' and trashed = false",
                                                spaces='drive',
                                                fields='nextPageToken, files(' + FIELDS + ')',
                                                pageToken=page_token).execute()
        for file in response.get('files', []):
            r.append(File(file))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return r


def get_file(id: str) -> File:
    try:
        return File(drive_service().files().get(fileId=id, fields=FIELDS).execute())
    except:
        return None


def _md5_from_local_file(path):
    r = hashlib.md5()
    with open(path, "rb") as f:
        block_size = 128 * r.block_size
        while piece := f.read(block_size):
            r.update(piece)

    return r.hexdigest()


drive_service = googleapi.Service('drive')
