# MkDocs-Note

<!-- [![PyPI version](https://badge.fury.io/py/mkdocs-note.svg)](https://badge.fury.io/py/mkdocs-note) -->

`MkDocs-Note` 是一个为 `MkDocs` 设计的插件，可以自动管理文档站点中的笔记。它专为与 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 主题无缝协作而设计，以创建统一的笔记记录和文档体验。

## 功能特性

- **最近笔记显示**: 自动在笔记索引页面显示最近笔记列表

- **多格式支持**: 支持 Markdown (.md) 和 Jupyter Notebook (.ipynb) 文件

- **智能过滤**: 从最近笔记列表中排除索引文件和其他指定模式

- **灵活配置**: 高度可定制的笔记目录、文件模式和显示选项

- **自动更新**: 构建文档时笔记列表会自动更新

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
```

## 使用方法

### 设置笔记目录

1. 在文档中创建笔记目录（例如，`docs/notes/`）
2. 在笔记目录中创建 `index.md` 文件
3. 在索引文件中添加标记注释：

```markdown
# 我的笔记

<!-- recent_notes_start -->
<!-- recent_notes_end -->
```

### 配置选项

插件在 `mkdocs.yml` 中支持以下配置选项：

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `enabled` | bool | `true` | 启用或禁用插件 |
| `notes_dir` | Path | `"docs/notes"` | 包含笔记的目录 |
| `index_file` | Path | `"docs/notes/index.md"` | 显示最近笔记的索引文件 |
| `max_notes` | int | `10` | 显示的最大笔记数量 |
| `start_marker` | str | `"<!-- recent_notes_start -->"` | 笔记插入的开始标记 |
| `end_marker` | str | `"<!-- recent_notes_end -->"` | 笔记插入的结束标记 |
| `supported_extensions` | Set[str] | `{".md", ".ipynb"}` | 作为笔记包含的文件扩展名 |
| `exclude_patterns` | Set[str] | `{"index.md", "README.md"}` | 要排除的文件模式 |
| `exclude_dirs` | Set[str] | `{"__pycache__", ".git", "node_modules"}` | 要排除的目录 |

### 工作原理

1. 插件扫描配置的笔记目录以查找支持的文件类型
2. 从每个笔记文件中提取元数据（标题、修改日期）
3. 按修改时间对笔记进行排序（最新的在前）
4. 将指定数量的最近笔记插入到索引页面的标记注释之间
5. 每次构建文档时都会自动运行此过程

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 文件了解指导原则。

## 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 许可证。
