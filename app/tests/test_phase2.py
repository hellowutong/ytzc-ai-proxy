#!/usr/bin/env python3
"""
Test script for Phase 2 APIs.

Tests:
1. Logs API endpoints
2. Config API endpoints
3. Dashboard API endpoints

Usage:
    python test_phase2.py
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
ADMIN_PREFIX = "/proxy/admin"

async def test_logs_api():
    """Test Logs API endpoints."""
    print("\n" + "="*60)
    print("Testing Logs API")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get all logs
        print("\n1. Testing GET /logs")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/logs?page=1&page_size=10")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Total logs: {data.get('data', {}).get('pagination', {}).get('total', 0)}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 2: Get system logs
        print("\n2. Testing GET /logs/system")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/logs/system")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
        
        # Test 3: Get operation logs
        print("\n3. Testing GET /logs/operation")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/logs/operation")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
        
        # Test 4: Get log statistics
        print("\n4. Testing GET /logs/stats")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/logs/stats?hours=24")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            stats = data.get('data', {})
            print(f"   System logs: {stats.get('system_logs', {}).get('total', 0)}")
            print(f"   Operation logs: {stats.get('operation_logs', {}).get('total', 0)}")


async def test_config_api():
    """Test Config API endpoints."""
    print("\n" + "="*60)
    print("Testing Config API")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get config tree
        print("\n1. Testing GET /config")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/config")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            config_data = data.get('data', {})
            print(f"   Config path: {config_data.get('config_path')}")
            print(f"   Total nodes: {config_data.get('total_nodes')}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 2: Get virtual models
        print("\n2. Testing GET /config/virtual-models")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/config/virtual-models")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            models = data.get('data', {}).get('models', {})
            print(f"   Virtual models count: {len(models)}")
        
        # Test 3: Get database config
        print("\n3. Testing GET /config/databases")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/config/databases")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")


async def test_dashboard_api():
    """Test Dashboard API endpoints."""
    print("\n" + "="*60)
    print("Testing Dashboard API")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get dashboard overview
        print("\n1. Testing GET /dashboard/overview")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/dashboard/overview")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            dashboard_data = data.get('data', {})
            overview = dashboard_data.get('overview', {})
            activity = dashboard_data.get('activity', {})
            print(f"   Virtual models: {overview.get('total_virtual_models')}")
            print(f"   Total routes: {overview.get('total_routes')}")
            print(f"   24h logs: {activity.get('recent_logs_24h')}")
            print(f"   24h errors: {activity.get('recent_errors_24h')}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 2: Get dashboard stats
        print("\n2. Testing GET /dashboard/stats")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/dashboard/stats")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
        
        # Test 3: Get services status
        print("\n3. Testing GET /dashboard/services")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/dashboard/services")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            services = data.get('data', {})
            for name, status in services.items():
                print(f"   {name}: {status.get('status', 'unknown')}")
        
        # Test 4: Get virtual models summary
        print("\n4. Testing GET /dashboard/virtual-models")
        response = await client.get(f"{BASE_URL}{ADMIN_PREFIX}/dashboard/virtual-models")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            models_data = data.get('data', {})
            print(f"   Total models: {models_data.get('total')}")
            print(f"   Enabled models: {models_data.get('enabled')}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Phase 2 API Testing")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        await test_logs_api()
        await test_config_api()
        await test_dashboard_api()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
