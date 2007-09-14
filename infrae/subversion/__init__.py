import os

class Recipe:

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        self.location = options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], self.name)
        self.urls = [l.split() for l in options['urls'].splitlines()
                     if l.strip()]
        
        self.export = eval(options.get('export', 'False').strip())
        self.newest = (
            buildout['buildout'].get('offline', 'false') == 'false'
            and
            buildout['buildout'].get('newest', 'true') == 'true'
            )

    def update(self):
        """Update the checkouts.

        Does nothing if buildout is in offline mode.
        """
        if not self.newest or self.export:
            return self.location
        assert os.system('svn up %s/*' % self.location) == 0

    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """
        for (url, name) in self.urls:
            assert os.system(
                'svn %s %s %s' % (
                self.export and 'export' or 'co',
                url,
                os.path.join(self.location, name))) == 0
        return self.location
