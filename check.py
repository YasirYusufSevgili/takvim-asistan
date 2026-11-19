import sys
from importlib.metadata import version

import app

print("Python:", sys.version.split()[0])
for paket in ["fastapi", "sqlmodel", "anthropic", "flet", "pytest"]:
    print(f"{paket}:", version(paket))
print("app paketi:", app.__file__)
print("\nHer şey hazır.")
