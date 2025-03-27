# #16 Structured Output

The OpenAI and other providers support the feature of providing an output structure or schema file. This allows us to aligns the output to match specific expectations.

See documentation at <https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses>

## Overview

Structured Output allows enforcing strict schema validation on AI responses, ensuring consistent and reliable data structures. This feature replaces the previous `--json` command and `mode=json` option with a more robust schema-based approach.

## Implementation Plan

2. Request Processing
   - Modify the request builder to include schema in the request text format field
   - Add schema validation before sending to OpenAI
   - Implement error handling for invalid schemas

3. Response Processing
  - handle refusals 
    - When using Structured Outputs with user-generated input, OpenAI models may occasionally refuse to fulfill the request for safety reasons. Since a refusal does not necessarily follow the schema you have supplied in response_format, the API response will include a new field called refusal to indicate that the model refused to fulfill the request.

    - When the refusal property appears in your output object, present the refusal in as a json error object

   - Implement pretty printing for markdown mode

4. CLI Integration
   - Replace `--json` with `--schema` parameter
   - Add schema validation at CLI level
   - Implement schema discovery in workspace

## Example Schema Structure

```json
{
  "type": "json_schema",
  "name": "book_characters",
  "schema": {
    "type": "object",
    "properties": {
      "characters": {
        "type": "array",
        "description": "An array of characters in the book.",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "The name of the character."
            },
            "description": {
              "type": "string",
              "description": "A brief description of the character."
            }
          },
          "required": [
            "name",
            "description"
          ],
          "additionalProperties": false
        }
      }
    },
    "required": [
      "characters"
    ],
    "additionalProperties": false
  },
  "strict": true
}
```

## Usage Examples

1. Basic Name Extraction:
```bash
alleycat --schema schemas/person.schema.json "my name is james romula i am 17 and like cats"
```

Response:
```json
{
  "name": "James Romula",
  "age": 17,
  "gender": "Male",
  "location": "Not specified",
  "interests": [
    "cats"
  ]
}
```

2. Character Extraction from File:
```bash
alleycat --file docs/alleyfacts.pdf --schema schemas/book_characters.schema.json "collect the characters from this book"
```

Response:
```json
{
  "characters": [
    {
      "name": "Dr. Felicity Schrödinger",
      "description": "Lead scientist at the Institute of Subatomic Zoology who discovered the quantum feline."
    },
    {
      "name": "Thaddeus Gloop",
      "description": "Renowned underwater taxidermist known for his unique gill-stuffing technique."
    },
    {
      "name": "Dr. Enoch Bumbershoot",
      "description": "Mathematician who proposed the Bumbershoot Paradox in 1956."
    }
  ]
}
```

3. Basic Character Extraction:

```bash
alleycat --schema book_characters.schema.json --file docs/books/bleak_house.txt "generate a list of characters and their descriptions in this book"
```

4. Structured Data Analysis:

```bash
# Using a schema for analyzing code metrics
alleycat --schema code_metrics.schema.json --file src/ "analyze code complexity and patterns"

# Using a schema for extracting meeting notes
alleycat --schema meeting_notes.schema.json --file transcript.txt "extract key points, action items, and decisions"
```

5. Batch Processing:

```bash
# Process multiple files with the same schema
alleycat --schema article_summary.schema.json --file articles/*.txt "summarize each article"

# Chain multiple schemas
alleycat --schema-chain "extract.schema.json,transform.schema.json" --file data.txt "process and transform the data"
```

## Technical Implementation

The feature will be implemented in the following modules:

1. Schema Management (`alleycat_core/schema/`):
   - Schema validation and parsing
   - Schema caching and optimization
   - Schema transformation utilities

2. Request Processing (`alleycat_core/request/`):
   - Schema integration with OpenAI requests
   - Request validation and optimization

3. Response Processing (`alleycat_core/response/`):
   - Response validation against schema
   - Pretty printing and formatting
   - Output transformation utilities

4. CLI Integration (`alleycat_apps/cli/`):
   - Schema-related command handling
   - Schema discovery and validation
   - User feedback and error reporting

## Error Handling

1. Schema Validation Errors:
   - Invalid schema format
   - Schema compatibility issues
   - Missing required fields

2. Runtime Errors:
   - Schema file not found
   - Invalid file permissions
   - Network connectivity issues

3. Response Errors:
   - Schema validation failures
   - Transformation errors
   - Output formatting issues

## Notes

- The schema file should be a valid JSON schema file
- The schema is applied to the request using the `text` field
- Response output will be JSON string, unformatted for stdout
- In markdown mode, JSON will be pretty-printed with syntax highlighting
- Schema validation happens before the request is sent to OpenAI
- Invalid schemas will result in immediate error feedback
