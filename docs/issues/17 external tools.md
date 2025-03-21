# 17 External Tools

Add support for built in tools
e.g `alleycat --tool web what is a good news story on bbc.co.uk`

The --tool command line parameter may be repeated for each tool enabled. 

These are supported by the responses API in this version we only implement simple tools provided by the API and not local function calling.

see <https://platform.openai.com/docs/guides/tools?api-mode=responses> for the Responses API documentation.

## Web search

<https://platform.openai.com/docs/guides/tools-web-search?api-mode=responses>

command parameter: --tool web
adds to the respond request: `"tools": [{"type": "web_search_preview"}],`

## File Search

<https://platform.openai.com/docs/guides/tools-file-search>

command parameer: --tool file-search {store_id}
adds to the respond request: tools=[{
        "type": "file_search",
        "vector_store_ids": ["<vector_store_id>"]
    }]

File search depends on file ids in the vector store. We have not yet enabled file upload to the vector store. so assume these have been done separately and we have a store id. the vector store for tests and examples is `alleycat_kb`.

A default vector store ID can be stored in the Settings and Environment variable.
e.g `ALLEYCAT_VECTOR_STORE_ID=vs_etc`

## Todo

- add tool settings and env var
- add tools to the AI provider base class interface [base.py](../../src/alleycat_core/llm/base.py)
- add web tool to AI provider implementation [openai.py](../../src/alleycat_core/llm/openai.py)
- add web tool to the command line interface [main.py](../../src/alleycat_apps/cli/main.py)
- test without mocks the web search tool
- update readme.md and other documentation
- add examples to the docs/examples file

- Implement and complete web search first before starting file store
