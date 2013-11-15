"""

BuildMonitor


BuildBotChat
Copyright (c) 2012 Mirko Nasato - All rights reserved.
Licensed under the BSD 2-clause license; see LICENSE.txt
"""

__author__ = 'mboylevt'

from time import sleep
from urllib import urlopen
from xml.etree import ElementTree
from Build import Build
import Config


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
            sleep(Config.UPDATE_INTERVAL)


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
        response = urlopen(Config.JENKINS_URL + '/cc.xml')
        projects = ElementTree.parse(response).getroot()
        for project in projects.iter('Project'):
            build = Build(project.attrib)
            builds[build.name] = build
        return builds




