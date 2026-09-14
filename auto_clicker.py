"""Ponto de entrada do Auto Clicker.

É este arquivo que o PyInstaller usa para montar o .exe (ele não consegue
partir de um pacote com importações relativas, como o autoclicker/__main__.py).
"""

import sys

from autoclicker.gui import main

if __name__ == "__main__":
    sys.exit(main())
