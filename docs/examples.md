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