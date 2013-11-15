#
#
# ShapeBot -- Shapeways-specific fork of buildbotchat, monitors jenkins and provides status on hosts
#
#
# BuildBotChat
# Copyright (c) 2012 Mirko Nasato - All rights reserved.
# Licensed under the BSD 2-clause license; see LICENSE.txt
#
import platform
from time import sleep
from urllib import urlopen
from Skype4Py import Skype
from xml.etree import ElementTree
import urllib2, re


JENKINS_URL = 'http://jenkins.nyc.shapeways.net'
SKYPE_CHAT = "#shapeways.josh/$xjohnnywang;b1a361b9e7279468"
UPDATE_INTERVAL = 5  # seconds
MESSAGE_PREFIX = '[Jenkins] '


class Build:
    def __init__(self, attrs):
        self.name = attrs['name']
        self.number = attrs['lastBuildLabel']
        self.status = attrs['lastBuildStatus']

class BuildMonitor:
    whitelist = list()
    whitelist = ["Trunk Continuous Integration",
                 "Production Artifact Deploy"]

    def __init__(self, listener):
        self.builds = None
        self.listener = listener

    def loop(self):
        while True:
            try:
                self.listener.read_chat()
                self.check_for_new_builds()
            except IOError as e:
                print 'WARNING! update failed:', e.strerror
            sleep(UPDATE_INTERVAL)


    def check_for_new_builds(self):
        builds = self.fetch_builds()
        if self.builds is not None:
            for build in builds.values():
                name = build.name
                if name in self.whitelist:
                    print "Checking build " + name + " #" + build.number
                    if not self.builds.has_key(name):
                        print "Reporting on new build."
                        self.handle_new_build(build, None)
                    elif build.number != self.builds[name].number:
                        print "Reporting on existing build"
                        self.handle_new_build(build, self.builds[name].status)
        self.builds = builds


    def handle_new_build(self, build, old_status):
        transition = (old_status, build.status)
        if build.name == "Production Artifact Deploy":
            self.listener.determine_live_rev_and_notify()
        elif transition == ('Failure', 'Failure'):
            self.listener.notify(build, '(rain) Still Failing')
        elif transition == ('Failure', 'Success'):
            self.listener.notify(build, '(sun) Fixed')
        elif build.status == 'Failure':
            self.listener.notify(build, '(rain) Failed')


    def fetch_builds(self):
        builds = {}
        response = urlopen(JENKINS_URL + '/cc.xml')
        projects = ElementTree.parse(response).getroot()
        for project in projects.iter('Project'):
            build = Build(project.attrib)
            builds[build.name] = build
        return builds


class BuildNotifier:
    def __init__(self):
        if platform.system() == 'Windows':
            skype = Skype()
        else:
            skype = Skype(Transport='x11')
        skype.Attach()
        self.chat = skype.Chat(SKYPE_CHAT)
        self.recent_msg = None

    def notify(self, build, event):
        message = event + ': ' + build.name + ' - ' + JENKINS_URL + '/job/' + build.name + '/' + build.number + '/'
        print message
        self.chat.SendMessage(MESSAGE_PREFIX + message)

    def determine_live_rev_and_notify(self):
        response = urllib2.urlopen("http://www.shapeways.com/status")
        html = response.read()
        revision = re.search('www.(\d+)', html).group(1)

        message = "(party) We live son!  Revision is " + revision
        print message
        self.chat.SendMessage(MESSAGE_PREFIX + message)

    def determine_qa1_rev_and_notify(self):
        response = urllib2.urlopen("http://qa1.nyc.shapeways.net/status")
        html = response.read()
        revision = re.search('www.(\d+)', html).group(1)

        message = "The current QA1 revision is " + revision
        print message
        self.chat.SendMessage(MESSAGE_PREFIX + message)

    def determine_qa2_rev_and_notify(self):
        response = urllib2.urlopen("http://qa2.nyc.shapeways.net/status")
        html = response.read()
        revision = re.search('www.(\d+)', html).group(1)

        message = "The current QA2 revision is " + revision
        print message
        self.chat.SendMessage(MESSAGE_PREFIX + message)

    def read_chat(self):
        echoed1 = False
        echoed2 = False

        if self.recent_msg == None:
            self.recent_msg = list()
            for msg in self.chat.RecentMessages:
                self.recent_msg.append(msg)
                return

        for msg in self.chat.RecentMessages:
            if msg not in self.recent_msg:
                self.recent_msg.append(msg)
                print msg.Body
                if "qa1 revision" in msg.Body and echoed1 == False:
                    print "Dumping qa1 revision"
                    self.determine_qa1_rev_and_notify()
                    echoed1 = True
                elif "qa2 revision" in msg.Body and echoed2 == False:
                    print "Dumping qa2 revision"
                    self.determine_qa2_rev_and_notify()
                    echoed2 = True

        if len(self.recent_msg) > 100000:
            print "Purging message queue"
            self.recent_msg = list()
        print str(len(self.recent_msg)) + " msgs"


if __name__ == '__main__':
    try:
        BuildMonitor(BuildNotifier()).loop()
    except KeyboardInterrupt:
        pass

