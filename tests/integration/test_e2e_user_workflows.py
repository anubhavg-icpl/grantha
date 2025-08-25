"""
End-to-End User Workflow Integration Tests for Grantha API.
Tests complete user journeys and workflows.
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30


class TestE2EUserWorkflows:
    """End-to-end user workflow tests."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method run before each test."""
        # Verify API is available
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API server not available")
        except requests.exceptions.RequestException:
            pytest.skip("API server not available")

    def test_new_user_onboarding_workflow(self):
        """Test complete new user onboarding workflow."""
        print("\n🚀 Testing New User Onboarding Workflow")
        
        # Step 1: User accesses the application
        print("Step 1: Accessing application...")
        response = requests.get(f"{API_BASE_URL}/")
        assert response.status_code == 200
        app_info = response.json()
        print(f"✓ Application: {app_info.get('name', 'Grantha API')}")
        
        # Step 2: Check if authentication is required
        print("Step 2: Checking authentication requirements...")
        auth_response = requests.get(f"{API_BASE_URL}/auth/status")
        assert auth_response.status_code == 200
        auth_status = auth_response.json()
        print(f"✓ Auth required: {auth_status.get('auth_required', False)}")
        
        # Step 3: Get available models and providers
        print("Step 3: Getting available models...")
        models_response = requests.get(f"{API_BASE_URL}/models/config")
        assert models_response.status_code == 200
        models_config = models_response.json()
        print(f"✓ Available providers: {len(models_config.get('providers', []))}")
        print(f"✓ Default provider: {models_config.get('defaultProvider', 'google')}")
        
        # Step 4: First interaction - simple chat
        print("Step 4: First chat interaction...")
        chat_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={
                "user_query": "Hello! What can you help me with?",
                "provider": models_config.get('defaultProvider', 'google'),
                "model": "gemini-pro"
            },
            timeout=TEST_TIMEOUT
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "message" in chat_data
        assert "status" in chat_data
        print(f"✓ First interaction successful: {chat_data['status']}")
        
        print("✅ New User Onboarding Workflow Complete!")

    def test_documentation_generation_workflow(self):
        """Test complete documentation generation workflow."""
        print("\n📚 Testing Documentation Generation Workflow")
        
        # Step 1: User selects repository for documentation
        repo_url = "https://github.com/octocat/Hello-World"
        print(f"Step 1: Selected repository: {repo_url}")
        
        # Step 2: Check authentication if required
        auth_response = requests.get(f"{API_BASE_URL}/auth/status")
        auth_data = auth_response.json()
        
        if auth_data.get('auth_required', False):
            print("Step 2: Authentication required - simulating validation...")
            # In real scenario, user would provide auth code
            validate_response = requests.post(
                f"{API_BASE_URL}/auth/validate",
                json={"code": "test_code"}
            )
            assert validate_response.status_code == 200
        else:
            print("Step 2: No authentication required")
        
        # Step 3: Generate wiki documentation
        print("Step 3: Generating wiki documentation...")
        wiki_response = requests.post(
            f"{API_BASE_URL}/wiki/generate",
            json={
                "repo_url": repo_url,
                "language": "en",
                "provider": "google",
                "model": "gemini-2.0-flash-exp"
            },
            timeout=TEST_TIMEOUT
        )
        assert wiki_response.status_code == 200
        wiki_data = wiki_response.json()
        assert "wiki_structure" in wiki_data
        assert wiki_data["status"] == "success"
        
        wiki_structure = wiki_data["wiki_structure"]
        print(f"✓ Wiki generated: {wiki_structure['title']}")
        print(f"✓ Number of pages: {len(wiki_structure['pages'])}")
        
        # Step 4: Review generated documentation
        if wiki_structure['pages']:
            first_page = wiki_structure['pages'][0]
            print(f"✓ First page: {first_page['title']}")
            print(f"✓ Content preview: {first_page['content'][:100]}...")
        
        print("✅ Documentation Generation Workflow Complete!")

    def test_interactive_research_workflow(self):
        """Test interactive research and Q&A workflow."""
        print("\n🔍 Testing Interactive Research Workflow")
        
        repo_url = "https://github.com/microsoft/vscode"
        
        # Step 1: Initial research question
        print("Step 1: Asking initial research question...")
        research_response = requests.post(
            f"{API_BASE_URL}/research/deep",
            json={
                "query": "What are the main architectural components of this system?",
                "repo_url": repo_url,
                "language": "en",
                "provider": "google",
                "model": "gemini-2.0-flash-exp"
            },
            timeout=TEST_TIMEOUT
        )
        assert research_response.status_code == 200
        research_data = research_response.json()
        assert "results" in research_data
        assert "status" in research_data
        print(f"✓ Research completed: {research_data['status']}")
        
        # Step 2: Follow-up questions based on research
        print("Step 2: Follow-up chat based on research...")
        follow_up_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={
                "user_query": "Can you explain more about the extension system?",
                "provider": "google",
                "model": "gemini-pro"
            },
            timeout=TEST_TIMEOUT
        )
        assert follow_up_response.status_code == 200
        follow_up_data = follow_up_response.json()
        assert "message" in follow_up_data
        print(f"✓ Follow-up answered: {len(follow_up_data['message'])} characters")
        
        # Step 3: RAG-based specific query
        print("Step 3: RAG-based specific query...")
        rag_response = requests.post(
            f"{API_BASE_URL}/simple/rag",
            json={
                "query": "How is authentication handled?",
                "repo_url": repo_url,
                "provider": "mock",
                "model": "mock-model"
            },
            timeout=TEST_TIMEOUT
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        assert "answer" in rag_data
        assert "sources" in rag_data
        print(f"✓ RAG query completed with {len(rag_data['sources'])} sources")
        
        print("✅ Interactive Research Workflow Complete!")

    def test_multi_model_comparison_workflow(self):
        """Test workflow using multiple AI models for comparison."""
        print("\n🤖 Testing Multi-Model Comparison Workflow")
        
        # Step 1: Get available models
        models_response = requests.get(f"{API_BASE_URL}/models/config")
        models_config = models_response.json()
        providers = models_config.get('providers', [])
        
        if not providers:
            print("⚠️ No providers available for comparison")
            return
        
        print(f"Step 1: Available providers: {[p.get('id') for p in providers]}")
        
        # Step 2: Ask the same question to different models/providers
        question = "Explain the benefits of microservices architecture"
        responses = {}
        
        # Test with different providers if available
        test_providers = ["google"]  # Add more as they become available
        
        for provider in test_providers:
            print(f"Step 2.{len(responses)+1}: Asking {provider}...")
            try:
                response = requests.post(
                    f"{API_BASE_URL}/simple/chat",
                    json={
                        "user_query": question,
                        "provider": provider,
                        "model": "gemini-pro" if provider == "google" else "default"
                    },
                    timeout=TEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    responses[provider] = data
                    print(f"✓ {provider} response: {len(data.get('message', ''))} characters")
            except Exception as e:
                print(f"⚠️ {provider} failed: {e}")
        
        # Step 3: Compare responses
        print("Step 3: Comparing responses...")
        if len(responses) > 0:
            for provider, data in responses.items():
                print(f"✓ {provider}: {data.get('status', 'unknown')} - {data.get('model', 'unknown')}")
        else:
            print("⚠️ No successful responses to compare")
        
        print("✅ Multi-Model Comparison Workflow Complete!")

    def test_error_handling_and_recovery_workflow(self):
        """Test user workflow with error conditions and recovery."""
        print("\n⚠️ Testing Error Handling and Recovery Workflow")
        
        # Step 1: Test with invalid input
        print("Step 1: Testing invalid input handling...")
        invalid_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={"invalid": "data"}  # Missing required fields
        )
        assert invalid_response.status_code == 422
        print("✓ Invalid input properly rejected")
        
        # Step 2: Recovery with valid input
        print("Step 2: Recovering with valid input...")
        valid_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={
                "user_query": "This is a valid query",
                "provider": "google",
                "model": "gemini-pro"
            },
            timeout=TEST_TIMEOUT
        )
        assert valid_response.status_code == 200
        print("✓ Valid input processed successfully")
        
        # Step 3: Test with non-existent endpoint
        print("Step 3: Testing non-existent endpoint...")
        not_found_response = requests.get(f"{API_BASE_URL}/nonexistent")
        assert not_found_response.status_code == 404
        print("✓ Non-existent endpoint properly handled")
        
        # Step 4: Test rate limiting / performance under load
        print("Step 4: Testing concurrent requests...")
        import concurrent.futures
        
        def make_request():
            return requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        successful_requests = sum(1 for r in results if r.status_code == 200)
        print(f"✓ {successful_requests}/5 concurrent requests successful")
        assert successful_requests >= 4  # Allow for some variability
        
        print("✅ Error Handling and Recovery Workflow Complete!")

    def test_session_persistence_workflow(self):
        """Test user session persistence across multiple interactions."""
        print("\n💾 Testing Session Persistence Workflow")
        
        # Step 1: Start a conversation
        print("Step 1: Starting conversation...")
        first_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={
                "user_query": "Hello, I'm starting a new conversation",
                "provider": "google",
                "model": "gemini-pro"
            },
            timeout=TEST_TIMEOUT
        )
        assert first_response.status_code == 200
        print("✓ First message sent")
        
        # Step 2: Continue conversation
        print("Step 2: Continuing conversation...")
        second_response = requests.post(
            f"{API_BASE_URL}/simple/chat",
            json={
                "user_query": "Can you remember what I just said?",
                "provider": "google",
                "model": "gemini-pro"
            },
            timeout=TEST_TIMEOUT
        )
        assert second_response.status_code == 200
        print("✓ Second message sent")
        
        # Step 3: Check different endpoints maintain state
        print("Step 3: Testing different endpoints...")
        models_response = requests.get(f"{API_BASE_URL}/models/config")
        assert models_response.status_code == 200
        
        health_response = requests.get(f"{API_BASE_URL}/health")
        assert health_response.status_code == 200
        
        print("✓ Different endpoints accessible")
        
        # Note: Session persistence would need to be implemented at the application level
        # This test verifies that the API can handle multiple sequential requests
        
        print("✅ Session Persistence Workflow Complete!")


class TestE2EPerformanceWorkflows:
    """Performance-focused end-to-end workflow tests."""
    
    @pytest.mark.slow
    def test_high_load_user_workflow(self):
        """Test user workflow under high load conditions."""
        print("\n🚀 Testing High Load User Workflow")
        
        import concurrent.futures
        import threading
        import time
        
        # Simulate multiple users performing workflows simultaneously
        def user_workflow(user_id):
            try:
                # Each user performs a complete workflow
                start_time = time.time()
                
                # Health check
                health = requests.get(f"{API_BASE_URL}/health", timeout=5)
                
                # Chat interaction
                chat = requests.post(
                    f"{API_BASE_URL}/simple/chat",
                    json={
                        "user_query": f"User {user_id} asks: What is Python?",
                        "provider": "google",
                        "model": "gemini-pro"
                    },
                    timeout=15
                )
                
                end_time = time.time()
                
                return {
                    "user_id": user_id,
                    "success": health.status_code == 200 and chat.status_code == 200,
                    "duration": end_time - start_time,
                    "health_status": health.status_code,
                    "chat_status": chat.status_code
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
        
        # Test with 10 concurrent users
        num_users = 10
        print(f"Step 1: Simulating {num_users} concurrent users...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_workflow, i) for i in range(num_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_users = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results if "duration" in r) / len(results)
        max_duration = max(r.get("duration", 0) for r in results)
        
        print(f"✓ Successful users: {successful_users}/{num_users}")
        print(f"✓ Average duration: {avg_duration:.2f}s")
        print(f"✓ Max duration: {max_duration:.2f}s")
        
        # Assertions for performance
        assert successful_users >= num_users * 0.8  # 80% success rate
        assert avg_duration < 20.0  # Average under 20 seconds
        assert max_duration < 30.0  # Max under 30 seconds
        
        print("✅ High Load User Workflow Complete!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])