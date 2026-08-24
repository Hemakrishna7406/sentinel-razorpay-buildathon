import urllib.request
import urllib.error

url = "https://mcp.razorpay.com/mcp"
headers = {
    "Authorization": "Basic cnpwX3Rlc3RfVFQ4bzhSQWR5RncxWXU6VDRSWFJPZlhBOW1PMm1XY0RvM1V2SXF5",
    "Accept": "text/event-stream"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"Status: {response.status}")
        print(f"Headers: {response.headers}")
        # Read a few lines of SSE
        for _ in range(5):
            line = response.readline()
            if not line: break
            print(line.decode('utf-8').strip())
except urllib.error.URLError as e:
    print(f"Error: {e}")
