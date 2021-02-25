
import os
import glob
import importlib

for module in os.listdir(os.path.dirname(__file__)):
    if '_' not in module and module.endswith('.py'):
        module = module.rsplit('.', 1)[0]
        importlib.import_module(f"sources.{module}")

