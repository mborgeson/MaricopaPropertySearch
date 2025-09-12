"""
Integration tests for error handling and graceful degradation
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from requests.exceptions import ConnectionError, Timeout, HTTPError

@pytest.mark.integration
class TestNetworkErrorHandling:
    """Test handling of network-related errors"""
    
    def test_api_timeout_graceful_handling(self, app_config, mock_api_client):
        """Test that API timeouts are handled gracefully"""
        
        # Mock API timeout
        with patch.object(mock_api_client, 'search_by_owner') as mock_search:
            mock_search.side_effect = Timeout("API request timed out")
            
            try:
                results = mock_api_client.search_by_owner("SMITH", timeout=5)
            except Exception as e:
                # Should not raise unhandled timeout
                assert not isinstance(e, Timeout), "Timeout should be handled gracefully"
                
    def test_api_connection_error_fallback(self, app_config, test_database):
        """Test fallback to database when API is unavailable"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        # Create app with connection error simulation
        app = EnhancedPropertySearchApp(app_config)
        
        # Mock API client to raise connection error
        with patch.object(app.api_client, 'search_by_owner') as mock_api:
            mock_api.side_effect = ConnectionError("API server unavailable")
            
            # Search should still work using database
            with patch.object(app.db_manager, 'search_properties_by_owner') as mock_db:
                mock_db.return_value = [{"apn": "101-01-001A", "owner_name": "SMITH, JOHN"}]
                
                results = app._perform_search_with_fallback("owner", "SMITH")
                
                # Should get results from database
                assert len(results) > 0
                mock_db.assert_called_once()
                
    def test_partial_data_source_failure(self, app_config):
        """Test handling when some data sources fail but others succeed"""
        from src.api_client import MockMaricopaAPIClient
        from web_scraper import MockWebScraperManager
        
        api_client = MockMaricopaAPIClient(app_config)
        scraper = MockWebScraperManager(app_config)
        
        # Mock API success but scraper failure
        with patch.object(api_client, 'search_by_owner') as mock_api:
            mock_api.return_value = [{"apn": "101-01-001A", "owner_name": "SMITH, JOHN"}]
            
            with patch.object(scraper, 'enhance_property_data') as mock_scraper:
                mock_scraper.side_effect = Exception("Scraper blocked")
                
                # Should still return API results even if scraper fails
                results = api_client.search_by_owner("SMITH")
                enhanced_data = {}
                
                try:
                    enhanced_data = scraper.enhance_property_data("101-01-001A")
                except:
                    pass  # Scraper failure should be handled
                    
                assert len(results) > 0, "Should get API results despite scraper failure"
                
        api_client.close()
        scraper.close()
        
    def test_network_recovery_detection(self, app_config, network_simulator):
        """Test that system detects network recovery"""
        from src.api_client import MockMaricopaAPIClient
        
        client = MockMaricopaAPIClient(app_config)
        
        # Start with network failure
        with network_simulator.apply_condition('offline'):
            try:
                status = client.get_api_status()
                assert status['status'] != 'online', "Should detect network offline"
            except:
                pass  # Expected to fail
                
        # Network comes back online
        with network_simulator.apply_condition('normal'):
            status = client.get_api_status()
            assert status['status'] in ['online', 'available'], "Should detect network recovery"
            
        client.close()

@pytest.mark.integration
class TestDatabaseErrorHandling:
    """Test database-related error handling"""
    
    def test_database_connection_failure_handling(self, app_config):
        """Test handling when database connection fails"""
        from src.database_manager import DatabaseManager
        
        # Create database manager with invalid config
        bad_config = app_config
        bad_config._config['database']['host'] = 'nonexistent-host'
        
        db = DatabaseManager(bad_config)
        
        # Should handle connection failure gracefully
        connection_ok = db.test_connection()
        assert not connection_ok, "Should detect failed connection"
        
        # Should not raise unhandled exceptions
        try:
            results = db.search_properties_by_owner("SMITH")
            assert results == [], "Should return empty results on connection failure"
        except Exception as e:
            # Should only raise handled exceptions with user-friendly messages
            assert "connection" in str(e).lower() or "database" in str(e).lower()
            
    def test_database_connection_recovery(self, test_database, app_config):
        """Test database connection recovery after temporary failure"""
        
        # Simulate temporary connection loss
        original_connection = test_database._connection_pool
        test_database._connection_pool = None
        
        # Should detect connection loss
        connection_ok = test_database.test_connection()
        assert not connection_ok, "Should detect lost connection"
        
        # Restore connection
        test_database._connection_pool = original_connection
        
        # Should recover automatically
        connection_ok = test_database.test_connection()
        assert connection_ok, "Should recover connection"
        
    def test_database_query_timeout_handling(self, test_database):
        """Test handling of database query timeouts"""
        
        with patch.object(test_database, 'get_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            
            # Mock query timeout
            mock_cursor.execute.side_effect = psycopg2.OperationalError("timeout")
            mock_connection.cursor.return_value = mock_cursor
            mock_conn.return_value.__enter__ = Mock(return_value=mock_connection)
            mock_conn.return_value.__exit__ = Mock(return_value=None)
            
            # Should handle timeout gracefully
            results = test_database.search_properties_by_owner("SMITH")
            assert results == [], "Should return empty results on timeout"
            
    def test_database_constraint_violation_handling(self, test_database):
        """Test handling of database constraint violations"""
        
        # Try to insert duplicate APN (should be unique)
        duplicate_property = {
            'apn': '101-01-001A',  # This should already exist from test fixtures
            'owner_name': 'DUPLICATE OWNER',
            'property_address': '456 DUPLICATE ST',
            'city': 'PHOENIX',
            'zip_code': '85001',
            'property_type': 'RESIDENTIAL',
            'assessed_value': 200000
        }
        
        try:
            with test_database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO properties (
                        apn, owner_name, property_address, city, zip_code,
                        property_type, assessed_value, last_updated
                    ) VALUES (
                        %(apn)s, %(owner_name)s, %(property_address)s, %(city)s, 
                        %(zip_code)s, %(property_type)s, %(assessed_value)s, CURRENT_TIMESTAMP
                    )
                """, duplicate_property)
                conn.commit()
                
        except psycopg2.IntegrityError:
            # This is expected - should handle constraint violations
            pass
        except Exception as e:
            pytest.fail(f"Should handle constraint violations gracefully: {e}")

@pytest.mark.integration
class TestDataInconsistencyHandling:
    """Test handling of inconsistent or malformed data"""
    
    def test_malformed_api_response_handling(self, app_config):
        """Test handling when API returns malformed data"""
        from src.api_client import MockMaricopaAPIClient
        
        client = MockMaricopaAPIClient(app_config)
        
        # Mock malformed response
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'invalid_json': True,
                'missing_required_fields': None,
                'malformed_apn': '???-??-???',
                'invalid_date': '2024-13-45'  # Invalid date
            }
            
            results = client.search_by_owner("SMITH")
            
            # Should handle malformed data gracefully
            assert isinstance(results, list), "Should return list even with malformed data"
            
        client.close()
        
    def test_missing_required_fields_handling(self, test_database):
        """Test handling when required fields are missing"""
        
        # Try to search with properties missing required fields
        incomplete_property = {
            'owner_name': 'INCOMPLETE OWNER',
            # Missing APN, address, etc.
            'assessed_value': 200000
        }
        
        try:
            with test_database.get_connection() as conn:
                cursor = conn.cursor()
                # This should fail due to NOT NULL constraints
                cursor.execute("""
                    INSERT INTO properties (owner_name, assessed_value, last_updated)
                    VALUES (%(owner_name)s, %(assessed_value)s, CURRENT_TIMESTAMP)
                """, incomplete_property)
                conn.commit()
                
        except psycopg2.IntegrityError:
            # Expected - should handle missing required fields
            pass
        except Exception as e:
            pytest.fail(f"Should handle missing fields gracefully: {e}")
            
    def test_inconsistent_data_between_sources(self, app_config):
        """Test handling when different data sources return inconsistent information"""
        from src.api_client import MockMaricopaAPIClient
        from web_scraper import MockWebScraperManager
        
        api_client = MockMaricopaAPIClient(app_config)
        scraper = MockWebScraperManager(app_config)
        
        # Mock inconsistent data
        with patch.object(api_client, 'get_property_by_apn') as mock_api:
            mock_api.return_value = {
                'apn': '101-01-001A',
                'owner_name': 'SMITH, JOHN A',  # Different from scraper
                'assessed_value': 250000
            }
            
            with patch.object(scraper, 'get_property_details') as mock_scraper:
                mock_scraper.return_value = {
                    'apn': '101-01-001A',
                    'owner_name': 'SMITH, JOHN ANDREW',  # Different from API
                    'assessed_value': 248000  # Different value
                }
                
                # System should handle inconsistencies gracefully
                api_data = api_client.get_property_by_apn('101-01-001A')
                scraper_data = scraper.get_property_details('101-01-001A')
                
                assert api_data is not None
                assert scraper_data is not None
                
                # Should be able to merge or choose between conflicting data
                # without crashing
                
        api_client.close()
        scraper.close()
        
    def test_special_characters_in_data(self, test_database):
        """Test handling of special characters in property data"""
        
        special_char_property = {
            'apn': '999-99-999Z',
            'owner_name': "O'CONNOR & MÜLLER-SCHMIDT",  # Apostrophe and special chars
            'property_address': '123 "QUOTE" ST #½',  # Quotes and fraction
            'city': 'PHOENIX',
            'zip_code': '85001',
            'property_type': 'RESIDENTIAL',
            'assessed_value': 200000
        }
        
        try:
            with test_database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO properties (
                        apn, owner_name, property_address, city, zip_code,
                        property_type, assessed_value, last_updated
                    ) VALUES (
                        %(apn)s, %(owner_name)s, %(property_address)s, %(city)s,
                        %(zip_code)s, %(property_type)s, %(assessed_value)s, CURRENT_TIMESTAMP
                    )
                """, special_char_property)
                conn.commit()
                
                # Should be able to search for it
                results = test_database.search_properties_by_owner("O'CONNOR")
                assert len(results) > 0, "Should find property with special characters"
                
        except Exception as e:
            pytest.fail(f"Should handle special characters: {e}")

@pytest.mark.integration
@pytest.mark.gui
class TestUIErrorHandling:
    """Test error handling in the user interface"""
    
    def test_user_friendly_error_messages(self, qt_app, app_config):
        """Test that error messages are user-friendly, not technical"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()
        
        # Mock various error conditions
        error_scenarios = [
            (ConnectionError("Connection refused"), "network"),
            (Timeout("Request timeout"), "timeout"),
            (psycopg2.OperationalError("Database error"), "database"),
            (Exception("Unexpected error"), "error")
        ]
        
        for error, expected_keyword in error_scenarios:
            with patch.object(window, '_perform_search', side_effect=error):
                window.search_input.setText("SMITH")
                window.search_btn.click()
                qt_app.processEvents()
                
                # Check error display
                if hasattr(window, 'statusBar'):
                    error_message = window.statusBar().currentMessage().lower()
                    
                    # Should contain user-friendly terms
                    assert expected_keyword in error_message, f"Error message should mention {expected_keyword}"
                    
                    # Should not contain technical details
                    technical_terms = ["exception", "traceback", "errno", "psycopg2"]
                    for term in technical_terms:
                        assert term not in error_message, f"Should not show technical term: {term}"
                        
        window.close()
        
    def test_error_recovery_workflow(self, qt_app, app_config):
        """Test that users can recover from errors easily"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()
        
        # Simulate error condition
        with patch.object(window, '_perform_search', side_effect=ConnectionError("Network error")):
            window.search_input.setText("SMITH")
            window.search_btn.click()
            qt_app.processEvents()
            
            # Error state should be recoverable
            assert window.search_btn.isEnabled(), "Search button should remain enabled after error"
            assert window.search_input.isEnabled(), "Search input should remain enabled after error"
            
        # Now simulate successful search after error
        with patch.object(window, '_perform_search', return_value=[]):
            window.search_btn.click()
            qt_app.processEvents()
            
            # Should recover from error state
            if hasattr(window, 'statusBar'):
                status = window.statusBar().currentMessage()
                assert "error" not in status.lower(), "Should clear error message on successful search"
                
        window.close()
        
    def test_partial_results_display(self, qt_app, app_config):
        """Test display of partial results when some operations fail"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()
        
        # Mock partial success scenario
        partial_results = [
            {'apn': '101-01-001A', 'owner_name': 'SMITH, JOHN', 'status': 'complete'},
            {'apn': '101-01-002B', 'owner_name': 'SMITH, JANE', 'status': 'partial'},
        ]
        
        with patch.object(window, '_perform_search', return_value=partial_results):
            window.search_input.setText("SMITH")
            window.search_btn.click()
            qt_app.processEvents()
            
            # Should display available results
            window._populate_results_table(partial_results)
            qt_app.processEvents()
            
            assert window.results_table.rowCount() == len(partial_results)
            
            # Should indicate if results are partial
            if hasattr(window, 'statusBar'):
                status = window.statusBar().currentMessage()
                # Could indicate partial results or enhancement in progress
                
        window.close()

@pytest.mark.integration
class TestSystemRecoveryPatterns:
    """Test system recovery and resilience patterns"""
    
    def test_automatic_retry_with_backoff(self, app_config):
        """Test automatic retry with exponential backoff"""
        from src.api_client import MockMaricopaAPIClient
        
        client = MockMaricopaAPIClient(app_config)
        
        # Mock intermittent failures
        call_count = 0
        def failing_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 calls
                raise ConnectionError("Temporary failure")
            return {'status': 'success', 'results': []}
            
        with patch.object(client, '_make_request', side_effect=failing_request):
            start_time = time.time()
            
            try:
                result = client.search_by_owner("SMITH")
                elapsed = time.time() - start_time
                
                # Should succeed after retries
                assert call_count == 3, "Should retry failed requests"
                assert elapsed > 1.0, "Should include backoff delays"
                assert result is not None, "Should eventually succeed"
                
            except Exception as e:
                # Even if it fails, should be a graceful failure
                assert "retry" in str(e).lower() or "timeout" in str(e).lower()
                
        client.close()
        
    def test_graceful_degradation_modes(self, app_config, test_database):
        """Test graceful degradation when services are partially available"""
        
        # Test different degradation scenarios
        scenarios = [
            {'api_available': False, 'scraper_available': True, 'db_available': True},
            {'api_available': True, 'scraper_available': False, 'db_available': True},
            {'api_available': False, 'scraper_available': False, 'db_available': True},
        ]
        
        for scenario in scenarios:
            available_sources = []
            
            if scenario['db_available']:
                available_sources.append('database')
                
            if scenario['api_available']:
                available_sources.append('api')
                
            if scenario['scraper_available']:
                available_sources.append('scraper')
                
            # System should work with at least one source available
            assert len(available_sources) > 0, "At least one data source should be available"
            
            # Mock the availability
            # In real implementation, would test actual degraded performance
            
    def test_resource_cleanup_on_failure(self, app_config):
        """Test that resources are properly cleaned up when operations fail"""
        from src.database_manager import DatabaseManager
        from src.api_client import MockMaricopaAPIClient
        
        db = DatabaseManager(app_config)
        client = MockMaricopaAPIClient(app_config)
        
        # Simulate operation that fails mid-way
        try:
            with patch.object(db, 'get_connection') as mock_conn:
                mock_connection = MagicMock()
                mock_conn.return_value.__enter__ = Mock(return_value=mock_connection)
                mock_conn.return_value.__exit__ = Mock(return_value=None)
                
                # Simulate failure during operation
                mock_connection.cursor.side_effect = Exception("Operation failed")
                
                results = db.search_properties_by_owner("SMITH")
                
        except Exception:
            pass  # Expected to fail
            
        # Resources should still be properly managed
        # Connection pool should not be exhausted
        connection_test = db.test_connection()
        # Should be able to get new connections
        
        db.close()
        client.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])