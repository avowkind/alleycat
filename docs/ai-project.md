# AlleyCat - Andrews command line AI chat tool

Goal: Create a simple command line tool that carry on a chat conversation with a remote LLM.  

## Features

### Core Functionality

1. **Dual Operation Modes**
   - Single-shot mode: Accept input and return one response (Unix pipe-friendly)
   - Interactive mode: Continuous conversation with shift+enter for submission

2. **Input/Output Handling**
   - Streaming responses in interactive mode
   - Support for multi-line input
   - Command history navigation (in interactive mode)
   - Optional response formatting (plain text, markdown, JSON)

3. **Configuration Management**
   - API key management:
     - Environment variable (LLM_API_KEY)
     - .env file support
     - Command-line parameter (--api-key)
   - Model selection:
     - Default model configuration
     - Command-line model override (--model)
     - Support for multiple LLM providers

4. **Session Management**
   - Conversation history persistence
   - Session export/import (JSON format)
   - Context window management
   - Optional conversation memory limits

5. **Developer Features**
   - Debug mode (--debug)
   - Request/response logging
   - Response timing statistics
   - Token usage tracking

### Additional Features

1. **System Prompts**
   - Load custom system prompts from files
   - Default role templates
   - Command-line system prompt override

2. **Output Control**
   - Temperature/creativity adjustment
   - Maximum token limit setting
   - Response format specification

3. **Utility Functions**
   - Conversation export to markdown/text
   - Clear conversation history
   - Save favorite prompts/conversations

4. **Error Handling**
   - Graceful API error recovery
   - Rate limit handling
   - Network timeout management
   - Clear error messages

## Package Architecture

### Core Package (`alleycat_core`)

1. **LLM Interface Layer**

   ```
   alleycat_core/
   ├── llm/
   │   ├── base.py          # Abstract base classes for LLM interfaces
   │   ├── openai.py        # OpenAI implementation
   │   ├── anthropic.py     # Future Anthropic implementation
   │   └── factory.py       # Factory for creating LLM instances
   ```

2. **Chat Management**

   ```
   alleycat_core/
   ├── chat/
   │   ├── session.py       # Chat session management
   │   ├── history.py       # Conversation history handling
   │   ├── message.py       # Message data structures
   │   └── context.py       # Context window management
   ```

3. **Configuration**

   ```
   alleycat_core/
   ├── config/
   │   ├── settings.py      # Configuration management
   │   ├── models.py        # Model configurations
   │   └── providers.py     # API provider settings
   ```

4. **Common Utilities**

   ```
   alleycat_core/
   ├── utils/
   │   ├── logging.py       # Logging utilities
   │   ├── formatting.py    # Response formatting
   │   └── errors.py       # Custom exceptions
   ```

### Applications (`alleycat_apps`)

1. **Command Line Interface**

   ```
   alleycat_apps/
   ├── cli/
   │   ├── main.py         # Entry point
   │   ├── single_shot.py  # Single response mode
   │   ├── interactive.py  # Interactive mode
   │   └── formatting.py   # CLI-specific formatting
   ```

2. **Future Web Interfaces**

   ```
   alleycat_apps/
   ├── api/                # Future FastAPI implementation
   └── web/                # Future Streamlit implementation
   ```

## Design Principles

1. **Clean Architecture**
   - Core business logic independent of delivery mechanisms
   - Dependencies flow inward: apps → core
   - Core package has no knowledge of applications

2. **Interface Segregation**
   - Abstract base classes for LLM providers
   - Common interface for all chat implementations
   - Separate interfaces for streaming vs non-streaming responses

3. **Dependency Injection**
   - LLM clients injected into chat sessions
   - Configuration injected into components
   - Facilitates testing and provider switching

4. **Configuration Management**
   - Hierarchical configuration (env vars → files → CLI)
   - Provider-specific settings isolated
   - Easy addition of new configuration options

5. **Error Handling**
   - Custom exception hierarchy
   - Error translation between providers
   - Consistent error reporting across interfaces

6. **Testing Strategy**
   - Core package thoroughly unit tested
   - Mock LLM providers for testing
   - Integration tests for applications
   - Separate test fixtures by provider

## Implementation Priority

1. Basic CLI with single-shot mode
2. Interactive mode with streaming
3. Configuration management
4. Session management
5. Additional features based on usage feedback
