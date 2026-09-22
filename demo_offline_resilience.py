import time
import urllib.request
import json

def post_fault(fault_type):
    url = "http://127.0.0.1:8000/api/inject_fault"
    data = json.dumps({"fault_type": fault_type}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)

def main():
    print("--- STARTING OFFLINE RESILIENCE DEMO ---")
    
    print("\n1. Verifying normal operation...")
    time.sleep(2)
    
    print("\n2. Simulating network disconnect (pulling the cable)...")
    post_fault("network_offline")
    print("Network is now OFFLINE. The backend is running locally and queuing events.")
    
    time.sleep(2)
    
    print("\n3. Injecting a BIAS DRIFT fault while offline...")
    post_fault("bias")
    
    print("Waiting 15 seconds to allow the EWMA algorithm to detect the drift and queue the fallback message...")
    for i in range(15):
        print(f"Offline processing... ({i+1}/15s)")
        time.sleep(1)
        
    print("\n4. Simulating network reconnect (plugging cable back in)...")
    post_fault("network_online")
        
    print("Network is now ONLINE. Watch the dashboard to see the queue flush and replace the fallback message with the real Gemini explanation!")
    
    print("\n--- DEMO COMPLETE ---")
    print("Check the UI Event Log and Network Status panel!")

if __name__ == "__main__":
    main()
