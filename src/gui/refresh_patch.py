#!/usr/bin/env python
"""
CRASH-SAFE REFRESH FUNCTIONS PATCH
This patch contains the fixed refresh functions to prevent application crashes.
"""

# CRASH-SAFE refresh_property_data function (line ~1082)
REFRESH_PROPERTY_DATA_REPLACEMENT = '''    def refresh_property_data(self):
        """CRASH-SAFE Force refresh property data by clearing cache and reloading details"""
        try:
            # Comprehensive safety checks first
            if not hasattr(self, 'property_data') or not self.property_data:
                QMessageBox.warning(self, "Error", "No property data available for refresh.")
                return
                
            apn = self.property_data.get('apn') if isinstance(self.property_data, dict) else None
            if not apn:
                QMessageBox.warning(self, "Error", "No APN available for refresh operation.")
                return
            
            # Initialize progress dialog with proper error handling
            progress = None
            try:
                from PyQt5.QtWidgets import QProgressDialog, QMessageBox
                from PyQt5.QtCore import Qt
                
                progress = QProgressDialog("Preparing refresh operation...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)  # Show immediately
                progress.show()
                progress.setValue(10)
                
            except Exception as progress_error:
                logger.warning(f"Failed to create progress dialog: {progress_error}")
                # Continue without progress dialog
            
            try:
                # SAFE cache clearing with comprehensive error handling
                if progress:
                    progress.setValue(20)
                    progress.setLabelText("Clearing cached data...")
                
                cache_cleared = False
                if self.background_manager:
                    try:
                        if hasattr(self.background_manager, 'worker') and self.background_manager.worker:
                            if hasattr(self.background_manager.worker, 'cache'):
                                try:
                                    self.background_manager.worker.cache.clear_apn_cache(apn)
                                    cache_cleared = True
                                    logger.info(f"Cleared cache for APN {apn}")
                                except Exception as cache_error:
                                    logger.warning(f"Failed to clear cache for APN {apn}: {cache_error}")
                                    # Don't fail the entire operation for cache clearing issues
                            else:
                                logger.debug("Background worker has no cache attribute")
                        else:
                            logger.debug("Background manager has no worker or worker is None")
                    except Exception as manager_error:
                        logger.warning(f"Error accessing background manager for cache clear: {manager_error}")
                
                if progress:
                    progress.setValue(40)
                    progress.setLabelText("Checking background collection service...")
                
                # SAFE background collection with comprehensive checks
                collection_success = False
                if self.background_manager:
                    try:
                        # Check if background service is running
                        is_running = False
                        if hasattr(self.background_manager, 'is_running'):
                            try:
                                is_running = self.background_manager.is_running()
                            except Exception as running_check_error:
                                logger.warning(f"Error checking if background service is running: {running_check_error}")
                        
                        if is_running:
                            if progress:
                                progress.setValue(60)
                                progress.setLabelText("Queuing fresh data collection...")
                            
                            # SAFE data collection request
                            try:
                                if hasattr(self.background_manager, 'collect_data_for_apn'):
                                    success = self.background_manager.collect_data_for_apn(
                                        apn, JobPriority.CRITICAL, force_fresh=True
                                    )
                                    
                                    if success:
                                        collection_success = True
                                        if progress:
                                            progress.setValue(90)
                                            progress.setLabelText("Collection queued successfully...")
                                        
                                        logger.info(f"Successfully queued fresh data collection for APN {apn}")
                                    else:
                                        logger.warning(f"Failed to queue data collection for APN {apn}")
                                else:
                                    logger.error("Background manager missing collect_data_for_apn method")
                                    
                            except Exception as collection_error:
                                logger.error(f"Error requesting data collection for APN {apn}: {collection_error}")
                        else:
                            logger.info("Background collection service is not running - using database refresh")
                            
                    except Exception as bg_service_error:
                        logger.error(f"Error with background collection service: {bg_service_error}")
                else:
                    logger.warning("No background manager available for refresh")
                
                if progress:
                    progress.setValue(80)
                    progress.setLabelText("Refreshing display...")
                
                # SAFE property details reload
                reload_success = False
                try:
                    if hasattr(self, 'load_property_details'):
                        self.load_property_details()
                        reload_success = True
                        logger.info(f"Successfully reloaded property details for APN {apn}")
                    else:
                        logger.error("Dialog missing load_property_details method")
                        
                except Exception as reload_error:
                    logger.error(f"Error reloading property details for APN {apn}: {reload_error}")
                
                if progress:
                    progress.setValue(100)
                
                # Show appropriate success message
                if collection_success:
                    QMessageBox.information(self, "Refresh Started", 
                                           f"Fresh data collection started for APN {apn}.\\n"
                                           "The dialog will refresh automatically when complete.")
                elif reload_success:
                    QMessageBox.information(self, "Data Refreshed", 
                                           "Property data has been refreshed with current database contents.")
                else:
                    QMessageBox.warning(self, "Partial Refresh", 
                                       "Refresh completed but some operations may have failed.\\n"
                                       "Check the application logs for more details.")
                    
            except Exception as main_error:
                logger.error(f"Error in main refresh operation for APN {apn}: {main_error}")
                QMessageBox.critical(self, "Refresh Error", 
                                   f"Error during refresh operation: {str(main_error)}\\n"
                                   "Please try again or restart the application if problems persist.")
            
            finally:
                # SAFE progress dialog cleanup
                if progress:
                    try:
                        progress.close()
                        progress.deleteLater()
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up progress dialog: {cleanup_error}")
                        
        except Exception as e:
            # ULTIMATE CRASH PREVENTION - catch absolutely everything
            logger.error(f"CRITICAL: Unhandled error in refresh_property_data for APN {getattr(self, 'property_data', {}).get('apn', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error but keep application running
            try:
                QMessageBox.critical(self, "Critical Refresh Error", 
                                   f"A critical error occurred during refresh:\\n{str(e)}\\n\\n"
                                   "The application will continue running.\\n"
                                   "Please restart the application if problems persist.")
            except:
                # Even the error dialog failed - just log it
                logger.error("Failed to show critical error dialog - application may be in unstable state")'''

# CRASH-SAFE _update_dialog_status function (line ~1135)
UPDATE_DIALOG_STATUS_REPLACEMENT = '''    def _update_dialog_status(self):
        """CRASH-SAFE Periodically update dialog status"""
        try:
            if not hasattr(self, 'background_manager') or not self.background_manager:
                return
                
            # SAFE status retrieval
            try:
                status = self.background_manager.get_collection_status()
                if hasattr(self, 'status_widget') and self.status_widget:
                    try:
                        self.status_widget.update_status(status)
                    except Exception as widget_error:
                        logger.warning(f"Error updating status widget: {widget_error}")
            except Exception as status_error:
                logger.warning(f"Error getting collection status: {status_error}")
            
            # SAFE collection completion check
            try:
                if hasattr(self, 'collection_in_progress') and self.collection_in_progress:
                    if hasattr(self, 'property_data') and self.property_data:
                        apn = self.property_data.get('apn') if isinstance(self.property_data, dict) else None
                        if apn and hasattr(self.background_manager, 'worker') and self.background_manager.worker:
                            try:
                                if hasattr(self.background_manager.worker, 'active_jobs'):
                                    if apn not in self.background_manager.worker.active_jobs:
                                        # Collection completed, refresh safely
                                        self.collection_in_progress = False
                                        if hasattr(self, 'load_property_details'):
                                            try:
                                                self.load_property_details()
                                            except Exception as load_error:
                                                logger.error(f"Error loading property details after completion: {load_error}")
                            except Exception as job_check_error:
                                logger.warning(f"Error checking active jobs: {job_check_error}")
            except Exception as completion_error:
                logger.warning(f"Error checking collection completion: {completion_error}")
                
        except Exception as e:
            logger.warning(f"Error in _update_dialog_status: {e}")
            # Don't re-raise - just log and continue'''

print("Refresh patch functions defined successfully.")
print("REFRESH_PROPERTY_DATA_REPLACEMENT contains the crash-safe refresh_property_data function")
print("UPDATE_DIALOG_STATUS_REPLACEMENT contains the crash-safe _update_dialog_status function")