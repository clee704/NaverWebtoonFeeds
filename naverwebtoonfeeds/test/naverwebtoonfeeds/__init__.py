import os

def setup_package():
    mode = os.environ.get('NWF_MODE', '')
    if mode != 'test':
        print "Run tests with 'runtest', not 'nosetests'."
        raise RuntimeError("Invalid NWF_MODE: '{0}'. It must be 'test'.".format(mode))
