# DataBridge Integration

A self-contained integration service demonstrating how to consume a SOAP/XML service and expose normalized JSON through a REST API.

> This is an independently built portfolio project using fictional customer data and a local SOAP fixture. It contains no employer code, credentials, schemas, or business data.

## What it demonstrates

- Building and sending a SOAP 1.1 XML envelope
- Parsing XML while handling namespaces
- Mapping an XML response into a validated Pydantic model
- Exposing normalized data through FastAPI
- Handling timeouts, connection failures, HTTP errors, SOAP faults, malformed XML, and missing fields
- Testing the API and SOAP client with mocked HTTP transports

## Architecture

```text
HTTP client
    |
    v
FastAPI route: GET /api/v1/customers/{customer_id}
    |
    v
SOAP customer client (httpx)
    |
    v
SOAP/XML provider
    |
    v
XML parser -> Pydantic validation -> JSON response
```

## Run locally

Python 3.11 or newer is recommended.

```bash
cd projects/databridge-integration
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows, use `Copy-Item .env.example .env` instead of `cp` if preferred.

Open the interactive documentation at <http://127.0.0.1:8000/docs>.

The default SOAP URL targets the local mock SOAP endpoint included in the application. The demo therefore needs no third-party account or credentials.

## Example request

```http
GET /api/v1/customers/CUST-1001
```

Example JSON response:

```json
{
  "customer_id": "CUST-1001",
  "first_name": "Avery",
  "last_name": "Morgan",
  "email": "avery.morgan@example.test",
  "status": "active"
}
```

Try `CUST-9999` to see how a SOAP fault is translated into an HTTP 502 response.

## Run tests

```bash
pytest -q
```

## Configuration

Settings are read from environment variables or `.env`:

| Variable | Purpose | Default |
|---|---|---|
| `APP_NAME` | FastAPI application title | `DataBridge Integration` |
| `SOAP_ENDPOINT_URL` | SOAP service endpoint | `http://127.0.0.1:8000/mock-soap` |
| `SOAP_TIMEOUT_SECONDS` | HTTP timeout | `5.0` |

## Design decisions

- XML parsing uses Python's standard library and compares local element names, avoiding dependence on namespace prefixes.
- The SOAP transport is isolated from the HTTP route and can be replaced with a mocked transport in tests.
- Provider failures are mapped to explicit gateway errors rather than being disguised as empty results.
- The mock provider uses synthetic data and makes the project reproducible without an external service.
