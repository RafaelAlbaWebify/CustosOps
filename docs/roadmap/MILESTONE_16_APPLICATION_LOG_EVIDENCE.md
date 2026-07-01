# Milestone 16 - Application Log Evidence v0.1

## Goal

Add operational application log review to CustosOps.

This module helps inspect imported application/API logs for evidence relevant to application support, software support, and technical troubleshooting.

## Added

- Application log import API.
- Generic text log parser.
- Application log analyzer.
- App Log Evidence dashboard panel.
- App log report export.
- App log archive support.
- Synthetic app/API logs.
- Backend tests.

## Detection Rules

CustosOps now detects evidence for:

- HTTP 5xx server errors
- 401 / 403 authentication or authorization failures
- repeated 404 responses
- timeout errors
- DNS / name-resolution errors
- TLS / certificate errors
- database dependency errors
- unhandled exceptions
- slow requests
- sensitive-data indicators in logs

## Safety

CustosOps does not modify applications, APIs, logs, services, DNS records, databases, or infrastructure.

Logs are processed locally.

Sensitive-data detection is included because application logs can contain:

- tokens
- authorization headers
- passwords
- connection strings
- API keys
- usernames or internal hostnames

## Sample Logs

Stored under:

samples/app_logs/

Included samples:

- fastapi-api-errors.log
- iis-like-api-errors.log

## Operator Use

Import a log file from the App Log Evidence card.

CustosOps will:

1. Parse the log.
2. Extract observable evidence.
3. Classify findings.
4. Provide safe next steps.
5. Generate archived reports.