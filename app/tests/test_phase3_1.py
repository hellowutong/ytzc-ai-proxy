"""
Phase 3.1 Test Script - Virtual Models CRUD API Tests

Tests the Virtual Model management endpoints:
- List, Create, Read, Update, Delete operations
- Enable/Disable toggle
- Model switching (small/big)
- Statistics endpoint
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httpx

BASE_URL = "http://localhost:8000"
ADMIN_URL = f"{BASE_URL}/proxy/admin"


async def test_list_virtual_models():
    """Test listing virtual models."""
    print("\n=== Test 1: List Virtual Models ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ADMIN_URL}/virtual-models")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('data'):
                print(f"Total models: {data['data'].get('total', 0)}")
                print(f"Enabled: {data['data'].get('enabled', 0)}")
                models = data['data'].get('models', [])
                if models:
                    print(f"\nModels:")
                    for m in models:
                        print(f"  - {m['name']}: {m['small_model']} / {m['big_model']} [{'ON' if m['enabled'] else 'OFF'}]")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_get_virtual_model():
    """Test getting a specific virtual model."""
    print("\n=== Test 2: Get Virtual Model ===")
    
    # First list to get a model name
    async with httpx.AsyncClient() as client:
        list_resp = await client.get(f"{ADMIN_URL}/virtual-models")
        if list_resp.status_code != 200:
            print("Failed to list models")
            return False
        
        models = list_resp.json()['data'].get('models', [])
        if not models:
            print("No models found to test with")
            return False
        
        model_name = models[0]['name']
        print(f"Testing with model: {model_name}")
        
        response = await client.get(f"{ADMIN_URL}/virtual-models/{model_name}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Model config keys: {list(data['data'].get('config', {}).keys())}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_create_virtual_model():
    """Test creating a new virtual model."""
    print("\n=== Test 3: Create Virtual Model ===")
    
    test_model = {
        "model_name": "test_model_api",
        "proxy_key": "test_api_key_12345",
        "base_url": "http://localhost:8000/proxy/v1",
        "current": "small",
        "force_current": False,
        "use": True,
        "small": {
            "model": "test/small-model",
            "api_key": "sk-test-small",
            "base_url": "https://api.test.com/v1"
        },
        "big": {
            "model": "test/big-model",
            "api_key": "sk-test-big",
            "base_url": "https://api.test.com/v1"
        },
        "knowledge": {
            "enabled": True,
            "shared": True,
            "skill": {
                "enabled": True,
                "version": "v1",
                "custom": {
                    "enabled": False,
                    "version": "v2"
                }
            }
        },
        "web_search": {
            "enabled": True,
            "skill": {
                "enabled": True,
                "version": "v1",
                "custom": {
                    "enabled": False,
                    "version": "v2"
                }
            },
            "target": []
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADMIN_URL}/virtual-models",
            json=test_model
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_update_virtual_model():
    """Test updating a virtual model."""
    print("\n=== Test 4: Update Virtual Model ===")
    
    update_data = {
        "proxy_key": "updated_api_key_67890",
        "use": True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{ADMIN_URL}/virtual-models/test_model_api",
            json=update_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_toggle_virtual_model():
    """Test enabling/disabling a virtual model."""
    print("\n=== Test 5: Toggle Virtual Model ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADMIN_URL}/virtual-models/test_model_api/enable",
            json={"enabled": False}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            
            # Toggle back to enabled
            response2 = await client.post(
                f"{ADMIN_URL}/virtual-models/test_model_api/enable",
                json={"enabled": True}
            )
            print(f"Re-enable Status: {response2.status_code}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_switch_model():
    """Test switching current model (small/big)."""
    print("\n=== Test 6: Switch Current Model ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADMIN_URL}/virtual-models/test_model_api/switch-model",
            json={"target": "big"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            
            # Switch back
            response2 = await client.post(
                f"{ADMIN_URL}/virtual-models/test_model_api/switch-model",
                json={"target": "small"}
            )
            print(f"Switch back Status: {response2.status_code}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_delete_virtual_model():
    """Test deleting a virtual model."""
    print("\n=== Test 7: Delete Virtual Model ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{ADMIN_URL}/virtual-models/test_model_api"
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def test_get_model_stats():
    """Test getting model statistics."""
    print("\n=== Test 8: Get Model Statistics ===")
    
    async with httpx.AsyncClient() as client:
        # List models first
        list_resp = await client.get(f"{ADMIN_URL}/virtual-models")
        if list_resp.status_code != 200:
            print("Failed to list models")
            return False
        
        models = list_resp.json()['data'].get('models', [])
        if not models:
            print("No models found to test with")
            return True  # Not a failure, just no data
        
        model_name = models[0]['name']
        
        response = await client.get(
            f"{ADMIN_URL}/virtual-models/{model_name}/stats"
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            stats = data.get('data', {})
            print(f"Last 24h stats: {stats.get('last_24h', {})}")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Phase 3.1 Virtual Models API Tests")
    print("=" * 60)
    
    results = []
    
    try:
        # Read-only tests first
        results.append(("List Models", await test_list_virtual_models()))
        results.append(("Get Model", await test_get_virtual_model()))
        results.append(("Get Stats", await test_get_model_stats()))
        
        # CRUD tests
        results.append(("Create Model", await test_create_virtual_model()))
        results.append(("Update Model", await test_update_virtual_model()))
        results.append(("Toggle Model", await test_toggle_virtual_model()))
        results.append(("Switch Model", await test_switch_model()))
        results.append(("Delete Model", await test_delete_virtual_model()))
        
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
