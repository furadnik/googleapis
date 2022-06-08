from __future__ import print_function
from . import googleapi
service = googleapi.get_service('youtube')

def search_vids(q):
    return [[item["snippet"]["title"], item["id"]["videoId"]] for item in service.search().list(q=q, part="snippet", type="video").execute()["items"]]

def get_vid_by_name(name):
    return search_vids(name)[0][1]

def get_name_by_id(id):
    its = service.videos().list(id=id, part="snippet").execute()["items"]
    return its[0]["snippet"]["title"]

def get_channel_id(username):
    if "youtu.be" in username or "/watch" in username:
        username = username.split("/")[-1].split("?")[-1].split("v=")[-1].split("&")[0]
        return service.videos().list(id=username, part="snippet").execute()["items"][0]["snippet"]["channelId"]
    username = username.replace('/featured', '').replace('/videos', '').replace('/playlists', '').replace('/community', '').replace('/channels', '').replace('/about', '').split('?')[0].split('/')[-1].strip()
    its = service.channels().list(part="id", forUsername=username).execute()
    if not "items" in its:return username
    return its["items"][0]["id"]

def is_livestream(id):
    vid = service.videos().list(id=id, part="snippet").execute()["items"][0]
    if (not "liveBroadcastContent" in vid["snippet"]) or vid["snippet"]["liveBroadcastContent"] != "upcoming":return False
    return True

def get_livestream_time(id):
    if not is_livestream(id):return None
    vid = service.videos().list(id=id, part="liveStreamingDetails").execute()["items"][0]
    date = vid["liveStreamingDetails"]["scheduledStartTime"] + " UTC"
    from datetime import datetime, timezone
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ %Z").replace(tzinfo=timezone.utc).astimezone(tz=None)

def add_vid_to_playlist(vid_id, playlist_id):
    service.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": vid_id}}}).execute()

def list_playlist(id, max_results=50):
    return service.playlistItems().list(part="contentDetails", playlistId=id, maxResults=max_results).execute()["items"]

def get_for_ytfollow(id):
    vid = service.videos().list(id=id, part="snippet").execute()["items"][0]
    return [vid["snippet"]["title"], ("liveBroadcastContent" in vid["snippet"]) and (vid["snippet"]["liveBroadcastContent"] == "upcoming")]
