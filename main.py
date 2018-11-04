# TODO Switch to QLIstView & QListViewItem
# TODO Implement itemWidgets (with hidden columns to aid sorting?)
# TODO Remove user control of sorting - this will likely be unused

# custom classes
from libgrabber import LibGrabber
from item_widgets import PodcastItemWidget, EpisodeItemWidget, PodcastDetails, EpisodeDetails
from settings import SettingsDialog
from opml_rw import OpmlRW
# multimedia
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
# gui
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QWidget, QListWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from PyQt5.Qt import QUrl
# system
from datetime import datetime
import sys
import os


class CustomQWidget(QWidget):
    def __init__(self, parent=None):
        super(CustomQWidget, self).__init__(parent)

        label = QLabel("I am a custom widget")

        button = QPushButton("A useless button")

        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)

        self.setLayout(layout)


class MainWindow(QWidget):
    """Main player window"""
    def __init__(self):
        super().__init__()
        # UI
        self.ui = uic.loadUi("nobs_ui.ui", self)
        self.ui.setWindowTitle("NOBS Player")
        self.settings_dialog = SettingsDialog(self)
        self.settings = self.settings_dialog.settings
        # Variables
        self.sort_ascending = False
        # Library object
        self.lib = LibGrabber()
        self.lib.load_lib()
        # Player object
        self.player = QMediaPlayer()
        self.main_playlist = QMediaPlaylist()
        # Setup
        self.connect_slots()
        self.populate_podcast_list()
        self.view_all_episodes()
        # Go!
        self.show()

    def connect_slots(self):
        """Connect controls and events to functions"""
        # Events
        self.player.positionChanged.connect(self.show_position)
        self.player.stateChanged.connect(self.state_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.ui.lstSubs.itemDoubleClicked.connect(self.view_episodes)
        self.ui.lstEps.itemDoubleClicked.connect(self.play_episode)
        self.ui.lstAllEps.itemDoubleClicked.connect(self.play_episode)
        # Controls
        self.ui.sldVolume.sliderMoved.connect(self.volume_changed)
        self.sldProgress.sliderMoved.connect(self.seek)
        self.btnPlayPause.clicked.connect(self.play_pause)
        self.btnFwd.clicked.connect(self.fwd)
        self.btnRwd.clicked.connect(self.rwd)
        self.btnSortEps.clicked.connect(self.sort_episodes)
        self.ui.btnSettings.clicked.connect(self.settings_dialog.show)
        self.ui.btnAddRss.clicked.connect(self.add_rss)
        self.ui.txtSubFilter.textChanged.connect(lambda: self.filter_sub(self.ui.lstSubs, self.ui.txtSubFilter.text()))
        self.ui.txtEpFilter.textChanged.connect(lambda: self.filter_sub(self.ui.lstEps, self.ui.txtEpFilter.text()))
        self.ui.txtAllEpFilter.textChanged.connect(lambda: self.filter_sub(self.ui.lstAllEps, self.ui.txtAllEpFilter.text()))

    def filter_sub(self, lst, filter_text):
        for i in range(lst.count()):
            item = lst.item(i)
            if filter_text:
                item.setHidden(not filter_text.lower() in item.text().lower())
            else:
                item.setHidden(False)

    # Media Buffering doesn't seem to want to play.
    def media_status_changed(self, media_status):
        pass
        # if media_status == QMediaPlayer.bufferStatusChanged():
        #     self.ui.lblBuffering.setText("Buffering")
        # else:
        #     self.ui.lblBuffering.setText("")

    def add_rss(self, _):
        url = self.ui.txtRssUrl.text()
        print(url)
        pass

    def sort_episodes(self):
        """Switch episode listing between ascending and descending list sort - is this even useful?"""
        # Current setting
        if self.sort_ascending:
            self.lstEps.sortItems(Qt.DescendingOrder)
            # toggle both the sort flag and the sort button icon
            self.sort_ascending = False
            self.btnSortEps.setIcon(QIcon(os.path.join("ui", "sort-ascending.png")))
        else:
            self.lstEps.sortItems(Qt.AscendingOrder)
            # toggle both the sort flag and the sort button icon
            self.sort_ascending = True
            self.btnSortEps.setIcon(QIcon(os.path.join("ui", "sort-descending.png")))

    def volume_changed(self, value):
        """Set volume and UI effects when volume slider is moved"""
        # Set player volume accordingly
        self.player.setVolume(value)
        # Set label to display volume level text
        self.ui.lblVolValue.setText(str(value))
        # Alter volume label image according to volume level
        if value == 0:
            self.ui.lblVolume.setPixmap(QPixmap(os.path.join('ui', 'mute_red.png')))
        elif 0 < value <= 33:
            self.ui.lblVolume.setPixmap(QPixmap(os.path.join('ui', 'volume1.png')))
        elif 33 < value <= 66:
            self.ui.lblVolume.setPixmap(QPixmap(os.path.join('ui', 'volume2.png')))
        elif 66 < value:
            self.ui.lblVolume.setPixmap(QPixmap(os.path.join('ui', 'volume3.png')))

    def populate_podcast_list(self):
        """List the podcasts themselves"""
        for feed in self.lib.feeds:
            if len(self.lib.raw_data[feed.pid]['episodes']) > 0:
                # Create new item with feed as data
                item = QListWidgetItem(self.ui.lstSubs)
                item.setData(Qt.UserRole, feed)
                item.setText(feed.title)
                # Add item to list
                self.ui.lstSubs.addItem(item)
                self.ui.lstSubs.update()
                self.ui.lstSubs.sortItems(Qt.AscendingOrder)

    def view_episodes(self, feed_item, clear: bool = True):
        """List the episodes associated with the current podcast item"""
        # Look up podcast dictionary in read JSON data
        print("Getting episode listing...")
        episodes = self.lib.raw_data[feed_item.data(Qt.UserRole).pid]['episodes']
        print("...done")
        print("Getting podcast title...")
        podcast_title = self.lib.raw_data[feed_item.data(Qt.UserRole).pid]['details'].get('title', "None")
        print("...done")
        # Switch to episode tab, display podcast title
        self.ui.tabWidget.setCurrentWidget(self.ui.tabEps)
        self.ui.lblCurrentShowTitle.setText(podcast_title)
        # Clear list for displaying one feed only
        if clear:
            self.ui.lstEps.clear()
        # Check how many to list (EPF = -1 means no restriction)
        if len(episodes) == 0:
            return

        eps_per_feed = self.settings['eps_per_feed']
        if eps_per_feed != -1:
            max_count = eps_per_feed
        print("set eps per feed")
        # Loop to max episode count OR to end of episode list
        ep_count = 0
        while ep_count < max_count:
            print(f"Count: {ep_count}")
            # Create new list item
            item = QListWidgetItem(self.ui.lstEps)
            item.setFlags(item.flags()|Qt.ItemIsUserCheckable)
            # Grab episode data
            episode = episodes[ep_count]
            title = episode.get('title', None)
            url = episode.get('link', None)
            published = episode.get('published', None)
            summary = episode.get('summary', None)
            # Parse date
            dt = self.extract_date(published) if published else None
            if dt:
                item.setText(
                    f"{dt.year}/{dt.month:02}/{dt.day:02} {dt.hour:02}:{dt.minute:02} | {episode.get('title', None)}")
            else:
                item.setText(episode.get("title", None))
            # Store data in named tuple, set as item data
            details = EpisodeDetails(podcast_title, title, url, summary, published, 0, 0)
            item.setData(Qt.UserRole, details)
            # Add item to list
            fp = os.path.join("imgs", self.lib.filename_friendly(podcast_title)+".png")
            self.ui.lstEps.addItem(item)
            ep_count += 1
        # Finally sort the items
        self.ui.lstEps.sortItems(Qt.DescendingOrder)

    @staticmethod
    def extract_date(date_string: str) -> datetime:
        """This was a pain in the hole"""
        # Anticipatory list of possible date formats to parse
        format_strings = ["%a, %d %b %Y %H:%M:%S %z",  # Tue, 22 Sep 2009 17:32:28 -0000
                          "%a, %d %b %Y %H:%M:%S %Z",  # Tue, 22 Sep 2009 17:32:28 GMT
                          "%d %b %Y %H:%M:%S %z",  # 22 Sep 2009 17:32:28 -0000
                          "%d %b %Y %H:%M:%S %Z",  # 22 Sep 2009 17:32:28 GMT
                          "%a, %d %b %Y %H:%M:%S",  # Tue, 22 Sep 2009 17:32:28
                          "%d %b %Y %H:%M:%S"]  # 22 Sep 2009 17:32:28
        # Attempt date parsing (I should really pay more attention to the exceptions)
        dt = None
        for format_string in format_strings:
            try:
                dt = datetime.strptime(date_string, format_string)
            except Exception as e:
                print(f"Error  parsing date:\n{date_string}\nError: {e}\n")
            if dt:
                return dt

    def view_all_episodes(self):  # Not up to date - rewrite to match code in view_episodes()
        """Populate the 'all episodes' tab.  This may end up being the only episodes tab"""
        for podcast in self.lib.feeds:
            podcast_title = self.lib.raw_data[podcast.pid]['details']['title']
            for episode in self.lib.raw_data[podcast.pid]['episodes']:
                # Create item
                item = QListWidgetItem(self.ui.lstAllEps)
                # Grab details
                title = episode.get('title', None)
                url = episode.get('link', None)
                published = episode.get('published', None)
                summary = episode.get('summary', None)
                # Date
                dt = self.extract_date(published) if published else None
                if dt:
                    item.setText(
                        f"{dt.year}/{dt.month:02}/{dt.day:02} {dt.hour:02}:{dt.minute:02} \
                        | {podcast_title} - {episode.get('title', None)}")
                else:
                    item.setText(f"0 -NO DATE- | {podcast_title} - {episode.get('title', None)}")
                # Store details in named tuple, set as item data
                details = EpisodeDetails(podcast.title, title, url, summary, published, 0, 0)
                item.setData(Qt.UserRole, details)
                # Add item to list
                self.ui.lstEps.addItem(item)
        self.ui.lstAllEps.sortItems(Qt.DescendingOrder)

    def play_episode(self, item):
        """Load file into media object, put it in a playlist object, send it around the world..."""
        # Load the track info named tuple from the item
        data = item.data(Qt.UserRole)
        # Create media object from URL
        track = QMediaContent(QUrl(data.url))
        # Get relevant date-time info
        date_string = " ".join(data.datetime.split()[:4])
        # Display track info
        self.ui.lblDate.setText(f"Published: {date_string}")
        self.ui.lblCurrentPodTitle.setText(data.podcast)
        self.ui.lblCurrentEpTitle.setText(data.title)
        # Actually play the thing
        self.main_playlist.clear()
        self.main_playlist.addMedia(track)
        self.player.setPlaylist(self.main_playlist)
        self.player.play()

    def show_position(self, position):
        """Displays values of track duration and progress, advances progress slider"""
        duration = self.player.duration()
        if duration == 0:
            self.ui.lblDuration.setText("Duration: please wait...")
        elif duration > 0:
            self.ui.sldProgress.setMaximum(duration)
            self.ui.sldProgress.setValue(position)
            # Calculate hours
            position_hours = (position // 3600000) % 60
            duration_hours = (duration // 3600000) % 60
            # minutes
            duration_minutes = (duration // 60000) % 60
            position_minutes = (position // 60000) % 60
            # and seconds
            position_seconds = (position // 1000) % 60
            duration_seconds = (duration // 1000) % 60
            # Assemble display strings
            position_string = f"{position_hours:02}:{position_minutes:02}:{position_seconds:02}"
            duration_string = f"{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}"
            # Display values
            self.ui.lblProgress.setText(f"{position_string}")
            self.ui.lblDuration.setText(f"Duration: {duration_string}")

    def state_changed(self, state):
        """Displays playing/paused/stopped state"""
        if state == QMediaPlayer.PlayingState:
            self.ui.btnPlayPause.setIcon(QIcon(os.path.join('ui', 'pause.png')))
            self.ui.lblPlayerState.setText('Playing')
        elif state == QMediaPlayer.PausedState:
            self.ui.btnPlayPause.setIcon(QIcon(os.path.join('ui', 'play.png')))
            self.ui.lblPlayerState.setText('Paused')
        elif state == QMediaPlayer.StoppedState:
            self.ui.lblPlayerState.setText('Stopped')

    def seek(self, position):
        """Seeks track to given position"""
        self.player.setPosition(position)

    def play_pause(self, _):
        """Toggle play/pause state"""
        if self.player.state() == self.player.PlayingState:
            self.player.pause()
        elif self.player.state() == self.player.PausedState:
            self.player.play()

    def fwd(self):
        """Skip forward by set amount (default 15 seconds)"""
        if self.player.state() == self.player.PlayingState:
            self.player.setPosition(self.player.position() + self.settings['skip_amount'])
            self.player.play()

    def rwd(self):
        """Skip backward by set amount"""
        if self.player.state() == self.player.PlayingState:
            self.player.setPosition(self.player.position() - self.settings['skip_amount'])
            self.player.play()

# Start
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())
