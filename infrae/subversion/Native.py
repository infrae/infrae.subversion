# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

from pysvn import wc_status_kind
import pysvn

import os, os.path
import re

def createSVNClient():
    """Create a pysvn client, and setup some callback and options.
    """

    def callback_ssl(info):
        print "-------- SECURITY WARNING --------"
        print "There is no valid SSL certificat for %s." % info['realm']
        print "Check that the files are correct after being fetched."
        print "-------- SECURITY WARNING --------"
        return True, 0, False

    client = pysvn.Client()
    client.set_interactive(True)
    client.callback_ssl_server_trust_prompt = callback_ssl

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


class Recipe:
    """infrae.subversion recipe.
    """

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        
        options['location'] = self.location = os.path.join(
            buildout['buildout']['parts-directory'], self.name)
        self.urls = [l.split()
                     for l in options['urls'].splitlines()
                     if l.strip()]
        self.export = options.get('export')
        self.newest = (
            buildout['buildout'].get('offline', 'false') == 'false'
            and
            buildout['buildout'].get('newest', 'true') == 'true'
            )

        self.client = createSVNClient()
        self.verbose = buildout['buildout'].get('verbosity', 0)

    def update(self):
        """Update the checkouts.

        Does nothing if buildout is in offline mode.
        """
        if not self.newest:
            return self.location

        ignore = self.options.get('ignore_updates', False) or self.export

        num_release = re.compile('.*@[0-9]+$')
        for link, sub_path in self.urls:
            path = os.path.join(self.location, sub_path)
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
            
        return self.location

    def _parseRevisionInUrl(self, url):
        """Parse URL to extract revision number. This is not done by
        pysvn, so we have to do it by ourself.
        """
        num_release = re.compile('(.*)@([0-9]+)$')
        match = num_release.match(url)
        if match:
            return (match.group(1),
                    pysvn.Revision(pysvn.opt_revision_kind.number,
                                   int(match.group(2))))
        return (url, pysvn.Revision(pysvn.opt_revision_kind.head))


    def _installPath(self, link, path):
        """Checkout a single entry.
        """
        if self.verbose:
            print "%s %s to %s" % (self.export and 'Export' or 'Fetch',
                                   link, path)
            
        link, revision = self._parseRevisionInUrl(link)
        if self.export:
            self.client.export(link, path, revision=revision, recurse=True)
        else:
            self.client.checkout(link, path, revision=revision, recurse=True)


    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """

        for link, sub_path in self.urls:
            path = os.path.join(self.location, sub_path)
            self._installPath(link, path)

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
    
    client = createSVNClient()

    bad_svn_status = [wc_status_kind.modified, 
                      wc_status_kind.missing,
                      wc_status_kind.unversioned, ]

    if not checkExistPath(location):
        return

    for sub_path in os.listdir(location):
        path = os.path.join(location, sub_path)
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


