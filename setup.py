from setuptools import setup, find_packages

name = "infrae.subversion"

setup(
    name = name,
    version="1.0",
    author="Eric Casteleijn, Guido Wesdorp, Daniel Nouri and Sylvain Viollon",
    author_email="info@infrae.com",
    description="Buildout recipe for checking out from subversion",
    long_description=open('README.txt').read(),
    url="https://svn.infrae.com/buildout/infrae.buildout/trunk/",
    license="ZPL 2.1",
    keywords="subversion buildout",
    classifiers=[
        "Framework :: Buildout",
        "License :: OSI Approved :: Zope Public License",
        "Topic :: Software Development :: Version Control",
    ],
    packages=find_packages(),
    namespace_packages = ['infrae'],
    test_suite = 'infrae.subversion.tests.test_impl.test_suite',
    tests_require = ['svnhelper', 
                     'zc.buildout', 
                     'zope.testing', 
                     'setuptools', 
                     'py == 0.9.0',],
    install_requires = [
        'zc.buildout', 
        'setuptools', 
        'py == 0.9.0'],
    entry_points = {
        'zc.buildout': ['default = %s:Recipe' % name],
        'zc.buildout.uninstall': ['default = %s:uninstall' % name]},
)
