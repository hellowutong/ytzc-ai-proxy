"""Navigate to Virtual Models page and verify fixes"""
from playwright.sync_api import sync_playwright

def test_virtual_models():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            print("Navigating to localhost:5175...")
            page.goto('http://localhost:5175', timeout=30000)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)

            print(f"Page title: {page.title()}")

            # Click on Model Management menu item (ģ�͹���)
            print("\nLooking for Model Management menu...")
            menu_items = page.locator('.el-menu-item').all()

            for item in menu_items:
                text = item.text_content()
                if '模型' in text or 'model' in text.lower():
                    print(f"Clicking: {text}")
                    item.click()
                    page.wait_for_timeout(2000)
                    break

            # Get current URL after navigation
            print(f"Current URL: {page.url}")

            # Get page content to check what loaded
            print("\nPage content (first 500 chars):")
            content = page.content()[:500]
            print(content)

            # Check for specific elements
            print("\n=== Verification Results ===")

            # Check for Proxy Key section
            proxy_elements = page.locator('.el-form-item:has-text("代理Key"), label:has-text("代理Key")').all()
            print(f"[FOUND] Proxy Key elements: {len(proxy_elements)}")

            # Check for Knowledge Skill
            knowledge_elements = page.locator('text=知识库Skill, text=knowledge').all()
            print(f"[FOUND] Knowledge elements: {len(knowledge_elements)}")

            # Check for Web Search
            websearch_elements = page.locator('text=联网搜索Skill, text=联网搜索').all()
            print(f"[FOUND] Web Search elements: {len(websearch_elements)}")

            # Check for Search Targets
            target_elements = page.locator('text=搜索目标, text=搜索').all()
            print(f"[FOUND] Search Target elements: {len(target_elements)}")

            # Take screenshot
            page.screenshot(path='D:/aiproject/ytzc-ai-proxy/virtual_models_page.png', full_page=True)
            print("\nScreenshot saved to virtual_models_page.png")

            # Print console errors
            errors = [log for log in console_logs if 'error' in log.lower()]
            if errors:
                print("\nConsole errors:")
                for error in errors[:5]:
                    print(f"  {error}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    test_virtual_models()
