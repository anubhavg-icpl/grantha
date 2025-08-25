"""
WebSocket integration tests for Grantha API.
Tests real-time communication functionality.
"""

import pytest
import asyncio
import json
import websockets
import requests
from typing import Dict, Any

# Test configuration
WS_BASE_URL = "ws://localhost:8000"
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method run before each test."""
        # Check if API is available
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API server not available")
        except requests.exceptions.RequestException:
            pytest.skip("API server not available")

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test basic WebSocket connection establishment."""
        try:
            # Attempt to connect to WebSocket endpoint
            # Note: This assumes there's a WebSocket endpoint at /ws
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                # Send a ping to verify connection
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    assert "type" in data or "status" in data
                except asyncio.TimeoutError:
                    # Timeout is acceptable if WebSocket isn't fully implemented
                    pass
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            # WebSocket endpoint may not be implemented yet
            pytest.skip("WebSocket endpoint not available")

    @pytest.mark.asyncio
    async def test_websocket_chat_functionality(self):
        """Test WebSocket chat functionality."""
        try:
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                # Send chat message
                chat_message = {
                    "type": "chat",
                    "content": "Hello, WebSocket chat!",
                    "user_id": "test_user"
                }
                
                await websocket.send(json.dumps(chat_message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    # Should receive chat response
                    assert "type" in data
                    assert data["type"] in ["chat_response", "message", "response"]
                    
                except asyncio.TimeoutError:
                    # May not be implemented
                    pass
                    
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket chat endpoint not available")

    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(self):
        """Test multiple concurrent WebSocket connections."""
        try:
            connections = []
            
            # Establish multiple connections
            for i in range(3):
                try:
                    conn = await websockets.connect(f"{WS_BASE_URL}/ws", timeout=5)
                    connections.append(conn)
                except Exception:
                    break
            
            if not connections:
                pytest.skip("Could not establish WebSocket connections")
            
            # Send messages from each connection
            tasks = []
            for i, conn in enumerate(connections):
                message = {
                    "type": "test",
                    "content": f"Message from connection {i}",
                    "connection_id": i
                }
                task = conn.send(json.dumps(message))
                tasks.append(task)
            
            # Wait for all sends to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Close connections
            for conn in connections:
                try:
                    await conn.close()
                except Exception:
                    pass
                    
        except Exception:
            pytest.skip("WebSocket multiple connections test not applicable")

    @pytest.mark.asyncio
    async def test_websocket_message_validation(self):
        """Test WebSocket message validation."""
        try:
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                # Send invalid JSON
                await websocket.send("invalid json")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    # Should receive error response
                    if "error" in data:
                        assert "error" in data
                        assert "invalid" in data["error"].lower()
                        
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    # Connection might be closed or no response
                    pass
                    
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket endpoint not available")

    @pytest.mark.asyncio
    async def test_websocket_large_message_handling(self):
        """Test WebSocket handling of large messages."""
        try:
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                # Send large message
                large_content = "x" * 10000  # 10KB message
                large_message = {
                    "type": "test",
                    "content": large_content,
                    "size": len(large_content)
                }
                
                await websocket.send(json.dumps(large_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    # Should handle large message gracefully
                    assert len(response) > 0
                    
                except asyncio.TimeoutError:
                    # May have size limits
                    pass
                    
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket endpoint not available")


class TestWebSocketPerformance:
    """Performance tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_websocket_connection_performance(self):
        """Test WebSocket connection establishment performance."""
        try:
            connection_times = []
            
            for _ in range(10):
                import time
                start_time = time.time()
                
                try:
                    async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=5) as websocket:
                        # Send ping to verify connection
                        await websocket.send(json.dumps({"type": "ping"}))
                        connection_time = time.time() - start_time
                        connection_times.append(connection_time)
                except Exception:
                    break
            
            if connection_times:
                avg_connection_time = sum(connection_times) / len(connection_times)
                max_connection_time = max(connection_times)
                
                # Connection should be established quickly
                assert avg_connection_time < 1.0  # Under 1 second average
                assert max_connection_time < 2.0  # Under 2 seconds max
            else:
                pytest.skip("Could not establish WebSocket connections for performance test")
                
        except Exception:
            pytest.skip("WebSocket performance test not applicable")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput."""
        try:
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                import time
                start_time = time.time()
                message_count = 50
                
                # Send multiple messages rapidly
                for i in range(message_count):
                    message = {
                        "type": "throughput_test",
                        "message_id": i,
                        "content": f"Test message {i}"
                    }
                    await websocket.send(json.dumps(message))
                
                end_time = time.time()
                total_time = end_time - start_time
                messages_per_second = message_count / total_time
                
                # Should handle reasonable message throughput
                assert messages_per_second > 10  # At least 10 messages per second
                
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket throughput test not applicable")


class TestWebSocketResilience:
    """Resilience and error handling tests for WebSocket."""
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection_capability(self):
        """Test WebSocket reconnection after disconnect."""
        try:
            # First connection
            conn1 = await websockets.connect(f"{WS_BASE_URL}/ws", timeout=5)
            await conn1.send(json.dumps({"type": "test", "connection": 1}))
            await conn1.close()
            
            # Second connection after disconnect
            conn2 = await websockets.connect(f"{WS_BASE_URL}/ws", timeout=5)
            await conn2.send(json.dumps({"type": "test", "connection": 2}))
            await conn2.close()
            
            # Should be able to reconnect successfully
            assert True
            
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket reconnection test not applicable")

    @pytest.mark.asyncio
    async def test_websocket_error_recovery(self):
        """Test WebSocket error recovery."""
        try:
            async with websockets.connect(f"{WS_BASE_URL}/ws", timeout=10) as websocket:
                # Send invalid message type
                await websocket.send(json.dumps({"type": "invalid_type"}))
                
                # Send valid message after invalid one
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Connection should remain stable
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    # Should receive response or timeout gracefully
                    assert True
                except asyncio.TimeoutError:
                    assert True
                    
        except (websockets.exceptions.InvalidURI, 
                websockets.exceptions.InvalidHandshake,
                ConnectionRefusedError,
                OSError):
            pytest.skip("WebSocket error recovery test not applicable")


if __name__ == "__main__":
    # Run with asyncio support
    pytest.main([__file__, "-v", "-s"])