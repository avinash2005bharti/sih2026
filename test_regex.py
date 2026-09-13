import re
import json

cleaned = """Here is the code you requested:

```json
{
  "name": "execute_python",
  "arguments": {
    "code": "print(12 * 12)"
  }
}
```
"""

cleaned = re.sub(r'```(?:json)?\s*', '', cleaned).replace('```', '').strip()
print("Cleaned text:", repr(cleaned))

tool_calls = []

# If line-by-line didn't match, search for any JSON objects
for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned):
    json_str = match.group(0)
    print("Found JSON string:", repr(json_str))
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and ("name" in data or "tool" in data):
            print("Successfully parsed tool call:", data)
            tool_calls.append(data)
    except Exception as e:
        print("Exception:", e)

print("Tool calls:", tool_calls)
