# Multi-Agent Meeting Assistant

基于 DeepSeek API 和 LangGraph 的会议纪要生成系统。将语音文本自动转换为摘要和结构化行动项。

## 功能

- 语音转文字（当前使用模拟节点，可替换真实 ASR）
- 按议题将长文本切分为逻辑段落
- 生成会议摘要
- 提取行动项（内容、负责人、截止时间），使用 Function Calling

## 技术栈

- FastAPI + Uvicorn
- LangGraph (StateGraph + TypedDict)
- Pydantic v2
- pydantic-settings
- langchain-openai (对接 DeepSeek API)
- deepseek-chat 模型

## 工作流

四个节点顺序执行：

1. transcribe_node - 返回会议文本
2. split_node - 调用 LLM 按议题分割
3. summary_node - 生成摘要
4. action_node - 提取行动项

分割后的内容同时输入摘要和行动项节点，最后整合返回。

## 环境变量

创建 `.env` 文件：
DEEPSEEK_API_KEY=sk-your-api-key
USE_MOCK_LLM=false
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

text

`USE_MOCK_LLM=true` 时不调用 API，使用假数据，方便调试。
