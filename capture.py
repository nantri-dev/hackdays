import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("http://localhost:5173")
    # Wait for the data to populate
    time.sleep(3)
    # Save to the artifacts directory
    page.screenshot(path="/Users/muskaansachdeo/.gemini/antigravity-ide/brain/e84f98eb-8668-497b-9cf1-2d1ebd880090/frontend_preview.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
