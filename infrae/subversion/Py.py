# Copyright (c) 2007-2008 Infrae. All rights reserved.
# $Id$

import os
from sets import Set            # For python 2.3 compatibility

from Common import BaseRecipe, checkExistPath, prepareURLs

import py

class Recipe(BaseRecipe):
    """infrae.subversion recipe.
    """

    def __init__(self, buildout, name, options):
        super(Recipe, self).__init__(buildout, name, options)
        self._updateAllRevisionInformation()
        self._exportInformationToOptions()

    def _updateRevisionInformation(self, link, path):
        """Update revision information on a path.
        """
        if isinstance(path, str):
            path = py.path.svnwc(path)
            
        revision = path.status().rev
        super(Recipe, self)._updateRevisionInformation(link, revision)


    def _updatePath(self, link, path):
        """Update a single path.
        """
        wc = py.path.svnwc(path)
        wc.update()
        self._updateRevisionInformation(link, wc)


    def _installPath(self, link, path):
        """Checkout a single entry.
        """
        if self.export:
            raise NotImplementedError
        wc = py.path.svnwc(path)
        wc.checkout(link)
        self._updateRevisionInformation(link, wc)


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

        wc = py.path.svnwc(path)
        status = wc.status(rec=1)
        badfiles = [] + status.modified + status.incomplete + status.unknown
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
  rm -rf """.join([file.strpath for file in badfiles])))
