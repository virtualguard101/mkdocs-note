---
date: 2025-10-17 14:07:48
title: Some Security Considerations
permalink: 
publish: true
---

# Some Security Considerations You Should Notice

## Working Scope and Behavior Boundaries

Because of some features which can cause undefined event like data loss and structure collision and chaos, etc. especially in [CLI](cli.md)!

During development, we introduced some security measures to help you avoid these issues, the content below is just a overview about it. If you're a developer, you can see more details in [Contributing Guide]().

However, whether the problem can be solved is not guaranteed, so you should be careful when using the plugin.

Strongly recommended to use [Git](https://git-scm.com/) as a version control system to backup your documentations and assets before you take some dangerous actions.

### Working Scope of the Plugin

<!-- The plugin's working scope is the directory of the notes, which is defined by the `notes_dir` option in `mkdocs.yml`.

All note scanning, file operations, and asset management are limited to this directory. -->
