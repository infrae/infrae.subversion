from setuptools import setup, find_packages

name = "infrae.subversion"

setup(
    name = name,
    version = "1.0",
    author = "Eric Casteleijn, Guido Wesdorp and Daniel Nouri",
    author_email = "crew@infrae.com",
    description = "Buildout recipe for checking out from subversion",
    long_description= open('README.txt').read(),
    license = "ZPL 2.1",
    keywords = "subversion buildout",
    packages = find_packages(),
    namespace_packages = ['infrae'],
    install_requires = ['zc.buildout', 'setuptools', 'py'],
    entry_points = {
        'zc.buildout': ['default = %s:Recipe' % name],
        'zc.buildout.uninstall': ['default = %s:uninstall' % name]},
)
