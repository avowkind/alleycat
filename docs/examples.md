# Various examples

## File handling

### read a text file

`alleycat -v -f docs/release-process.md summarise the release process for alleycat`

### read a PDF file

`alleycat -v -f docs/alleyfacts.pdf "When was the turnip rebellion"`

### Or analyze specific sections

`alleycat -v -f docs/alleycat-guide.pdf "Extract all code examples from this document"`

#### Get a critical review

```bash
alleycat -v -f docs/alleyfacts.pdf -i "You are a technical documentation reviewer. Analyze this guide for clarity, completeness, and accuracy." "Review this document"
```

## Knowledge Base

### Create and manage knowledge bases

```bash
# Create a new knowledge base
alleycat-admin kb create project_docs

# Add files to the knowledge base
alleycat-admin kb add project_docs docs/*.md

# Add PDF files to a knowledge base
alleycat-admin kb add project_docs docs/reference/*.pdf

# List all knowledge bases
alleycat-admin kb ls

# List files in a specific knowledge base
alleycat-admin kb ls --name project_docs

# Set a default knowledge base
alleycat-admin kb default project_docs

# Remove a file from a knowledge base
alleycat-admin kb delete project_docs file-123456abcdef

# Remove an entire knowledge base
alleycat-admin kb rm project_docs
```

### Query knowledge bases

```bash
# Query a specific knowledge base
alleycat --kb project_docs "What is the release process for the project?"

# Query multiple knowledge bases
alleycat --kb project_docs --kb reference_material "Compare the API design in our project with best practices"

# Use with streaming output
alleycat --kb project_docs --stream "Explain the authentication flow in detail"

# Combine with other tools
alleycat --kb project_docs --web "How does our implementation compare to current industry standards?"

# Use with verbose output to see debug information
alleycat --kb project_docs --verbose "What are the key components of our architecture?"
```

## External tools

### Web search

Get real-time information from the web:

```bash
alleycat --tool web "What are the latest developments in quantum computing?"
```

Or use the simpler alias:

```bash
alleycat --web "What are the latest developments in quantum computing?"
```

### File search using vector store

Search through documents in a vector store:

```bash
alleycat --tool file-search --vector-store alleycat_kb "Find information about neural networks"
```

Or use the simpler aliases:

```bash
alleycat --knowledge --vector-store alleycat_kb "Find information about neural networks"
```

```bash
alleycat -k --vector-store alleycat_kb "Find information about neural networks"
```

### Combining tools

Use multiple tools in a single query:

```bash
alleycat --tool web --tool file-search --vector-store vs_1234 "Compare the latest research on LLMs with what we have in our knowledge base"
```

You can also use aliases for a more concise command:

```bash
alleycat -w --knowledge --vector-store vs_1234 "Compare the latest research on LLMs with what we have in our knowledge base"
```