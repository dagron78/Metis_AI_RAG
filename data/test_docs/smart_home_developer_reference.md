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

After the user authorizes your application, they will be redirected to your `redirect_uri` with an authorization code:

```
https://your-app.example.com/callback?code=AUTHORIZATION_CODE
```

Exchange this code for an access token:

```http
POST https://auth.smarthome.example.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
redirect_uri=YOUR_REDIRECT_URI
```

Response:

```json
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN",
  "scope": "devices.read devices.write"
}
```

Include the access token in the Authorization header of all API requests:

```http
Authorization: Bearer ACCESS_TOKEN
```

## API Endpoints

### Devices

#### List all devices

```http
GET /devices
```

Parameters:
- `type`: Filter devices by type (optional)
- `room`: Filter devices by room (optional)
- `status`: Filter devices by status (online/offline) (optional)

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

Response:

```json
{
  "id": "device_123456",
  "name": "Living Room Motion Sensor",
  "type": "motion_sensor",
  "model": "SH-MS100",
  "firmware_version": "1.2.5",
  "connected": true,
  "battery": 87,
  "last_event": "2025-03-20T15:30:45Z",
  "room": "living_room",
  "capabilities": ["motion", "temperature", "light"],
  "attributes": {
    "motion": false,
    "temperature": 72.3,
    "light": 65
  },
  "created_at": "2024-12-15T08:30:00Z",
  "updated_at": "2025-03-20T15:30:45Z"
}
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

Response:

```json
{
  "id": "device_123456",
  "name": "Updated Device Name",
  "room": "bedroom"
  // ... other device properties
}
```

#### Control device

```http
POST /devices/{device_id}/commands
```

Request body:

```json
{
  "command": "set_level",
  "arguments": {
    "level": 75
  }
}
```

Response:

```json
{
  "status": "success",
  "command_id": "cmd_987654",
  "executed_at": "2025-03-22T14:25:30Z"
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

Response:

```json
{
  "events": [
    {
      "id": "evt_123456",
      "device_id": "device_123456",
      "type": "motion",
      "value": "active",
      "timestamp": "2025-03-20T15:30:45Z"
    },
    {
      "id": "evt_123457",
      "device_id": "device_789012",
      "type": "door",
      "value": "open",
      "timestamp": "2025-03-21T08:15:22Z"
    }
  ]
}
```

### Rooms

#### List all rooms

```http
GET /rooms
```

Response:

```json
{
  "rooms": [
    {
      "id": "room_123456",
      "name": "Living Room",
      "device_count": 5
    },
    {
      "id": "room_789012",
      "name": "Kitchen",
      "device_count": 3
    }
  ]
}
```

### Automations

#### List all automations

```http
GET /automations
```

Response:

```json
{
  "automations": [
    {
      "id": "auto_123456",
      "name": "Motion-activated lights",
      "enabled": true,
      "trigger": {
        "type": "device",
        "device_id": "device_123456",
        "event": "motion.active"
      },
      "conditions": [
        {
          "type": "time",
          "operation": "after_sunset"
        }
      ],
      "actions": [
        {
          "type": "device_command",
          "device_id": "device_654321",
          "command": "turn_on"
        }
      ]
    }
  ]
}
```

#### Create automation

```http
POST /automations
```

Request body:

```json
{
  "name": "Motion-activated lights",
  "enabled": true,
  "trigger": {
    "type": "device",
    "device_id": "device_123456",
    "event": "motion.active"
  },
  "conditions": [
    {
      "type": "time",
      "operation": "after_sunset"
    }
  ],
  "actions": [
    {
      "type": "device_command",
      "device_id": "device_654321",
      "command": "turn_on"
    }
  ]
}
```

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

Response:

```json
{
  "id": "webhook_123456",
  "url": "https://your-server.example.com/smarthome-webhook",
  "events": ["motion", "door", "button"],
  "created_at": "2025-03-22T12:00:00Z"
}
```

The secret will be used to sign webhook requests with an HMAC, allowing you to verify that requests come from the SmartHome system.

When an event occurs, the SmartHome system will send an HTTP POST request to your webhook URL:

```http
POST https://your-server.example.com/smarthome-webhook
Content-Type: application/json
X-SmartHome-Signature: sha256=...

{
  "event_type": "motion",
  "device_id": "device_123456",
  "value": "active",
  "timestamp": "2025-03-22T12:05:30Z"
}
```

To verify the signature:

```python
import hmac
import hashlib

def verify_webhook_signature(request_body, signature_header, webhook_secret):
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    signature = signature_header.split('=')[1]
    
    return hmac.compare_digest(signature, expected_signature)
```

## Real-time API

In addition to webhooks, you can use the SmartHome WebSocket API for real-time updates.

Connect to:

```
wss://api.smarthome.example.com/v1/ws
```

Authentication is done by including the access token as a query parameter:

```
wss://api.smarthome.example.com/v1/ws?access_token=YOUR_ACCESS_TOKEN
```

After connection, subscribe to device events:

```json
{
  "type": "subscribe",
  "topics": ["device.device_123456", "device.device_789012"]
}
```

You'll receive messages when events occur:

```json
{
  "topic": "device.device_123456",
  "type": "event",
  "data": {
    "event_type": "motion",
    "value": "active",
    "timestamp": "2025-03-22T12:05:30Z"
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests.

Common status codes:

- 200 OK: Request succeeded
- 201 Created: Resource was successfully created
- 400 Bad Request: Invalid request parameters
- 401 Unauthorized: Authentication failed
- 403 Forbidden: Permission denied
- 404 Not Found: Resource not found
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Server encountered an error

Error response format:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request is missing a required parameter",
    "details": {
      "missing_parameter": "name"
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to protect against abuse. Rate limits are applied on a per-token basis.

Current rate limits:
- 60 requests per minute
- 1000 requests per hour

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1648164342
```

If you exceed the rate limit, you'll receive a 429 Too Many Requests response.

## SDK Libraries

Official SmartHome SDK libraries are available for several programming languages:

- [JavaScript/Node.js](https://github.com/smarthome-example/smarthome-node)
- [Python](https://github.com/smarthome-example/smarthome-python)
- [Ruby](https://github.com/smarthome-example/smarthome-ruby)
- [Java](https://github.com/smarthome-example/smarthome-java)
- [Go](https://github.com/smarthome-example/smarthome-go)

Example using the Node.js SDK:

```javascript
const SmartHome = require('smarthome-sdk');

const client = new SmartHome.Client({
  clientId: 'YOUR_CLIENT_ID',
  clientSecret: 'YOUR_CLIENT_SECRET',
  redirectUri: 'YOUR_REDIRECT_URI'
});

// If you already have an access token
client.setAccessToken('ACCESS_TOKEN');

// Get all devices
client.devices.list()
  .then(devices => {
    console.log(devices);
  })
  .catch(error => {
    console.error(error);
  });

// Control a device
client.devices.sendCommand('device_123456', 'turn_on')
  .then(result => {
    console.log(result);
  })
  .catch(error => {
    console.error(error);
  });
```

## Integration Examples

### Motion-activated lighting

This example demonstrates how to create an automation that turns on lights when motion is detected, but only after sunset.

```javascript
const SmartHome = require('smarthome-sdk');
const client = new SmartHome.Client({ /* auth details */ });

async function createMotionLightingAutomation() {
  const automation = {
    name: "Motion-activated lights",
    enabled: true,
    trigger: {
      type: "device",
      device_id: "device_123456", // Motion sensor
      event: "motion.active"
    },
    conditions: [
      {
        type: "time",
        operation: "after_sunset"
      }
    ],
    actions: [
      {
        type: "device_command",
        device_id: "device_654321", // Light
        command: "turn_on"
      }
    ]
  };
  
  try {
    const result = await client.automations.create(automation);
    console.log("Automation created:", result);
  } catch (error) {
    console.error("Failed to create automation:", error);
  }
}

createMotionLightingAutomation();
```

### Security monitoring

This example shows how to set up a webhook to receive alerts when doors or windows are opened:

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

WEBHOOK_SECRET = "your_webhook_secret"

@app.route('/smarthome-webhook', methods=['POST'])
def webhook():
    # Verify signature
    signature_header = request.headers.get('X-SmartHome-Signature')
    if not signature_header:
        return jsonify({"error": "Missing signature"}), 401
    
    request_body = request.get_data().decode('utf-8')
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    signature = signature_header.split('=')[1]
    
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process the event
    event = request.json
    
    if event['event_type'] == 'door' and event['value'] == 'open':
        # Send alert, log event, etc.
        print(f"Door opened: {event['device_id']} at {event['timestamp']}")
    
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## Troubleshooting

### Common Issues

1. **Authentication failures**
   - Check that your client ID and secret are correct
   - Verify that your redirect URI exactly matches the one registered
   - Ensure your access token hasn't expired

2. **Rate limiting**
   - Implement exponential backoff for retries
   - Cache responses where appropriate
   - Optimize your code to reduce unnecessary API calls

3. **Webhook delivery issues**
   - Make sure your server is publicly accessible
   - Check that you're correctly verifying the signature
   - Implement proper error handling in your webhook endpoint

### Debugging Tools

The SmartHome Developer Portal provides several debugging tools:

1. **API Explorer**: Test API endpoints interactively
2. **Webhook Tester**: Send test events to your webhook endpoints
3. **Event Logs**: View recent API requests and responses
4. **Token Debugger**: Inspect your access tokens and permissions

## API Changelog

### v1.5 (2025-02-15)
- Added support for room grouping and hierarchy
- Expanded automation capabilities with more condition types
- Improved webhook reliability with delivery receipts
- Enhanced rate limiting with more granular controls

### v1.4 (2024-12-10)
- Added WebSocket API for real-time updates
- Introduced device categories and improved filtering
- Added batch operations for device control
- Expanded SDK support to include Go

### v1.3 (2024-10-05)
- Added historical data endpoints for device states
- Improved authentication with PKCE support
- Added support for geofencing triggers
- Enhanced error reporting with more detailed information

### v1.2 (2024-08-20)
- Added webhook signature verification
- Introduced automation API
- Expanded device capabilities
- Added SDK libraries for JavaScript, Python, and Ruby

### v1.1 (2024-06-15)
- Added support for device rooms and groups
- Improved rate limiting with header information
- Enhanced event filtering capabilities
- Added support for device commands

### v1.0 (2024-04-01)
- Initial release
- Basic device management
- Event history
- User authentication