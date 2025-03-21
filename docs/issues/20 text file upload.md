# handle text files for inclusion
https://github.com/avowkind/alleycat/issues/20

If the file content is not a PDF or json but text (e.g .txt, .log, .md, .csv) then do not use the file upload function as these formats are not supported. Instead attach the file as a user message to the prompts.

include a limit on the file size to avoid blowing out the context window.

Plan:

- refactor the OpenAIProvider to move the file upload and delete functions to another implementation class and associated abstract interface. call this RemoteFile

- include in the interface a function to get a file prompt from the file object. This file prompt should be able to return content in the form that matches an item suitable for inclusion in the input list:

```python
{
  "role": "user",
  "content": [
      {"type": "input_file", "file_id": self.file_id},
      {"type": "input_text", "text": input},
  ],
}
```

the input field of the request is of type ResponseInputParam: TypeAlias = List[ResponseInputItemParam]
which is one of 

```python
ResponseInputItemParam: TypeAlias = Union[
    EasyInputMessageParam,
    Message,
    ResponseOutputMessageParam,
    ResponseFileSearchToolCallParam,
    ResponseComputerToolCallParam,
    ComputerCallOutput,
    ResponseFunctionWebSearchParam,
    ResponseFunctionToolCallParam,
    FunctionCallOutput,
    ResponseReasoningItemParam,
    ItemReference,
]
```

so the getter for the file object might return a EasyInputMessageParam with the content set to a list of ResponseInputContentParam: TypeAlias = Union[ResponseInputTextParam, ResponseInputImageParam, ResponseInputFileParam]

where ResponseInputFileParam is the structure {"type": "input_file", "file_id": self.file_id}, used above.

Hence update the main openai.py file to do this:

- if there is a file parameter
- create a remote file instance
- if supported type then upload and hold the file_id
- if txt type and not too large (1mb) then just hold the file path.
- when asked return the EasyInputMessageParam that can be added to the accumulating list of prompts. 
- if we have a file ID return a ResponseInputFileParam 
- if we have just a path, read the file as text and return in a ResponseInputTextParam.

setup openai.py to handle input prompts consistently so that we can accumulate prompt list items from the user input, files, tools etc. 

To test we should be able to run :
`alleycat -f docs/alleycat-guide.md "how to generate a bash command"`
and get a suitable response.