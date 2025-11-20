import shodan
import os

api = shodan.Shodan("wmzJYQdGvWkgoNA3Ke0eoDW145FTKxYt")

# Simple test query (should work with free account)
try:
    # Test 1: Get API info
    info = api.info()
    print(f"✅ API Key valid!")
    print(f"Plan: {info.get('plan', 'unknown')}")
    print(f"Query credits: {info.get('query_credits', 0)}")
    print(f"Scan credits: {info.get('scan_credits', 0)}")
    
    # Test 2: Simple search (no filters, fewer credits needed)
    print(f"\n🔍 Testing simple search...")
    results = api.search('port:80', limit=1)
    print(f"✅ Search works! Found {results['total']} results")
    
except shodan.APIError as e:
    print(f"❌ Error: {e}")
