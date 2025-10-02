# 为 MkDocs-Note 贡献

首先，感谢您考虑为 `MkDocs-Note` 做出贡献！正是像您这样的人让开源社区变得如此美好。

## 项目架构

本节概述了 MkDocs-Note 插件的架构和调用流程，以帮助贡献者理解代码库结构。

### 整体架构

MkDocs-Note 插件采用模块化架构，具有清晰的关注点分离：

```
mkdocs_note/
├── __init__.py              # 包初始化
├── plugin.py                # MkDocs 插件主入口点
├── config.py                # MkDocs 配置管理
├── logger.py                # 日志工具
└── core/                    # 核心业务逻辑
    ├── file_manager.py      # 文件扫描和验证
    └── note_manager.py      # 笔记处理和管理
```

### 核心组件

#### 1. 插件入口点 (`plugin.py`)

`MkdocsNotePlugin` 类是与 MkDocs 集成的主入口点：

- **继承自**: `BasePlugin[PluginConfig]`

- **关键方法**:

  - `on_config()`: 配置 MkDocs 设置（TOC、slugify 函数）

  - `on_files()`: 扫描和处理笔记文件

  - `on_page_markdown()`: 将最近笔记插入索引页面

#### 2. 配置管理 (`config.py`)

`PluginConfig` 类管理所有插件设置：

- **配置选项**:

  - `enabled`: 启用/禁用插件

  - `notes_dir`: 包含笔记的目录

  - `index_file`: 最近笔记的目标索引文件

  - `max_notes`: 显示的最大笔记数量

  - `supported_extensions`: 要包含的文件类型（`.md`、`.ipynb`）

  - `exclude_patterns`: 要从处理中排除的文件

  - `exclude_dirs`: 扫描时要跳过的目录

#### 3. 文件管理 (`core/file_manager.py`)

`FileScanner` 类处理文件发现和验证：

- **职责**:

  - 递归扫描笔记目录

  - 按扩展名和模式过滤文件

  - 排除指定的目录和文件

  - 返回有效笔记文件列表

#### 4. 笔记处理 (`core/note_manager.py`)

多个类处理笔记处理和管理：

- **`NoteInfo`**: 存储笔记元数据的数据类

- **`NoteProcessor`**: 从文件中提取标题和元数据

- **`CacheManager`**: 管理缓存以避免不必要的更新

- **`IndexUpdater`**: 使用最近笔记更新索引文件

- **`RecentNotesUpdater`**: 主协调器类

#### 5. 日志记录 (`logger.py`)

`Logger` 类提供彩色控制台日志记录：

- 使用 `colorlog` 增强控制台输出

- 支持不同的日志级别（DEBUG、INFO、WARNING、ERROR）

- 可配置的日志格式

### 调用流程

插件执行遵循以下序列：

1. **初始化** (`__init__`)

   - 创建插件实例

   - 初始化日志记录器

   - 初始化最近笔记列表

2. **配置阶段** (`on_config`)

   - 插件启用/禁用检查

   - MkDocs TOC 配置设置

   - Slugify 函数配置（pymdownx 或回退）

3. **文件处理阶段** (`on_files`)

   - FileScanner 扫描笔记目录

   - NoteProcessor 从每个文件提取元数据

   - 按修改时间排序笔记

   - 填充最近笔记列表等

4. **页面渲染阶段** (`on_page_markdown`)

   - 检查当前页面是否为笔记索引页面

   - 在标记之间插入最近笔记 HTML

   - 返回修改后的 markdown 内容

### 数据流

项目目前只有一个功能，即**将最近笔记插入到笔记本目录的索引页面**。作为用户想要管理的笔记数据流示例，如下所示：

```
笔记目录
    ↓ (FileScanner)
有效笔记文件
    ↓ (NoteProcessor)
NoteInfo 对象
    ↓ (按修改时间排序)
最近笔记列表
    ↓ (HTML 生成)
索引页面内容
```

### 关键设计模式

1. **插件模式**: 与 MkDocs 插件系统集成

2. **策略模式**: 不同文件类型的不同标题提取

3. **模板方法**: 一致的笔记处理工作流

4. **观察者模式**: MkDocs 事件驱动架构

5. **数据传输对象**: NoteInfo 用于结构化数据传递

### 扩展点

架构支持几个扩展点：

1. **自定义文件类型**: 在 `supported_extensions` 中添加新文件扩展名

2. **标题提取**: 为新文件格式扩展 `NoteProcessor`

3. **输出格式**: 修改 `_generate_notes_html()` 中的 HTML 生成

4. **缓存策略**: 在 `CacheManager` 中实现自定义缓存

5. **过滤逻辑**: 在 `FileScanner` 中自定义文件过滤

### 测试策略

项目包含全面的单元测试：

- **插件测试**: 测试主要插件功能

- **核心测试**: 测试各个组件

- **集成测试**: 测试组件交互

- **模拟使用**: 广泛使用模拟进行隔离

### 性能考虑

1. **文件扫描**: 仅在必要时扫描

2. **缓存**: 避免冗余处理

3. **延迟加载**: 按需初始化组件

4. **内存管理**: 高效的笔记存储数据结构

## 如何贡献？

有很多贡献方式，从编写文档和教程到报告错误和提交代码更改。

### 报告错误

如果您发现错误，请打开一个问题并提供以下信息：

- 清晰描述性的标题。

- 问题的详细描述，包括重现步骤。

- 您的 `MkDocs` 配置（`mkdocs.yml`）。

- 任何相关的错误消息或日志。

### 建议增强

如果您对新功能或现有功能的改进有想法，请打开一个问题进行讨论。这允许我们协调工作并避免重复工作。

## 开发设置

要开始本地开发，请按照以下步骤操作：

1.  **Fork 和克隆仓库**

    ```bash
    git clone https://github.com/YOUR_USERNAME/mkdocs-note.git
    cd mkdocs-note
    ```

2.  **设置环境**

    强烈建议使用虚拟环境，并推荐使用 [uv](https://docs.astral.sh/uv/) 来管理项目配置和虚拟环境。

    ```bash
    uv init
    ```

3.  **安装依赖**

    以可编辑模式安装项目以及开发依赖。

    ```bash
    uv sync
    ```

4.  **运行测试**

    为确保一切设置正确，运行测试套件：

    ```bash
    ./tests/test.sh
    ```

## 拉取请求流程

1.  确保任何新代码都被测试覆盖。

2.  如果您添加或更改了任何功能，请更新文档。

3.  确保测试套件通过（`pytest`）。

4.  提交您的拉取请求！

感谢您的贡献！
