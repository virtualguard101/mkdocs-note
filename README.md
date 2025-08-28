# MkDocs Note - 智能笔记管理插件

## 项目概述

MkDocs Note 是一个为 MkDocs 设计的智能笔记管理插件，提供强大的笔记组织、链接解析和可视化功能。

## 核心模块结构 (src/mkdocs_note/core/)

```
src/mkdocs_note/core/
├── builders/              # 构建器模块 - 负责生成文档结构
│   ├── graph_builder.py   # 图构建器 - 构建笔记关系图
│   ├── __init__.py        # 构建器模块初始化
│   └── tree_builder.py    # 树构建器 - 构建文档树结构
├── __init__.py            # 核心模块初始化 - 提供主要API接口
├── legacy.py              # 遗留代码支持 - 兼容旧版本API
├── managers/              # 管理器模块 - 负责文件管理
│   ├── file_manager.py    # 文件管理器 - 处理文件操作
│   ├── __init__.py        # 管理器模块初始化
│   └── note_manager.py    # 笔记管理器 - 管理笔记内容
├── models/                # 数据模型模块 - 定义数据结构
│   ├── file_node.py       # 文件节点模型 - 表示文件结构
│   ├── __init__.py        # 模型模块初始化
│   ├── note_graph.py      # 笔记图模型 - 表示笔记关系
│   └── note_node.py       # 笔记节点模型 - 表示单个笔记
└── parsers/               # 解析器模块 - 负责内容解析
    ├── base_parser.py     # 基础解析器 - 提供解析接口
    ├── __init__.py        # 解析器模块初始化
    ├── link_parser.py     # 链接解析器 - 解析markdown内部链接
    └── metadata_parser.py # 元数据解析器 - 解析YAML front matter
```

## 模块功能详解

### 1. 数据模型模块 (models/)
- **FileNode** (`file_node.py`) - 文件节点模型，表示文件系统中的文件结构
- **NoteNode** (`note_node.py`) - 笔记节点模型，继承FileNode，专门处理.md笔记文件
- **NoteGraph** (`note_graph.py`) - 笔记图模型，管理笔记之间的关联关系

### 2. 解析器模块 (parsers/)
- **BaseParser** (`base_parser.py`) - 基础解析器接口，定义解析方法
- **LinkParser** (`link_parser.py`) - 链接解析器，专门解析markdown内部链接 `[[笔记名称]]`
- **MetadataParser** (`metadata_parser.py`) - 元数据解析器，解析YAML front matter

### 3. 构建器模块 (builders/)
- **TreeBuilder** (`tree_builder.py`) - 树构建器，构建文档的树状结构
- **GraphBuilder** (`graph_builder.py`) - 图构建器，构建笔记之间的关系图可视化

### 4. 管理器模块 (managers/)
- **FileManager** (`file_manager.py`) - 文件管理器，负责文件的读取和写入操作
- **NoteManager** (`note_manager.py`) - 笔记管理器，专门管理笔记内容的创建和更新

### 5. 核心模块
- **__init__.py** - 核心模块初始化，提供主要的API接口
- **legacy.py** - 遗留代码支持，确保向后兼容性

## 主要特性

1. **智能链接解析** - 自动解析和创建markdown内部链接
2. **可视化关系图** - 生成笔记之间的关联关系可视化
3. **元数据管理** - 支持YAML front matter元数据解析
4. **双向链接** - 实现笔记之间的双向链接功能
5. **搜索优化** - 提供高效的笔记搜索和检索功能
