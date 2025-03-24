# #23 Add knowlegebase support

As an alleycat user
I can on the command line

- create a new vector store with a friendly name and link the store id to the friendly name
- add individual files or a file spec to the vector db
- reference the vector db by name in alleycat searches.
- this is a separate command to the chat prompt command `alleycat`

So that I can use my documents as a knowledge base we will use the term kb or knowledge_base for vector_store.

e.g

```bash
alleycat-admin kb create my_knowledge_base
alleycat-admin kb add ~/Documents/my_project/*.pdf
alleycat-admin kb ls - lists vector storage areas
alleycat-admin  kb rm my_knowledge_base - removes the vector storage area
```

## Vector Store API wrapper

Add an abstract base class similar to LLMProvider for KBProvider

implement a concrete OpenAIKBProvider vector_store implementation module in the alleycat_core/kb folder
add the endpoints from <https://platform.openai.com/docs/api-reference/vector-stores>
e.g create, list, retrieve, modify, delete, search

## Knowledge base Command Line interface

- rename top level script in pyproject.toml alleycat-init to alleycat-admin
- Extend alleycat-admin to add a sub command 'kb'
- make the original default command 'setup'

### create {name}

OpenAI Vector storage is identified by a vs_nnnnnnnn style id.  we want to use friendly names such as `project_tomcat` or 'homework` when referencing the db in alleycat commands.  

- creates a new knowledge base using the given name,
- stores the name and vector store ID in the user configuration settings
- supports one or more knowledge bases
- include in the create metadata field the local name for the knowledge base.
- warn if the name already in use

### list - ls

- lists the available knowledge bases - their friendly name and remote ids
- ls {kb_name} - lists the files in that specific kb.

### add

- adds a file or files matching file spec to the vector store
- keeps a list of files added to the store ( or can regenerate the list from the API - List vector store files API )
- to add - first upload to the files area using the files API then add to the store using the file_id

### remove

- remove the entire vector store and associated files

### delete (file)

- removes a specific file from the store.

## Storage

keep the list of vector stores and files in the user's configuration. using the Settings object.

## Using the kb in Alleycat

Once some files are in the kb we can ask for them to be searched in an alleycat prompt

- this uses the tools array with remote tool file_search
main parameters:
- type - The type of the file search tool. Always file_search.
- vector_store_ids - array of The IDs of the vector stores to search.

Learn more about the [file search tool](https://platform.openai.com/docs/guides/tools-file-search).

We will specify the kb to use on the command line using a new switch: --kb name.

- this can be repeated multiple times to generate a list of kbs.
- name can be either the local name or the vector_store_id

example:

```bash

# create the kb
alleycat-admin kb create my_kb

# add some files
alleycat-admin kb add docs/*.pdf

# search the files
alleycat -v -kb my_kb what is the carrying weight of a blue sparrow?
```
---


# PR: Added Knowledge Base Support (Issue #23)

This PR implements knowledge base support for Alleycat, allowing users to create and manage vector stores with friendly names for document retrieval.

## Summary of Changes

- Created `alleycat-admin` CLI tool with KB management commands:
  - `kb create <name>` - Creates a new knowledge base with friendly name
  - `kb ls` - Lists all knowledge bases and their files
  - `kb add <name> <file_paths>` - Adds files to a knowledge base
  - `kb rm <name>` - Removes a knowledge base
  - `kb delete <name> <file_id>` - Removes a specific file from a knowledge base
  - `kb default <name>` - Sets a default knowledge base

- Implemented batch processing for file uploads:
  - Files are now uploaded in parallel
  - Processing status is monitored with appropriate feedback
  - Significantly improves performance for multiple file operations

- Added integration with main `alleycat` command:
  - New `--kb <name>` option to reference knowledge bases by name
  - Multiple KB specification supported via repeated option use
  - Removed redundant `--vector-store` option for simplified interface

- Improved logging and user experience:
  - Added detailed status reporting in KB listings
  - Debug output now properly controlled by verbose flag
  - Enhanced error handling and user feedback

- Added documentation:
  - Updated examples and core documentation
  - Created comprehensive knowledge base usage guide

## Testing

All commands have been tested extensively, including:
- Creating knowledge bases with friendly names
- Adding multiple files to knowledge bases using batch processing
- Listing knowledge bases and their contents
- Using knowledge bases with the main `alleycat` command

Closes #23
