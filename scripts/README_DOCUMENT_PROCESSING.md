# Document Processing Scripts

This directory contains scripts for processing documents and adding them to the vector database for RAG (Retrieval-Augmented Generation).

## Automatic Document Processing

When documents are uploaded through the API, they should be automatically processed and added to the vector database. However, if there are issues with the automatic processing, you can use the scripts in this directory to manually process documents.

## Manual Document Processing

### Process Pending Documents

The `process_pending_documents_cron.py` script can be run periodically to process any documents that are in the "pending" state:

```bash
python scripts/process_pending_documents_cron.py
```

This script will:
1. Find all documents in the "pending" state
2. Process each document (extract text, create chunks, generate embeddings)
3. Add the document chunks to the vector database
4. Update the document status to "completed"

### Setting Up a Cron Job

To ensure documents are processed automatically, you can set up a cron job to run the script periodically:

```bash
# Set up the cron job to run every 3 minutes
./scripts/setup_document_processing_cron.sh
```

This will create a cron job that runs the document processing script every 3 minutes and logs output to `/path/to/Metis_AI_RAG/logs/document_processing.log`.

## Checking Document Status

You can check the status of documents in the database using the `check_db_documents.py` script:

```bash
python scripts/check_db_documents.py
```

## Checking Vector Database Contents

You can check the contents of the vector database using the `check_vector_db_contents.py` script:

```bash
python scripts/check_vector_db_contents.py
```

## Troubleshooting

If documents are not being processed automatically, check the following:

1. Make sure the application is running
2. Check the application logs for errors
3. Run the `check_db_documents.py` script to see the status of documents
4. Run the `process_pending_documents_cron.py` script to manually process pending documents

If you encounter issues with the vector database, you can:

1. Run the `check_vector_db_contents.py` script to check the contents of the vector database
2. Reset document status to "pending" and try processing again:
   ```bash
   python scripts/reset_document_status.py
   ```

## System Timeouts

The system has been configured with the following timeout settings:

1. Default timeout for the Ollama client: 180 seconds (3 minutes)
2. Streaming response timeout: 300 seconds (5 minutes)

These timeouts ensure that the system has enough time to process large documents and generate responses, while still preventing indefinite hangs.