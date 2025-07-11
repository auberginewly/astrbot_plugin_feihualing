# 📋 版本更新日志

## v1.2.0 (2025-06-25)

### 🚀 新功能
- **LLM 智能古诗检测**：集成 AstrBot 的 LLM Provider API，使用大语言模型智能判断古诗词
- **多 LLM 支持**：支持 OpenAI、智谱AI、通义千问、Gemini、Claude 等多种 LLM 服务
- **智能降级**：LLM 不可用时自动回退到基础规则检测

### 🔧 改进优化
- **详细日志**：增加 emoji 标识的详细调试日志，方便问题排查
- **用户体验**：优化错误提示信息，提供更友好的反馈
- **提示词优化**：精心设计的 LLM 提示词，提高古诗词识别准确率
- **异步处理**：LLM 调用采用异步机制，不阻塞游戏流程

### 🎯 功能增强
- **配置检测**：自动检测 LLM Provider 配置状态
- **多格式支持**：兼容多种 LLM 响应格式（是/否/yes/true等）
- **错误处理**：完善的异常捕获和恢复机制
- **记分优化**：显示具体诗句内容，增强得分反馈

### 🐛 问题修复
- 解决古诗词识别准确度低的问题
- 修复基础检查中的边界条件处理
- 改进重复诗句检测逻辑

---

## v1.1.0 (2025-06-24)

### ✨ 初始功能
- 多群支持的飞花令游戏
- 精确计时和积分系统
- 诗句重复检测
- 数据持久化
- 会话隔离
