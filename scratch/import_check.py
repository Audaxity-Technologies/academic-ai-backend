import sys, os
sys.path.append(os.getcwd())
import importlib
module = importlib.import_module('app.api.v1.lectures.router')
print('import success')
