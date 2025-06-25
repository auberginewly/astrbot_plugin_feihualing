# 🌸 AstrBot 飞花令插件

> 一个支持限时飞花令记分的 AstrBot 插件，让古诗词游戏更有趣！

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-v3.5+-green.svg)](https://github.com/Soulter/AstrBot)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

## ✨ 功能特色

- 🎮 **多群支持** - 不同群/用户可同时进行独立的飞花令游戏
- ⏰ **精确计时** - 支持自定义游戏时长（1-60分钟）
- 🤖 **LLM 智能检测** - 使用 AstrBot 接入的 LLM API 智能判断输入是否为古诗词
- 🎯 **令字检验** - 自动验证诗句是否包含指定令字
- 🚫 **重复检测** - 防止同一局内重复使用诗句
- 📊 **积分系统** - 每句诗得1分，实时反馈，累积排行
- 🏆 **会话隔离** - 不同群聊/私聊的积分和排名完全独立
- 📋 **局历史** - 可查看最近一局的详细排名和游戏数据
- 💾 **数据持久化** - 积分和诗句历史自动保存
- 🎨 **用户友好** - 清晰的游戏提示和错误处理
- 🔧 **易于部署** - 完全符合AstrBot插件规范

## 🚀 快速开始

### 安装方式

#### 方法1: 通过AstrBot管理面板
1. 登录AstrBot管理面板
2. 进入"插件管理"页面
3. 点击"安装插件"
4. 输入仓库地址：`https://github.com/auberginewly/astrbot_plugin_feihualing.git`
5. 点击安装

#### 方法2: 通过命令行（需要管理员权限）
```
/plugin get https://github.com/auberginewly/astrbot_plugin_feihualing.git
```

#### 方法3: 手动安装
```bash
cd /path/to/astrbot/data/plugins
git clone https://github.com/auberginewly/astrbot_plugin_feihualing.git
```

### 基本使用

#### 1. 查看帮助
```
/feihualing_help
```

#### 2. 开始游戏
```
/feihualing <时间(分钟)> <令字>
```
例如：
```
/feihualing 2 月        # 开始2分钟的"月"字飞花令
/feihualing 5 花        # 开始5分钟的"花"字飞花令
```

#### 3. 回答诗句
游戏开始后，直接在群内发送包含令字的诗句：
```
明月几时有            # 包含"月"字
举头望明月            # 包含"月"字
月落乌啼霜满天        # 包含"月"字
```

#### 4. 查看积分
```
/feihualing_score
```

#### 5. 查看最近一局排名
```
/feihualing_last
```

#### 6. 强制结束游戏
```
/feihualing_stop
```

## 🎯 游戏规则

### 基本规则
1. **令字要求**：诗句必须包含指定的令字
2. **诗句格式**：3-20个汉字，去除标点符号后全为汉字
3. **单局唯一性**：同一轮游戏中不能重复使用相同诗句
4. **局间重置**：每局游戏结束后，诗句库清空，下局可重复使用
5. **计分规则**：每成功回答一句诗得1分

### 游戏流程
1. 管理员或有权限用户发起游戏
2. 系统宣布游戏开始，显示令字和时限
3. 玩家在群内回复包含令字的诗句
4. 系统实时验证并计分
5. 时间到后自动结束，公布积分榜

## 📊 指令列表

| 指令 | 说明 | 示例 |
|------|------|------|
| `/feihualing <时间> <令字>` | 开始飞花令游戏 | `/feihualing 2 月` |
| `/feihualing_help` | 显示帮助信息 | `/feihualing_help` |
| `/feihualing_score` | 查看总积分榜（当前会话） | `/feihualing_score` |
| `/feihualing_last` | 查看最近一局详细排名 | `/feihualing_last` |
| `/feihualing_stop` | 强制结束当前游戏 | `/feihualing_stop` |

## ⚙️ 配置说明

### 🤖 LLM 智能检测配置

**重要：** 本插件使用 LLM API 进行智能古诗词检测，需要在 AstrBot 中配置 LLM Provider。

#### 支持的 LLM Provider：
- 🇨🇳 **智谱AI (glm-4-flash)** - 推荐，响应快，准确度高
- 🌐 **OpenAI (gpt-3.5-turbo/gpt-4)** - 经典选择，稳定可靠  
- 🇨🇳 **阿里通义千问 (qwen-turbo)** - 国内服务，响应快
- 🌐 **Google Gemini** - 免费额度大
- 🌐 **Anthropic Claude** - 文学理解能力强
- 🔧 **其他兼容 OpenAI API 的服务**

#### 配置步骤：
1. **访问 AstrBot 管理面板**：http://localhost:6185
2. **进入 LLM 配置页面**：点击左侧菜单 `LLM 配置`
3. **添加 Provider**：选择任意一个 LLM 服务商
4. **设置为默认**：将添加的 Provider 设为默认
5. **重启 AstrBot**：使配置生效

#### 未配置 LLM 的影响：
- ⚠️ 插件会显示警告信息
- 🔄 自动回退到基础规则检测（准确度较低）
- 💡 建议配置 LLM 以获得最佳体验

详细配置教程：[LLM 配置指南](docs/llm-config.md)

### 📁 数据存储

插件数据存储在 `data/feihualing/` 目录下：
- `scores.json` - 总积分数据（按会话分类）
- `last_game.json` - 最近一局游戏详情（按会话分类）

**数据结构特点：**
- 所有数据按会话ID（群聊/私聊）独立存储
- 不同群聊之间的积分完全隔离
- 每局游戏结束后会保存详细的游戏记录
- 诗句重复检测仅在单局内生效，每局结束后重置

## 🛠️ 开发者信息

### 技术实现
- **异步处理** - 基于 asyncio 的异步游戏管理
- **多会话支持** - 使用会话ID区分不同聊天环境
- **LLM 古诗检测** - 调用 AstrBot 的 LLM Provider API 智能判断古诗词
- **数据持久化** - JSON格式存储游戏数据
- **错误处理** - 完善的异常捕获和用户友好提示

### LLM 古诗检测机制
- **智能识别** - 使用大语言模型判断输入是否为古诗词句子
- **基础过滤** - 先进行基础格式检查（长度、汉字等）
- **降级处理** - LLM 不可用时自动降级为基础检查
- **准确性提升** - 相比传统规则匹配，大幅提高识别准确率

### 依赖要求
- Python 3.10+
- AstrBot 3.5+
- 标准库：`asyncio`, `json`, `os`, `re`, `datetime`, `typing`

### 目录结构
```
astrbot_plugin_feihualing/
├── main.py          # 主程序文件
├── metadata.yaml    # 插件元数据
├── README.md        # 说明文档
└── LICENSE          # 许可证
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [AstrBot](https://github.com/Soulter/AstrBot) - 强大的多平台聊天机器人框架
- 感谢所有为中华古典诗词文化传承做出贡献的人们

## 📞 支持

- 🐛 [提交Bug报告](https://github.com/auberginewly/astrbot_plugin_feihualing/issues)
- 💡 [功能建议](https://github.com/auberginewly/astrbot_plugin_feihualing/issues)
- 📖 [AstrBot文档](https://astrbot.app)

---

<div align="center">
Made with ❤️ for AstrBot Community
</div>
