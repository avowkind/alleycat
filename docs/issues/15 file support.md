As a an alleycat user
when I add a --file {filename} to the command parameters
I see that the file is uploaded to OpenAI using the files API
and the the file_id is saved in the class state, and printed in the verbose debug info
and a suitable additional line referencing the file is added to the messages asking to reference the file
so that the responder can answer questions about the file

IMPLEMENTED ✅

example

alleycat -f geology_of_nz.pdf what is the largest dinosaur found in New Zealand

for testing provide a sample pdf file in the fixtures and evaluate questions that can only be answered from the pdf.

Other rules:

- when the process is completed the file should be removed from OpenAI - so implement a file remove function. Completed means that the script is single shot and reaches the end or it is interactive and the user has exited.
- 