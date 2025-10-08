# MkDocs-Note

<div align="center">
   <p>插件使用示例：<a href="https://wiki.virtualguard101.com/notes/" target="_blank">Notebook | virtualguard101's Wiki</a></p>
</div>

`MkDocs-Note` 是一个为 `MkDocs` 设计的插件，可以自动管理文档站点中的笔记。它专为与 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 主题无缝协作而设计，以创建统一的笔记记录和文档体验。

## 功能特性

- **最近笔记显示**: 自动在笔记索引页面显示最近笔记列表

- **多格式支持**: 支持 Markdown (.md) 和 Jupyter Notebook (.ipynb) 文件

- **智能过滤**: 从最近笔记列表中排除索引文件和其他指定模式

- **灵活配置**: 高度可定制的笔记目录、文件模式和显示选项

- **自动更新**: 构建文档时笔记列表会自动更新

- **命令行接口**: 内置的笔记管理 CLI 命令（`mkdocs note init`、`mkdocs note new` 等）

- **资产管理**: 为每个笔记自动创建和管理资产目录

- **模板系统**: 支持变量替换的可配置笔记模板

- **结构验证**: 确保符合规范的资产树结构，保持组织一致性

## 安装

推荐使用 [uv](https://docs.astral.sh/uv/) 来管理 Python 虚拟环境：

```
uv venv
uv pip install mkdocs-note
```

或者使用 `pip`：

```bash
pip install mkdocs-note
```

然后，将插件添加到你的 `mkdocs.yml` 中：

```yaml
plugins:
  - mkdocs-note:
      enabled: true
      notes_dir: "docs/notes"
      index_file: "docs/notes/index.md"
      max_notes: 10
      start_marker: "<!-- recent_notes_start -->"
      end_marker: "<!-- recent_notes_end -->"
      assets_dir: "docs/notes/assets"
      notes_template: "docs/notes/template/default.md"
```

> **⚠️ 重要**: 注意缩进格式！请使用**空格**（而非破折号 `-`）来缩进插件选项。配置必须是字典格式，而非列表格式。常见配置问题请参考[故障排除指南](TROUBLESHOOTING.md)。

## 使用方法

### 设置笔记目录

#### 方式一：使用命令行界面（推荐）

1. 初始化笔记目录结构：
```bash
mkdocs-note init
```

2. 创建新笔记：
```bash
mkdocs-note new docs/notes/my-new-note.md
```

#### 方式二：手动设置

1. 在文档中创建笔记目录（例如，`docs/notes/`）

2. 在笔记目录中创建 `index.md` 文件

3. 在索引文件中添加标记注释：

```markdown
# 我的笔记

<!-- recent_notes_start -->
<!-- recent_notes_end -->
```

### 命令行界面

插件提供了多个用于笔记管理的 CLI 命令：

#### 初始化笔记目录
```bash
mkdocs-note init [--path PATH]
```
- 创建笔记目录结构

- 分析现有资产结构

- 修复不符合规范的资产树

- 创建带有正确标记的索引文件

#### 创建新笔记
```bash
mkdocs-note new FILE_PATH [--template TEMPLATE_PATH]
```
- 使用模板内容创建新笔记文件

- 创建对应的资产目录

- 验证资产树结构合规性

#### 验证结构
```bash
mkdocs-note validate [--path PATH]
```
- 检查资产树结构是否符合插件设计规范

- 报告任何结构问题

#### 模板管理
```bash
mkdocs-note template [--check] [--create]
```
- 检查配置的模板文件是否存在

- 如果不存在则创建模板文件

### 配置选项

插件在 `mkdocs.yml` 中支持以下配置选项：

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `enabled` | bool | `true` | 启用或禁用插件 |
| `notes_dir` | Path | `"docs/notes"` | 包含笔记的目录 |
| `index_file` | Path | `"docs/notes/index.md"` | 显示最近笔记的索引文件 |
| `max_notes` | int | `11` | 显示的最大笔记数量（包含索引页面，但显示时不包含索引页面本身） |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | 笔记插入的开始标记 |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | 笔记插入的结束标记 |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | 作为笔记包含的文件扩展名 |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | 要排除的文件模式 |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | 要排除的目录 |
| `use_git_timestamps` | bool | `true` | 使用 Git 提交时间戳进行排序，而不是文件系统时间戳 |
| `timestamp_zone` | str | `"UTC+0"` | 时间戳显示的时区（例如 'UTC+0'、'UTC+8'、'UTC-5'）。确保不同部署环境中的时间戳显示一致 |
| `assets_dir` | Path | `"docs/notes/assets"` | 存储笔记资产的目录。使用树状结构，第一级子目录带有 `.assets` 后缀 |
| `notes_template` | Path | `"docs/notes/template/default.md"` | 新笔记的模板文件。支持变量：`{{title}}`、`{{date}}`、`{{note_name}}` |
| `cache_size` | int | `256` | 性能优化的缓存大小 |

### 模板系统

插件支持灵活的新笔记模板系统：

#### 模板变量

- `{{title}}`: 笔记标题（从文件名派生，格式化）

- `{{date}}`: 当前日期和时间

- `{{note_name}}`: 原始笔记文件名

#### 默认模板

默认模板（`docs/notes/template/default.md`）包含：

```markdown
# {{title}}

Created on {{date}}

Note: {{note_name}}
```

#### 自定义模板

创建笔记时可以使用自定义模板：

```bash
mkdocs-note new docs/notes/my-note.md --template path/to/custom-template.md
```

### 资产管理

插件使用**树状结构**自动管理每个笔记的资产：

#### 树状资产组织

- **层次化结构**：资产镜像您的笔记目录结构，防止不同目录中同名笔记之间的冲突

- **第一级分类**：第一级子目录具有 `.assets` 后缀以便更好地识别
  
  - `notes/dsa/` → `assets/dsa.assets/`

  - `notes/language/` → `assets/language.assets/`

  - `notes/ml/` → `assets/ml.assets/`

- **路径映射示例**：
  
  ```
  notes/dsa/anal/iter.md           → assets/dsa.assets/anal/iter/

  notes/language/python/intro.md  → assets/language.assets/python/intro/

  notes/language/cpp/intro.md     → assets/language.assets/cpp/intro/

  notes/quickstart.md              → assets/quickstart/
  ```

#### 自动路径转换

- **笔记中的相对引用**：只需像平常一样编写图片引用：
  
  ```markdown
  ![递归树](recursion_tree.png)
  ```

- **自动转换**：插件在构建期间自动转换路径：
  
  - 对于 `notes/dsa/anal/iter.md` → `../../assets/dsa.assets/anal/iter/recursion_tree.png`

  - 对于 `notes/quickstart.md` → `assets/quickstart/recursion_tree.png`

- **无需手动路径管理**：原始 markdown 文件保持简洁清晰

#### 优势

- ✅ **无命名冲突**：不同目录中的同名笔记不会冲突

- ✅ **清晰组织**：`.assets` 后缀使资产类别易于识别

- ✅ **自动处理**：图片路径在构建期间自动转换

- ✅ **MkDocs 兼容**：生成的路径与 MkDocs 无缝协作

### 工作原理

1. 插件扫描配置的笔记目录以查找支持的文件类型

2. 从每个笔记文件中提取元数据（标题、修改日期）

3. 按修改时间对笔记进行排序（最新的在前）

   - 默认使用 Git 提交时间戳，确保在不同部署环境中的一致排序

   - 如果 Git 不可用，则回退到文件系统时间戳

4. 将指定数量的最近笔记插入到索引页面的标记注释之间

5. 对于每个笔记页面，插件处理资产引用：
   
   - 检测 markdown 内容中的图片引用
   
   - 计算笔记在目录树中的位置
   
   - 将相对资产路径转换为带有正确 `../` 前缀的正确引用
   
   - 为第一级目录添加 `.assets` 后缀以进行组织

6. 每次构建文档时都会自动运行此过程

### 资产管理最佳实践

1. **目录结构**：在子目录中组织您的笔记以更好地分类
   
   ```
   docs/notes/
   ├── dsa/           # 数据结构与算法
   ├── language/      # 编程语言
   ├── ml/            # 机器学习
   └── tools/         # 开发工具
   ```

2. **资产放置**：将资产放置在相应的资产目录中
   
   ```
   docs/notes/assets/
   ├── dsa.assets/
   │   └── anal/
   │       └── iter/
   │           ├── recursion_tree.png
   │           └── diagram.png
   ```

3. **简单引用**：在笔记中编写简单的相对引用
   
   ```markdown
   ![我的图片](my-image.png)
   ![图表](diagrams/flow.png)
   ```

4. **自动转换**：让插件在构建期间处理路径转换

> **注意**：如果您正在从旧版本迁移，可能需要重新组织您的资产目录以匹配新的树状结构（第一级目录带有 `.assets` 后缀）。

### 时区配置

为了确保在不同部署环境（例如本地开发与远程 CI/CD）之间显示一致的时间戳，您可以配置时区：

```yaml
plugins:
  - mkdocs-note:
      timestamp_zone: "UTC+8"  # 北京/上海/香港时间
      # timestamp_zone: "UTC-5"  # 美国东部标准时间
      # timestamp_zone: "UTC+0"  # UTC（默认值）
```

这在您的本地环境和远程部署服务器位于不同时区时特别有用。如果没有此配置，`mkdocs serve`（本地）和部署的站点之间可能会显示不同的时间戳。

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 文件了解指导原则。

## 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 许可证。
