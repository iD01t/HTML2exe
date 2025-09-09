#!/usr/bin/env python3
"""
HTML2EXE Pro Premium - Launcher
"""
import runpy

if __name__ == "__main__":
    # This allows the script to be run from the root of the project
    # during development without having to install it.
    runpy.run_module("html2exe.main", run_name="__main__")
