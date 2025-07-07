[日本語](README.ja.md) | [English](README.md)

# Matrix Webhook Application Service

This repository contains a Matrix Application Service that provides webhook functionality for sending messages to Matrix rooms. It allows external services to send messages to Matrix rooms via simple HTTP POST requests.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Variables](#environment-variables)
4. [Configuration](#configuration)
5. [Running the Service](#running-the-service)
6. [Usage Examples](#usage-examples)

---

## Prerequisites

- Docker & Docker Compose (v3.8+)
- A running Matrix homeserver (Synapse)
- Python 3.8+ (if running without Docker)

---

## Initial Setup

1. Clone this repository
2. The Application Service configuration file `webhook_as.yaml` is located in the matrix-server directory. Configure it with:

   ```yaml
   # Example configuration
   hs_token: "random_secret_token" # Token for homeserver to authenticate AS
   as_token: "another_random_token" # Token for AS to authenticate to homeserver
   url: "http://localhost:9000" # URL where this service will run
   sender_localpart: "webhook" # The user ID localpart for the AS bot
   namespaces:
     users: []
     aliases: []
     rooms: []
   ```

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
# Matrix Webhook Environment Variables
MATRIX_URL=http://host.docker.internal:8008  # URL of your Matrix homeserver
SERVER_NAME=localhost                        # Your Matrix server name
BOT_LOCALPART=webhook_bot                   # Bot username localpart
AS_TOKEN=<generated>                        # Application Service token
```

These environment variables are used to configure the webhook service. The `.env` file should be kept secure and never committed to version control.

---

## Configuration

The service can be configured through environment variables or directly in the `docker-compose.yml` file:

```yaml
environment:
  - MATRIX_HOMESERVER_URL=http://synapse:8008
  - MATRIX_USER_ID=@webhook:example.com
  - AS_TOKEN=another_random_token
  - HS_TOKEN=random_secret_token
  - PORT=9000
```

---

## Running the Service

### Using Docker Compose (Recommended)

Start the service in detached mode:

```bash
docker-compose up -d
```

### Without Docker

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   python main.py
   ```

The service will listen on port 9000 by default.

---

## Usage Examples

### Sending a Message

Send a message to a room using curl:

```bash
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{"text":"Webhook via AS works test!","channel":"#test:localhost"}'
```

Successful response:

```json
{
  "ok": true,
  "event_id": "$VLnAIICMyUu8m39dA6lftWHz11B-WJzsRUtNuYg5mjQ"
}
```

### Message Format Options

You can send messages with different formats:

```bash
# HTML-formatted message
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{
           "text": "<b>Bold text</b> and <i>italic text</i>",
           "channel": "#test:localhost",
           "format": "html"
         }'

# Plain text with mentions
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{
           "text": "Hey @user:example.com, check this out!",
           "channel": "#test:localhost"
         }'
```

---

## Error Handling

The service returns appropriate HTTP status codes and JSON responses:

- 200: Message sent successfully
- 400: Invalid request format
- 401: Authentication failed
- 404: Room not found
- 500: Internal server error

Example error response:

```json
{
  "ok": false,
  "error": "Room not found"
}
```
