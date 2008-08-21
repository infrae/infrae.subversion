# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

import os.path
import re

def checkExistPath(path):
    """Check that a path exist.
    """
    status = os.path.exists(path)
    if not status:
        print "-------- WARNING --------"
        print "Directory %s have been removed." % os.path.abspath(path)
        print "Changes might be lost."
        print "-------- WARNING --------"
    return status


def prepareURLs(location, urls):
    """Given a list of urls/path, and a location, prepare a list of
    tuple with url, full path.
    """

    def prepareEntry(line):
        link, path = line.split()
        return os.path.join(location, path), link

    return dict([prepareEntry(l) for l in urls.splitlines() if l.strip()])


class BaseRecipe(object):
    """infrae.subversion recipe. Base class.
    """

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        
        options['location'] = self.location = os.path.join(
            buildout['buildout']['parts-directory'], self.name)
        self.revisions = {} # Store revision information for each link
        self.updated = []   # Store updated links
        self.urls = prepareURLs(self.location, options['urls'])
        self.export = options.get('export')
        self.newest = (
            buildout['buildout'].get('offline', 'false') == 'false'
            and
            buildout['buildout'].get('newest', 'true') == 'true'
            )
        self.verbose = buildout['buildout'].get('verbosity', 0)



    def _exportInformationToOptions(self):
        """Export revision and changed information to options.

        Options can only contains strings.
        """
        if self.options.get('export_info', False):
            self.options['updated'] = '\n'.join(self.updated)
            str_revisions = ['%s %s' % r for r in self.revisions.items() if r[1]]
            self.options['revisions'] = '\n'.join(sorted(str_revisions))


    def _updateAllRevisionInformation(self):
        """Update all revision information for defined urls.
        """
        for path, link in self.urls.items():
            if os.path.exists(path):
                self._updateRevisionInformation(link, path)


    def _updateRevisionInformation(self, link, revision):
        """Update revision information on a path.
        """
        old_revision = self.revisions.get(link, None)
        self.revisions[link] = revision
        if not (old_revision is None):
            self.updated.append(link)


    def _updatePath(self, link, path):
        """Update a single path.
        """
        raise NotImplementedError


    def update(self):
        """Update the checkouts.

        Does nothing if buildout is in offline mode.
        """
        if not self.newest:
            return self.location

        ignore = self.options.get('ignore_updates', False) or self.export

        num_release = re.compile('.*@[0-9]+$')
        for path, link in self.urls.items():
            if not checkExistPath(path):
                if self.verbose:
                    print "Entry %s deleted, checkout a new version ..." % link
                self._installPath(link, path)
                continue

            if ignore:
                continue
            
            if num_release.match(link):
                if self.verbose:
                    print "Given num release for %s, skipping." % link
                continue

            if self.verbose:
                print "Updating %s" % path
            self._updatePath(link, path)
            
        self._exportInformationToOptions()
        return self.location


    def _installPath(self, link, path):
        """Checkout a single entry.
        """
        raise NotImplementedError


    def _installPathVerbose(self, link, path):
        """Checkout a single entry with verbose.
        """
        if self.verbose:
            print "%s %s to %s" % (self.export and 'Export' or 'Fetch',
                                   link, path)
        self._installPath(link, path)
                                   

    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """

        for path, link in self.urls.items():
            self._installPathVerbose(link, path)

        self._exportInformationToOptions()
        return self.location


