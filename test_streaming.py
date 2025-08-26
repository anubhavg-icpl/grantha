#!/usr/bin/env python3
"""Simple test script to demonstrate streaming chat completions."""

import asyncio
import json
import aiohttp
import sys

async def test_streaming_endpoint():
    """Test the streaming chat completions endpoint."""
    
    url = "http://localhost:8000/chat/completions/stream"
    payload = {
        "messages": [
            {
                "role": "user", 
                "content": "Write a short poem about programming"
            }
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print("🚀 Testing streaming chat completions endpoint...")
    print(f"📡 URL: {url}")
    print(f"📝 Request: {json.dumps(payload, indent=2)}")
    print("\n" + "="*60)
    print("📡 STREAMING RESPONSE:")
    print("="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Error: HTTP {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return
                
                print("✅ Connection established, streaming response...")
                print("-" * 60)
                
                full_response = ""
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                
                                if data.get("error"):
                                    print(f"❌ Stream Error: {data['error']}")
                                    return
                                
                                if data.get("content"):
                                    content = data["content"]
                                    print(content, end="", flush=True)
                                    full_response += content
                                
                                if data.get("done"):
                                    print(f"\n\n✅ Stream completed!")
                                    print(f"📊 Model: {data.get('model', 'unknown')}")
                                    print(f"🏷️  Provider: {data.get('provider', 'unknown')}")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON Parse Error: {e}")
                                print(f"Raw data: {data_str}")
                
                print("\n" + "="*60)
                print("📋 FULL RESPONSE SUMMARY:")
                print("="*60)
                print(full_response)
                print("\n✅ Streaming test completed successfully!")
    
    except aiohttp.ClientError as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    print("🧪 Grantha Streaming Chat Completions Test")
    print("=" * 50)
    
    try:
        asyncio.run(test_streaming_endpoint())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)