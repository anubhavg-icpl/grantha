"""Performance tests for authentication system."""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from src.grantha.database.services import UserService, RefreshTokenService, AuthEventService
from src.grantha.database.auth_service import DatabaseJWTService
from src.grantha.database.models import User


@pytest.mark.asyncio
class TestAuthenticationPerformance:
    """Test authentication performance characteristics."""
    
    async def test_password_hashing_performance(self, test_session, user_data_factory):
        """Test password hashing performance."""
        # Test password hashing time
        start_time = time.perf_counter()
        
        # Create multiple users with password hashing
        users_to_create = 10
        tasks = []
        
        for i in range(users_to_create):
            user_data = user_data_factory(username=f"perfuser{i}")
            task = UserService.create_user(session=test_session, **user_data)
            tasks.append(task)
        
        users = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_per_user = total_time / users_to_create
        
        # Password hashing should be reasonably fast but not too fast (security vs performance)
        assert total_time < 10.0  # Should complete in under 10 seconds
        assert avg_time_per_user < 2.0  # Should take less than 2 seconds per user
        assert avg_time_per_user > 0.01  # Should take at least 10ms (indicates proper hashing)
        
        # Verify all users were created successfully
        assert len(users) == users_to_create
        for user in users:
            assert user.password_hash is not None
            assert user.verify_password("testpass123")
    
    async def test_login_performance(self, test_session, multiple_users):
        """Test login performance under load."""
        jwt_service = DatabaseJWTService()
        
        async def perform_login(user):
            start = time.perf_counter()
            
            access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=user.username,
                password=f"pass{user.username[-1]}123",  # Extract index from username
                ip_address="127.0.0.1",
                user_agent="perf-test-client"
            )
            
            end = time.perf_counter()
            login_time = end - start
            
            return {
                "user_id": str(user.id),
                "login_time": login_time,
                "success": access_token is not None,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        
        # Perform concurrent logins
        start_time = time.perf_counter()
        
        login_tasks = [perform_login(user) for user in multiple_users]
        results = await asyncio.gather(*login_tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Filter successful results
        successful_logins = [
            r for r in results 
            if not isinstance(r, Exception) and r.get("success")
        ]
        
        # Performance assertions
        assert len(successful_logins) >= len(multiple_users) * 0.8  # At least 80% success rate
        assert total_time < 5.0  # Should complete in under 5 seconds
        
        # Individual login times should be reasonable
        login_times = [r["login_time"] for r in successful_logins]
        avg_login_time = sum(login_times) / len(login_times)
        max_login_time = max(login_times)
        
        assert avg_login_time < 1.0  # Average login should be under 1 second
        assert max_login_time < 3.0  # No single login should take more than 3 seconds
        
        print(f"Concurrent logins: {len(successful_logins)}/{len(multiple_users)}")
        print(f"Average login time: {avg_login_time:.3f}s")
        print(f"Max login time: {max_login_time:.3f}s")
        print(f"Total time: {total_time:.3f}s")
    
    async def test_token_refresh_performance(self, test_session, test_user, sample_user_data):
        """Test token refresh performance."""
        jwt_service = DatabaseJWTService()
        
        # Generate initial tokens
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Perform multiple token refreshes
        refresh_count = 20
        refresh_times = []
        
        current_refresh_token = refresh_token
        
        for i in range(refresh_count):
            start = time.perf_counter()
            
            new_access_token, user_info = await jwt_service.refresh_access_token(
                session=test_session,
                refresh_token=current_refresh_token
            )
            
            end = time.perf_counter()
            refresh_time = end - start
            
            if new_access_token:
                refresh_times.append(refresh_time)
            else:
                break  # Refresh failed
        
        # Performance assertions
        assert len(refresh_times) >= refresh_count * 0.9  # At least 90% success rate
        
        avg_refresh_time = sum(refresh_times) / len(refresh_times)
        max_refresh_time = max(refresh_times)
        
        assert avg_refresh_time < 0.5  # Average refresh should be under 500ms
        assert max_refresh_time < 2.0   # No refresh should take more than 2 seconds
        
        print(f"Token refreshes: {len(refresh_times)}/{refresh_count}")
        print(f"Average refresh time: {avg_refresh_time:.3f}s")
        print(f"Max refresh time: {max_refresh_time:.3f}s")
    
    async def test_database_query_performance(self, test_session, multiple_users):
        """Test database query performance."""
        # Test user lookup performance
        lookup_times = []
        
        for user in multiple_users[:10]:  # Test first 10 users
            start = time.perf_counter()
            
            found_user = await UserService.get_user_by_username(
                session=test_session,
                username=user.username
            )
            
            end = time.perf_counter()
            lookup_time = end - start
            
            assert found_user is not None
            assert found_user.id == user.id
            lookup_times.append(lookup_time)
        
        avg_lookup_time = sum(lookup_times) / len(lookup_times)
        max_lookup_time = max(lookup_times)
        
        # Database lookups should be fast
        assert avg_lookup_time < 0.1   # Average lookup under 100ms
        assert max_lookup_time < 0.5   # No lookup over 500ms
        
        print(f"Average user lookup time: {avg_lookup_time:.3f}s")
        print(f"Max user lookup time: {max_lookup_time:.3f}s")
    
    async def test_concurrent_authentication_performance(self, test_session, multiple_users):
        """Test performance under concurrent authentication load."""
        jwt_service = DatabaseJWTService()
        
        async def authenticate_user(user, attempt_num):
            try:
                start = time.perf_counter()
                
                # Extract user index from username for password
                user_index = user.username.replace("user", "")
                password = f"pass{user_index}123"
                
                result = await jwt_service.authenticate_and_generate_tokens(
                    session=test_session,
                    username=user.username,
                    password=password,
                    ip_address=f"192.168.1.{(attempt_num % 254) + 1}",
                    user_agent=f"concurrent-client-{attempt_num}"
                )
                
                end = time.perf_counter()
                
                return {
                    "user_id": str(user.id),
                    "attempt": attempt_num,
                    "time": end - start,
                    "success": result[0] is not None
                }
                
            except Exception as e:
                return {
                    "user_id": str(user.id),
                    "attempt": attempt_num,
                    "time": None,
                    "success": False,
                    "error": str(e)
                }
        
        # Create concurrent authentication tasks
        concurrent_factor = 3  # 3 attempts per user
        tasks = []
        
        for attempt in range(concurrent_factor):
            for user in multiple_users:
                task = authenticate_user(user, attempt)
                tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful_auths = [
            r for r in results 
            if not isinstance(r, Exception) and r.get("success")
        ]
        
        failed_auths = [
            r for r in results 
            if isinstance(r, Exception) or not r.get("success")
        ]
        
        success_rate = len(successful_auths) / len(results) * 100
        
        # Performance assertions
        assert success_rate >= 70  # At least 70% success rate under load
        assert total_time < 30.0   # Should complete within 30 seconds
        
        if successful_auths:
            auth_times = [r["time"] for r in successful_auths if r["time"]]
            avg_auth_time = sum(auth_times) / len(auth_times)
            max_auth_time = max(auth_times)
            
            assert avg_auth_time < 2.0  # Average auth under 2 seconds
            assert max_auth_time < 10.0  # No auth over 10 seconds
            
            print(f"Concurrent authentications: {len(results)} total")
            print(f"Success rate: {success_rate:.1f}%")
            print(f"Total time: {total_time:.3f}s")
            print(f"Average auth time: {avg_auth_time:.3f}s")
            print(f"Max auth time: {max_auth_time:.3f}s")
            print(f"Failed authentications: {len(failed_auths)}")
    
    async def test_session_cleanup_performance(self, test_session, test_user):
        """Test performance of session cleanup operations."""
        # Create many refresh tokens (some expired)
        token_count = 100
        expired_count = 0
        
        for i in range(token_count):
            # Create mix of active and expired tokens
            if i % 3 == 0:  # Every 3rd token is expired
                expires_at = datetime.now(timezone.utc) - timedelta(days=1)
                expired_count += 1
            else:
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            await RefreshTokenService.create_refresh_token(
                session=test_session,
                user_id=str(test_user.id),
                token_id=f"perf_token_{i}",
                expires_at=expires_at
            )
        
        # Test cleanup performance
        start_time = time.perf_counter()
        
        jwt_service = DatabaseJWTService()
        cleaned_count = await jwt_service.cleanup_expired_tokens(test_session)
        
        end_time = time.perf_counter()
        cleanup_time = end_time - start_time
        
        # Verify cleanup worked
        assert cleaned_count == expired_count
        
        # Performance assertions
        assert cleanup_time < 5.0  # Cleanup should complete in under 5 seconds
        
        # Performance per token should be reasonable
        time_per_token = cleanup_time / token_count
        assert time_per_token < 0.1  # Under 100ms per token processed
        
        print(f"Cleaned up {cleaned_count}/{token_count} tokens in {cleanup_time:.3f}s")
        print(f"Time per token: {time_per_token:.3f}s")


@pytest.mark.asyncio
class TestScalabilityLimits:
    """Test system scalability and limits."""
    
    async def test_maximum_concurrent_sessions(self, test_session, test_user, sample_user_data):
        """Test maximum number of concurrent sessions per user."""
        jwt_service = DatabaseJWTService()
        
        # Create many concurrent sessions
        max_sessions = 50
        created_sessions = []
        
        for i in range(max_sessions):
            try:
                access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
                    session=test_session,
                    username=test_user.username,
                    password=sample_user_data["password"],
                    ip_address=f"10.0.{i//254}.{(i%254)+1}",
                    user_agent=f"session-client-{i}"
                )
                
                if access_token:
                    created_sessions.append({
                        "session_num": i,
                        "access_token": access_token,
                        "refresh_token": refresh_token
                    })
                    
            except Exception as e:
                print(f"Failed to create session {i}: {e}")
                break
        
        # Test session retrieval performance with many sessions
        start_time = time.perf_counter()
        
        user_sessions = await jwt_service.get_user_sessions(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        end_time = time.perf_counter()
        retrieval_time = end_time - start_time
        
        # Performance assertions
        assert len(created_sessions) >= max_sessions * 0.8  # At least 80% created successfully
        assert len(user_sessions) >= len(created_sessions) * 0.9  # At least 90% retrieved
        assert retrieval_time < 2.0  # Session retrieval should be fast even with many sessions
        
        print(f"Created {len(created_sessions)} sessions")
        print(f"Retrieved {len(user_sessions)} sessions in {retrieval_time:.3f}s")
    
    async def test_bulk_user_operations(self, test_session):
        """Test performance of bulk user operations."""
        # Test bulk user creation
        bulk_size = 100
        start_time = time.perf_counter()
        
        # Create users in batches to avoid overwhelming the database
        batch_size = 10
        created_users = []
        
        for batch_start in range(0, bulk_size, batch_size):
            batch_tasks = []
            
            for i in range(batch_start, min(batch_start + batch_size, bulk_size)):
                user_data = {
                    "username": f"bulk_user_{i}",
                    "password": f"bulkpass{i}123",
                    "email": f"bulk{i}@example.com",
                    "full_name": f"Bulk User {i}"
                }
                
                task = UserService.create_user(session=test_session, **user_data)
                batch_tasks.append(task)
            
            try:
                batch_users = await asyncio.gather(*batch_tasks)
                created_users.extend(batch_users)
            except Exception as e:
                print(f"Batch {batch_start//batch_size} failed: {e}")
                break
        
        creation_time = time.perf_counter() - start_time
        
        # Test bulk user lookup
        start_time = time.perf_counter()
        
        lookup_tasks = [
            UserService.get_user_by_username(session=test_session, username=user.username)
            for user in created_users[:50]  # Lookup first 50 users
        ]
        
        looked_up_users = await asyncio.gather(*lookup_tasks, return_exceptions=True)
        
        lookup_time = time.perf_counter() - start_time
        
        # Performance assertions
        assert len(created_users) >= bulk_size * 0.8  # At least 80% created
        
        successful_lookups = [
            u for u in looked_up_users 
            if not isinstance(u, Exception) and u is not None
        ]
        assert len(successful_lookups) >= 45  # At least 90% of 50 lookups successful
        
        # Time per operation should be reasonable
        time_per_creation = creation_time / len(created_users)
        time_per_lookup = lookup_time / len(successful_lookups)
        
        assert time_per_creation < 0.5  # Under 500ms per user creation
        assert time_per_lookup < 0.1    # Under 100ms per user lookup
        
        print(f"Created {len(created_users)} users in {creation_time:.3f}s ({time_per_creation:.3f}s each)")
        print(f"Looked up {len(successful_lookups)} users in {lookup_time:.3f}s ({time_per_lookup:.3f}s each)")
    
    async def test_authentication_event_logging_performance(self, test_session, test_user):
        """Test performance of authentication event logging."""
        # Create many auth events
        event_count = 500
        start_time = time.perf_counter()
        
        # Create events in batches
        batch_size = 50
        created_events = 0
        
        for batch_start in range(0, event_count, batch_size):
            batch_tasks = []
            
            for i in range(batch_start, min(batch_start + batch_size, event_count)):
                event_type = ["login", "logout", "password_change"][i % 3]
                success = i % 4 != 0  # 75% success rate
                
                task = AuthEventService.log_event(
                    session=test_session,
                    event_type=event_type,
                    user_id=str(test_user.id) if success else None,
                    success=success,
                    ip_address=f"192.168.{(i//254)+1}.{(i%254)+1}",
                    user_agent=f"perf-client-{i}",
                    failure_reason="test_failure" if not success else None
                )
                batch_tasks.append(task)
            
            try:
                await asyncio.gather(*batch_tasks)
                created_events += len(batch_tasks)
            except Exception as e:
                print(f"Event batch {batch_start//batch_size} failed: {e}")
                break
        
        creation_time = time.perf_counter() - start_time
        
        # Test event retrieval performance
        start_time = time.perf_counter()
        
        user_events = await AuthEventService.get_user_events(
            session=test_session,
            user_id=str(test_user.id),
            limit=100
        )
        
        security_events = await AuthEventService.get_security_events(
            session=test_session,
            hours_back=24,
            limit=100
        )
        
        stats = await AuthEventService.get_failed_login_stats(
            session=test_session,
            hours_back=24
        )
        
        retrieval_time = time.perf_counter() - start_time
        
        # Performance assertions
        assert created_events >= event_count * 0.8  # At least 80% created
        assert retrieval_time < 3.0  # Retrieval should be fast
        
        time_per_event = creation_time / created_events
        assert time_per_event < 0.1  # Under 100ms per event
        
        # Verify events were created and can be retrieved
        assert len(user_events) > 0
        assert len(security_events) > 0
        assert stats["failed_logins"] > 0
        
        print(f"Created {created_events} events in {creation_time:.3f}s ({time_per_event:.3f}s each)")
        print(f"Retrieved events in {retrieval_time:.3f}s")
        print(f"User events: {len(user_events)}, Security events: {len(security_events)}")


@pytest.mark.asyncio 
class TestMemoryUsage:
    """Test memory usage patterns."""
    
    async def test_token_storage_memory_usage(self, test_session, test_user):
        """Test memory usage of token storage."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many tokens
        token_count = 1000
        tokens = []
        
        for i in range(token_count):
            token = await RefreshTokenService.create_refresh_token(
                session=test_session,
                user_id=str(test_user.id),
                token_id=f"memory_token_{i}",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            tokens.append(token)
        
        # Get memory usage after creating tokens
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        memory_per_token = memory_increase / token_count
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Assertions (these are approximate due to garbage collection, etc.)
        assert memory_increase_mb < 100  # Should not use more than 100MB
        assert memory_per_token < 10000   # Should not use more than 10KB per token
        
        print(f"Created {token_count} tokens")
        print(f"Memory increase: {memory_increase_mb:.2f} MB")
        print(f"Memory per token: {memory_per_token:.0f} bytes")
        
        # Cleanup tokens
        for token in tokens:
            await RefreshTokenService.revoke_refresh_token(
                session=test_session,
                token_id=token.token_id,
                reason="memory_test_cleanup"
            )
    
    async def test_user_session_memory_scaling(self, test_session, multiple_users):
        """Test memory usage with many user sessions."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        jwt_service = DatabaseJWTService()
        active_sessions = []
        
        # Create sessions for each user
        for i, user in enumerate(multiple_users):
            password = f"pass{i}123"
            
            access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=user.username,
                password=password,
                ip_address=f"10.0.0.{i+1}",
                user_agent=f"memory-test-{i}"
            )
            
            if access_token:
                active_sessions.append({
                    "user": user,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_info": user_info
                })
        
        # Test getting all user sessions
        all_sessions = []
        for session_data in active_sessions:
            user_sessions = await jwt_service.get_user_sessions(
                session=test_session,
                user_id=session_data["user_info"]["id"]
            )
            all_sessions.extend(user_sessions)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory usage should scale reasonably with number of sessions
        session_count = len(active_sessions)
        memory_per_session = memory_increase / session_count if session_count > 0 else 0
        
        assert memory_increase_mb < 50  # Should not use more than 50MB
        assert memory_per_session < 50000  # Should not use more than 50KB per session
        
        print(f"Created {session_count} user sessions")
        print(f"Retrieved {len(all_sessions)} session objects")
        print(f"Memory increase: {memory_increase_mb:.2f} MB")
        print(f"Memory per session: {memory_per_session:.0f} bytes")


@pytest.mark.asyncio
class TestCachePerformance:
    """Test caching and performance optimizations."""
    
    async def test_user_lookup_caching_simulation(self, test_session, multiple_users):
        """Simulate user lookup caching performance benefits."""
        # Simulate cache with simple dictionary
        user_cache = {}
        
        # First pass: cold cache (database lookups)
        cold_start = time.perf_counter()
        
        for user in multiple_users[:10]:  # Test first 10 users
            if user.username not in user_cache:
                db_user = await UserService.get_user_by_username(
                    session=test_session,
                    username=user.username
                )
                user_cache[user.username] = db_user
        
        cold_time = time.perf_counter() - cold_start
        
        # Second pass: warm cache (cached lookups)
        warm_start = time.perf_counter()
        
        for user in multiple_users[:10]:
            cached_user = user_cache.get(user.username)
            assert cached_user is not None
        
        warm_time = time.perf_counter() - warm_start
        
        # Cache should provide significant performance improvement
        speedup_ratio = cold_time / warm_time if warm_time > 0 else float('inf')
        
        assert speedup_ratio > 10  # Cache should be at least 10x faster
        assert cold_time > 0.01    # Database lookups should take measurable time
        assert warm_time < 0.001   # Cached lookups should be very fast
        
        print(f"Cold cache time: {cold_time:.3f}s")
        print(f"Warm cache time: {warm_time:.3f}s")
        print(f"Speedup ratio: {speedup_ratio:.1f}x")
    
    async def test_jwt_token_validation_performance(self, jwt_service):
        """Test JWT token validation performance."""
        # Generate test tokens
        token_count = 100
        test_tokens = []
        
        for i in range(token_count):
            user_id = f"user-{i}"
            token = jwt_service._fallback_service.generate_tokens(user_id)[0]
            test_tokens.append(token)
        
        # Test token validation performance
        start_time = time.perf_counter()
        
        validation_results = []
        for token in test_tokens:
            result = jwt_service.validate_access_token(token)
            validation_results.append(result is not None)
        
        end_time = time.perf_counter()
        validation_time = end_time - start_time
        
        # Performance assertions
        valid_tokens = sum(validation_results)
        assert valid_tokens == token_count  # All tokens should be valid
        
        time_per_validation = validation_time / token_count
        assert time_per_validation < 0.001  # Should validate each token in under 1ms
        assert validation_time < 0.1         # Total time should be under 100ms
        
        print(f"Validated {token_count} tokens in {validation_time:.3f}s")
        print(f"Time per validation: {time_per_validation:.6f}s")
        
        # Test validation with mix of valid and invalid tokens
        invalid_tokens = ["invalid.token.here"] * 50
        mixed_tokens = test_tokens[:50] + invalid_tokens
        
        start_time = time.perf_counter()
        
        mixed_results = []
        for token in mixed_tokens:
            result = jwt_service.validate_access_token(token)
            mixed_results.append(result is not None)
        
        mixed_validation_time = time.perf_counter() - start_time
        
        valid_count = sum(mixed_results)
        assert valid_count == 50  # Only the valid tokens should pass
        
        mixed_time_per_validation = mixed_validation_time / len(mixed_tokens)
        assert mixed_time_per_validation < 0.002  # Should handle invalid tokens quickly too
        
        print(f"Mixed validation: {valid_count}/{len(mixed_tokens)} valid in {mixed_validation_time:.3f}s")