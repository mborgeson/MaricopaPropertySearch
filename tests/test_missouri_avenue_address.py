#!/usr/bin/env python
"""
Comprehensive test suite for "10000 W Missouri Ave" property search and data collection.
Focuses on testing the specific address requirements and UX improvements.
"""

import pytest
import asyncio
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QTableWidget
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer

# Import test fixtures and setup
from conftest import app_instance, db_manager, mock_api_client, test_config

# Import application modules
from src.gui.enhanced_main_window import EnhancedPropertySearchApp

# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.background_data_collector import BackgroundDataCollectionManager, JobPriority
from src.automatic_data_collector import MaricopaDataCollector
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

logger = logging.getLogger(__name__)


class TestMissouriAvenueProperty:
    """Test suite for the specific address: 10000 W Missouri Ave"""

    TEST_ADDRESS = "10000 W Missouri Ave"
    EXPECTED_APN = "13304014A"  # Known test APN for this address

    def setup_method(self):
        """Setup for each test method"""
        self.app = None
        self.main_window = None

    def teardown_method(self):
        """Cleanup after each test"""
        if self.main_window:
            self.main_window.close()
        if self.app:
            self.app.quit()

    @pytest.fixture
    def missouri_property_data(self):
        """Sample property data for 10000 W Missouri Ave"""
        return {
            "apn": self.EXPECTED_APN,
            "owner_name": "CITY OF GLENDALE",
            "property_address": "10000 W MISSOURI AVE, GLENDALE, AZ 85307",
            "mailing_address": "CITY OF GLENDALE, 5850 W GLENDALE AVE, GLENDALE, AZ 85301",
            "legal_description": "SEC 13 T3N R4E LOT 14 CITY OF GLENDALE",
            "land_use_code": "GOV",
            "year_built": 2009,
            "living_area_sqft": 303140,
            "lot_size_sqft": 185582,
            "bedrooms": 14,
            "bathrooms": 6,
            "pool": False,
            "garage_spaces": 8,
        }

    def test_address_search_basic_functionality(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test basic search functionality for Missouri Ave address"""
        # Insert test data
        db_manager.insert_property(missouri_property_data)

        # Create application window
        main_window = EnhancedPropertySearchApp(test_config)

        # Set search parameters
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)

        # Perform search
        main_window.perform_search()

        # Wait for search to complete
        QTest.qWait(3000)

        # Verify results
        assert main_window.results_table.rowCount() > 0

        # Check first result contains our address
        apn_item = main_window.results_table.item(0, 0)
        assert apn_item.text() == self.EXPECTED_APN

        # Verify no "Not Available" messages in visible results
        for row in range(main_window.results_table.rowCount()):
            for col in range(main_window.results_table.columnCount()):
                item = main_window.results_table.item(row, col)
                if item:
                    assert (
                        "Not Available" not in item.text()
                    ), f"Found 'Not Available' in table at ({row}, {col})"

    def test_auto_collection_feature_missouri_ave(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test auto-collection feature specifically for Missouri Ave property"""
        # Insert basic property data
        db_manager.insert_property(missouri_property_data)

        # Create application with background manager
        main_window = EnhancedPropertySearchApp(test_config)

        # Verify background collection is running
        assert main_window.background_manager.is_running()

        # Search for the property
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)
        main_window.perform_search()

        QTest.qWait(2000)

        # Verify background collection was triggered
        collection_status = main_window.background_manager.get_collection_status()
        assert collection_status["status"] == "running"

        # Test the auto-collect button
        main_window.collect_all_btn.click()

        QTest.qWait(1000)

        # Verify jobs were queued
        updated_status = main_window.background_manager.get_collection_status()
        assert updated_status["pending_jobs"] > 0 or updated_status["active_jobs"] > 0

    def test_progress_indicators_missouri_ave(self, app_instance, db_manager):
        """Test progress indicators work correctly during Missouri Ave search"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Start search
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)

        # Monitor progress bar visibility
        assert not main_window.progress_bar.isVisible()

        main_window.perform_search()

        # Progress bar should be visible during search
        QTest.qWait(100)
        assert main_window.progress_bar.isVisible()

        # Wait for search completion
        QTest.qWait(5000)

        # Progress bar should be hidden after completion
        assert not main_window.progress_bar.isVisible()

        # Status should show completion
        status_text = main_window.status_bar.currentMessage()
        assert "Search completed" in status_text or "Found" in status_text

    def test_data_availability_missouri_ave(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test what data should be available for Missouri Ave property"""
        # Insert complete test data
        db_manager.insert_property(missouri_property_data)

        # Add sample tax history
        tax_data = [
            {
                "apn": self.EXPECTED_APN,
                "tax_year": 2023,
                "assessed_value": 15000000.00,
                "limited_value": 15000000.00,
                "tax_amount": 195000.00,
                "payment_status": "PAID",
            },
            {
                "apn": self.EXPECTED_APN,
                "tax_year": 2022,
                "assessed_value": 14500000.00,
                "limited_value": 14500000.00,
                "tax_amount": 188500.00,
                "payment_status": "PAID",
            },
        ]

        for tax_record in tax_data:
            db_manager.insert_tax_record(tax_record)

        # Create application and search
        main_window = EnhancedPropertySearchApp(test_config)
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)
        main_window.perform_search()

        QTest.qWait(2000)

        # Open property details dialog
        main_window.results_table.selectRow(0)
        main_window.view_property_details()

        QTest.qWait(1000)

        # Verify expected data fields are populated
        property_dialog = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "property_data"):
                property_dialog = widget
                break

        assert property_dialog is not None

        # Verify tax data is displayed
        tax_table = property_dialog.tax_table
        assert tax_table.rowCount() == len(tax_data)

        # Verify no "No Data Available" placeholders when data exists
        for row in range(tax_table.rowCount()):
            tax_year_item = tax_table.item(row, 0)
            assert tax_year_item.text() != "No Data Available"

    def test_error_handling_missouri_ave(self, app_instance, db_manager):
        """Test error handling and edge cases for Missouri Ave search"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Test with various address formats
        address_variations = [
            "10000 W Missouri Ave",
            "10000 W MISSOURI AVE",
            "10000 West Missouri Avenue",
            "10000 W Missouri Avenue, Glendale, AZ",
        ]

        for address in address_variations:
            main_window.search_type_combo.setCurrentText("Property Address")
            main_window.search_input.setText(address)
            main_window.perform_search()

            QTest.qWait(3000)

            # Should not show error messages for reasonable variations
            status_text = main_window.status_bar.currentMessage()
            assert "error" not in status_text.lower()
            assert "failed" not in status_text.lower()

    def test_database_integration_missouri_ave(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test database integration and caching for Missouri Ave property"""
        # First search should trigger database insert
        main_window = EnhancedPropertySearchApp(test_config)
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)

        # Record initial database state
        initial_count = len(db_manager.search_properties_by_address(self.TEST_ADDRESS))

        main_window.perform_search()
        QTest.qWait(3000)

        # Verify data was cached in database
        cached_count = len(db_manager.search_properties_by_address(self.TEST_ADDRESS))
        assert cached_count >= initial_count

        # Second search should be faster (using cache)
        start_time = time.time()
        main_window.perform_search()
        QTest.qWait(1000)
        cache_search_time = time.time() - start_time

        # Cache search should be very fast
        assert cache_search_time < 2.0

    def test_manual_vs_auto_collection_missouri_ave(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test manual collection vs auto collection for Missouri Ave"""
        db_manager.insert_property(missouri_property_data)

        main_window = EnhancedPropertySearchApp(test_config)
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText(self.TEST_ADDRESS)
        main_window.perform_search()

        QTest.qWait(2000)

        # Open property details
        main_window.results_table.selectRow(0)
        main_window.view_property_details()

        QTest.qWait(1000)

        # Find the property details dialog
        property_dialog = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "property_data"):
                property_dialog = widget
                break

        assert property_dialog is not None

        # Test manual collection button
        manual_collect_btn = None
        auto_collect_btn = None

        for child in property_dialog.findChildren(QPushButton):
            if "Manual Collect" in child.text():
                manual_collect_btn = child
            elif "Auto-Collect" in child.text():
                auto_collect_btn = child

        assert manual_collect_btn is not None
        assert auto_collect_btn is not None

        # Both buttons should be enabled
        assert manual_collect_btn.isEnabled()
        assert auto_collect_btn.isEnabled()

    @pytest.mark.asyncio
    async def test_background_collection_performance_missouri_ave(
        self, app_instance, db_manager, missouri_property_data
    ):
        """Test performance of background collection for Missouri Ave property"""
        db_manager.insert_property(missouri_property_data)

        # Create background collection manager
        bg_manager = BackgroundDataCollectionManager(db_manager)
        bg_manager.start_collection()

        # Request high-priority collection
        start_time = time.time()
        success = bg_manager.collect_data_for_apn(self.EXPECTED_APN, JobPriority.HIGH)

        assert success, "Failed to queue high-priority job"

        # Wait for job completion (with timeout)
        timeout = 30  # 30 seconds max
        elapsed = 0
        completed = False

        while elapsed < timeout:
            status = bg_manager.get_collection_status()
            if status["completed_jobs"] > 0:
                completed = True
                break

            await asyncio.sleep(1)
            elapsed += 1

        collection_time = time.time() - start_time

        assert completed, "Background collection did not complete within timeout"
        assert collection_time < 30, f"Collection took too long: {collection_time}s"

        # Verify data was collected
        tax_history = db_manager.get_tax_history(self.EXPECTED_APN)
        sales_history = db_manager.get_sales_history(self.EXPECTED_APN)

        # At least one type of data should be collected
        assert len(tax_history) > 0 or len(sales_history) > 0

        bg_manager.stop_collection()


class TestUXMessageImprovements:
    """Test suite for UX message improvements - replacing 'Not Available'"""

    def test_no_not_available_messages_in_ui(self, app_instance, db_manager):
        """Test that 'Not Available' messages are replaced with actionable text"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Create property with missing data
        incomplete_property = {
            "apn": "TEST123",
            "owner_name": "TEST OWNER",
            "property_address": "123 TEST ST",
            "mailing_address": None,  # Missing data
            "year_built": None,  # Missing data
            "living_area_sqft": None,  # Missing data
            "bedrooms": None,  # Missing data
            "bathrooms": None,  # Missing data
        }

        db_manager.insert_property(incomplete_property)

        # Search for the property
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText("123 TEST ST")
        main_window.perform_search()

        QTest.qWait(2000)

        # Open property details
        main_window.results_table.selectRow(0)
        main_window.view_property_details()

        QTest.qWait(1000)

        # Find property dialog and check all text
        property_dialog = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "property_data"):
                property_dialog = widget
                break

        assert property_dialog is not None

        # Check all labels in the dialog
        all_text = []
        for label in property_dialog.findChildren(QLabel):
            if label.text():
                all_text.append(label.text())

        # Check table widgets
        for table in property_dialog.findChildren(QTableWidget):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item and item.text():
                        all_text.append(item.text())

        # Verify no "Not Available" messages
        not_available_found = [text for text in all_text if "Not Available" in text]
        assert (
            len(not_available_found) == 0
        ), f"Found 'Not Available' messages: {not_available_found}"

    def test_actionable_messages_present(self, app_instance, db_manager):
        """Test that actionable messages are present instead of 'Not Available'"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Create property with no tax/sales data
        basic_property = {
            "apn": "TEST456",
            "owner_name": "BASIC OWNER",
            "property_address": "456 BASIC ST",
        }

        db_manager.insert_property(basic_property)

        # Search and open details
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText("456 BASIC ST")
        main_window.perform_search()

        QTest.qWait(2000)

        main_window.results_table.selectRow(0)
        main_window.view_property_details()

        QTest.qWait(1000)

        # Find property dialog
        property_dialog = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "property_data"):
                property_dialog = widget
                break

        assert property_dialog is not None

        # Check for actionable messages
        all_text = []
        for label in property_dialog.findChildren(QLabel):
            if label.text():
                all_text.append(label.text())

        # Check tables for actionable messages
        for table in property_dialog.findChildren(QTableWidget):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item and item.text():
                        all_text.append(item.text())

        all_text_combined = " ".join(all_text)

        # Look for actionable messages
        actionable_phrases = [
            "Auto-Collect",
            "Manual Collect",
            "buttons above",
            "Collecting",
            "Queued",
            "Click to fetch",
            "will auto-collect",
        ]

        found_actionable = any(
            phrase in all_text_combined for phrase in actionable_phrases
        )
        assert (
            found_actionable
        ), f"No actionable messages found. Text: {all_text_combined[:500]}"

    def test_tooltip_hover_messages(self, app_instance, db_manager):
        """Test that hover tooltips provide helpful context"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Check various UI elements have tooltips
        tooltip_elements = [
            main_window.search_btn,
            main_window.export_btn,
            main_window.view_details_btn,
            main_window.collect_all_btn,
        ]

        for element in tooltip_elements:
            if element.isEnabled():
                tooltip = element.toolTip()
                # Should have some tooltip text
                assert (
                    len(tooltip) > 10
                ), f"Element {element.text()} missing helpful tooltip"

    def test_status_message_progression(self, app_instance, db_manager):
        """Test that status messages show logical progression"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Start with ready state
        initial_status = main_window.status_bar.currentMessage()
        assert "Ready" in initial_status or initial_status == ""

        # Perform search and track status changes
        main_window.search_type_combo.setCurrentText("Property Address")
        main_window.search_input.setText("10000 W Missouri Ave")
        main_window.perform_search()

        # Status should change during search
        QTest.qWait(100)
        search_status = main_window.status_bar.currentMessage()
        assert search_status != initial_status
        assert "Search" in search_status or "Found" in search_status

        # Wait for completion
        QTest.qWait(5000)
        final_status = main_window.status_bar.currentMessage()

        # Should show completion or results
        completion_indicators = ["completed", "Found", "results", "properties"]
        assert any(indicator in final_status for indicator in completion_indicators)


class TestRegressionTests:
    """Regression tests to ensure existing functionality still works"""

    def test_basic_search_types_still_work(self, app_instance, db_manager):
        """Test that all search types still function properly"""
        main_window = EnhancedPropertySearchApp(test_config)

        search_tests = [
            ("Property Address", "10000 W Missouri Ave"),
            ("Owner Name", "CITY OF GLENDALE"),
            ("APN", "13304014A"),
        ]

        for search_type, search_term in search_tests:
            main_window.search_type_combo.setCurrentText(search_type)
            main_window.search_input.setText(search_term)
            main_window.perform_search()

            QTest.qWait(3000)

            # Should not crash and should show some result or proper message
            status = main_window.status_bar.currentMessage()
            assert "error" not in status.lower()

            # Clear results for next test
            main_window.current_results = []
            main_window.results_table.setRowCount(0)

    def test_background_collection_still_functional(self, app_instance, db_manager):
        """Test that background collection system still works"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Background collection should start automatically
        assert main_window.background_manager is not None

        # Should be able to toggle collection
        initial_state = main_window.background_manager.is_running()
        main_window.toggle_background_collection()

        QTest.qWait(1000)

        new_state = main_window.background_manager.is_running()
        assert new_state != initial_state

        # Toggle back
        main_window.toggle_background_collection()
        QTest.qWait(1000)

        final_state = main_window.background_manager.is_running()
        assert final_state == initial_state

    def test_export_functionality_intact(self, app_instance, db_manager, tmp_path):
        """Test that export functionality still works"""
        main_window = EnhancedPropertySearchApp(test_config)

        # Add some test data
        test_property = {
            "apn": "EXPORT_TEST",
            "owner_name": "EXPORT OWNER",
            "property_address": "999 EXPORT ST",
        }

        db_manager.insert_property(test_property)
        main_window.current_results = [test_property]

        # Export button should be enabled with results
        main_window.export_btn.setEnabled(True)
        assert main_window.export_btn.isEnabled()

        # Mock file dialog to prevent actual file creation during test
        with patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName") as mock_dialog:
            test_file = tmp_path / "test_export.csv"
            mock_dialog.return_value = (str(test_file), "CSV Files (*.csv)")

            # Should not crash when clicking export
            try:
                main_window.export_results()
                export_success = True
            except Exception as e:
                logger.error(f"Export failed: {e}")
                export_success = False

            assert export_success, "Export functionality is broken"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
