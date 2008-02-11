try:
    # Try to use a native binding, use native SVN.
    import Native
    Recipe = Native.Recipe
    uninstall = Native.uninstall
except:
    # Or if the binding is not present, use slow pypi.
    import PyPi
    Recipe = PyPi.Recipe
    uninstall = PyPi.uninstall

