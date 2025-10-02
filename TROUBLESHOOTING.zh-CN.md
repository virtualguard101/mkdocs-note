# 故障排除指南

本文档提供了使用 MkDocs-Note 插件时常见问题的解决方案。

## 配置错误："Invalid config options for the 'mkdocs-note' plugin"

### 问题描述

您可能遇到以下错误：

```
ERROR   -  Config value 'plugins': Invalid config options for the 'mkdocs-note' plugin.
```

### 根本原因

此错误通常是由于 `mkdocs.yml` 配置文件中的 YAML 格式不正确导致的。最常见的错误是使用破折号（`-`）而不是适当的缩进来配置插件选项。

### 错误配置（❌）

```yaml
plugins:
  - mkdocs-note:
    - notes_dir: docs/notes  # ❌ 错误：使用破折号会创建列表而不是字典
```

这会被解析为：`{'mkdocs-note': [{'notes_dir': 'docs/notes'}]}`，这是一个**列表**，而不是**字典**。

### 正确配置（✓）

```yaml
plugins:
  - mkdocs-note:
      notes_dir: docs/notes  # ✓ 正确：适当的缩进创建字典
```

这会被解析为：`{'mkdocs-note': {'notes_dir': 'docs/notes'}}`，这是一个**字典**。

### 解决方案

1. 打开您的 `mkdocs.yml` 文件
2. 找到 `mkdocs-note` 插件配置
3. 确保插件选项使用**空格缩进**（不是破折号）
4. 在插件名称后使用 2 或 4 个空格（保持一致）

### 完整配置示例

#### 最小配置

```yaml
plugins:
  - search
  - mkdocs-note:
      notes_dir: docs/notes
```

#### 完整配置

```yaml
plugins:
  - search
  - mkdocs-note:
      enabled: true
      notes_dir: "docs/notes"
      index_file: "docs/notes/index.md"
      max_notes: 10
      start_marker: "<!-- recent_notes_start -->"
      end_marker: "<!-- recent_notes_end -->"
```

## 配置类型错误："Expected type: <class 'pathlib.Path'> but received: <class 'str'>"

### 问题描述

您可能遇到以下错误：

```
ERROR   -  Config value 'plugins': Plugin 'mkdocs-note' option 'notes_dir': Expected type: <class 'pathlib.Path'> but received: <class 'str'>
```

### 根本原因

此错误发生在期望的配置类型与实际提供的类型不匹配时。通常发生在以下情况：

1. 插件配置定义不正确
2. 与 MkDocs 版本存在兼容性问题
3. 配置选项类型验证过于严格

### 解决方案

此错误已在最新版本的插件中修复。如果您遇到此错误：

1. **更新插件**到最新版本：
   ```bash
   pip install --upgrade mkdocs-note
   ```

2. **检查您的 MkDocs 版本**：
   ```bash
   mkdocs --version
   ```

3. **如果错误仍然存在**，请确保您的 `mkdocs.yml` 配置正确：
   ```yaml
   plugins:
     - mkdocs-note:
         notes_dir: docs/notes  # 字符串路径是正确的
   ```

### 注意

插件内部会根据需要将字符串路径转换为 `pathlib.Path` 对象，因此您应该在配置中始终提供字符串路径。

## Jupyter 弃用警告

### 问题描述

在使用 `.ipynb` 文件时，您可能会看到此警告：

```
INFO    -  DeprecationWarning: Jupyter is migrating its paths to use standard platformdirs
           given by the platformdirs library.  To remove this warning and
           see the appropriate new directories, set the environment variable
           `JUPYTER_PLATFORM_DIRS=1` and then run `jupyter --paths`.
```

### 根本原因

此警告来自 Jupyter 迁移到使用 `platformdirs` 库进行路径管理。**这不是 MkDocs-Note 插件的错误** - 这是 Jupyter 本身的弃用警告。

### 解决方案

此警告是无害的，可以安全地忽略。如果您想消除它：

1. **设置环境变量**（推荐以实现未来兼容性）：

   ```bash
   export JUPYTER_PLATFORM_DIRS=1
   mkdocs build
   ```

2. **更新 Jupyter Core** 到版本 6 或更高版本：

   ```bash
   pip install --upgrade jupyter_core
   ```

3. **抑制警告**（临时解决方案）：

   ```bash
   export PYTHONWARNINGS="ignore::DeprecationWarning"
   mkdocs build
   ```

### 注意

MkDocs-Note 插件**不会**导入任何 Jupyter 库。它只是将 `.ipynb` 文件作为 JSON 解析以提取元数据。该警告出现是因为您环境中的其他工具（如 MkDocs 扩展或其他插件）可能正在导入 Jupyter 库。

## 其他常见问题

### 问题：未显示最近笔记

**可能的原因：**

1. **缺少标记** - 确保您的索引文件包含两个标记：
   ```markdown
   <!-- recent_notes_start -->
   <!-- recent_notes_end -->
   ```

2. **错误的笔记目录** - 验证配置中的 `notes_dir` 路径

3. **被排除的文件** - 检查您的笔记是否与 `exclude_patterns` 匹配

### 问题：笔记未更新

**解决方案：** 
1. 清除 MkDocs 构建缓存：`rm -rf site/`
2. 重新构建：`mkdocs build`

### 问题：找不到笔记

**解决方案：**
1. 验证笔记目录是否存在
2. 检查笔记是否具有支持的扩展名（`.md` 或 `.ipynb`）
3. 确保笔记不在被排除的目录中（`__pycache__`、`.git`、`node_modules`）

## 获取帮助

如果您遇到本指南未涵盖的问题：

1. 查看 [README.zh-CN.md](README.zh-CN.md) 了解配置详情
2. 查看 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md) 了解架构信息
3. 在 [GitHub](https://github.com/virtualguard101/mkdocs-note/issues) 上提交问题，包括：
   - 您的 MkDocs 版本：`mkdocs --version`
   - 您的插件版本：`pip show mkdocs-note`
   - 您的 `mkdocs.yml` 配置
   - 完整的错误消息和追溯信息

