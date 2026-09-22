import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Track console messages
    page.on("console", lambda msg: print(f"Browser Console [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda err: print(f"Browser Error: {err}"))
    
    # Track WebSocket frames
    def handle_websocket(ws):
        print(f"WebSocket Opened: {ws.url}")
        ws.on("framereceived", lambda payload: print(f"WS Frame Received: {str(payload)[:200]}..."))
        ws.on("close", lambda ws: print("WebSocket Closed"))
        
    page.on("websocket", handle_websocket)
    
    print("Navigating to dashboard...")
    page.goto("http://localhost:5173")
    
    # Wait for the data to populate
    time.sleep(10)
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
