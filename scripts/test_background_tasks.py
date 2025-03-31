#!/usr/bin/env python3
"""
Test script for the Background Task System

This script demonstrates the functionality of the Background Task System
by submitting various types of tasks and monitoring their execution.
"""
import asyncio
import json
import sys
import time
from datetime import datetime, timedelta

import httpx

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

async def submit_task(name, task_type, params=None, priority="normal"):
    """
    Submit a task to the Background Task System
    
    Args:
        name: Task name
        task_type: Task type
        params: Task parameters
        priority: Task priority
        
    Returns:
        Task ID
    """
    url = f"{BASE_URL}/tasks"
    data = {
        "name": name,
        "task_type": task_type,
        "priority": priority,
        "params": params or {}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()["id"]

async def get_task(task_id):
    """
    Get task details
    
    Args:
        task_id: Task ID
        
    Returns:
        Task details
    """
    url = f"{BASE_URL}/tasks/{task_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

async def get_task_stats():
    """
    Get task statistics
    
    Returns:
        Task statistics
    """
    url = f"{BASE_URL}/tasks/stats"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

async def wait_for_task_completion(task_id, timeout_seconds=60):
    """
    Wait for a task to complete
    
    Args:
        task_id: Task ID
        timeout_seconds: Timeout in seconds
        
    Returns:
        Task details
    """
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        task = await get_task(task_id)
        if task["status"] in ("completed", "failed", "cancelled"):
            return task
        
        # Print progress
        print(f"Task {task_id} - Status: {task['status']}, Progress: {task['progress']:.1f}%")
        
        # Wait before checking again
        await asyncio.sleep(1)
    
    raise TimeoutError(f"Task {task_id} did not complete within {timeout_seconds} seconds")

async def test_document_processing():
    """
    Test document processing task
    """
    print("\n=== Testing Document Processing Task ===")
    
    # Submit task
    task_id = await submit_task(
        name="Process Test Document",
        task_type="document_processing",
        params={"document_id": "test123"},
        priority="high"
    )
    
    print(f"Submitted document processing task: {task_id}")
    
    # Wait for completion
    task = await wait_for_task_completion(task_id)
    
    # Print result
    print(f"Task completed with status: {task['status']}")
    if task["result"]:
        print(f"Result: {json.dumps(task['result'], indent=2)}")
    if task["error"]:
        print(f"Error: {task['error']}")

async def test_vector_store_update():
    """
    Test vector store update task
    """
    print("\n=== Testing Vector Store Update Task ===")
    
    # Submit task
    task_id = await submit_task(
        name="Update Vector Store",
        task_type="vector_store_update",
        params={"document_ids": ["doc1", "doc2", "doc3"]},
        priority="normal"
    )
    
    print(f"Submitted vector store update task: {task_id}")
    
    # Wait for completion
    task = await wait_for_task_completion(task_id)
    
    # Print result
    print(f"Task completed with status: {task['status']}")
    if task["result"]:
        print(f"Result: {json.dumps(task['result'], indent=2)}")
    if task["error"]:
        print(f"Error: {task['error']}")

async def test_report_generation():
    """
    Test report generation task
    """
    print("\n=== Testing Report Generation Task ===")
    
    # Submit task
    task_id = await submit_task(
        name="Generate Monthly Report",
        task_type="report_generation",
        params={
            "report_type": "comprehensive",
            "document_ids": ["doc1", "doc2", "doc3", "doc4", "doc5"]
        },
        priority="normal"
    )
    
    print(f"Submitted report generation task: {task_id}")
    
    # Wait for completion
    task = await wait_for_task_completion(task_id)
    
    # Print result
    print(f"Task completed with status: {task['status']}")
    if task["result"]:
        print(f"Result: {json.dumps(task['result'], indent=2)}")
    if task["error"]:
        print(f"Error: {task['error']}")

async def test_system_maintenance():
    """
    Test system maintenance task
    """
    print("\n=== Testing System Maintenance Task ===")
    
    # Submit task
    task_id = await submit_task(
        name="Database Optimization",
        task_type="system_maintenance",
        params={"maintenance_type": "optimization"},
        priority="low"
    )
    
    print(f"Submitted system maintenance task: {task_id}")
    
    # Wait for completion
    task = await wait_for_task_completion(task_id)
    
    # Print result
    print(f"Task completed with status: {task['status']}")
    if task["result"]:
        print(f"Result: {json.dumps(task['result'], indent=2)}")
    if task["error"]:
        print(f"Error: {task['error']}")

async def test_task_dependencies():
    """
    Test task dependencies
    """
    print("\n=== Testing Task Dependencies ===")
    
    # Submit first task
    first_task_id = await submit_task(
        name="First Task",
        task_type="document_processing",
        params={"document_id": "dep_test_1"},
        priority="normal"
    )
    
    print(f"Submitted first task: {first_task_id}")
    
    # Submit second task that depends on first task
    second_task_id = await submit_task(
        name="Second Task",
        task_type="vector_store_update",
        params={
            "document_ids": ["dep_test_1"],
            "dependencies": [{"task_id": first_task_id, "required_status": "completed"}]
        },
        priority="normal"
    )
    
    print(f"Submitted second task (depends on first): {second_task_id}")
    
    # Submit third task that depends on second task
    third_task_id = await submit_task(
        name="Third Task",
        task_type="report_generation",
        params={
            "report_type": "summary",
            "document_ids": ["dep_test_1"],
            "dependencies": [{"task_id": second_task_id, "required_status": "completed"}]
        },
        priority="normal"
    )
    
    print(f"Submitted third task (depends on second): {third_task_id}")
    
    # Wait for first task to complete
    print("\nWaiting for first task to complete...")
    await wait_for_task_completion(first_task_id)
    
    # Wait for second task to complete
    print("\nWaiting for second task to complete...")
    await wait_for_task_completion(second_task_id)
    
    # Wait for third task to complete
    print("\nWaiting for third task to complete...")
    await wait_for_task_completion(third_task_id)
    
    print("\nAll dependent tasks completed successfully!")

async def test_task_priorities():
    """
    Test task priorities
    """
    print("\n=== Testing Task Priorities ===")
    
    # Submit low priority task
    low_task_id = await submit_task(
        name="Low Priority Task",
        task_type="system_maintenance",
        params={"maintenance_type": "cleanup"},
        priority="low"
    )
    
    print(f"Submitted low priority task: {low_task_id}")
    
    # Submit normal priority task
    normal_task_id = await submit_task(
        name="Normal Priority Task",
        task_type="document_processing",
        params={"document_id": "priority_test_1"},
        priority="normal"
    )
    
    print(f"Submitted normal priority task: {normal_task_id}")
    
    # Submit high priority task
    high_task_id = await submit_task(
        name="High Priority Task",
        task_type="vector_store_update",
        params={"document_ids": ["priority_test_1"]},
        priority="high"
    )
    
    print(f"Submitted high priority task: {high_task_id}")
    
    # Submit critical priority task
    critical_task_id = await submit_task(
        name="Critical Priority Task",
        task_type="report_generation",
        params={"report_type": "summary", "document_ids": ["priority_test_1"]},
        priority="critical"
    )
    
    print(f"Submitted critical priority task: {critical_task_id}")
    
    # Wait for all tasks to complete
    print("\nWaiting for all tasks to complete...")
    await asyncio.gather(
        wait_for_task_completion(low_task_id),
        wait_for_task_completion(normal_task_id),
        wait_for_task_completion(high_task_id),
        wait_for_task_completion(critical_task_id)
    )
    
    print("\nAll priority tasks completed!")

async def test_scheduled_tasks():
    """
    Test scheduled tasks
    """
    print("\n=== Testing Scheduled Tasks ===")
    
    # Schedule a task for 10 seconds in the future
    schedule_time = datetime.now() + timedelta(seconds=10)
    
    # Submit scheduled task
    task_id = await submit_task(
        name="Scheduled Task",
        task_type="system_maintenance",
        params={
            "maintenance_type": "backup",
            "schedule_time": schedule_time.isoformat()
        },
        priority="normal"
    )
    
    print(f"Submitted scheduled task: {task_id}")
    print(f"Scheduled for: {schedule_time.isoformat()}")
    
    # Wait for completion
    task = await wait_for_task_completion(task_id, timeout_seconds=30)
    
    # Print result
    print(f"Task completed with status: {task['status']}")
    if task["result"]:
        print(f"Result: {json.dumps(task['result'], indent=2)}")
    if task["error"]:
        print(f"Error: {task['error']}")

async def test_task_cancellation():
    """
    Test task cancellation
    """
    print("\n=== Testing Task Cancellation ===")
    
    # Submit a long-running task
    task_id = await submit_task(
        name="Long Running Task",
        task_type="report_generation",
        params={
            "report_type": "comprehensive",
            "document_ids": ["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8", "doc9", "doc10"]
        },
        priority="low"
    )
    
    print(f"Submitted long-running task: {task_id}")
    
    # Wait a bit for the task to start
    await asyncio.sleep(2)
    
    # Get task status
    task = await get_task(task_id)
    print(f"Task status before cancellation: {task['status']}")
    
    # Cancel the task
    url = f"{BASE_URL}/tasks/{task_id}/cancel"
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        response.raise_for_status()
    
    print(f"Cancelled task: {task_id}")
    
    # Get task status after cancellation
    task = await get_task(task_id)
    print(f"Task status after cancellation: {task['status']}")

async def test_concurrent_tasks():
    """
    Test concurrent task execution
    """
    print("\n=== Testing Concurrent Task Execution ===")
    
    # Number of tasks to submit
    num_tasks = 10
    
    # Submit multiple tasks
    task_ids = []
    for i in range(num_tasks):
        task_id = await submit_task(
            name=f"Concurrent Task {i+1}",
            task_type="document_processing",
            params={"document_id": f"concurrent_test_{i+1}"},
            priority="normal"
        )
        task_ids.append(task_id)
        print(f"Submitted task {i+1}: {task_id}")
    
    # Wait for all tasks to complete
    print(f"\nWaiting for all {num_tasks} tasks to complete...")
    start_time = time.time()
    
    # Wait for tasks to complete
    await asyncio.gather(*[wait_for_task_completion(task_id) for task_id in task_ids])
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    print(f"\nAll {num_tasks} tasks completed in {elapsed_time:.2f} seconds")
    print(f"Average time per task: {elapsed_time / num_tasks:.2f} seconds")

async def main():
    """
    Main function
    """
    print("=== Background Task System Test ===")
    
    try:
        # Get initial task stats
        stats = await get_task_stats()
        print(f"Initial task stats: {json.dumps(stats, indent=2)}")
        
        # Run tests
        await test_document_processing()
        await test_vector_store_update()
        await test_report_generation()
        await test_system_maintenance()
        await test_task_dependencies()
        await test_task_priorities()
        await test_scheduled_tasks()
        await test_task_cancellation()
        await test_concurrent_tasks()
        
        # Get final task stats
        stats = await get_task_stats()
        print(f"\nFinal task stats: {json.dumps(stats, indent=2)}")
        
        print("\n=== All tests completed successfully! ===")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))