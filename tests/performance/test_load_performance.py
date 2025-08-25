"""
Performance tests for Grantha API endpoints.
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from api.api import app


@pytest.fixture
def perf_client():
    """Create test client for performance testing."""
    return TestClient(app)


@pytest.mark.slow
@pytest.mark.performance
class TestAPIPerformance:
    """Performance test suite for API endpoints."""
    
    def test_health_endpoint_response_time(self, perf_client):
        """Test health endpoint response time."""
        # Warm up
        perf_client.get("/health")
        
        start_time = time.time()
        response = perf_client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms
        
    def test_root_endpoint_response_time(self, perf_client):
        """Test root endpoint response time."""
        # Warm up
        perf_client.get("/")
        
        start_time = time.time()
        response = perf_client.get("/")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.2  # Should respond within 200ms
        
    def test_models_config_endpoint_response_time(self, perf_client):
        """Test models config endpoint response time."""
        # Warm up
        perf_client.get("/models/config")
        
        start_time = time.time()
        response = perf_client.get("/models/config")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Configuration loading should be fast
        
    def test_concurrent_health_checks(self, perf_client):
        """Test concurrent health check requests."""
        def make_request():
            return perf_client.get("/health")
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
            end_time = time.time()
        
        total_time = end_time - start_time
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Total time should be reasonable for 10 concurrent requests
        assert total_time < 2.0
        
    def test_wiki_cache_performance(self, perf_client):
        """Test wiki cache retrieval performance."""
        params = {
            "owner": "testuser",
            "repo": "testrepo",
            "repo_type": "github", 
            "language": "en"
        }
        
        # Warm up
        perf_client.get("/api/wiki_cache", params=params)
        
        start_time = time.time()
        response = perf_client.get("/api/wiki_cache", params=params)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Cache lookup should be fast
        
    @patch('api.api.WikiGenerator')
    @patch('api.api.download_repo')
    def test_wiki_generation_performance(self, mock_download, mock_wiki_gen, perf_client):
        """Test wiki generation performance."""
        # Mock dependencies to avoid actual processing
        mock_download.return_value = "/tmp/test_repo"
        mock_generator = Mock()
        mock_generator.generate_wiki_structure.return_value = {
            "title": "Test Wiki",
            "pages": [{"id": "page1", "title": "Test Page"}]
        }
        mock_wiki_gen.return_value = mock_generator
        
        request_data = {
            "repo_url": "https://github.com/test/repo",
            "language": "en",
            "provider": "google",
            "repo_type": "github"
        }
        
        start_time = time.time()
        response = perf_client.post("/api/wiki/generate", json=request_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        # Mocked generation should be fast
        assert response_time < 2.0
        
    def test_large_payload_handling(self, perf_client):
        """Test handling of large request payloads.""" 
        # Create large wiki data payload
        large_pages = []
        for i in range(100):  # 100 pages
            large_pages.append({
                "id": f"page_{i}",
                "title": f"Test Page {i}",
                "content": "x" * 1000,  # 1KB content per page
                "filePaths": [f"file_{i}.py"],
                "importance": "medium",
                "relatedPages": []
            })
        
        export_request = {
            "repo_url": "https://github.com/test/large-repo",
            "format": "json",
            "pages": large_pages
        }
        
        start_time = time.time()
        response = perf_client.post("/export/wiki", json=export_request)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should handle large payloads reasonably fast
        
    def test_memory_usage_wiki_cache_storage(self, perf_client):
        """Test memory usage during wiki cache storage."""
        import tracemalloc
        
        # Start tracing memory
        tracemalloc.start()
        
        cache_data = {
            "repo": {
                "owner": "test",
                "repo": "memory-test",
                "type": "github",
                "repoUrl": "https://github.com/test/memory-test"
            },
            "language": "en",
            "wiki_structure": {
                "id": "test_wiki",
                "title": "Memory Test Wiki",
                "description": "Testing memory usage",
                "pages": [
                    {
                        "id": f"page_{i}",
                        "title": f"Page {i}",
                        "content": "x" * 500,  # 500 bytes per page
                        "filePaths": [f"file_{i}.py"],
                        "importance": "medium",
                        "relatedPages": []
                    }
                    for i in range(50)  # 50 pages
                ],
                "sections": [],
                "rootSections": []
            },
            "generated_pages": {},
            "provider": "google",
            "model": "gemini-2.5-flash"
        }
        
        with patch('api.api.save_wiki_cache') as mock_save:
            mock_save.return_value = True
            
            # Measure memory before
            snapshot1 = tracemalloc.take_snapshot()
            
            response = perf_client.post("/api/wiki_cache", json=cache_data)
            
            # Measure memory after
            snapshot2 = tracemalloc.take_snapshot()
            
        # Stop tracing
        tracemalloc.stop()
        
        assert response.status_code == 200
        
        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_diff = sum(stat.size_diff for stat in top_stats)
        
        # Memory increase should be reasonable (less than 10MB for this test)
        assert total_memory_diff < 10 * 1024 * 1024
        
    def test_response_compression_efficiency(self, perf_client):
        """Test response size for large content."""
        # Create large export request
        large_content = "# Large Document\n\n" + ("This is repeated content. " * 1000)
        large_pages = [{
            "id": "large_page",
            "title": "Large Page",
            "content": large_content,
            "filePaths": ["large_file.py"],
            "importance": "high",
            "relatedPages": []
        }]
        
        export_request = {
            "repo_url": "https://github.com/test/large-content",
            "format": "markdown",
            "pages": large_pages
        }
        
        response = perf_client.post("/export/wiki", json=export_request)
        
        assert response.status_code == 200
        
        # Response should contain the large content
        content_size = len(response.content)
        assert content_size > 10000  # Should be substantial
        
        # Check if compression headers are present (if implemented)
        if "content-encoding" in response.headers:
            assert response.headers["content-encoding"] in ["gzip", "br", "deflate"]
            
    def test_api_rate_limiting_behavior(self, perf_client):
        """Test API behavior under rapid requests."""
        def make_rapid_requests():
            responses = []
            for i in range(20):  # 20 rapid requests
                response = perf_client.get("/health")
                responses.append(response)
                time.sleep(0.05)  # 50ms between requests
            return responses
        
        start_time = time.time()
        responses = make_rapid_requests()
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All requests should succeed (no rate limiting in basic setup)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 18  # Allow for some potential timeouts
        
        # Should complete within reasonable time
        assert total_time < 5.0
        
    @pytest.mark.asyncio
    async def test_async_endpoint_performance(self, perf_client):
        """Test asynchronous endpoint performance."""
        async def make_async_request():
            # Simulate async operation timing
            start = time.time()
            # Using sync client in async context for testing
            response = perf_client.get("/models/config")
            end = time.time()
            return response, end - start
        
        # Run multiple async requests
        tasks = [make_async_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        responses, times = zip(*results)
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Average response time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0
        
    def test_database_connection_performance(self, perf_client):
        """Test database/cache connection performance."""
        # Test rapid cache access
        params = {
            "owner": "perftest",
            "repo": "cacherepo", 
            "repo_type": "github",
            "language": "en"
        }
        
        times = []
        for _ in range(10):
            start_time = time.time()
            response = perf_client.get("/api/wiki_cache", params=params)
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        # Cache access should be consistently fast
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 0.5
        assert max_time < 1.0
        
    def test_processed_projects_listing_performance(self, perf_client):
        """Test processed projects listing performance."""
        with patch('os.listdir') as mock_listdir:
            # Mock many cache files
            cache_files = [
                f"grantha_cache_github_user{i}_repo{i}_en.json"
                for i in range(100)
            ]
            mock_listdir.return_value = cache_files
            
            with patch('os.stat') as mock_stat:
                mock_stat.return_value = Mock(st_mtime=time.time())
                
                start_time = time.time()
                response = perf_client.get("/api/processed_projects")
                end_time = time.time()
                
                response_time = end_time - start_time
                
                assert response.status_code == 200
                assert response_time < 2.0  # Should handle many files quickly
                
                projects = response.json()
                assert len(projects) == 100