infrae.subversion
=================

This zc.buildout recipe will check out a *number* of URLs into its
parts directory.  It won't remove its parts directory if there are any
changes in the checkout, so it's safe to work with that checkout for
development.

This is an example buildout part that uses this recipe::

    [development-products]
    recipe = infrae.subversion
    urls = 
        https://svn.plone.org/svn/collective/PDBDebugMode/trunk PDBDebugMode

This will maintain a working copy of ``PDBDebugMode`` in the
``parts/development-products/PDBDebugMode`` directory (*not* in the
parts directory itself).  Thus, the recipe handles multiple URLs fine.

If you have pysvn installed on the computer, it will be use. This
implies better performances.

Sample
------

For an example buildout that uses this recipe, please see the `Silva
buildout <https://svn.infrae.com/buildout/silva/trunk>`_.

Export
------

With pysvn installed, you can specify:

   export = True

in your buildout part to get an SVN export instead of an SVN checkout.


Latest version
--------------

The latest version is available in a `Subversion repository
<https://svn.infrae.com/buildout/infrae.subversion/trunk#egg=infrae.subversion-dev>`_.


