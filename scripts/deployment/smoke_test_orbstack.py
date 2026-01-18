import requests
import time
import sys

def check_url(url, description, expect_json=False):
    print(f"Checking {description} at {url}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {description} is UP ({response.status_code})")
            if expect_json:
                try:
                    data = response.json()
                    print(f"   Response JSON: {data}")
                    return True
                except ValueError:
                    print(f"❌ {description} returned 200 but failed to parse JSON")
                    return False
            return True
        else:
            print(f"❌ {description} returned {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {description} failed to connect: {e}")
        return False

def wait_for_service(url, name, retries=10, delay=5):
    for i in range(retries):
        if check_url(url, name):
            return True
        print(f"   Waiting for {name} to be ready... ({i+1}/{retries})")
        time.sleep(delay)
    return False

print("=== Starting Smoke Test for Docker Deployment ===")

# 1. Check Backend Direct
if not wait_for_service("http://localhost:8000/api/v1/health", "FastAPI Direct"):
    print("❌ Backend failed to start. Aborting.")
    sys.exit(1)

# 2. Check Frontend Static
if not wait_for_service("http://localhost:3000", "Frontend Static"):
    print("❌ Frontend failed to start. Aborting.")
    sys.exit(1)

# 3. Check Proxy (Frontend -> Backend)
print("\nTesting Nginx Proxy Configuration...")
if check_url("http://localhost:3000/api/v1/health", "Frontend Proxy to API", expect_json=True):
    print("\n🎉 SUCCESS: Frontend is correctly proxying requests to Backend!")
else:
    print("\n❌ FAILURE: Nginx proxy is not working correctly.")
    sys.exit(1)
