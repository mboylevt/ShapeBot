"""

BuildNotifier

BuildBotChat
Copyright (c) 2012 Mirko Nasato - All rights reserved.
Licensed under
 the BSD 2-clause license; see LICENSE.txt
"""
import platform
from Skype4Py import Skype
import urllib2, re
import Config

__author__ = 'mboylevt'

class BuildNotifier:

    REVISION_REPORT = 1
    BEER = 2
    chat_listen = {
        REVISION_REPORT: "revision",
        BEER: "(beer)",
    }
    sites_monitored = {
        "qa1":    "http://qa1.nyc.shapeways.net",
        "qa2":    "http://qa2.nyc.shapeways.net",
        "live":   "http://www.shapeways.com",
        "beta":   "http://beta.shapeways.com",
    }

    def __init__(self):
        if platform.system() == 'Windows':
            skype = Skype()
        else:
            skype = Skype(Transport='x11')
        skype.Attach()
        self.chat = skype.Chat(Config.SKYPE_CHAT)
        self.recent_msg = None

    def notify(self, build, event):
        message = event + ': ' + build.name + ' - ' + Config.JENKINS_URL + '/job/' + build.name + '/' + build.number + '/'
        print message
        self.chat.SendMessage(Config.MESSAGE_PREFIX + message)

    def determine_rev_and_notify(self, message):
        locale = None
        match_mid = re.search(" (.*) (.*?) revision", message)
        if match_mid:
            locale = match_mid.group(2)
        else:
            match_start = re.search("^(.*?) revision", message)
            if match_start:
                locale = match_start.group(1)

        if locale is None:
            print "Match not found"
            return

        locale = locale.lower()
        if locale in self.sites_monitored.keys():
            response = urllib2.urlopen(self.sites_monitored[locale] + "/status")
            html = response.read()
            revision = re.search('www.(\d+)', html).group(1)

            message = "The current {locale} version is {rev}".format(locale=locale, rev=revision)
            print message
            self.chat.SendMessage(Config.MESSAGE_PREFIX + message)


    def read_chat(self):

        if self.recent_msg is None:
            print "Initializing recent messages"
            self.recent_msg = list()
            for msg in self.chat.RecentMessages:
                print "Appending message " + msg.Body
                self.recent_msg.append(msg)
            return
        else:
            for msg in self.chat.RecentMessages:
                if msg not in self.recent_msg:
                    self.recent_msg.append(msg)
                    print msg.Body
                    if Config.MESSAGE_PREFIX not in msg.Body:
                        if "revision" in msg.Body:
                            self.determine_rev_and_notify(msg.Body)
                        if "(beer)" in msg.Body:
                            self.chat.SendMessage(Config.MESSAGE_PREFIX + "Too much (beer) makes you (puke)")

        if len(self.recent_msg) > 100000:
            print "Purging message queue"
            self.recent_msg = list()
        print str(len(self.recent_msg)) + " msgs"