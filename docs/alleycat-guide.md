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

Alleycat supports an interactive chat mode that allows continuous back-and-forth conversations with the AI model. The chat maintains context between messages, enabling you to have coherent multi-turn dialogues.

```bash
# Start a chat with an initial message
alleycat --chat "Hello, tell me about yourself"

# Start a chat without an initial message
alleycat --chat

# talk with Dr Johnson or Diderot
alleycat -c -i prompts/johnson.txt

# Start a chat with a file and discuss its contents
alleycat --chat -f docs/alleyfacts.pdf "Let's discuss this document about alleycat features"
```

In interactive chat mode:

1. The AI responds to your message
2. You're prompted to enter your next message with a simple ">" prompt
3. The conversation continues until you:
   - Press Enter with an empty message
   - Press Ctrl+C to interrupt the session

Example chat session:

```
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

```
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

The conversation context is maintained through OpenAI's conversation API, which preserves the context between messages using response IDs. This allows the AI to understand references to previous messages and maintain a coherent conversation without having to repeat information.

You can combine chat mode with other options, such as model selection, temperature, and output format:

```bash
alleycat --chat --model gpt-4o --temperature 0.8 --mode markdown
```

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

## Future Features

The roadmap for Alleycat includes exciting additions:

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
