# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

from sets import Set            # For python 2.3 compatibility
import os.path
import os
import re


import zc.buildout


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


def checkAddedPaths(location, urls):
    """Check that no path have been added to that location.
    """
    current_paths = Set([os.path.join(location, s) for s in
                         os.listdir(location)])
    recipe_paths = Set(urls.keys())
    added_paths = current_paths.difference(recipe_paths)
    if '.svn' in added_paths:
        added_paths.remove('.svn')
    if added_paths:
        msg = "New path have been added to the location: %s."
        raise ValueError(msg % ', '.join(added_paths))


def prepareURLs(location, urls):
    """Given a list of urls/path, and a location, prepare a list of
    tuple with url, full path.
    """

    def prepareEntry(line):
        link, path = line.split()
        return os.path.join(location, path), link

    return dict([prepareEntry(l) for l in urls.splitlines() if l.strip()])


def extractNames(urls):
    """Return just the target names of the urls (used for egg names)"""

    def extractName(line):
        link, name = line.split()
        return name

    return [extractName(line) for line in urls.splitlines() if line.strip()]


class BaseRecipe(object):
    """infrae.subversion recipe. Base class.
    """

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        # location is overridable if desired.
        location = options.get('location', None)
        if location:
            self.location = os.path.join(
                buildout['buildout']['directory'], location)
        else:
            self.location = os.path.join(
                buildout['buildout']['parts-directory'], self.name)
        options['location'] = self.location
        self.revisions = {} # Store revision information for each link
        self.updated = []   # Store updated links
        self.urls = prepareURLs(self.location, options['urls'])
        self.export = options.get('export')
        self.offline = buildout['buildout'].get('offline', 'false') == 'true'
        self.eggify = options.get('as_eggs', False)
        self.eggs = self.eggify and extractNames(options['urls']) or []
        self.newest = (
            not self.offline and
            buildout['buildout'].get('newest', 'true') == 'true'
            )
        self.verbose = buildout['buildout'].get('verbosity', 0)

    def _exportInformationToOptions(self):
        """Export revision and changed information to options.

        Options can only contains strings.
        """
        if self.options.get('export_info', False):
            self.options['updated'] = str('\n'.join(self.updated))
            str_revisions = ['%s %s' % r for r in self.revisions.items()
                             if r[1]]
            self.options['revisions'] = str('\n'.join(sorted(str_revisions)))
        # Always export egg list
        self.options['eggs'] = '\n'.join(sorted(self.eggs))

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

        if self.eggify:
            self._eggify()
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

    def _eggify(self):
        """Install everything as development eggs if eggs=true"""
        if self.eggify:
            target = self.buildout['buildout']['develop-eggs-directory']
            for path in self.urls.keys():
                zc.buildout.easy_install.develop(path, target)

    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """

        for path, link in self.urls.items():
            self._installPathVerbose(link, path)
        installed = [self.location]

        if self.eggify:
            self._eggify()
            # And also return the develop-eggs/*.egg-link files that are
            # ours so that an uninstall automatically zaps them.
            dev_dir = self.buildout['buildout']['develop-eggs-directory']
            egg_links = ['%s.egg-link' % egg for egg in self.eggs]
            egg_links = [os.path.join(dev_dir, link) for link in egg_links]
            installed += egg_links
        self._exportInformationToOptions()

        return installed
