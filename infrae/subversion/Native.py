
from pysvn import wc_status_kind
import pysvn

import os

class Recipe:

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

        self.client = pysvn.Client()
        self.client.set_interactive(True) # Let buildout ask for
                                          # password/for SSL
                                          # certificate

    def update(self):
        """Update the checkouts.

        Does nothing if buildout is in offline mode.
        """
        if not self.newest:
            return self.location
        if self.export:
            return self.location

        for (_, name) in self.urls:
            path = os.path.join(self.location, name)
            self.client.update(path)
            
        return self.location

    def install(self):
        """Checkout the checkouts.

        Fails if buildout is running in offline mode.
        """

        for (url, name) in self.urls:
            path = os.path.join(self.location, name)
            if self.export:
                self.client.export(url, path, recurse=True)
            else:
                self.client.checkout(url, path, recurse=True)

        return self.location

def uninstall(name, options):
    r"""
    This is an uninstallation hook for the 'infrae.subversion' recipe.

    Its only job is to raise an exception when there are changes in a
    subversion tree that a user might not want to lose.  This function
    does *not* delete or otherwise touch any files.

    The location of the path is passed as options['location'].
    
    Create an SVN repository to play with:
    
      >>> import py
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

    If we were to put 'bar.py' into the 'svn:ignore' property, uninstall 

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

    Then another commit makes it go away again:

      >>> rev3 = package.commit()
      >>> rev3 == rev2 + 1
      True
      >>> uninstall('test', {'location': wc.strpath})

    When 'svn:ignore' is set to ignore a directory, we should not
    descend into that directory when visiting:

      >>> build_dir = os.path.join(package.strpath, 'build')
      >>> os.mkdir(build_dir)
      >>> open(os.path.join(build_dir, 'boo.txt'), 'wb').write('booey')
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      ValueError: In '.../package/build':
      local modifications detected while uninstalling 'test': Uninstall aborted!
      ...

      >>> package.propset('svn:ignore', 'build')
      >>> uninstall('test', {'location': wc.strpath}) # doctest: +ELLIPSIS
      >>> ignore = package.propdel('svn:ignore')

    If our location doesn't exist, nothing will happen:

      >>> uninstall('test', {'location': 'no way'})
    """
    if bool(options.get('export', False)):
        return                  # SVN Export, there is nothing to check.

    # XXX This makes the assumption that we're in the buildout
    #     directory and that our part is in 'parts'.  We don't have
    #     options['buildout'] available so no
    #     'buildout:parts-directory'.
    location = options.get('location', os.path.join('.', 'parts', name))

    client = pysvn.Client()
    client.set_interactive(True)

    bad_svn_status = [wc_status_kind.modified, 
                      wc_status_kind.missing,
                      wc_status_kind.unversioned, ]

    for path in os.listdir(location):

        badfiles = filter(lambda e: e['text_status'] in bad_svn_status, 
                          client.status(os.path.join(location, path)))
    
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
