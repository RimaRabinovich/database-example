import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8080"

def run_test(url, expected_output, test_num, step_num):
    print(f"Test {test_num}, Step {step_num}:")
    print(f"  Request: {url}")
    
    try:
        response = requests.get(url)
        actual_output = response.text.strip()
        
        print(f"  Expected: {expected_output}")
        print(f"  Actual: {actual_output}")
        
        if actual_output == expected_output:
            print("  ✅ PASS")
        else:
            print("  ❌ FAIL")
        
        print()
        return actual_output
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        print()
        return None

def run_sequence_1():
    print("\n=== RUNNING TEST SEQUENCE 1 ===\n")
    run_test(f"{BASE_URL}/set?name=ex&value=10", "ex = 10", 1, 1)
    run_test(f"{BASE_URL}/get?name=ex", "10", 1, 2)
    run_test(f"{BASE_URL}/unset?name=ex", "ex = None", 1, 3)
    run_test(f"{BASE_URL}/get?name=ex", "None", 1, 4)
    run_test(f"{BASE_URL}/end", "CLEANED", 1, 5)

def run_sequence_2():
    print("\n=== RUNNING TEST SEQUENCE 2 ===\n")
    run_test(f"{BASE_URL}/set?name=a&value=10", "a = 10", 2, 1)
    run_test(f"{BASE_URL}/set?name=b&value=10", "b = 10", 2, 2)
    run_test(f"{BASE_URL}/numequalto?value=10", "2", 2, 3)
    run_test(f"{BASE_URL}/numequalto?value=20", "0", 2, 4)
    run_test(f"{BASE_URL}/set?name=b&value=30", "b = 30", 2, 5)
    run_test(f"{BASE_URL}/numequalto?value=10", "1", 2, 6)
    run_test(f"{BASE_URL}/end", "CLEANED", 2, 7)

def run_sequence_3():
    print("\n=== RUNNING TEST SEQUENCE 3 ===\n")
    run_test(f"{BASE_URL}/set?name=a&value=10", "a = 10", 3, 1)
    run_test(f"{BASE_URL}/set?name=b&value=20", "b = 20", 3, 2)
    run_test(f"{BASE_URL}/get?name=a", "10", 3, 3)
    run_test(f"{BASE_URL}/get?name=b", "20", 3, 4)
    run_test(f"{BASE_URL}/undo", "b = None", 3, 5)
    run_test(f"{BASE_URL}/get?name=a", "10", 3, 6)
    run_test(f"{BASE_URL}/get?name=b", "None", 3, 7)
    run_test(f"{BASE_URL}/set?name=a&value=40", "a = 40", 3, 8)
    run_test(f"{BASE_URL}/get?name=a", "40", 3, 9)
    run_test(f"{BASE_URL}/undo", "a = 10", 3, 10)
    run_test(f"{BASE_URL}/get?name=a", "10", 3, 11)
    run_test(f"{BASE_URL}/undo", "a = None", 3, 12)
    run_test(f"{BASE_URL}/get?name=a", "None", 3, 13)
    run_test(f"{BASE_URL}/undo", "NO COMMANDS", 3, 14)
    run_test(f"{BASE_URL}/redo", "a = 10", 3, 15)
    run_test(f"{BASE_URL}/redo", "a = 40", 3, 16)
    run_test(f"{BASE_URL}/end", "CLEANED", 3, 17)

def main():
    print("Starting tests...")
    print("Make sure your Flask application is running at http://127.0.0.1:8080")
    print("Press Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nTests cancelled.")
        sys.exit(0)
    
    run_sequence_1()
    time.sleep(1)
    
    run_sequence_2()
    time.sleep(1)
    
    run_sequence_3()
    
    print("\n=== TEST SUMMARY ===")
    print("All test sequences completed. Check the output above for any failures.")

if __name__ == "__main__":
    main() 