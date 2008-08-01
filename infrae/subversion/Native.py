# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

from pysvn import wc_status_kind, opt_revision_kind, wc_notify_action
import pysvn

from sets import Set            # For python 2.3 compatibility
import os, os.path
import re

def createSVNClient(recipe):
    """Create a pysvn client, and setup some callback and options.
    """

    def callback_ssl(info):
        print "-------- SECURITY WARNING --------"
        print "There is no valid SSL certificat for %s." % info['realm']
        print "Check that the files are correct after being fetched."
        print "-------- SECURITY WARNING --------"
        return True, 0, False

    def callback_notify(info):
        if info['action'] == wc_notify_action.update_completed:
            path = info['path']
            recipe._updateRevisionInformation(path, recipe.urls[path], info['revision'])

    client = pysvn.Client()
    client.set_interactive(True)
    client.callback_ssl_server_trust_prompt = callback_ssl
    if not (recipe is None):
        client.callback_notify = callback_notify
    return client


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


class Recipe(object):
    """infrae.subversion recipe.
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

        self.client = createSVNClient(self)
        self.verbose = buildout['buildout'].get('verbosity', 0)
        self._updateAllRevisionInformation()
        self._exportInformationToOptions()


    def _exportInformationToOptions(self):
        """Export revision and changed information to options.

        Options can only contains strings.
        """
        self.options['updated'] = '\n'.join(self.updated)
        str_revisions = ['%s %s' % r for r in self.revisions.items() if r[1]]
        self.options['revisions'] = '\n'.join(str_revisions)


    def _updateAllRevisionInformation(self):
        """Update all revision information for defined urls.
        """
        for path, link in self.urls.items():
            if os.path.exists(path):
                self._updateRevisionInformation(link, path)


    def _updateRevisionInformation(self, link, path, revision=None):
        """Update revision information on a path.
        """
        if revision is None:
            info = self.client.info(path)
            revision = info['revision']

        assert (revision.kind == opt_revision_kind.number)

        old_revision = self.revisions.get(link, None)
        self.revisions[link] = revision.number
        if not (old_revision is None):
            self.updated.append(link)


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
            self.client.update(path)
            
        self._exportInformationToOptions()
        return self.location

    def _parseRevisionInUrl(self, url):
        """Parse URL to extract revision number. This is not done by
        pysvn, so we have to do it by ourself.
        """
        num_release = re.compile('(.*)@([0-9]+)$')
        match = num_release.match(url)
        if match:
            return (match.group(1),
                    pysvn.Revision(opt_revision_kind.number,
                                   int(match.group(2))))
        return (url, pysvn.Revision(opt_revision_kind.head))


    def _installPath(self, link, path):
        """Checkout a single entry.
        """
        if self.verbose:
            print "%s %s to %s" % (self.export and 'Export' or 'Fetch',
                                   link, path)
            
        link, wanted_revision = self._parseRevisionInUrl(link)
        if self.export:
            method = self.client.export
        else:
            method = self.client.checkout
        method(link, path, revision=wanted_revision, recurse=True)


    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """

        for path, link in self.urls.items():
            self._installPath(link, path)

        self._exportInformationToOptions()
        return self.location


def uninstall(name, options):
    r"""
    This is an uninstallation hook for the 'infrae.subversion' recipe.

    Its only job is to raise an exception when there are changes in a
    subversion tree that a user might not want to lose.  This function
    does *not* delete or otherwise touch any files.

    The location of the path is passed as options['location'].
    """
    if bool(options.get('export', False)):
        return                  # SVN Export, there is nothing to check.

    if bool(options.get('ignore_verification', False)):
        return                  # Verification disabled.

    # XXX This makes the assumption that we're in the buildout
    #     directory and that our part is in 'parts'.  We don't have
    #     options['buildout'] available so no
    #     'buildout:parts-directory'.
    location = options.get('location', os.path.join('.', 'parts', name))
    urls = prepareURLs(location, options['urls'])
    client = createSVNClient(None)

    bad_svn_status = [wc_status_kind.modified, 
                      wc_status_kind.missing,
                      wc_status_kind.unversioned, ]

    if not checkExistPath(location):
        return

    current_paths = Set([os.path.join(location, s) for s in os.listdir(location)])
    recipe_paths = Set(urls.keys())
    added_paths = current_paths.difference(recipe_paths)
    if added_paths:
        msg = "New path have been added to the location: %s."
        raise ValueError(msg, ', '.join(added_paths))

    for path in urls.keys():
        if not checkExistPath(path):
            continue

        badfiles = filter(lambda e: e['text_status'] in bad_svn_status, 
                          client.status(path))
    
        if badfiles:
            raise ValueError("""\
In '%s':
local modifications detected while uninstalling %r: Uninstall aborted!

Please check for local modifications and make sure these are checked
in.

If you sure that these modifications can be ignored, remove the
checkout manually:

  rm -rf %s

Or if applicable, add the file to the 'svn:ignore' property of the
file's container directory.  Alternatively, add an ignore glob pattern
to your subversion client's 'global-ignores' configuration variable.
""" % (path, name, """
  rm -rf """.join([file['path'] for file in badfiles])))


