import time
import subprocess
import requests
import sys

def main():
    print("Starting Flask server for E2E Auth test...")
    # Start Flask dev server in a background process
    server_process = subprocess.Popen(
        [sys.executable, "backend/run.py"],
        env={
            "PYTHONPATH": ".",
            "FLASK_ENV": "development",
            "PORT": "5001",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"
        }
    )
    
    # Wait for server to start up
    time.sleep(3)
    
    base_url = "http://127.0.0.1:5001/api/auth"
    email = f"test_e2e_{int(time.time())}@cortex.dev"
    password = "secure_password_123"
    
    try:
        # 1. Test Registration
        print("\nTesting Registration...")
        reg_response = requests.post(f"{base_url}/register", json={
            "email": email,
            "password": password,
            "github_token": "gh_pat_mock_value_123"
        })
        print(f"Status Code: {reg_response.status_code}")
        print(f"Response: {reg_response.json()}")
        assert reg_response.status_code == 201, "Registration failed"
        
        # 2. Test Login
        print("\nTesting Login...")
        login_response = requests.post(f"{base_url}/login", json={
            "email": email,
            "password": password
        })
        print(f"Status Code: {login_response.status_code}")
        login_data = login_response.json()
        print(f"Response: {login_data}")
        assert login_response.status_code == 200, "Login failed"
        token = login_data.get("token")
        assert token is not None, "No token returned"
        
        # 3. Test GET /me with token
        print("\nTesting Profile (authorized)...")
        me_response = requests.get(f"{base_url}/me", headers={
            "Authorization": f"{token}" # Flask-Security token auth expects token directly in Authorization header
        })
        print(f"Status Code: {me_response.status_code}")
        me_data = me_response.json()
        print(f"Response: {me_data}")
        assert me_response.status_code == 200, "Authorized profile request failed"
        assert me_data["user"]["email"] == email, "Email mismatch"
        assert me_data["user"]["has_github_token"] is True, "GitHub token should be present"
        
        # 4. Test GET /me with Bearer token (Flask-Security-Too handles Bearer as well)
        print("\nTesting Profile with 'Bearer <token>' prefix...")
        me_bearer_response = requests.get(f"{base_url}/me", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Status Code: {me_bearer_response.status_code}")
        print(f"Response: {me_bearer_response.json()}")
        # Note: Depending on scheme settings, if Bearer is enabled, it resolves.
        # If default settings, it might expect token direct. We will check here.
        
        # 5. Test GET /me without token
        print("\nTesting Profile (unauthorized)...")
        unauth_response = requests.get(f"{base_url}/me", headers={"Accept": "application/json"})
        print(f"Status Code: {unauth_response.status_code}")
        assert unauth_response.status_code == 401, "Expected 401 unauthorized"
        
        # 6. Test Logout
        print("\nTesting Logout...")
        logout_response = requests.post(f"{base_url}/logout", headers={
            "Authorization": f"{token}"
        })
        print(f"Status Code: {logout_response.status_code}")
        assert logout_response.status_code == 200, "Logout failed"
        
        print("\nAll auth E2E tests passed successfully!")
        
    except Exception as e:
        print(f"\nE2E Auth Test failed: {e}")
        server_process.terminate()
        sys.exit(1)
    finally:
        print("Stopping Flask server...")
        server_process.terminate()
        server_process.wait()

if __name__ == '__main__':
    main()
