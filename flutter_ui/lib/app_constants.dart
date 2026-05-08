/// Default API base URL (``python -m uvicorn api_server:app`` or ``python api_server.py``).
const String kDefaultApiBaseUrl = String.fromEnvironment(
  'ZEROTRACE_API',
  defaultValue: 'http://127.0.0.1:8765',
);
