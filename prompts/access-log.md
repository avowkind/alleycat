# logfile analyser

Analyze the following nginx access logs and provide a summary. Return ONLY raw JSON matching this schema, with no markdown formatting, explanation, or other text:
{
  "summary": {
    "total_requests": number,
    "unique_ips": number,
    "top_paths": Array<{ path: string, count: number }>,
    "status_codes": { [code: string]: number },
    "peak_hour": { hour: string, requests: number }
  },
  "potential_issues": Array<{
    "type": "error" | "warning" | "info",
    "message": string,
    "recommendation": string
  }>,
  "performance_metrics": {
    "avg_response_time": number,
    "p95_response_time": number,
    "bandwidth_mb": number
  }
}

Here are the logs:

192.168.1.101 - - [15/Mar/2024:10:15:32 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0" 0.123
192.168.1.102 - - [15/Mar/2024:10:15:33 +0000] "POST /api/login HTTP/1.1" 401 789 "-" "PostmanRuntime/7.32.3" 0.089
192.168.1.101 - - [15/Mar/2024:10:15:34 +0000] "GET /api/products HTTP/1.1" 200 5432 "-" "Mozilla/5.0" 0.231
192.168.1.103 - - [15/Mar/2024:10:15:35 +0000] "GET /api/products HTTP/1.1" 200 5432 "-" "Mozilla/5.0" 0.198
192.168.1.104 - - [15/Mar/2024:10:15:36 +0000] "GET /api/products/1234 HTTP/1.1" 404 345 "-" "Mozilla/5.0" 0.045
192.168.1.102 - - [15/Mar/2024:10:15:37 +0000] "POST /api/login HTTP/1.1" 200 567 "-" "PostmanRuntime/7.32.3" 0.156
192.168.1.101 - - [15/Mar/2024:10:15:38 +0000] "GET /api/cart HTTP/1.1" 500 890 "-" "Mozilla/5.0" 2.345
192.168.1.105 - - [15/Mar/2024:10:15:39 +0000] "GET /api/products HTTP/1.1" 200 5432 "-" "Mozilla/5.0" 0.187
192.168.1.102 - - [15/Mar/2024:10:15:40 +0000] "GET /api/orders HTTP/1.1" 200 2345 "-" "PostmanRuntime/7.32.3" 0.234
192.168.1.101 - - [15/Mar/2024:10:15:41 +0000] "GET /api/products HTTP/1.1" 200 5432 "-" "Mozilla/5.0" 0.876

Please analyze these logs and provide insights about the API usage patterns, potential issues, and performance metrics. Make sure the response is only valid JSON matching the schema above.
