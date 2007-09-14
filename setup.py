from setuptools import setup, find_packages

name = "infrae.subversion"

setup(
    name = name,
    version = "1.0",
    author = "Casteleijn & Sons",
    author_email = "eric@infrae.com",
    description = "Buildout recipe for checking out from subversion",
    long_description= "",
    license = "ZPL 2.1",
    keywords = "subversion buildout",
    packages = find_packages(),
    namespace_packages = ['infrae'],
    install_requires = ['zc.buildout', 'setuptools'],
    entry_points = {'zc.buildout': ['default = %s:Recipe' % name]},
    )
