# Place your PDF files here

The agent automatically loads every `*.pdf` file found in this directory
at startup. The text is chunked, embedded with Gemini `text-embedding-004`,
and stored in an in-memory vector index.

At query time the top-3 most relevant chunks are retrieved (cosine
similarity) and injected into the Gemini prompt as grounding context.

**Tips**
- You can add multiple PDFs (product manuals, FAQs, policies, etc.)
- Restart the server after adding or removing PDFs
- PDF text extraction works best with searchable (non-scanned) PDFs
