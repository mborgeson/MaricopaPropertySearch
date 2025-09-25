"""
Unit tests for UnifiedGUILauncher

Tests the consolidated GUI launcher that combines 4 previous implementations
with features including platform detection, progressive fallback, and environment setup.
"""

import os
import platform
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the component under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gui_launcher_unified import (
    EnvironmentConfigurer,
    GUILaunchManager,
    LaunchStrategy,
    PlatformDetector,
    UnifiedGUILauncher,
)


class TestUnifiedGUILauncher:
    """Test suite for UnifiedGUILauncher component."""

    @pytest.fixture
    def platform_detector(self):
        """Create a PlatformDetector instance for testing."""
        return PlatformDetector()

    @pytest.fixture
    def environment_configurer(self):
        """Create an EnvironmentConfigurer instance for testing."""
        return EnvironmentConfigurer()

    @pytest.fixture
    def gui_launcher(self):
        """Create a UnifiedGUILauncher instance for testing."""
        with patch("gui_launcher_unified.get_logger"):
            launcher = UnifiedGUILauncher()
            return launcher

    @pytest.mark.unit
    def test_launcher_initialization(self):
        """Test proper initialization of the GUI launcher."""
        with patch("gui_launcher_unified.get_logger"):
            launcher = UnifiedGUILauncher()

            assert launcher.platform_detector is not None
            assert launcher.environment_configurer is not None
            assert launcher.launch_manager is not None
            assert launcher.config is not None

    @pytest.mark.unit
    @patch("platform.system")
    @patch("os.name")
    def test_platform_detection_windows(
        self, mock_os_name, mock_platform_system, platform_detector
    ):
        """Test platform detection for Windows."""
        mock_platform_system.return_value = "Windows"
        mock_os_name.return_value = "nt"

        platform_info = platform_detector.detect_platform()

        assert platform_info["os_type"] == "Windows"
        assert platform_info["is_wsl"] is False
        assert platform_info["gui_backend"] == "Windows"

    @pytest.mark.unit
    @patch("platform.system")
    @patch("os.name")
    @patch("os.path.exists")
    def test_platform_detection_linux(
        self, mock_exists, mock_os_name, mock_platform_system, platform_detector
    ):
        """Test platform detection for Linux."""
        mock_platform_system.return_value = "Linux"
        mock_os_name.return_value = "posix"
        mock_exists.return_value = False  # Not WSL

        platform_info = platform_detector.detect_platform()

        assert platform_info["os_type"] == "Linux"
        assert platform_info["is_wsl"] is False
        assert platform_info["gui_backend"] in ["XCB", "Wayland"]

    @pytest.mark.unit
    @patch("platform.system")
    @patch("os.name")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_platform_detection_wsl(
        self,
        mock_open,
        mock_exists,
        mock_os_name,
        mock_platform_system,
        platform_detector,
    ):
        """Test platform detection for WSL."""
        mock_platform_system.return_value = "Linux"
        mock_os_name.return_value = "posix"
        mock_exists.return_value = True  # WSL detected
        mock_open.return_value.__enter__.return_value.read.return_value = "Microsoft"

        platform_info = platform_detector.detect_platform()

        assert platform_info["os_type"] == "Linux"
        assert platform_info["is_wsl"] is True
        assert platform_info["gui_backend"] in ["Wayland", "XCB"]

    @pytest.mark.unit
    def test_environment_detection_display_available(
        self, environment_configurer, mock_environment
    ):
        """Test environment detection with display available."""
        env_info = environment_configurer.detect_environment()

        assert env_info["display_available"] is True
        assert env_info["display_server"] in ["wayland", "x11"]

    @pytest.mark.unit
    @patch.dict(os.environ, {}, clear=True)
    def test_environment_detection_headless(self, environment_configurer):
        """Test environment detection in headless mode."""
        env_info = environment_configurer.detect_environment()

        assert env_info["display_available"] is False
        assert env_info["display_server"] == "none"

    @pytest.mark.unit
    def test_qt_platform_configuration_wayland(
        self, environment_configurer, mock_environment
    ):
        """Test Qt platform configuration for Wayland."""
        platform_info = {"gui_backend": "Wayland", "is_wsl": True}

        qt_config = environment_configurer.configure_qt_platform(platform_info)

        assert qt_config["QT_QPA_PLATFORM"] == "wayland"
        assert "wayland" in qt_config

    @pytest.mark.unit
    def test_qt_platform_configuration_xcb(self, environment_configurer):
        """Test Qt platform configuration for XCB."""
        platform_info = {"gui_backend": "XCB", "is_wsl": False}

        qt_config = environment_configurer.configure_qt_platform(platform_info)

        assert qt_config["QT_QPA_PLATFORM"] == "xcb"

    @pytest.mark.unit
    def test_qt_platform_configuration_windows(self, environment_configurer):
        """Test Qt platform configuration for Windows."""
        platform_info = {"gui_backend": "Windows", "is_wsl": False}

        qt_config = environment_configurer.configure_qt_platform(platform_info)

        assert qt_config["QT_QPA_PLATFORM"] == "windows"

    @pytest.mark.unit
    def test_launch_strategy_selection(self, gui_launcher):
        """Test launch strategy selection based on platform."""
        # Test Enhanced GUI strategy selection
        platform_info = {
            "os_type": "Linux",
            "gui_backend": "Wayland",
            "display_available": True,
        }

        strategy = gui_launcher.select_launch_strategy(platform_info)
        assert strategy == LaunchStrategy.ENHANCED_GUI

        # Test Basic GUI fallback
        platform_info["display_available"] = False
        strategy = gui_launcher.select_launch_strategy(platform_info)
        assert strategy == LaunchStrategy.BASIC_GUI

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_dependency_checking(self, mock_subprocess, gui_launcher):
        """Test dependency checking functionality."""
        # Mock successful dependency check
        mock_subprocess.return_value.returncode = 0

        dependencies = gui_launcher.check_dependencies()

        assert "python" in dependencies
        assert dependencies["python"]["available"] is True

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_dependency_checking_missing(self, mock_subprocess, gui_launcher):
        """Test handling of missing dependencies."""
        # Mock failed dependency check
        mock_subprocess.return_value.returncode = 1

        dependencies = gui_launcher.check_dependencies()

        # Should handle missing dependencies gracefully
        assert isinstance(dependencies, dict)

    @pytest.mark.unit
    @patch("subprocess.Popen")
    def test_enhanced_gui_launch(self, mock_popen, gui_launcher):
        """Test launching Enhanced GUI."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        mock_popen.return_value = mock_process

        result = gui_launcher.launch_enhanced_gui()

        assert result["success"] is True
        assert result["strategy"] == "enhanced_gui"
        mock_popen.assert_called_once()

    @pytest.mark.unit
    @patch("subprocess.Popen")
    def test_basic_gui_launch(self, mock_popen, gui_launcher):
        """Test launching Basic GUI as fallback."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        mock_popen.return_value = mock_process

        result = gui_launcher.launch_basic_gui()

        assert result["success"] is True
        assert result["strategy"] == "basic_gui"
        mock_popen.assert_called_once()

    @pytest.mark.unit
    def test_progressive_fallback_mechanism(self, gui_launcher):
        """Test progressive fallback from Enhanced to Basic GUI."""
        with patch.object(gui_launcher, "launch_enhanced_gui") as mock_enhanced:
            with patch.object(gui_launcher, "launch_basic_gui") as mock_basic:
                # Simulate Enhanced GUI failure
                mock_enhanced.return_value = {
                    "success": False,
                    "error": "PyQt5 not available",
                }
                mock_basic.return_value = {"success": True, "strategy": "basic_gui"}

                result = gui_launcher.launch_with_fallback()

                # Verify fallback occurred
                assert result["success"] is True
                assert result["strategy"] == "basic_gui"
                mock_enhanced.assert_called_once()
                mock_basic.assert_called_once()

    @pytest.mark.unit
    def test_test_mode_functionality(self, gui_launcher):
        """Test GUI testing mode functionality."""
        test_result = gui_launcher.test_gui_capability()

        assert "display_available" in test_result
        assert "qt_available" in test_result
        assert "platform_info" in test_result
        assert isinstance(test_result["success"], bool)

    @pytest.mark.unit
    @patch("sys.argv", ["gui_launcher_unified.py", "--test-gui"])
    def test_command_line_arguments_test_mode(self, gui_launcher):
        """Test command line argument parsing for test mode."""
        args = gui_launcher.parse_command_line_arguments()

        assert args.test_gui is True

    @pytest.mark.unit
    @patch("sys.argv", ["gui_launcher_unified.py", "--platform", "linux"])
    def test_command_line_arguments_platform_override(self, gui_launcher):
        """Test command line platform override."""
        args = gui_launcher.parse_command_line_arguments()

        assert args.platform == "linux"

    @pytest.mark.unit
    @patch("sys.argv", ["gui_launcher_unified.py", "--fallback-only"])
    def test_command_line_arguments_fallback_only(self, gui_launcher):
        """Test command line fallback-only mode."""
        args = gui_launcher.parse_command_line_arguments()

        assert args.fallback_only is True

    @pytest.mark.unit
    @pytest.mark.performance
    def test_startup_performance(self, gui_launcher, performance_timer):
        """Test GUI startup performance."""
        with patch.object(gui_launcher, "launch_enhanced_gui") as mock_launch:
            mock_launch.return_value = {"success": True, "strategy": "enhanced_gui"}

            # Measure startup time
            performance_timer.start()
            result = gui_launcher.launch()
            startup_time = performance_timer.stop()

            # Verify performance meets baseline
            assert result["success"] is True
            assert startup_time < 5.0  # Should start under 5 seconds

    @pytest.mark.unit
    def test_error_handling_and_logging(self, gui_launcher):
        """Test comprehensive error handling and logging."""
        with patch.object(gui_launcher, "logger") as mock_logger:
            with patch.object(gui_launcher, "launch_enhanced_gui") as mock_launch:
                mock_launch.side_effect = Exception("Launch error")

                # Execute launch with error
                result = gui_launcher.launch()

                # Verify error handling
                assert result["success"] is False
                assert "error" in result

                # Verify logging
                mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_environment_variable_management(self, gui_launcher, mock_environment):
        """Test environment variable setup and management."""
        with patch.dict(os.environ, mock_environment):
            env_vars = gui_launcher.setup_environment_variables()

            # Verify environment setup
            assert "QT_QPA_PLATFORM" in env_vars
            assert "DISPLAY" in env_vars or "WAYLAND_DISPLAY" in env_vars

    @pytest.mark.unit
    def test_database_connection_testing(self, gui_launcher):
        """Test database connection validation during launch."""
        with patch("threadsafe_database_manager.ThreadSafeDatabaseManager") as mock_db:
            mock_db.return_value.health_check.return_value = {"status": "healthy"}

            db_status = gui_launcher.test_database_connection()

            assert db_status["available"] is True
            assert db_status["status"] == "healthy"

    @pytest.mark.unit
    def test_database_connection_failure_handling(self, gui_launcher):
        """Test handling of database connection failures."""
        with patch("threadsafe_database_manager.ThreadSafeDatabaseManager") as mock_db:
            mock_db.return_value.health_check.side_effect = Exception(
                "Connection failed"
            )

            db_status = gui_launcher.test_database_connection()

            assert db_status["available"] is False
            assert "error" in db_status

    @pytest.mark.unit
    def test_splash_screen_functionality(self, gui_launcher):
        """Test splash screen display functionality."""
        with patch("builtins.print") as mock_print:
            gui_launcher.show_splash_screen()

            # Verify splash screen was displayed
            mock_print.assert_called()
            call_args = str(mock_print.call_args_list)
            assert "MARICOPA PROPERTY SEARCH" in call_args

    @pytest.mark.unit
    def test_missouri_ave_workflow_validation(self, gui_launcher):
        """Test Missouri Avenue workflow validation functionality."""
        validation_result = gui_launcher.validate_missouri_ave_workflow()

        assert "workflow_available" in validation_result
        assert "components_healthy" in validation_result
        assert isinstance(validation_result["success"], bool)

    @pytest.mark.unit
    def test_configuration_file_management(self, gui_launcher, temp_dir):
        """Test configuration file creation and management."""
        config_file = temp_dir / "test_config.json"

        # Test config file creation
        result = gui_launcher.create_default_config(str(config_file))
        assert result is True
        assert config_file.exists()

        # Test config file loading
        config = gui_launcher.load_config(str(config_file))
        assert config is not None
        assert isinstance(config, dict)

    @pytest.mark.unit
    def test_launch_recovery_mechanisms(self, gui_launcher):
        """Test launch recovery and retry mechanisms."""
        with patch.object(gui_launcher, "launch_enhanced_gui") as mock_enhanced:
            with patch.object(gui_launcher, "launch_basic_gui") as mock_basic:
                # Simulate multiple failures then success
                mock_enhanced.side_effect = [
                    {"success": False, "error": "First failure"},
                    {"success": False, "error": "Second failure"},
                    {"success": True, "strategy": "enhanced_gui"},
                ]

                result = gui_launcher.launch_with_retry(max_retries=3)

                # Verify recovery succeeded
                assert result["success"] is True
                assert mock_enhanced.call_count == 3

    @pytest.mark.unit
    def test_resource_cleanup(self, gui_launcher):
        """Test proper resource cleanup on exit."""
        # Simulate launched processes
        gui_launcher.launched_processes = [Mock(), Mock()]

        # Test cleanup
        gui_launcher.cleanup()

        # Verify cleanup was called on all processes
        for process in gui_launcher.launched_processes:
            process.terminate.assert_called_once()

    @pytest.mark.unit
    def test_accessibility_configuration(self, gui_launcher):
        """Test accessibility configuration setup."""
        accessibility_config = gui_launcher.configure_accessibility()

        assert "high_contrast" in accessibility_config
        assert "screen_reader" in accessibility_config
        assert "keyboard_navigation" in accessibility_config

    @pytest.mark.unit
    def test_platform_specific_optimizations(self, gui_launcher):
        """Test platform-specific performance optimizations."""
        # Test WSL optimizations
        wsl_optimizations = gui_launcher.apply_wsl_optimizations()
        assert "wayland_config" in wsl_optimizations

        # Test Windows optimizations
        windows_optimizations = gui_launcher.apply_windows_optimizations()
        assert "dpi_awareness" in windows_optimizations

        # Test Linux optimizations
        linux_optimizations = gui_launcher.apply_linux_optimizations()
        assert "x11_config" in linux_optimizations

    @pytest.mark.unit
    def test_compatibility_mode_detection(self, gui_launcher):
        """Test compatibility mode detection and handling."""
        compatibility_info = gui_launcher.detect_compatibility_mode()

        assert "compatibility_required" in compatibility_info
        assert "compatibility_mode" in compatibility_info
        assert isinstance(compatibility_info["compatibility_required"], bool)

    @pytest.mark.unit
    def test_version_information_display(self, gui_launcher):
        """Test version information display."""
        with patch("builtins.print") as mock_print:
            gui_launcher.show_version_info()

            # Verify version info was displayed
            mock_print.assert_called()
            call_args = str(mock_print.call_args_list)
            assert "Unified GUI Launcher" in call_args

    @pytest.mark.unit
    def test_help_information_display(self, gui_launcher):
        """Test help information display."""
        with patch("builtins.print") as mock_print:
            gui_launcher.show_help()

            # Verify help was displayed
            mock_print.assert_called()
            call_args = str(mock_print.call_args_list)
            assert "Usage:" in call_args or "Options:" in call_args
