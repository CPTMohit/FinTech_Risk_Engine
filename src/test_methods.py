# src/test_methods.py

from SmartApi import SmartConnect

print([m for m in dir(SmartConnect) if not m.startswith("_")])