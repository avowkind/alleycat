# Knowledge Base Feature

The knowledge base feature in Alleycat allows you to create, manage, and query collections of documents using vector embeddings. This powerful capability enables natural language queries against your own content, making it ideal for document-based assistants, project documentation, research papers, and more.

## Overview

Knowledge bases in Alleycat leverage OpenAI's vector stores to:

1. Store and index document content using semantic embeddings
2. Perform efficient similarity searches based on natural language queries
3. Integrate document knowledge with the LLM's reasoning capabilities
4. Support multiple document formats including PDF, markdown, and text files
5. Allow batch processing of multiple files for efficient uploads

## Command-line Interface

Alleycat provides a dedicated admin command for managing knowledge bases and a simple query interface for interrogating them.

### Creating and Managing Knowledge Bases

All knowledge base management is handled through the `alleycat-admin kb` command suite:

#### Creating a Knowledge Base

```bash
alleycat-admin kb create my_project
```

This command:
- Creates a new vector store in your OpenAI account
- Assigns a friendly name ("my_project" in this example) for easy reference
- Stores the mapping in your local Alleycat configuration
- Sets it as the default knowledge base if it's your first one

#### Adding Files to a Knowledge Base

```bash
alleycat-admin kb add my_project path/to/file.pdf path/to/another.md
```

You can add multiple files at once, and Alleycat will:
- Upload the files to OpenAI
- Process them in a batch for efficiency
- Store file references in your local configuration
- Track the status of file processing

Files are processed in the background and typically become available within a few seconds to a minute depending on file size and complexity.

#### Listing Knowledge Bases

To see all your knowledge bases:

```bash
alleycat-admin kb ls
```

This will show a table with:
- Knowledge base friendly names
- Associated vector store IDs
- Number of files in each knowledge base
- Which knowledge base is set as the default (if any)

#### Listing Files in a Knowledge Base

To see the files in a specific knowledge base:

```bash
alleycat-admin kb ls --name my_project
```

This displays:
- File IDs
- File paths
- Processing status

#### Setting a Default Knowledge Base

```bash
alleycat-admin kb default my_project
```

Setting a default knowledge base allows you to use `alleycat` without explicitly specifying a knowledge base with the `--kb` option.

#### Clearing the Default Knowledge Base

```bash
alleycat-admin kb clear-default
```

#### Removing Files

To remove a specific file from a knowledge base:

```bash
alleycat-admin kb delete my_project file-id123456
```

The file ID can be found using the `alleycat-admin kb ls --name my_project` command.

#### Removing a Knowledge Base

```bash
alleycat-admin kb rm my_project
```

This will:
- Remove the vector store from your OpenAI account
- Remove references to it from your local configuration
- Clear it as the default knowledge base if it was set as such
- Prompt for confirmation unless the `--force` flag is used

For forced removal without confirmation:

```bash
alleycat-admin kb rm my_project --force
```

### Verbose Output

All knowledge base commands support a `--verbose` (or `-v`) flag that outputs detailed debug information:

```bash
alleycat-admin kb ls --verbose
alleycat-admin kb add my_project docs/*.pdf --verbose
```

### Querying Knowledge Bases

Once you've created and populated knowledge bases, you can use them with the main `alleycat` command:

```bash
alleycat --kb my_project "What are the key components described in our architecture?"
```

#### Multiple Knowledge Bases

You can query multiple knowledge bases simultaneously:

```bash
alleycat --kb project_docs --kb reference_material "Compare our approach with standard recommendations"
```

#### Advanced Options

Combine knowledge base queries with other Alleycat features:

```bash
# Streaming output for long responses
alleycat --kb my_project --stream "Give a detailed analysis of our system architecture"

# Markdown formatting
alleycat --kb my_project --mode markdown "Create a summary of key features in bullet points"

# With web search for additional context
alleycat --kb my_project --web "Compare our implementation with current industry standards"

# With specific instructions
alleycat --kb my_project --instructions "You are a technical reviewer providing constructive feedback" "Review our API design"

# With interactive chat mode to follow up on responses
alleycat --kb my_project --chat "Let's discuss the authentication flow"
```

## Practical Examples

### Creating a Project Documentation Assistant

1. Create a knowledge base for your project:
   ```bash
   alleycat-admin kb create my_project
   ```

2. Add your documentation files:
   ```bash
   alleycat-admin kb add my_project docs/*.md README.md CONTRIBUTING.md
   ```

3. Query your documentation:
   ```bash
   alleycat --kb my_project "What are the steps for setting up the development environment?"
   ```

### Building a Research Paper Assistant

1. Create a knowledge base for your research papers:
   ```bash
   alleycat-admin kb create research_papers
   ```

2. Add your PDF papers:
   ```bash
   alleycat-admin kb add research_papers papers/*.pdf
   ```

3. Ask questions about your research:
   ```bash
   alleycat --kb research_papers "Summarize the key findings from the papers about machine learning"
   ```

### Creating a Technical Support Assistant

1. Create a knowledge base for product support:
   ```bash
   alleycat-admin kb create product_support
   ```

2. Add manuals, FAQs, and troubleshooting guides:
   ```bash
   alleycat-admin kb add product_support manuals/*.pdf faqs/*.md troubleshooting/*.txt
   ```

3. Ask support questions:
   ```bash
   alleycat --kb product_support "How do I resolve the error 'connection refused' in the admin panel?"
   ```

## Implementation Details

The knowledge base feature uses OpenAI's vector stores to efficiently store and retrieve document content. When you query a knowledge base, Alleycat:

1. Converts your query to a vector embedding
2. Searches for semantically similar document sections
3. Retrieves the most relevant information
4. Provides the information to the LLM along with your question
5. Returns a response that integrates document knowledge with LLM capabilities

File processing happens in batches, allowing efficient addition of multiple documents. All vector store IDs and file mappings are stored in your local Alleycat configuration file at `~/.config/alleycat/config.yml` (or equivalent on your platform).

## Limitations and Tips

- **File Types**: The system supports PDF, markdown, and text files. PDFs with scanned content may not be fully readable without OCR processing.
- **Token Limits**: Large documents may be truncated to fit within OpenAI's token limits.
- **Processing Time**: Large documents take longer to process, but batch processing makes adding multiple files more efficient.
- **Organization**: Consider creating multiple, focused knowledge bases rather than one large collection for better performance and organization.
- **Default KB**: Setting a default knowledge base simplifies day-to-day usage.
- **Cost Consideration**: Vector stores in OpenAI may incur storage and usage costs. Monitor your usage through your OpenAI account. 