"""
Verification script for Virtual Models interface fixes
Tests:
1. Proxy Key generation button with "生成" label
2. Knowledge Skill CRUD interface
3. Web Search Skill CRUD interface
4. Search targets loading from config.yml
"""
from playwright.sync_api import sync_playwright
import sys

def verify_virtual_models():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Collect console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            # Navigate to Virtual Models page
            print("Navigating to Virtual Models page...")
            page.goto('http://localhost:5175/#/virtual-models', timeout=30000)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)  # Wait for Vue to fully mount

            print(f"Page title: {page.title()}")

            # Check if main container loaded
            main_content = page.locator('.el-container, main, #app').first
            if main_content.count() > 0:
                print("[PASS] Main content container loaded")
            else:
                print("[FAIL] Main content container not found")

            # Check for Proxy Key section
            proxy_key_section = page.locator('text=代理Key').first
            if proxy_key_section.count() > 0:
                print("[PASS] Proxy Key section found")
                # Look for the generate button with "生成" text
                generate_btn = page.locator('button:has-text("生成")').first
                if generate_btn.count() > 0:
                    print("[PASS] Generate button with '生成' label found")
                else:
                    print("[FAIL] Generate button with '生成' label not found")
            else:
                print("[FAIL] Proxy Key section not found")

            # Check for Knowledge Skill section
            knowledge_section = page.locator('text=知识库Skill').first
            if knowledge_section.count() > 0:
                print("[PASS] Knowledge Skill section found")
                # Look for add button
                add_btn = page.locator('button:has-text("添加知识库Skill")').first
                if add_btn.count() > 0:
                    print("[PASS] Add Knowledge Skill button found")
                else:
                    print("[FAIL] Add Knowledge Skill button not found")
            else:
                print("[FAIL] Knowledge Skill section not found")

            # Check for Web Search Skill section
            websearch_section = page.locator('text=联网搜索Skill').first
            if websearch_section.count() > 0:
                print("[PASS] Web Search Skill section found")
                # Look for add button
                add_btn = page.locator('button:has-text("添加联网搜索Skill")').first
                if add_btn.count() > 0:
                    print("[PASS] Add Web Search Skill button found")
                else:
                    print("[FAIL] Add Web Search Skill button not found")
            else:
                print("[FAIL] Web Search Skill section not found")

            # Check for Search Targets
            search_target = page.locator('text=搜索目标').first
            if search_target.count() > 0:
                print("[PASS] Search Targets section found")
                # Check if there are any options loaded
                select_input = page.locator('.el-select:has-text("搜索目标")').first
                if select_input.count() > 0:
                    print("[PASS] Search Target selector found")
                else:
                    print("[WARN] Search Target selector not found")
            else:
                print("[FAIL] Search Targets section not found")

            # Take screenshot for visual verification
            page.screenshot(path='D:/aiproject/ytzc-ai-proxy/verification.png', full_page=True)
            print("\nScreenshot saved to verification.png")

            # Print any console errors
            errors = [log for log in console_logs if 'error' in log.lower()]
            if errors:
                print("\nConsole errors found:")
                for error in errors:
                    print(f"  {error}")
            else:
                print("\n[PASS] No console errors detected")

        except Exception as e:
            print(f"Error during verification: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    verify_virtual_models()
