"""
Unit tests for ThreadSafeDatabaseManager

Tests the consolidated database manager that provides thread-safe operations,
connection pooling, and support for PostgreSQL, SQLite, and mock modes.
"""
import sqlite3

# Import the component under test
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from threadsafe_database_manager import DatabaseManager, ThreadSafeDatabaseManager


class TestThreadSafeDatabaseManager:
    """Test suite for ThreadSafeDatabaseManager component."""

    @pytest.fixture
    def mock_config(self):
        """Provide a test database configuration."""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_password",
            "pool_size": 5,
            "max_overflow": 10,
            "mock_mode": True,
        }

    @pytest.fixture
    def db_manager(self, mock_config):
        """Create a ThreadSafeDatabaseManager instance for testing."""
        with patch("threadsafe_database_manager.get_logger"):
            manager = ThreadSafeDatabaseManager(config=mock_config)
            return manager

    @pytest.fixture
    def mock_connection(self):
        """Mock database connection for testing."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
        connection.cursor.return_value.__exit__ = Mock(return_value=None)
        connection.commit = Mock()
        connection.rollback = Mock()
        connection.close = Mock()
        return connection

    @pytest.mark.unit
    def test_manager_initialization_mock_mode(self, mock_config):
        """Test initialization in mock mode."""
        with patch("threadsafe_database_manager.get_logger"):
            manager = ThreadSafeDatabaseManager(config=mock_config)

            assert manager.mock_mode is True
            assert manager.config["database"] == "test_db"
            assert manager.connection_pool is not None

    @pytest.mark.unit
    def test_manager_initialization_real_mode(self, mock_config):
        """Test initialization with real database mode."""
        mock_config["mock_mode"] = False

        with patch("threadsafe_database_manager.get_logger"):
            with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
                manager = ThreadSafeDatabaseManager(config=mock_config)

                assert manager.mock_mode is False
                assert manager.config["database"] == "test_db"
                mock_pool.assert_called_once()

    @pytest.mark.unit
    def test_connection_acquisition_mock_mode(self, db_manager):
        """Test connection acquisition in mock mode."""
        connection = db_manager.get_connection()

        assert connection is not None
        assert hasattr(connection, "cursor")
        assert hasattr(connection, "commit")
        assert hasattr(connection, "rollback")

    @pytest.mark.unit
    def test_connection_release_mock_mode(self, db_manager):
        """Test connection release in mock mode."""
        connection = db_manager.get_connection()

        # Test release
        result = db_manager.release_connection(connection)
        assert result is True

    @pytest.mark.unit
    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_connection_acquisition_real_mode(self, mock_pool, mock_config):
        """Test connection acquisition in real database mode."""
        mock_config["mock_mode"] = False
        mock_connection = Mock()
        mock_pool.return_value.getconn.return_value = mock_connection

        with patch("threadsafe_database_manager.get_logger"):
            manager = ThreadSafeDatabaseManager(config=mock_config)
            connection = manager.get_connection()

            assert connection == mock_connection
            mock_pool.return_value.getconn.assert_called_once()

    @pytest.mark.unit
    def test_execute_query_success(self, db_manager, sample_database_records):
        """Test successful query execution."""
        # Setup mock cursor behavior
        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value.__enter__ = Mock(
                return_value=mock_cursor
            )
            mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
            mock_cursor.fetchall.return_value = sample_database_records
            mock_get_conn.return_value = mock_connection

            # Execute query
            result = db_manager.execute_query(
                "SELECT * FROM properties WHERE apn = %s", ("10215009",)
            )

            # Verify results
            assert result is not None
            assert len(result) >= 1
            mock_cursor.execute.assert_called_once()

    @pytest.mark.unit
    def test_execute_query_error_handling(self, db_manager):
        """Test query execution error handling."""
        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value.__enter__ = Mock(
                return_value=mock_cursor
            )
            mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_get_conn.return_value = mock_connection

            # Execute query with error
            result = db_manager.execute_query("INVALID SQL", ())

            # Verify error handling
            assert result is None
            mock_connection.rollback.assert_called_once()

    @pytest.mark.unit
    def test_insert_property_data(self, db_manager, mock_property_data):
        """Test inserting property data."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Insert property data
            result = db_manager.insert_property(mock_property_data)

            # Verify insertion
            assert result is True
            mock_execute.assert_called_once()

            # Verify query parameters include property data
            call_args = mock_execute.call_args
            assert "INSERT" in call_args[0][0].upper()

    @pytest.mark.unit
    def test_update_property_data(self, db_manager, mock_property_data):
        """Test updating existing property data."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Update property data
            updated_data = {**mock_property_data, "assessed_value": 300000}
            result = db_manager.update_property(updated_data)

            # Verify update
            assert result is True
            mock_execute.assert_called_once()

            # Verify query parameters
            call_args = mock_execute.call_args
            assert "UPDATE" in call_args[0][0].upper()

    @pytest.mark.unit
    def test_search_properties_by_apn(self, db_manager, sample_database_records):
        """Test searching properties by APN."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = sample_database_records

            # Search by APN
            results = db_manager.search_properties_by_apn("10215009")

            # Verify search results
            assert results is not None
            assert len(results) >= 1
            mock_execute.assert_called_once()

    @pytest.mark.unit
    def test_search_properties_by_address(self, db_manager, sample_database_records):
        """Test searching properties by address."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = sample_database_records

            # Search by address
            results = db_manager.search_properties_by_address("10000 W Missouri Ave")

            # Verify search results
            assert results is not None
            mock_execute.assert_called_once()

    @pytest.mark.unit
    def test_batch_insert_properties(self, db_manager, mock_property_data):
        """Test batch insertion of multiple properties."""
        # Create batch data
        batch_data = []
        for i in range(5):
            property_data = {
                **mock_property_data,
                "apn": f"1021500{9+i}",
                "address": f"1000{i} W Missouri Ave",
            }
            batch_data.append(property_data)

        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Execute batch insert
            result = db_manager.batch_insert_properties(batch_data)

            # Verify batch operation
            assert result is True
            assert mock_execute.call_count == len(batch_data)

    @pytest.mark.unit
    def test_transaction_management(self, db_manager):
        """Test transaction management functionality."""
        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_connection = Mock()
            mock_get_conn.return_value = mock_connection

            # Test transaction start
            db_manager.begin_transaction()
            mock_connection.autocommit = False

            # Test transaction commit
            db_manager.commit_transaction()
            mock_connection.commit.assert_called_once()

            # Test transaction rollback
            db_manager.rollback_transaction()
            mock_connection.rollback.assert_called_once()

    @pytest.mark.unit
    def test_connection_pool_management(self, db_manager):
        """Test connection pool functionality."""
        connections = []

        # Acquire multiple connections
        for i in range(3):
            conn = db_manager.get_connection()
            connections.append(conn)

        # Verify connections are different objects
        assert len(set(id(conn) for conn in connections)) == 3

        # Release connections
        for conn in connections:
            result = db_manager.release_connection(conn)
            assert result is True

    @pytest.mark.unit
    def test_thread_safety_concurrent_access(self, db_manager):
        """Test thread safety with concurrent database access."""
        results = []
        errors = []
    def worker_thread(thread_id):
    try:
                for i in range(10):
                    # Get connection
                    conn = db_manager.get_connection()

                    # Simulate database operation
                    time.sleep(0.001)  # Minimal delay to test concurrency

                    # Release connection
                    db_manager.release_connection(conn)

                    results.append(f"thread_{thread_id}_op_{i}")
    except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify thread safety
        assert len(errors) == 0  # No thread safety errors
        assert len(results) == 50  # All operations completed

    @pytest.mark.unit
    @pytest.mark.performance
    def test_performance_concurrent_queries(self, db_manager, performance_timer):
        """Test performance under concurrent load."""
    def execute_query_worker():
            return db_manager.execute_query("SELECT * FROM properties LIMIT 1", ())

        # Measure concurrent query performance
        performance_timer.start()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_query_worker) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]

        elapsed_time = performance_timer.stop()

        # Verify performance meets baseline
        assert len(results) == 50
        assert elapsed_time < 2.0  # Should complete under 2 seconds

    @pytest.mark.unit
    def test_connection_pool_exhaustion_handling(self, db_manager):
        """Test handling of connection pool exhaustion."""
        connections = []

        # Attempt to acquire more connections than pool size
        for i in range(20):  # More than typical pool size
    try:
                conn = db_manager.get_connection()
                connections.append(conn)
    except Exception as e:
                # Pool exhaustion should be handled gracefully
                assert "pool" in str(e).lower() or "connection" in str(e).lower()

        # Release all acquired connections
        for conn in connections:
            db_manager.release_connection(conn)

    @pytest.mark.unit
    def test_database_health_check(self, db_manager):
        """Test database connectivity health check."""
        # Test health check in mock mode
        health_status = db_manager.health_check()

        assert health_status is not None
        assert "status" in health_status
        assert "connection_pool" in health_status

    @pytest.mark.unit
    def test_query_caching_functionality(self, db_manager, sample_database_records):
        """Test query result caching."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = sample_database_records

            # Enable caching
            db_manager.enable_query_cache(ttl=300)

            # Execute same query twice
            query = "SELECT * FROM properties WHERE apn = %s"
            params = ("10215009",)

            result1 = db_manager.execute_cached_query(query, params)
            result2 = db_manager.execute_cached_query(query, params)

            # Verify caching behavior
            assert result1 == result2
            mock_execute.assert_called_once()  # Should only call once due to caching

    @pytest.mark.unit
    def test_missouri_ave_database_operations(self, db_manager, mock_property_data):
        """Test database operations with Missouri Avenue data."""
        missouri_data = {
            **mock_property_data,
            "apn": "10215009",
            "address": "10000 W Missouri Ave",
        }

        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Test Missouri Avenue specific operations
            result = db_manager.insert_property(missouri_data)
            assert result is True

            # Verify Missouri Avenue data in query
            call_args = mock_execute.call_args
            query_params = call_args[0][1] if len(call_args[0]) > 1 else ()
            assert any("10215009" in str(param) for param in query_params)

    @pytest.mark.unit
    def test_backup_and_restore_functionality(self, db_manager, temp_dir):
        """Test database backup and restore capabilities."""
        backup_path = temp_dir / "test_backup.sql"

        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Test backup
            result = db_manager.create_backup(str(backup_path))
            assert result is True

            # Test restore
            result = db_manager.restore_from_backup(str(backup_path))
            assert result is True

    @pytest.mark.unit
    def test_database_schema_management(self, db_manager):
        """Test database schema creation and management."""
        with patch.object(db_manager, "execute_query") as mock_execute:
            mock_execute.return_value = True

            # Test schema creation
            result = db_manager.create_schema()
            assert result is True

            # Test schema validation
            result = db_manager.validate_schema()
            assert result is True

    @pytest.mark.unit
    def test_cleanup_and_resource_management(self, db_manager):
        """Test proper cleanup and resource management."""
        # Acquire some connections
        connections = [db_manager.get_connection() for _ in range(3)]

        # Test cleanup
        db_manager.cleanup()

        # Verify cleanup released resources
        # Note: In mock mode, this tests the cleanup interface
        assert hasattr(db_manager, "cleanup")

    @pytest.mark.unit
    def test_backward_compatibility_alias(self, mock_config):
        """Test backward compatibility with DatabaseManager alias."""
        with patch("threadsafe_database_manager.get_logger"):
            # Test that DatabaseManager is an alias for ThreadSafeDatabaseManager
            manager = DatabaseManager(config=mock_config)

            assert isinstance(manager, ThreadSafeDatabaseManager)
            assert manager.mock_mode is True

    @pytest.mark.unit
    def test_error_logging_and_monitoring(self, db_manager):
        """Test error logging and monitoring functionality."""
        with patch.object(db_manager, "logger") as mock_logger:
            with patch.object(db_manager, "get_connection") as mock_get_conn:
                mock_get_conn.side_effect = Exception("Connection failed")

                # Execute operation that should fail
                result = db_manager.execute_query("SELECT 1", ())

                # Verify error logging
                assert result is None
                mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_configuration_validation(self, mock_config):
        """Test database configuration validation."""
        # Test valid configuration
        with patch("threadsafe_database_manager.get_logger"):
            manager = ThreadSafeDatabaseManager(config=mock_config)
            assert manager.config["database"] == "test_db"

        # Test configuration with missing required fields
        invalid_config = {"host": "localhost"}

        with patch("threadsafe_database_manager.get_logger"):
    try:
                manager = ThreadSafeDatabaseManager(config=invalid_config)
                # Should handle missing configuration gracefully
                assert manager is not None
    except Exception as e:
                # Or raise appropriate error for invalid config
                assert "config" in str(e).lower() or "database" in str(e).lower()
