#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="mkdocs-note",
    version="1.2.4",
    author="virtualguard101",
    author_email="virtualguard101@gmail.com",
    description="A MkDocs plugin to add note boxes to your documentation.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/virtualguard101/mkdocs-note",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        "mkdocs>=1.6.1",
        "colorlog>=6.9.0",
        "pyyaml>=6.0",
        "pymdown-extensions>=10.15",
        "mkdocs-material>=9.6.4",
        "mkdocs-material-extensions>=1.3.1",
        "mkdocs-jupyter>=0.25.1",
        "mkdocs-minify-plugin>=0.8.0",
        "mkdocs-git-revision-date-localized-plugin>=1.4.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3 License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'mkdocs.plugins': [
            'mkdocs-note = mkdocs_note.plugin:MkdocsNotePlugin'
        ]
    },
    python_requires='>=3.12',
)
