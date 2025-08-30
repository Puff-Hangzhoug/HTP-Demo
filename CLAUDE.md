# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Alternative: Use pip to install dependencies
pip install -r requirements.txt

# Optional: Install drawing component if needed
pip install streamlit-tldraw
```

### Running the Application
```bash
# Run the main application
uv run streamlit run main.py

# Run specific pages
uv run streamlit run pages/1_Drawing_Canvas.py
uv run streamlit run pages/2_HTP_Analysis.py
uv run streamlit run pages/3_Prompt_Management.py
```

### Environment Configuration

Create a `.env` file in the root directory with the following AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

## Code Architecture

### Overview

This project is a House-Tree-Person (HTP) psychological projection test system using a modular architecture, integrating LangChain, LangGraph, and Streamlit. The system provides an interactive drawing canvas, AI-powered analysis, chat interface, psychological assessment with DASS-21 scale, all within a modular design.

### Key Components

1. **Main Structure**
   - `main.py`: Main entry point and dashboard
   - `pages/`: Streamlit pages for different features
   - `modules/`: Core functional modules
   - `prompts/`: YAML-based prompt templates

2. **Modules**
   - `modules/agents/`: HTP analysis agent and LangGraph nodes
   - `modules/prompts/`: Prompt management system
   - `modules/surveys/`: Questionnaires (DASS-21)
   - `modules/ui/`: UI components
   - `modules/utils/`: Utility functions

3. **State Management**
   - Uses a `HTPState` TypedDict defined in `modules/utils/state.py`
   - Manages image data, conversation history, analysis results, and progress tracking

4. **LLM Integration**
   - AWS Bedrock as the LLM provider
   - Supports multiple models with `amazon.nova-pro-v1:0` recommended
   - Connection managed in `modules/utils/models.py`

5. **Prompt System**
   - YAML-based prompts in `prompts/` directory
   - LangChain compatible format
   - Managed by `PromptManager` in `modules/prompts/manager.py`

6. **LangGraph Implementation**
   - Although LangGraph workflow is defined, the system primarily uses direct node function calls
   - Node functions in `modules/agents/nodes.py`
   - Agent class in `modules/agents/htp_agent.py`

## Development Patterns

### Adding New Analysis Nodes

1. Add node functions in `modules/agents/nodes.py`
2. Add agent methods in `modules/agents/htp_agent.py`
3. Call new methods from relevant pages

### Adding New Prompts

1. Create YAML files in `prompts/` directory
2. Follow existing metadata format
3. Update mappings in `modules/prompts/manager.py`

### Creating UI Components

1. Add components in `modules/ui/components.py`
2. Follow Streamlit best practices
3. Keep components reusable

### Performance Optimizations

- Use `@st.cache_data` for prompt loading
- Use `@st.cache_resource` for model instances
- Manage session state size efficiently
