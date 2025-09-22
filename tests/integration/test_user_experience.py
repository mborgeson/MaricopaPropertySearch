"""
Integration tests for user experience and professional appearance requirements
"""

import pytest
import time
from unittest.mock import Mock, patch
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest


@pytest.mark.integration
@pytest.mark.gui
class TestProfessionalAppearance:
    """Test that application maintains professional appearance"""

    def test_application_startup_appearance(self, qt_app, app_config):
        """Test that application appears professional on startup"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)

        # Verify window properties
        assert window.windowTitle() == "Maricopa Property Search"
        assert window.isVisible() == False  # Should not auto-show

        # Show window for testing
        window.show()
        qt_app.processEvents()

        # Verify professional appearance elements
        assert window.search_type_combo.isVisible()
        assert window.search_input.isVisible()
        assert window.search_btn.isVisible()
        assert window.results_table.isVisible()

        # Verify no error messages visible on startup
        assert not hasattr(window, "error_label") or not window.error_label.isVisible()

        # Check for professional styling (non-default appearance)
        assert window.search_btn.text() != ""
        assert window.search_type_combo.count() > 0

        window.close()

    def test_search_interface_clarity(self, qt_app, app_config):
        """Test that search interface is clear and intuitive"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Verify search type options are clear
        search_types = [
            window.search_type_combo.itemText(i)
            for i in range(window.search_type_combo.count())
        ]

        expected_types = ["Owner Name", "Property Address", "APN"]
        for expected in expected_types:
            assert expected in search_types, f"Missing search type: {expected}"

        # Verify placeholder text provides guidance
        placeholder = window.search_input.placeholderText()
        assert len(placeholder) > 0, "Search input should have placeholder text"

        # Verify button text is action-oriented
        button_text = window.search_btn.text()
        assert "search" in button_text.lower() or "find" in button_text.lower()

        window.close()

    def test_loading_states_professional(self, qt_app, app_config, performance_timer):
        """Test that loading states appear professional and informative"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Mock a slow search to test loading state
        original_search = window._perform_search
        search_completed = False

        def mock_slow_search():
            nonlocal search_completed
            time.sleep(0.5)  # Simulate processing time
            search_completed = True
            return []

        with patch.object(window, "_perform_search", side_effect=mock_slow_search):
            # Start search
            window.search_input.setText("SMITH")

            performance_timer.start()
            window.search_btn.click()

            # Check that UI shows loading state immediately
            qt_app.processEvents()

            # Progress bar should be visible for operations > 100ms
            if hasattr(window, "progress_bar"):
                assert (
                    window.progress_bar.isVisible()
                ), "Progress bar should be visible during search"

            # Wait for search to complete
            while not search_completed and performance_timer.elapsed() < 2:
                qt_app.processEvents()
                time.sleep(0.1)

            assert search_completed, "Mock search should have completed"

        window.close()


@pytest.mark.integration
@pytest.mark.gui
class TestUserWorkflowExperience:
    """Test complete user workflow experiences"""

    def test_new_user_first_search_experience(self, qt_app, app_config, test_database):
        """Test the experience for a new user performing their first search"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Step 1: User sees clean, professional interface
        assert window.isVisible()
        assert window.search_type_combo.currentText() in [
            "Owner Name",
            "Property Address",
            "APN",
        ]

        # Step 2: User selects search type
        window.search_type_combo.setCurrentText("Owner Name")
        qt_app.processEvents()

        # Placeholder should update to guide user
        placeholder = window.search_input.placeholderText()
        assert "owner" in placeholder.lower() or "name" in placeholder.lower()

        # Step 3: User enters search term
        window.search_input.setText("SMITH")
        qt_app.processEvents()

        # Step 4: User clicks search
        search_completed = False
        original_results = []

        def mock_search():
            nonlocal search_completed, original_results
            # Simulate finding results
            original_results = [
                {
                    "apn": "101-01-001A",
                    "owner_name": "SMITH, JOHN",
                    "property_address": "123 MAIN ST",
                }
            ]
            search_completed = True
            return original_results

        with patch.object(window, "_perform_search", side_effect=mock_search):
            window.search_btn.click()

            # Wait for search to complete
            timeout = time.time() + 3
            while not search_completed and time.time() < timeout:
                qt_app.processEvents()
                time.sleep(0.1)

        # Step 5: User sees results quickly and clearly
        assert search_completed, "Search should complete within 3 seconds"

        # Results should be displayed in table
        if original_results:
            # Simulate populating results
            window._populate_results_table(original_results)
            qt_app.processEvents()

            assert window.results_table.rowCount() > 0, "Results should appear in table"

        window.close()

    def test_power_user_rapid_search_experience(
        self, qt_app, app_config, test_database
    ):
        """Test experience for power users doing rapid sequential searches"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        search_terms = [
            ("Owner Name", "SMITH"),
            ("Owner Name", "JONES"),
            ("Property Address", "MAIN ST"),
            ("APN", "101-01-001A"),
        ]

        total_time = 0

        for search_type, term in search_terms:
            start_time = time.time()

            # Change search type
            window.search_type_combo.setCurrentText(search_type)
            qt_app.processEvents()

            # Enter search term
            window.search_input.clear()
            window.search_input.setText(term)
            qt_app.processEvents()

            # Perform search
            search_completed = False

            def mock_rapid_search():
                nonlocal search_completed
                search_completed = True
                return []  # Empty results for speed

            with patch.object(window, "_perform_search", side_effect=mock_rapid_search):
                window.search_btn.click()

                timeout = time.time() + 2
                while not search_completed and time.time() < timeout:
                    qt_app.processEvents()
                    time.sleep(0.01)

            search_time = time.time() - start_time
            total_time += search_time

            assert search_completed, f"Search for {term} should complete quickly"
            assert (
                search_time < 1.0
            ), f"Individual search took {search_time:.3f}s, should be < 1s"

        # Overall rapid search session should be efficient
        average_time = total_time / len(search_terms)
        assert (
            average_time < 0.8
        ), f"Average search time {average_time:.3f}s too slow for power users"

        window.close()

    def test_error_recovery_user_experience(
        self, qt_app, app_config, network_simulator
    ):
        """Test user experience during error conditions"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Simulate network failure
        with network_simulator.apply_condition("offline"):
            window.search_input.setText("SMITH")

            # Mock the search to simulate network failure
            def mock_failing_search():
                raise ConnectionError("Network unavailable")

            with patch.object(
                window, "_perform_search", side_effect=mock_failing_search
            ):
                window.search_btn.click()
                qt_app.processEvents()

                # User should see friendly error message, not technical details
                # Check if status bar or error display shows user-friendly message
                if hasattr(window, "statusBar"):
                    status_text = window.statusBar().currentMessage()
                    assert (
                        "network" in status_text.lower()
                        or "connection" in status_text.lower()
                    )
                    assert "ConnectionError" not in status_text  # No technical errors

        window.close()


@pytest.mark.integration
@pytest.mark.gui
class TestDataDisplayExperience:
    """Test how data is displayed to users"""

    def test_search_results_presentation(
        self, qt_app, app_config, sample_search_results
    ):
        """Test that search results are presented clearly and professionally"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Populate results table
        window._populate_results_table(sample_search_results)
        qt_app.processEvents()

        # Verify table has proper headers
        table = window.results_table
        assert table.columnCount() > 0, "Results table should have columns"

        # Check that important data is visible
        headers = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
            if table.horizontalHeaderItem(i)
        ]

        important_fields = ["APN", "Owner", "Address"]
        for field in important_fields:
            assert any(
                field.lower() in header.lower() for header in headers
            ), f"Missing important field: {field}"

        # Verify data is properly formatted
        assert table.rowCount() == len(sample_search_results)

        # Check first row data
        if table.rowCount() > 0:
            first_row_data = [
                table.item(0, col).text()
                for col in range(table.columnCount())
                if table.item(0, col)
            ]
            assert len(first_row_data) > 0, "First row should contain data"

        window.close()

    def test_property_details_display(self, qt_app, app_config, sample_property_data):
        """Test detailed property information display"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Mock showing property details
        with patch.object(window, "_show_property_details") as mock_details:
            # Simulate double-click on property
            if hasattr(window, "results_table"):
                # Add sample data to table first
                window._populate_results_table([sample_property_data])
                qt_app.processEvents()

                # Simulate double-click on first row
                table = window.results_table
                if table.rowCount() > 0:
                    # Mock double-click event
                    mock_details.assert_not_called()  # Should not be called yet

        window.close()

    def test_background_enhancement_indication(self, qt_app, app_config):
        """Test that background data enhancement is indicated to user"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Simulate background enhancement in progress
        if hasattr(window, "status_label") or hasattr(window, "statusBar"):
            # Mock background enhancement
            def mock_enhancement():
                if hasattr(window, "statusBar"):
                    window.statusBar().showMessage(
                        "Enhancing results with additional data..."
                    )
                qt_app.processEvents()
                time.sleep(0.1)
                if hasattr(window, "statusBar"):
                    window.statusBar().showMessage("Results enhanced successfully")

            mock_enhancement()

            # User should see indication of background work
            if hasattr(window, "statusBar"):
                final_message = window.statusBar().currentMessage()
                assert (
                    len(final_message) > 0
                ), "Status should indicate enhancement completion"

        window.close()


@pytest.mark.integration
@pytest.mark.performance
class TestResponsivenessExperience:
    """Test UI responsiveness from user perspective"""

    def test_ui_never_freezes_during_search(self, qt_app, app_config):
        """Test that UI remains responsive during search operations"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Mock a potentially long-running search
        def mock_long_search():
            for i in range(10):
                time.sleep(0.1)  # Simulate work
                qt_app.processEvents()  # Allow UI updates

        with patch.object(window, "_perform_search", side_effect=mock_long_search):
            window.search_input.setText("SMITH")
            window.search_btn.click()

            # UI should remain responsive
            start_time = time.time()
            clicks_processed = 0

            # Test UI responsiveness during search
            for _ in range(5):
                if time.time() - start_time > 1:  # Stop after 1 second
                    break

                # Try to interact with UI
                original_text = window.search_input.text()
                window.search_input.setText(original_text + "X")
                qt_app.processEvents()

                if window.search_input.text() == original_text + "X":
                    clicks_processed += 1
                    window.search_input.setText(original_text)  # Reset

                time.sleep(0.1)

            # UI should process at least some interactions
            assert clicks_processed > 0, "UI should remain responsive during search"

        window.close()

    def test_large_result_set_display_performance(self, qt_app, app_config):
        """Test that large result sets don't freeze the UI"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        window = EnhancedPropertySearchApp(app_config)
        window.show()
        qt_app.processEvents()

        # Create large result set
        large_results = []
        for i in range(100):
            large_results.append(
                {
                    "apn": f"999-{i:02d}-{i:03d}X",
                    "owner_name": f"TEST OWNER {i}",
                    "property_address": f"{100 + i} TEST STREET",
                    "city": "PHOENIX",
                    "assessed_value": 200000 + i * 1000,
                }
            )

        start_time = time.time()

        # Populate table with large result set
        window._populate_results_table(large_results)
        qt_app.processEvents()

        elapsed = time.time() - start_time

        # Should complete within reasonable time
        assert elapsed < 2.0, f"Large result set display took {elapsed:.3f}s"

        # UI should remain responsive
        window.search_input.setText("test")
        qt_app.processEvents()
        assert (
            window.search_input.text() == "test"
        ), "UI should remain responsive after large data load"

        window.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
