# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

from pysvn import wc_status_kind, opt_revision_kind, wc_notify_action
import pysvn

from Common import BaseRecipe, checkExistPath, prepareURLs

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

class Recipe(BaseRecipe):
    """infrae.subversion recipe.
    """

    def __init__(self, buildout, name, options):
        super(Recipe, self).__init__(buildout, name, options)
        self.client = createSVNClient(self)
        self._updateAllRevisionInformation()
        self._exportInformationToOptions()


    def _updateRevisionInformation(self, link, path, revision=None):
        """Update revision information on a path.
        """
        if revision is None:
            info = self.client.info(path)
            revision = info['revision']

        assert (revision.kind == opt_revision_kind.number)
        super(Recipe, self)._updateRevisionInformation(link, revision.number)


    def _updatePath(self, link, path):
        """Update a single path.
        """
        self.client.update(path)


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
        link, wanted_revision = self._parseRevisionInUrl(link)
        if self.export:
            method = self.client.export
        else:
            method = self.client.checkout
        method(link, path, revision=wanted_revision, recurse=True)



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


