import gphoto2 as gp
import logging
import asyncio
from typing import Dict, Optional, Any

class CanonEOSR50:
    """Manages communication with Canon EOS R50 camera via gphoto2."""
    
    def __init__(self):
        self.camera = None
        self.context = None
        self.live_view_enabled = False
        self._logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        """Initialize connection to the camera."""
        try:
            self.context = gp.Context()
            self.camera = gp.Camera()
            self.camera.init(self.context)
            self._logger.info("Camera connected successfully")
            return True
        except Exception as e:
            self._logger.error(f"Failed to connect to camera: {str(e)}")
            return False

    async def disconnect(self) -> None:
        """Safely disconnect from the camera."""
        if self.camera:
            try:
                if self.live_view_enabled:
                    await self.toggle_live_view(False)
                self.camera.exit()
                self._logger.info("Camera disconnected successfully")
            except Exception as e:
                self._logger.error(f"Error disconnecting camera: {str(e)}")
            finally:
                self.camera = None
                self.context = None

    async def capture_photo(self) -> bool:
        """Capture a photo with pre and post delays."""
        if not self.camera:
            self._logger.error("Camera not connected")
            return False

        try:
            await self._sleep(0.2)  # Pre-capture delay
            self._logger.info("Capturing photo")
            self.camera.trigger_capture()
            await self._sleep(0.2)  # Post-capture delay
            return True
        except Exception as e:
            self._logger.error(f"Error capturing photo: {str(e)}")
            return False

    async def start_video(self) -> bool:
        """Start video recording."""
        if not self.camera:
            self._logger.error("Camera not connected")
            return False

        try:
            config = self.camera.get_config()
            if movie_mode := self._get_config_value(config, 'eosmoviemode'):
                movie_mode.set_value(1)
                self.camera.set_config(config)
            
            if remote_mode := self._get_config_value(config, 'eosremoterelease'):
                remote_mode.set_value("Record Start")
                self.camera.set_config(config)
                self._logger.info("Video recording started")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error starting video: {str(e)}")
            return False

    async def stop_video(self) -> bool:
        """Stop video recording."""
        if not self.camera:
            self._logger.error("Camera not connected")
            return False

        try:
            config = self.camera.get_config()
            if remote_mode := self._get_config_value(config, 'eosremoterelease'):
                remote_mode.set_value("Record Stop")
                self.camera.set_config(config)
                self._logger.info("Video recording stopped")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error stopping video: {str(e)}")
            return False

    async def toggle_live_view(self, enable: bool = None) -> bool:
        """Toggle live view on/off."""
        if not self.camera:
            self._logger.error("Camera not connected")
            return False

        try:
            if enable is None:
                enable = not self.live_view_enabled

            config = self.camera.get_config()
            viewfinder = self._get_config_value(config, 'viewfinder')
            if not viewfinder:
                self._logger.error("Viewfinder not found in camera config")
                return False

            viewfinder.set_value(1 if enable else 0)
            self.camera.set_config(config)
            await self._sleep(0.3)  # Give camera time to process change
            
            self.live_view_enabled = enable
            self._logger.info(f"Live view {'enabled' if enable else 'disabled'}")
            return True
        except Exception as e:
            self._logger.error(f"Error toggling live view: {str(e)}")
            return False

    async def capture_preview(self) -> Optional[bytes]:
        """Capture a preview image from the camera."""
        if not self.camera or not self.context:
            self._logger.error("Camera not connected")
            return None

        try:
            # Make sure live view is enabled
            self._logger.debug(f"Live view status before capture: {self.live_view_enabled}")
            if not self.live_view_enabled:
                self._logger.debug("Enabling live view for preview")
                if not await self.toggle_live_view(True):
                    self._logger.error("Failed to enable live view")
                    return None
                await self._sleep(0.5)  # Additional delay after enabling live view

            max_io_retries = 3
            retry_delay = 0.5

            # Helper function to safely capture preview with retries
            async def try_capture_preview(is_buffer_clear=False):
                for attempt in range(max_io_retries):
                    try:
                        try:
                            camera_file = self.camera.capture_preview()
                            if not camera_file:
                                self._logger.error("Capture returned None")
                                continue

                            # Log available methods and properties
                            self._logger.debug(f"Camera file type: {type(camera_file)}")
                            self._logger.debug(f"Camera file dir: {dir(camera_file)}")

                            # Get data from camera file
                            file_data = camera_file.get_data_and_size()
                            if not file_data:
                                self._logger.error("No data returned from preview")
                                continue
                                
                            self._logger.debug(f"Raw data type: {type(file_data)}")
                            
                            # Convert FileData to bytes
                            data = bytes(file_data)
                            self._logger.debug(f"Converted data size: {len(data)} bytes")
                            
                            # Verify we got JPEG data
                            mime_type = camera_file.get_mime_type()
                            self._logger.debug(f"MIME type: {mime_type}")
                            if not mime_type.startswith('image/'):
                                self._logger.error(f"Unexpected MIME type: {mime_type}")
                                continue

                            return data
                        finally:
                            # Clean up camera file
                            if 'camera_file' in locals():
                                camera_file.clean()
                    except gp.GPhoto2Error as e:
                        if e.code == -110:  # I/O in progress
                            self._logger.warning(f"I/O in progress (attempt {attempt + 1}/{max_io_retries})")
                            await self._sleep(retry_delay)
                            continue
                        raise
                return None

            # First preview to clear buffer
            self._logger.debug("Capturing first preview (buffer clear)")
            await try_capture_preview(is_buffer_clear=True)
            await self._sleep(0.2)  # Longer delay after buffer clear

            # Actual preview capture
            self._logger.debug("Capturing main preview")
            data = await try_capture_preview()
            
            if not data:
                self._logger.error("Failed to get valid preview data")
                return None

            self._logger.debug(f"Successfully captured preview ({len(data)} bytes)")
            return data
        except gp.GPhoto2Error as e:
            if e.code == -110:  # I/O in progress
                self._logger.warning("I/O in progress, retrying after delay")
                await self._sleep(0.5)
                return await self.capture_preview()
            self._logger.error(f"GPhoto2 error capturing preview: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            self._logger.error(f"Error capturing preview: {str(e)}", exc_info=True)
            return None

    async def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information from camera."""
        if not self.camera:
            return {'available_shots': 0, 'error': 'Camera not connected'}

        try:
            config = self.camera.get_config()
            available = self._get_config_value(config, 'availableshots')
            battery = self._get_config_value(config, 'batterylevel')
            
            # Parse battery level - handle percentage string
            battery_value = battery.get_value() if battery else '0%'
            battery_level = int(battery_value.rstrip('%')) if battery_value.endswith('%') else int(battery_value)

            return {
                'available_shots': int(available.get_value()) if available else 0,
                'battery_level': battery_level
            }
        except Exception as e:
            self._logger.error(f"Error getting storage info: {str(e)}")
            return {'available_shots': 0, 'error': str(e)}

    async def get_settings(self) -> Dict[str, Any]:
        """Get current camera settings."""
        if not self.camera:
            return {'error': 'Camera not connected'}

        try:
            config = self.camera.get_config()
            settings = {}
            
            setting_keys = [
                'iso', 'aperture', 'shutterspeed', 'autoexposuremode',
                'imageformat', 'whitebalance'
            ]
            
            for key in setting_keys:
                if value := self._get_config_value(config, key):
                    settings[key] = value.get_value()
            
            return settings
        except Exception as e:
            self._logger.error(f"Error getting camera settings: {str(e)}")
            return {'error': str(e)}

    async def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update camera settings."""
        if not self.camera:
            self._logger.error("Camera not connected")
            return False

        try:
            config = self.camera.get_config()
            for key, value in settings.items():
                if setting := self._get_config_value(config, key):
                    setting.set_value(value)
            
            self.camera.set_config(config)
            self._logger.info("Camera settings updated successfully")
            return True
        except Exception as e:
            self._logger.error(f"Error updating camera settings: {str(e)}")
            return False

    def _get_config_value(self, config, name: str) -> Optional[gp.CameraWidget]:
        """Helper method to get camera configuration values."""
        try:
            return config.get_child_by_name(name)
        except Exception:
            return None

    @staticmethod
    async def _sleep(seconds: float) -> None:
        """Async sleep helper."""
        await asyncio.sleep(seconds)
