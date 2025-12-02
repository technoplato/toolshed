import requests
import sys
import time

def verify_deployment(url, username="admin", password="secret"):
    print(f"Verifying deployment at {url}...")

    # 1. Test without credentials (expect 401)
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 401:
            print("✅ Auth check passed: Request without credentials returned 401.")
        else:
            print(f"❌ Auth check failed: Expected 401, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

    # 2. Test with credentials (expect 200)
    try:
        response = requests.get(url, auth=(username, password), timeout=5)
        if response.status_code == 200:
            print("✅ Access check passed: Request with credentials returned 200.")
            print("Response content snippet:")
            print(response.text[:200]) # Print first 200 chars
            return True
        else:
            print(f"❌ Access check failed: Expected 200, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_deployment.py <VPS_IP_OR_URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    success = verify_deployment(target_url)
    if success:
        print("\n🎉 Deployment verification SUCCESSFUL!")
        sys.exit(0)
    else:
        print("\nDeployment verification FAILED.")
        sys.exit(1)
