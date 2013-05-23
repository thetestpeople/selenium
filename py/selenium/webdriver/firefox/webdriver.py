# Copyright 2008-2013 Software freedom conservancy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

import base64
import shutil
import sys
from .firefox_binary import FirefoxBinary
from selenium.common.exceptions import ErrorInResponseException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities 
from selenium.webdriver.firefox.extension_connection import ExtensionConnection
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webelement import WebElement

class WebDriver(RemoteWebDriver):

    # There is no native event support on Mac
    NATIVE_EVENTS_ALLOWED = sys.platform != "darwin"

    def __init__(self, firefox_profile=None, firefox_binary=None, timeout=30,
                 capabilities=None, proxy=None):

        self.binary = firefox_binary
        self.profile = firefox_profile

        if self.profile is None:
            self.profile = FirefoxProfile()
       
        self.profile.native_events_enabled = self.NATIVE_EVENTS_ALLOWED and self.profile.native_events_enabled

        if self.binary is None:
            self.binary = FirefoxBinary()

        if capabilities is None:
            capabilities = DesiredCapabilities.FIREFOX

        if proxy is not None:
            proxy.add_to_capabilities(capabilities)


        RemoteWebDriver.__init__(self,
            command_executor=ExtensionConnection("127.0.0.1", self.profile,
            self.binary, timeout),
            desired_capabilities=capabilities)
        self._is_remote = False

    def create_web_element(self, element_id):
        """Override from RemoteWebDriver to use firefox.WebElement."""
        return WebElement(self, element_id)

    def quit(self):
        """Quits the driver and close every associated window."""
        try:
            RemoteWebDriver.quit(self)
        except http_client.BadStatusLine:
            # Happens if Firefox shutsdown before we've read the response from
            # the socket.
            pass
        self.binary.kill()
        try:
            shutil.rmtree(self.profile.path)
            if self.profile.tempfolder is not None:
                shutil.rmtree(self.profile.tempfolder)
        except Exception as e:
            print(str(e))

    @property
    def firefox_profile(self):
        return self.profile

    def clear_cache(self):
        """
        Delete all cookies in the scope of the session.

        :Usage:
            driver.delete_all_cookies()
        """
        self.execute(Command.CLEAR_CACHE)
