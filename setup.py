#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="schedaus",
    version="1.0",
    description="Text based gantt chart renderer",
    author="rsp9u",
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        "flask",
        "svgwrite",
        "graph-theory",
        "cairosvg",
    ],
)
