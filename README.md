# AI Meeting Room

An AI meeting room system based on LLM models, supporting multi-model and multi-role intelligent meeting discussions.

## Features

- Support for different LLM models (OpenAI compatible API)
- Different role configurations for the same model
- Configurable number of participants and roles
- Online search function to support argumentation
- Host maintains meeting order and organizes conclusions
- Automatically generate Markdown meeting records

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit the `config.yaml` file to configure LLM models:

```yaml
llm_models:
  - name: "gpt-4"
    base_url: "https://api.openai.com/v1"
    api_key: "your_api_key_here"
    model: "gpt-4"
```

## Running

```bash
python app.py
```

Visit http://localhost:7860

## Meeting Process

1. Host opens the meeting and announces the topic
2. Round 1: Participants speak in turn
3. Subsequent rounds: Discussion (pros and cons, rationality, etc.)
4. Host summarizes and generates conclusions

## Project Structure

- `app.py` - Gradio main program
- `meeting_engine.py` - Meeting process control engine
- `llm_client.py` - LLM model client
- `llm_loader.py` - Model configuration loader
- `searcher.py` - Online search module
- `config.py` - Global configuration
- `config.yaml` - LLM model configuration file
- `meetings/` - Meeting records storage directory

---

# AI会议室

一个基于LLM模型的AI会议室系统,支持多模型、多角色的智能会议讨论。

## 功能特性

- 支持接入不同的LLM模型(OpenAI兼容API)
- 同一模型的不同角色配置
- 可配置参会人数和角色
- 在线搜索功能支持观点论证
- 主持人维持会议秩序并整理结论
- 自动生成Markdown会议记录

## 安装

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml` 文件配置LLM模型:

```yaml
llm_models:
  - name: "gpt-4"
    base_url: "https://api.openai.com/v1"
    api_key: "your_api_key_here"
    model: "gpt-4"
```

## 运行

```bash
python app.py
```

访问 http://localhost:7860

## 会议流程

1. 主持人开场并宣布议题
2. 第一轮:参会者依次发言
3. 后续轮次:讨论环节(优缺点、合理性等)
4. 主持人总结并生成结论

## 项目结构

- `app.py` - Gradio主程序
- `meeting_engine.py` - 会议流程控制引擎
- `llm_client.py` - LLM模型客户端
- `llm_loader.py` - 模型配置加载器
- `searcher.py` - 在线搜索模块
- `config.py` - 全局配置
- `config.yaml` - LLM模型配置文件
- `meetings/` - 会议记录存储目录
