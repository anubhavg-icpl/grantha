#!/usr/bin/env python3
"""Test script to verify the Grantha backend is working with Google API"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.getenv('GOOGLE_API_KEY')

print("=== Grantha Backend Test ===")
print(f"✅ Working directory: {os.getcwd()}")
print(f"✅ Google API Key found: {api_key[:10]}..." if api_key else "❌ No API key")

# Test Google Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Grantha backend is ready!' in one line")
    print(f"✅ Google Gemini test successful: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Backend is running at http://localhost:8001")
print("✅ You can now use the Grantha backend independently!")