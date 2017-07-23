#!/usr/bin/env python3

import sys
import re
import logging

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtWebKitWidgets import QWebView

from gogapi.token import Token, get_auth_url



logging.basicConfig()
log = logging.getLogger("embedauth")

LOGIN_CODE_RE = re.compile(r"code=([\w\-]+)")

class LoginBrowser:
    def __init__(self):
        self.webview = QWebView()

        self.webview.urlChanged.connect(self.handle_url_change)
        self.webview.load(QUrl(get_auth_url()))
        self.webview.show()

    def handle_url_change(self, url):
        log.debug("Handling url change to %s", url.toString())
        url_path = url.path()
        url_query = url.query()
        if not url_path.startswith("/on_login_success"):
            return

        log.debug("Detected on_login_success")
        query_match = LOGIN_CODE_RE.search(url_query)
        if query_match is not None:
            login_code = query_match.group(1)
            log.debug("Got login code %s", login_code)
            token = Token.from_code(login_code)
            filename, _ = QFileDialog.getSaveFileName(
                self.webview,
                caption="Save Login Token",
                filter="JSON (*.json)")
            if filename:
                if not filename.endswith(".json"):
                    filename += ".json"
                token.save(filename)
        else:
            log.error("Could not parse code from query: %s", url_query)

        self.webview.close()


app = QApplication(sys.argv)
browser = LoginBrowser()
app.exec_()
