import requests
import time
import json

def test_cache():
    base_url = "http://localhost:5000"
    
    def make_request(url, description):
        print(f"\n{description}")
        try:
            start_time = time.time()
            response = requests.get(url)
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response data: {json.dumps(data, indent=2)}")
            else:
                print(f"Error response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure the Flask app is running.")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Test 1: First request (should hit database)
    make_request(f"{base_url}/students/at_risk", "Test 1: First request (should hit database)")
    
    # Test 2: Second request (should use cache)
    make_request(f"{base_url}/students/at_risk", "Test 2: Second request (should use cache)")
    
    # Test 3: Different query parameters (should hit database)
    make_request(f"{base_url}/students/at_risk?page=2", "Test 3: Different query parameters (should hit database)")
    
    # Test 4: Same query parameters again (should use cache)
    make_request(f"{base_url}/students/at_risk?page=2", "Test 4: Same query parameters again (should use cache)")

if __name__ == "__main__":
    print("Starting cache test...")
    print("Make sure the Flask application is running on http://localhost:5000")
    test_cache() 