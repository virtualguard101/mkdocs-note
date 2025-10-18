---
date: 2025-10-17 11:52:55
title: Templating System
permalink: 
publish: true
---

# Templating System

The plugin supports a flexible template system with frontmatter support for creating new notes:

## Template Variables

- `{{title}}`: The note title (derived from filename, formatted)

- `{{date}}`: Current date and time

- `{{note_name}}`: The original note filename

!!! tip
    Template variables are replaced **only in the frontmatter section**, keeping the note body clean and free from template syntax.

## Default Template

The default template contains:

```markdown
---
date: {{date}}
title: {{title}}
permalink: 
publish: true
---

# {{title}}

Start writing your note content...
```

If you use `mkdocs-note new` of the [Command Line Interface](cli.md) in this plugin to create a new note, the template will be applied automatically.

But notice that the template file above should be created manually by yourself in order to make the plugin automatically apply it.

## Custom Template

You can create a custom template by creating a new file in the `templates` directory.

However, please notice that your template files should contain at least the following content so that the plugin can replace some metadata variables:

```markdown
---
date: {{date}}
title: {{title}}
---

# {{title}}
```

## Frontmatter Support

Notes support YAML frontmatter for metadata management:

- **Standard Fields**:
  
  - `date`: Creation or publication date

  - `title`: The note title
  
  - `permalink`: Custom permalink for the note
  
  - `publish`: Whether the note should be published (true/false)

- **Custom Fields**: You can add custom metadata fields through the extensible registration system

- **Metadata Registry**: The plugin provides a metadata registration interface for adding new fields without modifying core code
