import importlib
module = importlib.import_module('fbs_runtime._frozen')
module.PUBLIC_SETTINGS = {'app_name': 'Splittar', 'author': 'David Boutelier', 'version': '0.0.0', 'environment': 'local'}