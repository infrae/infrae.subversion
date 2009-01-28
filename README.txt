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

You can select a different location with ``location``, for instance::

   location = src

Will extract ``PDBDebugMode`` in ``src/PDBDebugMode`` instead of
``parts``.

If you have ``pysvn`` installed on the computer, it will be used. This
implies better performances.

Update
------

By default, when buildout update the part, an ``svn up`` is done for
each link. However, when a revision number is specified like this::

   https://svn.infrae.com/buildout/infrae.subversion/trunk@27829

The SVN link is skipped for update. If you want to prevent update for
all SVN link of the part even if they do not contain revision number,
you can add the following option::

   ignore_updates = true

Export
------

With ``pysvn`` installed, you can specify::

   export = true

in your buildout part to get an SVN export instead of an SVN checkout.

Verification
------------

By default, your checkout are checked against local modification
before any uninstallation step. This can take time on large checkouts,
and you may don't want it in some case (like when used on buildbot for
instance). To prevent this step, you can use this option::

  ignore_verification = true

As well, when the recipe update it can emit some warnings because a
directory have been removed. You can suppress that warning with::

  no_warnings = true

The verification will still be done, and the directory will be checked
out again to replace the missing one.

Eggs
----

If you set the option ``as_eggs`` in your configuration file,
checkouted URLs will be registered as development eggs in your
buildout. This only work for non-recipe development eggs.

.. warning:: If you add a new egg, this will trigger a new
  uninstall-reinstall cycle. You may want to use that option to setup
  eggs coming from SVN for production, but not for development.

Exported Variables
------------------

If you set::

  export_info = true

Two variables will be exported by this recipe:

- ``revisions`` which gives for each URL the corresponding revision
  number,

- ``updated`` which gives a list of URLs which have been updated with
  new code.

Since values to these variables changes each time you run buildout
(revision number changes), this trigger an uninstall/reinstall of the
part. We recommand to activate it only if you need it.

Is always exported a variable ``location`` to say where are done the
checkouts, and a variable ``eggs`` which contains a list of
checkouted eggs.

Sample
------

For an example buildout that uses this recipe, please see the `Silva
buildout <https://svn.infrae.com/buildout/silva/trunk>`_.

As well, the `doctest file
<https://svn.infrae.com/buildout/infrae.subversion/trunk/infrae/subversion/tests/IMPL.txt>`_
can provide more sample.

Latest version
--------------

The latest version is available in a `Subversion repository
<https://svn.infrae.com/buildout/infrae.subversion/trunk#egg=infrae.subversion-dev>`_.


