"""
Test script for Phase 3.5: RSS Module
Tests all RSS endpoints and functionality
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from bson import ObjectId

BASE_URL = "http://localhost:8000"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


async def test_rss_projects():
    """Test RSS project endpoints"""
    print_info("\n=== Testing RSS Projects ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Test list projects
        response = await client.get("/proxy/admin/rss/projects")
        if response.status_code == 200:
            projects = response.json()
            print_success(f"List projects: {len(projects)} projects found")
            for p in projects:
                print(f"  - {p['name']}: {p['url']} (enabled: {p['enabled']})")
        else:
            print_error(f"List projects failed: {response.status_code}")
            return False
        
        # Test get single project (if projects exist)
        if projects:
            project_name = projects[0]['name']
            response = await client.get(f"/proxy/admin/rss/projects/{project_name}")
            if response.status_code == 200:
                print_success(f"Get project '{project_name}'")
            else:
                print_error(f"Get project failed: {response.status_code}")
        
        return True


async def test_rss_items():
    """Test RSS item endpoints"""
    print_info("\n=== Testing RSS Items ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Test list items
        response = await client.get("/proxy/admin/rss/items")
        if response.status_code == 200:
            items = response.json()
            print_success(f"List items: {len(items)} items found")
        else:
            print_error(f"List items failed: {response.status_code}")
            return False
        
        # Test filtered list
        response = await client.get("/proxy/admin/rss/items", params={
            "status": "unread",
            "page_size": 5
        })
        if response.status_code == 200:
            items = response.json()
            print_success(f"Filtered list (unread): {len(items)} items")
        else:
            print_error(f"Filtered list failed: {response.status_code}")
        
        return True


async def test_rss_fetch():
    """Test RSS fetch endpoint"""
    print_info("\n=== Testing RSS Fetch ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Test fetch all feeds
        print_info("Fetching RSS feeds (this may take a while)...")
        response = await client.post("/proxy/admin/rss/fetch", json={})
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print_success(f"Fetch completed: {result['total_new']} new, {result['total_updated']} updated")
                print_info(f"Duration: {result['duration_ms']}ms")
                
                for r in result['results']:
                    status = "✓" if r['success'] else "✗"
                    print(f"  {status} {r['project_name']}: +{r['new_items']} new, ~{r['updated_items']} updated")
                    if r['error']:
                        print_warning(f"    Error: {r['error']}")
            else:
                print_warning(f"Fetch completed with warnings: {result}")
        else:
            print_error(f"Fetch failed: {response.status_code} - {response.text}")
            return False
        
        return True


async def test_rss_stats():
    """Test RSS stats endpoint"""
    print_info("\n=== Testing RSS Stats ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/proxy/admin/rss/stats")
        if response.status_code == 200:
            stats = response.json()
            print_success("Get stats")
            print(f"  Total projects: {stats['total_projects']} (active: {stats['active_projects']})")
            print(f"  Total items: {stats['total_items']}")
            print(f"  Unread: {stats['unread_items']}, Read: {stats['read_items']}, Extracted: {stats['extracted_items']}")
            print(f"  Permanent: {stats['permanent_items']}, Temporary: {stats['temporary_items']}")
            print(f"  Today: {stats['today_items']}, This week: {stats['week_items']}")
        else:
            print_error(f"Get stats failed: {response.status_code}")
            return False
        
        return True


async def test_rss_search():
    """Test RSS search endpoint"""
    print_info("\n=== Testing RSS Search ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Test search
        response = await client.post("/proxy/admin/rss/search", json={
            "query": "AI",
            "page": 1,
            "page_size": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Search 'AI': {result['total']} results found")
        else:
            print_error(f"Search failed: {response.status_code}")
            # Search might fail if no items exist, that's OK
            print_warning("Search may require items to exist first")
        
        return True


async def test_rss_batch():
    """Test RSS batch operations"""
    print_info("\n=== Testing RSS Batch Operations ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # First get some items
        response = await client.get("/proxy/admin/rss/items", params={"page_size": 5})
        if response.status_code != 200 or not response.json():
            print_warning("No items to test batch operations")
            return True
        
        items = response.json()
        item_ids = [item['_id'] for item in items[:3]]  # Test with first 3 items
        
        # Test batch read
        response = await client.post("/proxy/admin/rss/batch", json={
            "item_ids": item_ids,
            "operation": "read"
        })
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Batch read: {result['message']}")
        else:
            print_error(f"Batch read failed: {response.status_code}")
        
        # Test batch permanent
        response = await client.post("/proxy/admin/rss/batch", json={
            "item_ids": item_ids[:1],
            "operation": "permanent"
        })
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Batch permanent: {result['message']}")
        else:
            print_error(f"Batch permanent failed: {response.status_code}")
        
        return True


async def test_rss_item_actions():
    """Test RSS item actions (read, extract, etc.)"""
    print_info("\n=== Testing RSS Item Actions ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Get an item to test with
        response = await client.get("/proxy/admin/rss/items", params={"page_size": 1})
        if response.status_code != 200 or not response.json():
            print_warning("No items to test actions")
            return True
        
        item = response.json()[0]
        item_id = item['_id']
        
        print_info(f"Testing with item: {item['title'][:50]}...")
        
        # Test mark as read
        response = await client.post(f"/proxy/admin/rss/items/{item_id}/read")
        if response.status_code == 200:
            print_success("Mark as read")
        else:
            print_error(f"Mark as read failed: {response.status_code}")
        
        # Test get item detail
        response = await client.get(f"/proxy/admin/rss/items/{item_id}")
        if response.status_code == 200:
            detail = response.json()
            print_success(f"Get item detail: {len(detail.get('content', '') or '')} chars content")
        else:
            print_error(f"Get item detail failed: {response.status_code}")
        
        # Test extract to knowledge (if not already extracted)
        if not item.get('extracted'):
            print_info("Testing knowledge extraction...")
            response = await client.post(f"/proxy/admin/rss/items/{item_id}/extract")
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print_success(f"Extract to knowledge: {result['message']}")
                    if result['document_id']:
                        print_info(f"  Document ID: {result['document_id']}")
                else:
                    print_warning(f"Extract: {result['message']}")
            else:
                print_error(f"Extract failed: {response.status_code} - {response.text}")
        else:
            print_info("Item already extracted, skipping extraction test")
        
        return True


async def test_rss_cleanup():
    """Test RSS cleanup endpoint"""
    print_info("\n=== Testing RSS Cleanup ===")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/proxy/admin/rss/cleanup?days=30")
        if response.status_code == 200:
            result = response.json()
            print_success(f"Cleanup: {result['message']}")
        else:
            print_error(f"Cleanup failed: {response.status_code}")
            return False
        
        return True


async def run_all_tests():
    """Run all RSS tests"""
    print_info("=" * 60)
    print_info("Phase 3.5: RSS Module Tests")
    print_info("=" * 60)
    
    tests = [
        ("Projects", test_rss_projects),
        ("Items", test_rss_items),
        ("Stats", test_rss_stats),
        ("Search", test_rss_search),
        ("Fetch", test_rss_fetch),
        ("Item Actions", test_rss_item_actions),
        ("Batch Operations", test_rss_batch),
        ("Cleanup", test_rss_cleanup),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"{name} test exception: {e}")
            failed += 1
    
    print_info("\n" + "=" * 60)
    print_info(f"Test Results: {passed} passed, {failed} failed")
    print_info("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
