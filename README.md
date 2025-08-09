# HTP 心理分析系统 - 模块化版本

## 🧠 项目简介

基于现代化架构的房-树-人（HTP）心理投射测试系统，采用模块化设计，集成了 LangChain、LangGraph 和 Streamlit 技术栈。

## ✨ 系统特性

- **🎨 绘画创作**: 支持 st_tldraw 画布或文件上传
- **🤖 智能分析**: 基于 AWS Bedrock 的多阶段分析
- **💬 聊天界面**: 自然的对话式问答体验
- **📊 心理评估**: 结合 DASS-21 量表的综合评估
- **🔧 模块化设计**: 清晰的代码架构，便于维护

## 📁 项目结构

```
NewProject/
├── main.py                    # 主页面
├── pages/
│   ├── 1_Drawing_Canvas.py    # 绘画画布
│   ├── 2_HTP_Analysis.py      # HTP分析
│   └── 3_Prompt_Management.py # Prompt管理
├── modules/
│   ├── agents/                # HTP分析代理
│   ├── prompts/               # Prompt管理
│   ├── surveys/               # 问卷调查 (DASS-21)
│   ├── ui/                    # UI组件
│   └── utils/                 # 工具模块
├── prompts/            # YAML Prompt 文件
├── requirements.txt           # 依赖列表
└── README.md                  # 本文档
```

## 🚀 快速开始

### 1. 环境准备

> - [Installation | uv](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1)
>
> `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
uv sync
```

> ```bash
> # 安装依赖
> pip install -r requirements.txt
> 
> # 可选：安装绘画组件 (如果需要画布功能)
> pip install streamlit-tldraw
> ```

### 2. 环境配置

创建 `.env` 文件并配置 AWS 凭据：

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 3. 运行系统

```bash
# 启动主应用
uv run streamlit run main.py

# 或直接启动特定页面
# uv run streamlit run pages/1_Drawing_Canvas.py
# uv run streamlit run pages/2_HTP_Analysis.py
# uv run streamlit run pages/3_Prompt_Management.py
```

## 📋 使用流程

1. **🖼️ 绘画阶段**: 在画布中创作或上传 HTP 绘画
2. **🤖 分析阶段**: 系统分析图像并进行智能问答
3. **📝 评估阶段**: 完成 DASS-21 量表评估
4. **📊 报告阶段**: 获得完整的心理状态评估报告

## 🔧 系统配置

### AWS Bedrock 模型

支持的模型：
- `amazon.nova-pro-v1:0` (推荐)
- `amazon.nova-lite-v1:0`
- `amazon.nova-micro-v1:0`
- ...

### Prompt 管理

- 所有 prompt 使用 YAML 格式存储
- 支持 metadata、版本管理
- 基于 LangChain `load_prompt` 标准

## 🏗️ 架构设计

### 模块化组件

1. **agents/**: HTP 分析代理
   - `htp_agent.py`: 主要代理类
   - `nodes.py`: LangGraph 节点函数

2. **prompts/**: Prompt 管理
   - `manager.py`: Prompt 管理器

3. **surveys/**: 问卷模块
   - `dass21.py`: DASS-21 量表实现

4. **ui/**: UI 组件
   - `chat.py`: 聊天界面
   - `components.py`: 通用组件

5. **utils/**: 工具模块
   - `state.py`: 状态管理
   - `models.py`: LLM 模型管理
   - `image.py`: 图像处理

### 状态管理

使用 `HTPState` TypedDict 管理完整的分析流程状态：
- 图像数据
- 对话历史
- 分析结果
- 进度跟踪

## 🔍 技术特点

### LangGraph 集成

虽然定义了 LangGraph 工作流，但实际实现中采用直接调用节点函数的方式，原因：
- 更好的 Streamlit 集成
- 更灵活的状态管理
- 更直观的错误处理

### Prompt 标准化

- 符合 LangChain Prompt Serialization 标准
- YAML 格式，易于维护
- 支持变量验证和类型推断

## 🛠️ 开发指南

### 添加新的分析节点

1. 在 `modules/agents/nodes.py` 添加节点函数
2. 在 `modules/agents/htp_agent.py` 添加代理方法
3. 在相应页面调用新方法

### 添加新的 Prompt

1. 在 `prompts/` 创建 YAML 文件
2. 遵循现有的 metadata 格式
3. 在 `modules/prompts/manager.py` 添加映射

### 自定义 UI 组件

1. 在 `modules/ui/components.py` 添加新组件
2. 遵循 Streamlit 最佳实践
3. 保持组件的可复用性

## 🐛 故障排除

### 常见问题

1. **Prompt 加载失败**
   - 检查 `prompts/` 目录是否存在
   - 验证 YAML 文件格式

2. **模型调用失败**
   - 检查 AWS 凭据配置
   - 确认 Bedrock 服务可用性

3. **绘画功能不可用**
   - 安装 `streamlit-tldraw` 组件
   - 使用文件上传作为备选方案

## 📈 性能优化

- 使用 `@st.cache_data` 缓存 Prompt 加载
- 使用 `@st.cache_resource` 缓存模型实例
- 合理管理会话状态大小

## 🔒 安全考虑

- 所有数据仅在会话期间存储
- 不保存用户绘画或分析结果
- 遵循心理咨询伦理标准

## 📄 许可证

本项目仅供学习和研究使用，不可用于商业目的。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进系统。

---

**注意**: 本系统提供的心理分析仅供参考，不能替代专业的心理咨询或临床诊断。
