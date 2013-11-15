"""

ShapeBot -- Shapeways-specific fork of buildbotchat, monitors jenkins and provides status on hosts


BuildBotChat
Copyright (c) 2012 Mirko Nasato - All rights reserved.
Licensed under the BSD 2-clause license; see LICENSE.txt
"""

from BuildMonitor import BuildMonitor
from BuildNotifier import BuildNotifier

if __name__ == '__main__':
    try:
        BuildMonitor(BuildNotifier()).loop()
    except KeyboardInterrupt:
        pass

