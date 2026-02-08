"""Explore page structure and find the correct route"""
from playwright.sync_api import sync_playwright

def explore_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            # Start at root and explore
            print("Navigating to localhost:5175...")
            page.goto('http://localhost:5175', timeout=30000)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)

            print(f"Page title: {page.title()}")

            # Get all links/routes
            print("\nAll links on page:")
            links = page.locator('a').all()
            for link in links[:20]:
                href = link.get_attribute('href')
                text = link.text_content()
                if href or text:
                    print(f"  {href}: {text}")

            # Get all button text
            print("\nAll buttons on page:")
            buttons = page.locator('button').all()
            for btn in buttons[:20]:
                text = btn.text_content()
                if text:
                    print(f"  Button: {text}")

            # Get all headings
            print("\nAll headings on page:")
            headings = page.locator('h1, h2, h3, h4').all()
            for h in headings[:10]:
                text = h.text_content()
                if text:
                    print(f"  {h.locator('xpath=..').get_attribute('tagName')}: {text}")

            # Check if sidebar exists with navigation
            sidebar = page.locator('.el-menu, nav, .sidebar').first
            if sidebar.count() > 0:
                print("\n[SIDEBAR FOUND]")
                menu_items = page.locator('.el-menu-item, .menu-item').all()
                for item in menu_items[:10]:
                    text = item.text_content()
                    print(f"  Menu: {text}")

            # Take screenshot
            page.screenshot(path='D:/aiproject/ytzc-ai-proxy/explore.png', full_page=True)
            print("\nScreenshot saved to explore.png")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    explore_page()
