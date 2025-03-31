# Background Task System Testing

This directory contains scripts for testing the Background Task System implementation in the Metis_RAG project.

## Prerequisites

Before running the tests, make sure you have the following dependencies installed:

```bash
pip install httpx psutil
```

## Running the Tests

### 1. Run Database Migrations

First, run the database migrations to create the necessary tables for the Background Task System:

```bash
python scripts/run_migrations.py
```

This will run the Alembic migrations to create the `background_tasks` table in the database.

### 2. Start the Application

Start the Metis_RAG application using the provided script:

```bash
python scripts/run_app.py
```

This script will:
1. Start the application with uvicorn
2. Wait for the application to start
3. Open a browser window to http://localhost:8000
4. Display application logs in the terminal

Alternatively, you can start the application manually:

```bash
uvicorn app.main:app --reload
```

The application should be running on http://localhost:8000.

### 3. Run the Tests

You can run all tests for the Background Task System using the provided script:

```bash
python scripts/run_background_task_tests.py
```

This script will:

1. Run database migrations
2. Start the application
3. Run the test_background_tasks.py script
4. Run pytest tests for the Background Task System
5. Stop the application

If you want to skip the database migrations, you can use the `--skip-migrations` flag:

```bash
python scripts/run_background_task_tests.py --skip-migrations
```

Alternatively, you can run the tests manually:

```bash
# In a separate terminal, run the test script
python scripts/test_background_tasks.py
```

The test_background_tasks.py script will:

1. Submit various types of tasks (document processing, vector store updates, report generation, system maintenance)
2. Test task dependencies
3. Test task priorities
4. Test scheduled tasks
5. Test task cancellation
6. Test concurrent task execution

## Viewing the Results

You can view the results of the tests in the terminal output. Additionally, you can access the Background Task System dashboard at:

```
http://localhost:8000/tasks
```

This dashboard provides a visual interface for monitoring tasks, viewing task details, and managing the Background Task System.

## Test Descriptions

### Document Processing Test

Tests the document processing task type, which processes a document and extracts its content.

### Vector Store Update Test

Tests the vector store update task type, which updates the vector store with new document embeddings.

### Report Generation Test

Tests the report generation task type, which generates reports based on document analysis.

### System Maintenance Test

Tests the system maintenance task type, which performs system maintenance operations like cleanup, optimization, and backups.

### Task Dependencies Test

Tests the task dependency system, which ensures that tasks are executed in the correct order based on their dependencies.

### Task Priorities Test

Tests the task priority system, which ensures that higher-priority tasks are executed before lower-priority tasks.

### Scheduled Tasks Test

Tests the scheduled task system, which allows tasks to be scheduled for execution at a specific time.

### Task Cancellation Test

Tests the task cancellation system, which allows tasks to be cancelled before or during execution.

### Concurrent Tasks Test

Tests the concurrent task execution system, which allows multiple tasks to be executed simultaneously.

## Troubleshooting

If you encounter any issues while running the tests, check the following:

1. Make sure the application is running on http://localhost:8000
2. Make sure the database migrations have been applied
3. Check the application logs for any errors
4. Make sure the required dependencies are installed

If you continue to experience issues, please refer to the Background Task System documentation or contact the development team.