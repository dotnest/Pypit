# Pypit
Python companion script for PoE

![](resources/example.gif)

## Linux

- good luck
- i had to install some additional python libraries on ubuntu to make Tkinter work, google ["ubuntu install tkinter"](https://www.google.com/search?q=ubuntu+install+tkinter) in case of problems
- if you're getting `AttributeError: When using gi.repository you must not import static modules like "gobject"...`, try commenting out 6 lines of this try/except/else block in your pyperclip `__init__.py` file to force pyperclip to use xclip or other alternatives (found mine at `~/.local/lib/python3.8/site-packages/pyperclip/__init__.py`)
```python
# Setup for the LINUX platform:
if HAS_DISPLAY:
    # try:
    #     import gtk  # check if gtk is installed
    # except ImportError:
    #     pass # We want to fail fast for all non-ImportError exceptions.
    # else:
    #     return init_gtk_clipboard()
```