# Metis RAG End-to-End Test Plan

## Overview

This document outlines a comprehensive end-to-end test for the Metis RAG system. The test will evaluate the entire pipeline from document upload and processing to query response generation, using all supported file formats (PDF, TXT, CSV, MD).

## Test Objectives

1. Verify document upload and processing across all supported file formats
2. Test the chunking and embedding functionality
3. Validate cross-document retrieval capabilities
4. Assess query refinement and response quality
5. Evaluate factual accuracy and citation quality
6. Measure system performance metrics

## Test Documents Design

We will create a set of test documents with complementary and interlinking information across different file formats:

### 1. Technical Documentation (PDF)
- Filename: `smart_home_technical_specs.pdf`
- Content focus: Technical specifications, architecture, and implementation details
- Key information: Device specifications, system architecture, connectivity protocols

### 2. User Guide (TXT)
- Filename: `smart_home_user_guide.txt`
- Content focus: User instructions, setup procedures, troubleshooting
- Key information: Configuration steps, usage scenarios, maintenance procedures

### 3. Device Comparison (CSV)
- Filename: `smart_home_device_comparison.csv`
- Content focus: Structured data on various smart home devices
- Key information: Model numbers, prices, features, compatibility data

### 4. Developer Reference (Markdown)
- Filename: `smart_home_developer_reference.md`
- Content focus: API documentation, code examples, integration guidelines
- Key information: API endpoints, authentication methods, sample code, best practices

## Test Document Content

The test documents will contain information about a fictional "SmartHome" system, with each document containing complementary information that creates opportunities for testing cross-document retrieval and synthesis.

### Example Content for Technical Documentation (PDF)

```
# SmartHome Technical Specifications

## System Architecture

The SmartHome system follows a hub-and-spoke architecture with the following components:

### SmartHome Hub (Model SH-100)
- Central processing unit: ARM Cortex-A53 quad-core @ 1.4GHz
- Memory: 2GB RAM
- Storage: 16GB eMMC
- Connectivity: Wi-Fi (802.11ac), Bluetooth 5.0, Zigbee 3.0, Z-Wave
- Power: 5V DC, 2A

### Communication Protocols
The SmartHome system uses the following protocols for device communication:
- SmartHome Connect (SHC) - proprietary protocol for secure device communication
- MQTT for lightweight messaging
- CoAP for constrained devices
- HTTP/HTTPS for cloud connectivity

### Security Features
- End-to-end encryption (AES-256)
- Secure boot
- Automatic security updates
- Certificate-based device authentication
- OAuth 2.0 for API authentication
```

### Example Content for User Guide (TXT)

```
SmartHome User Guide
====================

Getting Started
--------------

1. Unbox your SmartHome Hub (Model SH-100) and connect it to power using the provided adapter.
2. Download the SmartHome mobile app from the App Store or Google Play.
3. Launch the app and follow the on-screen instructions to create an account.
4. Connect your hub to your home Wi-Fi network through the app.
5. Once connected, the hub will automatically check for and install the latest firmware.

Adding Devices
-------------

To add a new device to your SmartHome system:

1. Press the "Add Device" button in the mobile app.
2. Select the device type from the list or scan the QR code on the device.
3. Put the device in pairing mode according to its instructions (usually by holding a button for 5 seconds).
4. Follow the app instructions to complete the pairing process.

Troubleshooting
--------------

Hub LED Status Indicators:
- Solid Blue: Hub is powered and working normally
- Blinking Blue: Hub is in pairing mode
- Solid Red: Hub is starting up
- Blinking Red: Hub has no internet connection
- Alternating Red/Blue: Hub is updating firmware

Common Issues:

1. Devices won't connect:
   - Ensure the device is within range of the hub (30-50 feet for most devices)
   - Check that the device is in pairing mode
   - Verify the device is compatible with SmartHome (see compatible devices list)

2. Hub offline:
   - Check your internet connection
   - Restart your router
   - Power cycle the hub by unplugging it for 10 seconds, then plugging it back in
```

### Example Content for Device Comparison (CSV)

```
Device ID,Device Name,Category,Protocol,Battery Life,Price,Indoor Range,Outdoor Range,Water Resistant,Voice Control,Hub Required
SH-MS100,Motion Sensor,Sensor,Zigbee,2 years,$24.99,40 ft,25 ft,No,No,Yes
SH-DS100,Door Sensor,Sensor,Zigbee,2 years,$19.99,50 ft,30 ft,No,No,Yes
SH-LS100,Light Switch,Switch,Z-Wave,N/A,$34.99,100 ft,75 ft,No,Yes,Yes
SH-PL100,Smart Plug,Plug,Wi-Fi,N/A,$29.99,150 ft,100 ft,No,Yes,No
SH-BL100,Smart Bulb,Lighting,Bluetooth,N/A,$15.99,30 ft,N/A,No,Yes,No
SH-KB100,Smart Keypad,Security,SHC,1 year,$79.99,N/A,N/A,Yes,No,Yes
SH-CM100,Smart Camera,Security,Wi-Fi,8 hours,$129.99,N/A,100 ft,Yes,Yes,No
SH-TH100,Temperature/Humidity Sensor,Sensor,Zigbee,18 months,$39.99,60 ft,45 ft,Yes,No,Yes
SH-WV100,Water Valve Controller,Plumbing,Z-Wave,N/A,$89.99,50 ft,N/A,Yes,Yes,Yes
SH-RC100,Remote Control,Controller,RF,$79.99,1 year,75 ft,50 ft,No,Yes,Yes
```

### Example Content for Developer Reference (Markdown)

```markdown
# SmartHome Developer Reference

## API Overview

The SmartHome system provides a RESTful API that allows developers to integrate with and extend the functionality of their SmartHome installation.

### Base URL

All API requests should be made to:

```
https://api.smarthome.example.com/v1
```

### Authentication

The API uses OAuth 2.0 for authentication. To obtain an access token:

1. Register your application at the [SmartHome Developer Portal](https://developer.smarthome.example.com)
2. Implement the OAuth 2.0 authorization code flow
3. Request the appropriate scopes for your application

Example authorization request:

```http
GET https://auth.smarthome.example.com/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  scope=devices.read devices.write
```

## API Endpoints

### Devices

#### List all devices

```http
GET /devices
```

Response:

```json
{
  "devices": [
    {
      "id": "device_123456",
      "name": "Living Room Motion Sensor",
      "type": "motion_sensor",
      "model": "SH-MS100",
      "connected": true,
      "battery": 87,
      "last_event": "2025-03-20T15:30:45Z"
    },
    {
      "id": "device_789012",
      "name": "Front Door Sensor",
      "type": "door_sensor",
      "model": "SH-DS100",
      "connected": true,
      "battery": 92,
      "last_event": "2025-03-21T08:15:22Z"
    }
  ]
}
```

#### Get device details

```http
GET /devices/{device_id}
```

#### Update device

```http
PATCH /devices/{device_id}
```

Request body:

```json
{
  "name": "Updated Device Name",
  "room": "bedroom"
}
```

### Events

#### Get recent events

```http
GET /events
```

Parameters:
- `limit`: Maximum number of events to return (default: 50, max: 500)
- `device_id`: Filter events by device ID
- `event_type`: Filter events by type (motion, door, button, etc.)
- `start_time`: ISO 8601 formatted timestamp
- `end_time`: ISO 8601 formatted timestamp

## Webhook Integration

You can register webhook URLs to receive real-time notifications when events occur in the SmartHome system.

To register a webhook:

```http
POST /webhooks
```

Request body:

```json
{
  "url": "https://your-server.example.com/smarthome-webhook",
  "events": ["motion", "door", "button"],
  "secret": "your_webhook_secret"
}
```

The secret will be used to sign webhook requests with an HMAC, allowing you to verify that requests come from the SmartHome system.
```

## Test Queries

We will develop a series of test queries designed to evaluate different aspects of the RAG system:

### Single-Document Queries

1. "What are the specifications of the SmartHome Hub?"
   - Target: PDF document
   - Expected facts: ARM Cortex-A53, 2GB RAM, 16GB storage, connectivity options

2. "How do I troubleshoot when devices won't connect?"
   - Target: TXT document
   - Expected facts: Check device range, ensure pairing mode, verify compatibility

3. "What is the battery life of the motion sensor?"
   - Target: CSV document
   - Expected facts: 2 years, device ID SH-MS100

4. "How do I authenticate with the SmartHome API?"
   - Target: MD document
   - Expected facts: OAuth 2.0, authorization code flow, developer portal

### Multi-Document Queries

5. "Compare the Motion Sensor and Door Sensor specifications and setup process."
   - Target: CSV + TXT documents
   - Expected facts: Specifications from CSV, setup process from TXT

6. "Explain how to integrate a motion sensor with a third-party application."
   - Target: MD + PDF + TXT documents
   - Expected facts: API details from MD, technical specifications from PDF, setup from TXT

7. "What security features does the SmartHome system provide for both users and developers?"
   - Target: PDF + MD documents
   - Expected facts: End-to-end encryption from PDF, OAuth and HMAC from MD

### Complex Analysis Queries

8. "Which devices require the hub and what protocols do they use?"
   - Target: CSV + PDF documents
   - Expected facts: Hub-required devices from CSV, protocol details from PDF

9. "If I want to create a water leak detection system, which devices should I use and how would I set them up?"
   - Target: All documents
   - Expected synthesis across documents

10. "What's the difference between Zigbee and Z-Wave devices in the SmartHome ecosystem?"
    - Target: PDF + CSV documents
    - Expected synthesis of technical differences and practical implications

## Test Implementation Structure

The implementation will follow this structure:

1. **Setup**: Create test directories and files
2. **Document Creation**: Generate all test documents with complementary content
3. **Test Functions**:
   - Document upload and processing
   - Single-document query testing
   - Multi-document query testing
   - Complex query testing
   - Response quality assessment
4. **Metrics Calculation**:
   - Factual accuracy
   - Response completeness
   - Citation quality
   - Performance metrics
5. **Results Reporting**: Generate detailed test reports

## Code Implementation

The end-to-end test will be implemented as a single comprehensive script with clear sections. Below is a pseudocode outline of the implementation:

```python
#!/usr/bin/env python3
"""
End-to-End test for the Metis RAG system.
This test evaluates the complete pipeline from document upload to query response.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_metis_rag_e2e")

# Import necessary components
from app.main import app
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.models.document import Document, Chunk

# Test client
client = TestClient(app)

# Test document content (defined as variables or loaded from files)
PDF_CONTENT = """# SmartHome Technical Specifications..."""
TXT_CONTENT = """SmartHome User Guide..."""
CSV_CONTENT = """Device ID,Device Name,Category..."""
MD_CONTENT = """# SmartHome Developer Reference..."""

# Test queries with expected facts
TEST_QUERIES = [
    {
        "query": "What are the specifications of the SmartHome Hub?",
        "expected_facts": ["ARM Cortex-A53", "2GB RAM", "16GB storage", "Wi-Fi", "Bluetooth 5.0", "Zigbee 3.0", "Z-Wave"],
        "target_docs": ["smart_home_technical_specs.pdf"]
    },
    # Additional queries...
]

@pytest.fixture
def test_documents_dir():
    """Create a directory for test documents"""
    temp_dir = tempfile.mkdtemp(prefix="metis_rag_e2e_test_")
    yield temp_dir
    # Clean up
    shutil.rmtree(temp_dir)

@pytest.fixture
def create_test_documents(test_documents_dir):
    """Create test documents of different formats with complementary information"""
    # Implementation to create all document files
    # Return paths to created documents

@pytest.fixture
async def setup_vector_store():
    """Set up a separate vector store for testing"""
    # Implementation

@pytest.fixture
async def setup_rag_engine(setup_vector_store):
    """Set up RAG engine with test vector store"""
    # Implementation

@pytest.mark.asyncio
async def test_document_upload_and_processing():
    """Test uploading and processing of all document types"""
    # Implementation

@pytest.mark.asyncio
async def test_single_document_queries(setup_rag_engine):
    """Test queries that target a single document"""
    # Implementation

@pytest.mark.asyncio
async def test_multi_document_queries(setup_rag_engine):
    """Test queries that require information from multiple documents"""
    # Implementation

@pytest.mark.asyncio
async def test_complex_queries(setup_rag_engine):
    """Test complex queries requiring synthesis and analysis"""
    # Implementation

@pytest.mark.asyncio
async def test_response_quality(setup_rag_engine):
    """Test quality aspects like factual accuracy, completeness, and citations"""
    # Implementation

@pytest.mark.asyncio
async def test_system_performance():
    """Test performance metrics like processing time and response time"""
    # Implementation

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test the complete workflow from upload to query response"""
    # Implementation

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
```

## Test Document Creation

For the actual test implementation, we'll need to create physical files for each format. The PDF file creation will require a PDF generation library like ReportLab, PyFPDF, or WeasyPrint. The other file formats (TXT, CSV, MD) can be created using standard file I/O operations.

## Test Execution Process

The test execution will follow these steps:

1. Create a clean test environment with separate directories for test documents and vector store
2. Generate all test documents with the designed content
3. Upload and process each document
4. Run all test queries and collect responses
5. Evaluate responses against expected facts
6. Calculate quality metrics
7. Generate a comprehensive test report

## Next Steps

To implement this test plan:

1. Switch to Code mode to implement the actual test script
2. Create helper functions for document generation, especially for PDF files
3. Implement the test queries and evaluation logic
4. Run the tests in a clean environment to ensure accurate results

The implementation should take into account potential environment-specific issues, such as dependencies for PDF handling and vector store persistence.