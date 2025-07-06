<p align="right">
  <a href="./docs/README.en.md">English</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Tera Terminal AI 终端助手

![Tera Terminal AI](./docs/imgs/tera.png)

Tera Terminal AI 是一款轻量级的命令行大语言模型聊天代理，支持多 **LLM 源**、多 **角色设定**、**代码片段执行反馈**以及可选 **长期记忆**，专注极简与跨平台体验。

> A lightweight terminal chat agent with multi-endpoint, multi-character, optional long-term memory and code execution feedback.

> **目前支持 Windows / macOS / Linux**（需预装 Python 3.9+）

## 下载与安装（需预装 Python 3.9+）

```bash
# 克隆仓库并进入目录
git clone https://github.com/yourname/tera-terminal-ai.git
cd tera-terminal-ai

# 以可编辑模式安装（便于本地修改）
pip install -e .

# 运行
tera <command>
```

## 快速开始

首次使用需先添加LLM源，然后再进入聊天模式；LLM源获取可参考[常用LLM源](./docs/llm_sources.md)
```bash
# 1. 添加 LLM 源（首次使用必须）
tera source add # 源名称仅用作该源的标识，在切换源时使用

# 2. 进入聊天
tera
```

（可选）记忆功能采用本地嵌入模型，需要先下载较大的模型文件，因此默认关闭，需要执行以下代码手动开启；如需使用CUDA加速推理，参考[torch安装](https://pytorch.org/get-started/locally/)安装系统对应版本torch。
```bash
pip install -e .[memory]
tera memory on
```

更多示例：

```bash
# 查看所有命令
tera --help

# 切换当前模型源
tera source use my-openai

# 添加并切换角色
tera character add
tera character use anime-girl

# 开启/关闭长期记忆
tera memory on
tera memory off
```

## 功能亮点

- 🛰️ **多源管理**：支持同时保存多个 OpenAI-API 兼容端点，一行命令快速切换。  
- 🧑‍🎤 **角色系统**：为不同场景预设 prompt，一键切换人格。  
- 💻 **代码执行反馈**：AI 回复中的 Python / Shell 代码可本地执行并将输出回传模型。  
- 💾 **长期记忆**（可选）：基于 Sentence-Transformer + Faiss，本地向量检索个人偏好。  
- 🖥️ **跨平台 CLI**：依赖极少，纯 Python + Click，一次安装到处运行。  

## 许可证

本项目基于 MIT 协议开源，详见 [LICENSE](LICENSE)。