import os
import sys

import py

class Recipe:

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        
        self.location = os.path.join(
            buildout['buildout']['parts-directory'], self.name)
        self.urls = [l.split()
                     for l in options['urls'].splitlines()
                     if l.strip()]
        
        self.newest = (
            buildout['buildout'].get('offline', 'false') == 'false'
            and
            buildout['buildout'].get('newest', 'true') == 'true'
            )

    def update(self):
        """Update the checkouts.

        Does nothing if buildout is in offline mode.
        """
        if not self.newest:
            return self.location
        part = py.path.local(self.location)
        for (url, name) in self.urls:
            wc = py.path.svnwc(self.location).join(name)
            wc.update()
        return self.location

    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """
        for (url, name) in self.urls:
            wc = py.path.svnwc(self.location).join(name)
            wc.checkout(url)
        return self.location

def uninstall(name, options):
    r"""
    This is an uninstallation hook for the 'infrae.subversion' recipe.

    Its only job is to raise an exception when there are changes in a
    subversion tree that a user might not want to lose.  This function
    does *not* delete or otherwise touch any files.

    The location of the path is passed as options['location'].
    
    Create an SVN repository to play with:
    
      >>> from py.__ import path
      >>> from py.__.path.svn.testing import svntestbase
      >>> repo, wc = svntestbase.getrepowc() # doctest: +ELLIPSIS
      created svn repository /.../basetestrepo
      checked out new repo into /.../wc

      created svn repository /.../repo
      checked out new repo into /.../wc

    To our SVN repository, we add a package and in that package we
    create a file called 'foo.py', which we immediately add:

      >>> package = wc.join('package').ensure(dir=True)
      >>> foo = wc.join('package/foo.py')
      >>> foo.write('print "foo"\n')
      >>> foo.add()

    We commit our 'foo.py' file and see that uninstall does *not*
    raise any exception:

      >>> rev1 = package.commit('testing')
      >>> uninstall('test', {'location': wc.strpath})
      >>> foo.read()
      'print "foo"\n'

      >>> bar = package.join('bar.py')
      >>> bar.write('print "bar"\n')
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      ValueError: In '.../package/bar.py':
      local modifications detected while uninstalling 'test': Uninstall aborted!
      ...

    'uninstall' shouldn't raise an exception if 'bar.py' is in the
    'svn:ignore' property:

      >>> package.propset('svn:ignore', 'bar.py')
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      >>> ignore = package.propdel('svn:ignore')

    If we were to put 'bar.py' into the 'svn:ingore' property, uninstall 

    Let's add 'bar.py'.  This should still fail, because 'bar.py'
    isn't committed yet:

      >>> bar.add()
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      ValueError: In '.../package/bar.py':
      local modifications detected while uninstalling 'test': Uninstall aborted!
      ...

    A committed 'bar.py' should work:
      
      >>> rev2 = package.commit()
      >>> rev2 == rev1 + 1
      True
      >>> uninstall('test', {'location': wc.strpath})

    A modified 'bar.py' should fail again:
    
      >>> bar.write('print "somethingelse"\n')
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      ValueError: In '.../package/bar.py':
      local modifications detected while uninstalling 'test': Uninstall aborted!
      ...

    If our location doesn't exist, nothing will happen:

      >>> uninstall('test', {'location': 'no way'})
    """
    # XXX This makes the assumption that we're in the buildout
    #     directory and that our part is in 'parts'.  We don't have
    #     options['buildout'] available so no
    #     'buildout:parts-directory'.
    location = options.get('location', os.path.join('.', 'parts', name))
    wc = py.path.svnwc(location)
    if not os.path.exists(wc.strpath):
        # The path doesn't exist anyway, nothing to preserve
        return
    
    for fpath in wc.visit():
        status = fpath.status()
        if not status.ignored:
            changed = fpath.check(versioned=False)
            changed = changed or not status.unchanged
            if changed:
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
""" % (fpath, name, wc.strpath))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
