import os
import opml
import json
import feedparser
from requests import get as req_get
from pathlib import Path
from item_widgets import PodcastDetails


class LibGrabber:
    def __init__(self):
        # create podcasts dictionary
        self.raw_data = {}
        self.feeds = []
        self.links = []
        # create images directory
        self.img_dir = "imgs"
        try:
            os.mkdir(self.img_dir)
        except FileExistsError:
            pass
        except IOError:
            print("Error creating images directory 'imgs'.")

    def load_lib(self):
        self.feeds = []
        with open('podcasts.json', 'r') as f:
            self.raw_data = json.load(f)
        for pid in self.raw_data.keys():
            title = self.raw_data[pid]['details']['title']
            url = self.raw_data[pid]['details']['xmlUrl']
            summary = self.raw_data[pid]['details']['summary']
            # image = raw_data[podcast]['details']['image']
            image = os.path.join('imgs', 'default.png')
            self.feeds.append(PodcastDetails(pid, title, url, summary, image))

    @staticmethod
    def load_opml(f="backup.opml"):         # Confirmed WORKING
        # read podcast URL list from OPML
        if Path(f).is_file():
            outline = opml.parse(f)
            rss_links_from_opml = [a.xmlUrl for a in outline]
            return rss_links_from_opml
        return []

    def save_img(self, url, title, folder=None):
        img = req_get(url).content
        if img:
            path = os.path.join(folder if folder else self.img_dir, f"{title}.png")
            if not os.path.exists(path):
                with open(path, "wb") as _:
                    _.write(img)
        return path

    @staticmethod
    def filename_friendly(unfriendly):
        # make title filename-friendly
        no_spaces = "-".join(unfriendly.split())
        friendly = "".join([c for c in no_spaces if c.isalpha() or c.isdigit() or c == "-"]).strip()
        return friendly

    def refresh_all(self, links):
        # clear raw data
        self.raw_data = {}
        # grab xml episode lists per URL
        print("start:", end="")
        for link in links:
            self.refresh_one(link)
            print(":", end="")
        print(":end")

    def refresh_one(self, link):
            # GRAB XML EPISODE LISTING FROM RSS
            data = feedparser.parse(link)
            # STORE PODCAST TITLE AND SUMMARY
            podcast_title = data.feed.get("title", "untitled")
            filesafe_title = self.filename_friendly(podcast_title)
            podcast_summary = data.feed.get("summary", "no summary")
            # ASSIGN A UNIQUE PODCAST ID
            pid = hash(link)
            # CREATE A DICTIONARY ENTRY
            self.raw_data[pid] = {'details': {}, 'episodes': []}
            # GRAB AND SAVE PODCAST COVER IMAGE
            has_image = data.feed.get('image', False)
            img_url = None
            if has_image:
                img_url = data.feed.image.get('href', None)
                if img_url:
                    self.save_img(img_url, filesafe_title, 'imgs')
            # STORE PODCAST DETAILS
            self.raw_data[pid]['details']['image'] = img_url
            self.raw_data[pid]['details']['title'] = podcast_title
            self.raw_data[pid]['details']['summary'] = podcast_summary
            self.raw_data[pid]['details']['xmlUrl'] = link
            print(len(data.entries), end="")
            # STORE EPISODE DETAILS
            for i, ep in enumerate(data.entries):
                # look for audio link - not always labeled appropriately hence search by file extension
                episode_links = [link.get('href', "") for link in ep.links if ".mp3" in link.get('href', "")]
                episode_link = episode_links[0] if len(episode_links) > 0 else ""
                # create entry for podcast details
                episode_details = {'id': hash((link, ep)),
                                   'title': ep.get('title', None),
                                   'published': str(ep.get("published", None)),
                                   'published_parsed': str(ep.get("published_parsed", None)),
                                   'link': episode_link if episode_link else None,
                                   'summary': ep.summary if ep.get('summary', None) else None}
                # save details to dictionary
                self.raw_data[pid]['episodes'].append(episode_details)

    def save_lib(self):
        # SAVE PODCAST INFO TO JSON FILE
        with open("podcasts.json", "w") as f:
            json.dump(self.raw_data, f, indent=2)


if __name__ == "__main__":
    print("Creating LibGrabber Object")
    lib = LibGrabber()
    print("Loading from OPML backup")
    links = lib.load_opml()
    print("Refreshing links in active dictionary")
    lib.refresh_all(links)
    print("Saving to JSON file")
    lib.save_lib()
    print("Done.")