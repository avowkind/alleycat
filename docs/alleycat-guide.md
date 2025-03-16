# Alleycat: AI-Powered Text Transformation Tool

Alleycat is a command-line text processing utility that transforms input text using Large Language Models (LLMs). Like traditional Unix tools such as `awk` or `sed`, alleycat reads from standard input or command arguments and writes transformed text to standard output. Instead of using pattern matching or scripted transformations, alleycat leverages AI to interpret and modify text based on natural language instructions.

## Why Alleycat?

Alleycat follows Unix philosophy: it does one thing well - transforming text through AI. It accepts input through pipes or arguments, processes the text using LLMs, and outputs the result in various formats (plain text, markdown, or JSON). This makes it a powerful addition to shell scripts and text processing pipelines, enabling sophisticated text transformations through simple natural language commands.

## Key Features

- **Single-shot Mode**: Perfect for quick queries and Unix pipe-friendly operations
- **Flexible Input/Output**: Supports multiple input methods and formatting options (text, markdown, JSON)
- **Configurable**: Easy setup via environment variables, .env files, or command-line parameters
- **Modern Architecture**: Built on top of the latest OpenAI API with room for more providers
- **Rich Output Formatting**: Beautiful terminal output with support for markdown rendering

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

### Advanced Options

Customize your experience with various command-line options:

```bash
alleycat --model gpt-4 --temperature 0.9 --format markdown "Write a haiku about coding"
In code, thoughts take flight, Binary truths weave through night, Silent keys alight. 
```

Key options include:

- `--model, -m`: Choose your LLM model
- `--temperature, -t`: Adjust response creativity (0.0-2.0)
- `--format, -f`: Set output format (text, markdown, json)
- `--stream, -s`: Stream responses as they're generated

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
$ alleycat -i prompts/johnson.txt "What is Python?"
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
$ alleycat -i prompts/diderot.txt "What is Python?"
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

3. Translating Diderot's French response to English using pipes:
```bash
$ alleycat -i prompts/diderot.txt "What is Python?" | alleycat -i "You are a precise translator. Translate the French text to English while preserving the original formatting and structure. Maintain all section headers in their original format."
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

## Future Features

The roadmap for Alleycat includes exciting additions:

- Interactive mode for continuous conversations
- Support for multiple LLM providers
- Chat history management
- Custom prompt templates
- Streaming responses
- Context window management

## Getting Started

1. Clone the repository and change to the project directory:

```bash
git clone https://github.com/avowkind/alleycat.git
cd alleycat
```

2. Create and activate a virtual environment using Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

3. Install the package in development mode with dependencies:

```bash
pip install -e ".[dev]"
```

4. Set up your OpenAI API key:

```bash
export ALLEYCAT_OPENAI_API_KEY="your-api-key"
# or add to .env file:
echo "ALLEYCAT_OPENAI_API_KEY=your-api-key" > .env
```

5. Verify the installation:

```bash
alleycat "Hello, Alleycat!"
```

## Conclusion

Alleycat brings the power of AI to your command line in a clean, efficient package. Whether you're using it for quick queries in the terminal or integrating it system-wide for text processing, its flexibility and ease of use make it an invaluable tool for developers and writers alike.

By setting up system-wide shortcuts, you can leverage Alleycat's capabilities in any application that handles text, making it a truly versatile assistant for all your AI-powered text processing needs.
