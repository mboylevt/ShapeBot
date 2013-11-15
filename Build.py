"""
Build class
"""
class Build:
    def __init__(self, attrs):
        self.name = attrs['name']
        self.number = attrs['lastBuildLabel']
        self.status = attrs['lastBuildStatus']
