import gphoto2 as gp
import time
import logging
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
            # Pre-capture delay
            await self._sleep(0.2)
            
            # Capture
            self._logger.info("Capturing photo")
            self.camera.trigger_capture()
            
            # Post-capture delay
            await self._sleep(0.2)
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
            # Enable movie mode
            config = self.camera.get_config()
            movie_mode = self._get_config_value(config, 'eosmoviemode')
            if movie_mode:
                movie_mode.set_value(1)
                self.camera.set_config(config)
                
            # Start recording
            remote_mode = self._get_config_value(config, 'eosremoterelease')
            if remote_mode:
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
            remote_mode = self._get_config_value(config, 'eosremoterelease')
            if remote_mode:
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
            if viewfinder:
                viewfinder.set_value(1 if enable else 0)
                self.camera.set_config(config)
                self.live_view_enabled = enable
                self._logger.info(f"Live view {'enabled' if enable else 'disabled'}")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error toggling live view: {str(e)}")
            return False

    async def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information from camera."""
        if not self.camera:
            return {'available_shots': 0, 'error': 'Camera not connected'}

        try:
            config = self.camera.get_config()
            available = self._get_config_value(config, 'availableshots')
            battery = self._get_config_value(config, 'batterylevel')
            
            return {
                'available_shots': int(available.get_value()) if available else 0,
                'battery_level': int(battery.get_value()) if battery else 0
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
            
            # Map of settings to retrieve
            setting_keys = [
                'iso', 'aperture', 'shutterspeed', 'autoexposuremode',
                'imageformat', 'whitebalance'
            ]
            
            for key in setting_keys:
                value = self._get_config_value(config, key)
                if value:
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
                setting = self._get_config_value(config, key)
                if setting:
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
        time.sleep(seconds)  # For simplicity, using sync sleep
