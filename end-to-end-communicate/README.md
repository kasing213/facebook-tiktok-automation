# End to End Communication

Purpose: document how Facebook-automation (core) communicates with backend projects over HTTP.

Core
- /mnt/d/Facebook-automation

Backends
- /mnt/d/Invoice-generator
- /mnt/d/scriptclient
- /mnt/d/ads-alert
- /mnt/d/audit-sales

Project summaries
- /mnt/d/Facebook-automation/project-md/invoice-generator.md
- /mnt/d/Facebook-automation/project-md/scriptclient.md
- /mnt/d/Facebook-automation/project-md/ads-alert.md
- /mnt/d/Facebook-automation/project-md/audit-sales.md

Known HTTP endpoints (from backend docs)
- scriptclient
  - GET /health
  - GET /screenshots/verified
  - GET /screenshots/verified/{file}
  - Header: x-download-token (required for screenshots)
- audit-sales
  - GET /reports/daily/jpg?date=YYYY-MM-DD
  - GET /reports/monthly/excel?month=YYYY-MM
  - GET /health
- invoice-generator
  - No HTTP API documented yet
- ads-alert
  - No HTTP API documented yet

Integration checklist
1) Define base URLs for each backend
2) Define auth scheme (token header or network allowlist)
3) Define request and response schemas per endpoint
4) Define retry and timeout rules
5) Add logging and correlation IDs
6) Add health checks and alerting

Suggested shared config (edit as needed)
- CORE_BASE_URL
- INVOICE_GENERATOR_BASE_URL
- SCRIPTCLIENT_BASE_URL
- ADS_ALERT_BASE_URL
- AUDIT_SALES_BASE_URL
- INVOICE_GENERATOR_API_TOKEN
- SCRIPTCLIENT_API_TOKEN
- ADS_ALERT_API_TOKEN
- AUDIT_SALES_API_TOKEN
