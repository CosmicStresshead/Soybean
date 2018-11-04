from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication
import sys
import json
from opml_rw import OpmlRW


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        # UI
        self.ui = uic.loadUi("nobs_settings.ui", self)
        # Variables
        self.settings = {}
        self.parent = parent
        # Setup
        self._read_settings()
        self.connect_slots()

    def backup_links(self):
        opml = OpmlRW()
        opml.write(self.parent.lib.links)
        pass

    def restore_from_backup(self):
        pass

    def connect_slots(self):
        self.ui.bbxSettings.accepted.connect(self.apply_settings)

    def get_settings(self):
        return self.settings

    def _read_settings(self):
        with open("settings.json", "r") as f:
            self.settings = json.load(f)
        self.ui.sbxEpsPerFeed.setValue(self.settings['eps_per_feed'])
        self.ui.sbxSkipAmount.setValue(self.settings['skip_amount'] // 1000)

    def write_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=2)

    def apply_settings(self):
        self.settings['eps_per_feed'] = self.ui.sbxEpsPerFeed.value()
        self.settings['skip_amount'] = self.ui.sbxSkipAmount.value() * 1000
        self.write_settings()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    d = SettingsDialog()
    d.show()
    sys.exit(app.exec_())
