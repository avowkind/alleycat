# Alleycat: AI-Powered Text Transformation Tool

Alleycat is a command-line text processing utility that transforms input text using Large Language Models (LLMs). Like traditional Unix tools such as `awk` or `sed`, alleycat reads from standard input or command arguments and writes transformed text to standard output. Instead of using pattern matching or scripted transformations, alleycat leverages AI to interpret and modify text based on natural language instructions.

## Why Alleycat?

Alleycat follows Unix philosophy: it does one thing well - transforming text through AI. It accepts input through pipes or arguments, processes the text using LLMs, and outputs the result in various formats (plain text, markdown, or JSON). This makes it a powerful addition to shell scripts and text processing pipelines, enabling sophisticated text transformations through simple natural language commands.

## Key Features

- **Single-shot Mode**: Perfect for quick queries and Unix pipe-friendly operations
- **Interactive Chat Mode**: Engage in continuous back-and-forth conversations
- **Flexible Input/Output**: Supports multiple input methods and formatting options (text, markdown, JSON)
- **Configurable**: Easy setup via environment variables, .env files, or command-line parameters
- **Modern Architecture**: Built on top of the latest OpenAI API with room for more providers
- **Rich Output Formatting**: Beautiful terminal output with support for markdown rendering

## Getting Started

1. Install AlleyCat using pip:

   ```bash
   pip install alleycat
   ```

2. Set up your configuration (you'll need an OpenAI API key):

   ```bash
   alleycat-admin setup
   ```

3. Run a basic prompt:

   ```bash
   alleycat "Hello, Alleycat!"
   ```

For developers interested in contributing to or modifying AlleyCat, please refer to our [Developer's Guide](developers-guide.md).

## Basic Usage

The simplest way to use Alleycat is through direct command-line queries:

```bash
alleycat "What is the capital of France?"
The capital of France is Paris.
```

You can also pipe content into Alleycat:

```bash
echo "Explain Bells paradox in 2 sentences" | alleycat
Bell's paradox, also known as Bell's spaceship paradox, involves two spaceships 
accelerating simultaneously in the same direction with a string connecting them. 
Due to relativistic effects, such as length contraction from the perspective of an 
observer at rest, the string experiences tension and eventually breaks, 
illustrating non-intuitive aspects of special relativity.
```

You can run an interactive chat session:

```bash
alleycat --chat lets talk about space.
```

You can include a file in the prompt:

```bash
alleycat --file docs/alleyfacts.pdf tell me something about this document
```

### Advanced Options

Customize your experience with various command-line options:

```bash
alleycat --model gpt-4 --temperature 0.9 --mode markdown "Write a haiku about coding"
In code, thoughts take flight, Binary truths weave through night, Silent keys alight. 
```

Key options include:

- `--model`: Choose your LLM model
- `--temperature, -t`: Adjust response creativity (0.0-2.0)
- `--mode, -m`: Set output mode (text, markdown, json)
- `--file, -f`: Upload and reference a file in your conversation
- `--stream, -s`: Stream responses as they're generated
- `--chat, -c`: Enter interactive chat mode with continuous conversation

### Command Generation and Execution

Alleycat is especially useful for generating and executing shell commands. You can ask it to create a command in natural language and then pipe the result directly to your shell:

```bash
# Ask for a command to list files sorted by modification time
alleycat "Give me the bash command to list all files in the current directory sorted by modification time, newest first. Just return the raw command without explanation or backticks." | bash

# The command generated and executed might be:
# ls -lt
```

For more consistent results when generating commands, use the included `bash.txt` prompt file:

```bash
# Use the bash prompt to get clean, executable commands
alleycat -i prompts/bash.txt "list files sorted by modification time" | bash

# Commands will be returned without explanations, ready for piping
alleycat -i prompts/bash.txt "find files larger than 10MB" | bash
```

The bash prompt is designed to:

- Return only the raw command with no explanations or formatting
- Generate safe and non-destructive commands where possible
- Add appropriate safeguards for potentially dangerous operations
- Produce output that can be directly piped to bash

This approach is particularly helpful for complex commands that you might not remember:

```bash
# Find large files
alleycat "Command to find the 10 largest files in this directory and subdirectories" | bash
# Might execute: find . -type f -exec du -h {} \; | sort -rh | head -n 10

# Complex grep pattern
alleycat "Command to find all Python files containing either 'import pandas' or 'import numpy'" | bash
# Might execute: grep -E "import (pandas|numpy)" --include="*.py" -r .
```

For safety, you can review the command before execution:

```bash
# Review the command first
command=$(alleycat "Command to back up all .py files to a timestamped directory")
echo "About to execute: $command"
read -p "Execute? (y/n) " confirm
[[ $confirm == [yY] ]] && eval "$command"
```

This makes Alleycat an excellent tool for command discovery and automation, combining AI assistance with the power of the shell.

### Interactive Chat Mode

Alleycat supports an interactive chat mode that allows continuous back-and-forth conversations with the AI model. The chat maintains context between messages, enabling you to have coherent multi-turn dialogues. Chat mode automatically enables response streaming for a more interactive experience (unless using JSON or schema output formats).

```bash
# Start a chat with an initial message
alleycat --chat "Hello, tell me about yourself"

# Start a chat without an initial message
alleycat --chat

# talk with Dr Johnson or Diderot
alleycat -c -i prompts/johnson.txt

# Start a chat with a file and discuss its contents
alleycat --chat -f docs/alleyfacts.pdf "Let's discuss this document about alleycat features"

# Disable streaming in chat mode if needed
alleycat --chat --no-stream "Hello"
```

In interactive chat mode:

1. The AI responds to your message
2. You're prompted to enter your next message with a simple ">" prompt
3. The conversation continues until you:
   - Press Enter with an empty message
   - Press Ctrl+C to interrupt the session

Example chat session:

```bash
$ alleycat --chat "What are the three laws of robotics?"

Alleycat Interactive Chat

The three laws of robotics, formulated by science fiction author Isaac Asimov, are:

1. First Law: A robot may not injure a human being or, through inaction, allow a human being to come to harm.

2. Second Law: A robot must obey the orders given it by human beings except where such orders would conflict with the First Law.

3. Third Law: A robot must protect its own existence as long as such protection does not conflict with the First or Second Law.

These laws first appeared in Asimov's 1942 short story "Runaround" and became a foundation for many of his science fiction works involving robots.

>Who created these laws?
Isaac Asimov created the Three Laws of Robotics. He was an American writer and professor of biochemistry, known for his works of science fiction and popular science. Asimov introduced these laws in his 1942 short story "Runaround," which was part of his Robot series. The laws became a central theme in many of his subsequent stories and novels about robots and have since become influential in discussions about AI ethics and robot behavior, even beyond the realm of fiction.

>
```

Example chat session with a file:

```bash
$ alleycat --chat -f docs/alleyfacts.pdf "What is this document about?"

Alleycat Interactive Chat

This document is about AlleyCat, a command-line text processing utility that uses Large Language Models (LLMs) to transform input text. The document details the key features, usage examples, and capabilities of AlleyCat, including its ability to process text through standard input/output, support for various formatting options, and integration with Unix-style workflows.

>What file formats does it support?

According to the document, AlleyCat supports multiple file formats, including PDF, TXT, and CSV files. It can analyze these files when provided through the -f or --file option, allowing users to ask questions about the file content or extract information from them.

>How does it handle file cleanup?

The document mentions that when files are used with AlleyCat, they are temporarily uploaded to the LLM provider (specifically OpenAI) for analysis, and then automatically deleted when the program exits. This ensures that no files remain on the provider's servers after your session ends.

>
```

Interactive chat mode maintains conversation context between messages, allowing the AI to reference earlier parts of the conversation. This makes it ideal for:

- Iterative problem solving
- Extended discussions on complex topics
- Educational dialogues where follow-up questions build on previous answers
- Creative writing assistance with ongoing feedback

### Knowledge Base Support

Alleycat includes a powerful knowledge base feature that allows you to create, manage, and query collections of documents. Knowledge bases use vector embeddings to enable natural language queries against your own content, making it ideal for document-based assistants, project documentation, research papers, and more.

```bash
# Create a new knowledge base
alleycat-admin kb create my_project

# Add files to the knowledge base
alleycat-admin kb add my_project docs/*.md docs/*.pdf

# Query your knowledge base
alleycat --kb my_project "What are the key components of our architecture?"

# Set a default knowledge base
alleycat-admin kb default my_project

# List all knowledge bases
alleycat-admin kb ls

# List files in a specific knowledge base
alleycat-admin kb ls --name my_project

# Remove a knowledge base
alleycat-admin kb rm my_project
```

Knowledge bases are particularly useful for:

- Creating documentation assistants for your projects
- Building domain-specific knowledge repositories
- Creating specialized chatbots with access to proprietary information
- Maintaining living documentation that can be queried naturally

You can combine knowledge base queries with other Alleycat features:

```bash
# Use with streaming output
alleycat --kb my_project --stream "Explain our authentication flow in detail"

# Use with chat mode
alleycat --kb my_project --chat "Let's discuss our API design"

# Query multiple knowledge bases
alleycat --kb project_docs --kb reference_material "Compare our approach with best practices"

# Combine with web search
alleycat --kb my_project --web "How does our implementation compare to current trends?"
```

For detailed information about knowledge base features, including implementation details and best practices, see the [Knowledge Base documentation](docs/knowledge-base.md).

### File Analysis

Alleycat can analyze files and answer questions about their content using the `-f` or `--file` option:

```bash
# Basic file analysis
alleycat -f docs/alleyfacts.pdf "Summarize this document"

# Ask specific questions about the content
alleycat -f docs/alleyfacts.pdf "What are the key features of alleycat mentioned in this document?"

# Combine with markdown output
alleycat -f docs/alleyfacts.pdf -m markdown "Extract the main points as a bulleted list"

# Use with custom instructions
alleycat -f docs/alleyfacts.pdf -i "You are a technical reviewer. Be critical and identify any issues or limitations in the document." "Review this document"
```

The file is temporarily uploaded to the LLM provider (OpenAI) for analysis and automatically deleted when the program exits.

#### Supported File Formats and Limitations

The following file formats are currently supported:

- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- CSV (.csv)
- JSON (.json)
- JSONL (.jsonl)

**Important limitations:**

- **File Size**: Files must be within the token limit of the model being used. If your file is too large, you'll receive a token limit error.
- **Content Processing**: The quality of analysis depends on the model's ability to parse and understand the file content.

**Tips for handling large files:**

1. Split the file into smaller parts
2. Use a model with a larger context window (like gpt-4-turbo with a 128k token context)
3. Extract only the most relevant sections before uploading

## System-Wide Integration

One of the most powerful ways to use Alleycat is by integrating it with your system-wide text editing workflow. Here's how to set it up on macOS:

### 1. Create an Automator Service

1. Open Automator
2. Create a new "Quick Action"
3. Configure the workflow:
   - Workflow receives: "text"
   - In: "any application"
4. Add a "Run Shell Script" action
5. Configure the shell script:

```bash
#!/bin/zsh
VENV_PATH="$HOME/path/to/your/venv"
source "$VENV_PATH/bin/activate"
echo "$1" | alleycat
```

6. Save the service with a memorable name (e.g., "Ask Alleycat")

### 2. Set Up a Keyboard Shortcut

1. Open System Settings
2. Navigate to Keyboard > Keyboard Shortcuts > Services
3. Find your "Ask Alleycat" service
4. Assign a keyboard shortcut (e.g., ⌘⌥A)

Now you can use Alleycat from any text editor:

1. Select text you want to process
2. Press your keyboard shortcut
3. The selected text will be replaced with Alleycat's response

This setup is particularly useful for:

- Quick text transformations in Notes app
- Code documentation in any editor
- Writing assistance in email clients
- Format conversion in text editors

## System Instructions

Alleycat can be configured to respond in different styles or personas using system instructions. These can be provided either directly via the `-i` option or through instruction files.

### Example: Historical Personas

Here's how the same query about Python yields dramatically different responses using two historical personas:

1. Using Dr. Johnson's style (from `prompts/johnson.txt`):

```bash
alleycat -i prompts/johnson.txt "What is Python?"
```

```
PYTHON [ˈpaɪθɑn] n.s. [from Greek Πύθων]

1. A species of serpent, much celebrated in antiquity; now more commonly encountered in the gardens of natural philosophers.

2. By modern usage: A system of computation, invented by one Van Rossum, a Dutch mechanick, whereby instructions are given to those engines of calculation that plague our present age. Like its serpentine namesake, it is said to embrace its objects wholly, though whether it constricts or merely comprehends them, I leave to the reader's judgment.

"The Python's coils, though writ in text so plain,
Do wrap our logic in their smooth domain." -- Contemporary Verse

USAGE: Distinguished from other computational tongues by its clarity and philosophical bent toward explicit expression, though I observe that, like all modern contrivances, it may lead the unwary into labyrinths of error through excessive liberty of method.

See also: COMPUTATION, ENGINE, PROGRAM (terms which, in our declining age, have acquired meanings their fathers knew not).
```

2. Using Diderot's style (from `prompts/diderot.txt`):

```bash
alleycat -i prompts/diderot.txt "What is Python?"
```

```
**Python (Substantif, masculin)**

*Définition:* Python est un langage de programmation interprété, à la fois puissant et 
accessible, largement employé dans divers domaines de l'informatique et de la science des 
données. Ce langage se distingue par sa syntaxe claire et lisible, favorisant ainsi une adoption
aisée par les néophytes tout en offrant des capacités avancées pour les experts.

*Histoire et évolution:* Créé par le programmeur Guido van Rossum et publié pour la première 
fois en 1991, Python tire son nom de la troupe humoristique britannique Monty Python, témoignage
de l'esprit ludique de son créateur. Au fil des décennies, il a connu une adoption croissante, 
devenant un pilier essentiel des technologies modernes grâce à sa flexibilité et son large 
écosystème de bibliothèques.

*Observations scientifiques et philosophiques:* Python incarne l'idéal des Lumières en mettant 
l'accent sur la raison et la simplicité. Sa conception encourage une approche rationnelle de la 
résolution de problèmes, permettant aux savants et artisans du numérique de manipuler des 
données complexes avec une efficacité accrue. La communauté qui le soutient valorise le partage 
du savoir et l'amélioration continue, principes chers à notre époque éclairée.

*Arts et métiers pratiques:* Python est utilisé dans des domaines aussi variés que le 
développement web, l'intelligence artificielle, l'analyse de données, et même les arts 
numériques. Sa capacité à automatiser des tâches répétitives et à analyser de vastes ensembles 
de données le rend indispensable pour les chercheurs et ingénieurs modernes.

*Raison et progrès:* Python, par sa nature ouverte et collaborative, représente un progrès pour 
la société, permettant à chacun d'accéder aux outils nécessaires pour innover et contribuer au 
bien commun. Il favorise l'éducation et la démocratisation du savoir technique, en écho à notre 
ambition encyclopédique de disséminer la connaissance.

*Voir aussi:* Informatique, Langage de programmation, Science des données, Intelligence 
artificielle, Automatisation, Partage du savoir.

Ainsi, Python n'est pas simplement un outil technique, mais un vecteur de progrès et de 
transformation sociale, fidèle aux idéaux de notre temps.
```

3. Translating Diderot's French response to English using pipes:

```bash
alleycat -i prompts/diderot.txt "What is Python?" | alleycat -i "You are a precise translator. Translate the French text to English while preserving the original formatting and structure. Maintain all section headers in their original format."
```

```
PYTHON, (Mechanical Arts & Modern Philosophy) n.m. Programming language that takes its name from the Python serpent, a mythological creature from Greek antiquity. Invented by the philosopher-mechanic Guido van Rossum, this language represents the remarkable union between philosophical simplicity and practical utility in the modern art of programming.

METHODICAL DEFINITION: System of instructions intended for calculating machines, characterized by its natural readability and pragmatic philosophy, expressed in its manifesto "The Zen of Python" (see: PHILOSOPHY OF LANGUAGES).

HISTORY & EVOLUTION: Created in 1991, this language perfectly illustrates the progress of reason in the mechanical arts. It follows the principles of clarity and elegance that we, philosophers, seek in all expressions of thought.

PRACTICAL OBSERVATIONS:
- The simplicity of its syntax allows even apprentices to contribute to the mechanical arts
- Its modular approach reflects the very organization of our Encyclopedia
- The libraries (see: MODULES) represent the organized accumulation of knowledge

RELATIONSHIP WITH THE ARTS:
The use of Python extends from astronomical calculations to visual arts, thus demonstrating the universality of rational principles across all domains of knowledge.

See also: PROGRAMMING, ALGORITHMS, MACHINE (Science of calculations), LOGIC (Modern Philosophy)

N.B.: The growing adoption of this language in public instruction suggests a democratization of technical knowledge that we can only approve of.
```

These examples demonstrate how system instructions can transform Alleycat from a simple text processor into a sophisticated tool that can adopt specific voices, styles, and perspectives. The instructions files contain detailed guidance about tone, structure, and characteristic traits of each persona.

## Configuration

Alleycat can be configured through environment variables or a `.env` file:

```bash
ALLEYCAT_OPENAI_API_KEY=your-api-key
ALLEYCAT_MODEL=gpt-4
ALLEYCAT_TEMPERATURE=0.7
```

## Configuration and Setup

AlleyCat includes an interactive setup wizard that makes configuration simple and straightforward.

### Automatic First-time Setup

When you run AlleyCat for the first time, if no configuration file exists and no API key is provided, you'll automatically be guided through the setup process. This ensures a smooth onboarding experience without having to read documentation or learn commands.

The setup wizard will:

1. Create necessary configuration directories following XDG standards
   - Config files: `~/.config/alleycat/` (Linux/macOS) or equivalent on Windows
   - Data files: `~/.local/share/alleycat/` (Linux/macOS) or equivalent on Windows
2. Prompt for your OpenAI API key
3. Let you select your preferred model from available options
4. Configure other settings like temperature and tool defaults

### Manual Configuration Commands

You can revisit the setup process at any time using either of these commands:

```bash
# Use the dedicated setup command
alleycat-admin setup

# Or the --setup flag with the main command
alleycat --setup
```

Both methods provide the same interactive configuration experience.

### Removing Configuration

If you want to remove AlleyCat's configuration and data files, you can use:

```bash
# Remove config using the dedicated command
alleycat-admin setup --remove

# Or with the main command option
alleycat --remove-config
```

This will:

1. Display all configuration and data files that will be removed
2. Ask for confirmation before deletion
3. Optionally remove persona files (with a separate confirmation)

### Configuration File Location

AlleyCat follows the XDG Base Directory Specification for storing configuration:

- **Linux/macOS**: `~/.config/alleycat/config.yml`
- **Windows**: `%APPDATA%\alleycat\config.yml`

The configuration contains settings like your API key (securely stored), preferred model, temperature, and other defaults that will be used for all AlleyCat commands.

## Schema-Based Output

AlleyCat provides powerful schema-based output capabilities that allow you to enforce strict structure on the AI's responses. This feature is particularly useful for automation, data processing, and integration with other tools.

### Overview

The schema feature allows you to:

- Define expected response structures using JSON Schema
- Ensure consistent output format across multiple queries
- Chain multiple schemas for complex transformations
- Validate responses against defined schemas
- Integrate AI responses with automated workflows

### Basic Usage

To use schema-based output, provide a JSON schema file that defines your expected response structure:

```bash
# Basic schema usage
alleycat --schema schemas/person.schema.json "my name is andrew invent a profile for me"

# With file input
alleycat --schema schemas/book_characters.schema.json --file book.txt "extract all characters"
```

### Schema Files

Schema files are JSON documents that follow the JSON Schema specification. Here's an example schema for person profiles:

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "The person's name"
    },
    "age": {
      "type": "number",
      "description": "The person's age"
    },
    "gender": {
      "type": "string",
      "description": "The person's gender"
    },
    "location": {
      "type": "string",
      "description": "The person's location"
    },
    "interests": {
      "type": "array",
      "description": "An array of interests of the person",
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["name", "age", "gender", "location", "interests"],
  "additionalProperties": false
}
```

### Schema Chaining

For complex transformations, you can chain multiple schemas together:

```bash
# Chain extraction and transformation schemas
alleycat --schema-chain "extract.schema.json,transform.schema.json" "process this data"
```

Schema chains are processed sequentially, with each schema's output serving as input for the next schema in the chain.

### Important Notes

1. **Streaming**: Schema-based output automatically disables streaming to ensure complete, valid responses.
2. **Validation**: Responses are validated against the schema before being returned.
3. **Error Handling**: Invalid schemas or responses that don't match the schema will result in clear error messages.
4. **Performance**: Schema validation adds minimal overhead to response processing.

### Example Use Cases

1. **Data Extraction**:

   ```bash
   # Extract structured data from text
   alleycat --schema contact.schema.json "extract contact details from this email"
   ```

2. **Document Analysis**:

   ```bash
   # Analyze document structure
   alleycat --schema document.schema.json --file report.pdf "analyze this report's structure"
   ```

3. **API Integration**:

   ```bash
   # Generate API-compatible responses
   alleycat --schema api_response.schema.json "convert this data for our API"
   ```

4. **Batch Processing**:

   ```bash
   # Process multiple files with consistent output
   for file in docs/*.txt; do
     alleycat --schema summary.schema.json --file "$file" "summarize this document"
   done
   ```

### Best Practices

1. **Schema Design**:
   - Keep schemas focused and specific
   - Use clear, descriptive property names
   - Include detailed descriptions for each field
   - Specify required fields explicitly

2. **Validation**:
   - Test schemas with sample data
   - Handle edge cases in your schema
   - Use appropriate data types
   - Consider adding constraints where needed

3. **Error Handling**:
   - Implement proper error handling in your scripts
   - Validate schemas before using in production
   - Monitor for validation failures

4. **Performance**:
   - Cache frequently used schemas
   - Optimize schema complexity
   - Use schema chains judiciously

## External Tools

Alleycat supports integration with external tools through the OpenAI Responses API. These tools extend the capabilities of the LLM, allowing it to access real-time information or search through document repositories.

### Knowledge Bases

Alleycat now includes a powerful knowledge base feature that allows you to create, manage, and query collections of documents. Knowledge bases use vector embeddings to efficiently search through your documents and provide relevant information to your queries.

#### Managing Knowledge Bases

Use the `alleycat-admin` command to manage your knowledge bases:

```bash
# Create a new knowledge base
alleycat-admin kb create project_docs

# Add files to a knowledge base
alleycat-admin kb add project_docs docs/*.md docs/*.pdf

# List all knowledge bases
alleycat-admin kb ls

# List files in a specific knowledge base
alleycat-admin kb ls --name project_docs

# Set a default knowledge base
alleycat-admin kb default project_docs

# Delete a file from a knowledge base
alleycat-admin kb delete project_docs file-id123456

# Delete an entire knowledge base
alleycat-admin kb rm project_docs
```

#### Querying Knowledge Bases

Once you've created and populated knowledge bases, you can query them directly with the main Alleycat command:

```bash
# Query a specific knowledge base
alleycat --kb project_docs "What are the key components of our architecture?"

# Query multiple knowledge bases
alleycat --kb project_docs --kb reference_material "Compare our API design with best practices"

# Combine with streaming for long responses
alleycat --kb project_docs --stream "Explain the authentication flow in detail"

# Combine with web search for up-to-date information
alleycat --kb project_docs --web "How does our implementation compare to current trends?"
```

The knowledge base feature is particularly useful for:

- Creating documentation assistants for your projects
- Building domain-specific knowledge repositories
- Creating specialized chatbots with access to proprietary information
- Maintaining living documentation that can be queried naturally

For more detailed information, see the [Knowledge Base documentation](docs/knowledge-base.md).

### Web Search

The web search tool allows Alleycat to retrieve up-to-date information from the internet, making it useful for questions about current events, recent developments, or any information that might be beyond the model's training data.

```bash
# Get the latest information about a topic
alleycat --tool web "What are the latest developments in quantum computing?"

# Or use the simpler alias
alleycat --web "What are the latest developments in quantum computing?"

# Ask about current events
alleycat --tool web "What were the major headlines today?"

# Research technical information
alleycat --tool web "What are the new features in Python 3.12?"
```

### File Search with Vector Store

The file search tool enables Alleycat to search through document collections stored in a vector database. This is particularly useful for retrieving specific information from large document repositories or knowledge bases.

```bash
# Search for information in a specific vector store
alleycat --tool file-search --vector-store alleycat_kb "Find information about neural networks"

# Or use the --knowledge alias (preferred)
alleycat --knowledge --vector-store alleycat_kb "Find information about neural networks"

# Or the shorter -k alias
alleycat -k --vector-store alleycat_kb "Find information about neural networks"

# Ask detailed questions about your knowledge base
alleycat --knowledge --vector-store vs_11111111111111 "What does our documentation say about error handling?"
```

Note: Before using the file search tool, you need to set up your vector store and upload documents to it through the OpenAI API.

### Combining Tools

You can also combine multiple tools in a single query for more complex information retrieval:

```bash
# Compare information from the web with your knowledge base
alleycat --tool web --tool file-search --vector-store alleycat_kb "Compare the latest research on LLMs with what we have in our documentation"
```

Using aliases makes the command more concise:

```bash
# Same command with aliases
alleycat --web --knowledge --vector-store vs_11111111111111 "Compare the latest research on LLMs with what we have in our documentation"

# Even shorter with short-form aliases
alleycat -w -k --vector-store vs_11111111111111 "Compare the latest research on LLMs with what we have in our documentation"
```

### Environment Variables

Configure default settings for tools using environment variables:

```bash
# Set a default vector store ID
export ALLEYCAT_VECTOR_STORE=vs_11111111111111
```

## Conclusion

Alleycat brings the power of AI to your command line in a clean, efficient package. Whether you're using it for quick queries in the terminal or integrating it system-wide for text processing, its flexibility and ease of use make it an invaluable tool for developers and writers alike.

By setting up system-wide shortcuts, you can leverage Alleycat's capabilities in any application that handles text, making it a truly versatile assistant for all your AI-powered text processing needs.
