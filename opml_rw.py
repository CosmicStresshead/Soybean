import sys
import opml
from datetime import datetime


class OpmlRW:
    """
    Parses and stores links to and from OPML files
    Constructor takes a filename
    """
    def __init__(self, filename: str):
        self.list = []
        self.filename = filename
        self.header = ("""<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
  <opml version='2.0'>
    <head>
      <dateCreated>
        {0}
      </dateCreated>
    </head>
    <body>
""")
        self.outline = "      <outline xmlUrl='{0}' />\n"  # use .format() method to include url
        self.footer = "    </body>\n  </opml>"

    def read(self):
        """
        reads and parses OPML file (set by constructor)
        """
        data = opml.parse(self.filename)
        for _ in data:
            self.list.append(_.xmlUrl)

    def write(self, links: list = None):
        if not links:
            links = self.list
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.list:
            try:
                with open("backup.opml", "w") as opml_file:
                    opml_file.write(self.header.format(now))
                    for link in links:
                        opml_file.write(self.outline.format(link))
                    opml_file.write(self.footer)
                    return True
            except PermissionError:
                print(f"Permission denied while writing file: {e}")
                return False
            except:
                print(f"Unanticipated error: {sys.exc_info()[0]}\nPlease report this bug to bugs@bensmylie.com!")

    def getlist(self) -> list:
        return self.list

    def add(self, links: list):
        self.list.extend(links)

    def clear(self):
        self.list = []


if __name__ == "__main__":
    w = OpmlRW("backup.opml")
    w.read()
    print(w.getlist())
    w.write()
