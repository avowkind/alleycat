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