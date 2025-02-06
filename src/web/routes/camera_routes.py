from flask import Blueprint, jsonify, request, Response
from src.web.controllers.profile_controller import profile_controller
from src.mjpeg_streamer import MJPEGStreamer
import gphoto2 as gp
import asyncio
import logging

logger = logging.getLogger(__name__)
camera_routes = Blueprint('camera_routes', __name__)

# Global MJPEG streamer instance
mjpeg_streamer = None

def get_mjpeg_streamer():
    """Get or create MJPEGStreamer instance."""
    global mjpeg_streamer
    if mjpeg_streamer is None and profile_controller.camera is not None:
        mjpeg_streamer = MJPEGStreamer(profile_controller.camera)
    return mjpeg_streamer

def cleanup_streamer():
    """Clean up MJPEG streamer on shutdown."""
    global mjpeg_streamer
    if mjpeg_streamer and mjpeg_streamer.is_streaming:
        asyncio.run(mjpeg_streamer.reset())
    mjpeg_streamer = None

def ensure_camera_connected():
    """Ensure camera is connected and live view is enabled."""
    try:
        if not profile_controller.camera_connected:
            success, error = run_async(profile_controller.connect_camera())
            if not success:
                logger.error(f"Failed to connect camera: {error}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error connecting camera: {str(e)}")
        return False

def check_camera_connected():
    """Check if camera is connected and return error response if not."""
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    return None

def run_async(coro):
    """Helper to run coroutines in Flask routes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@camera_routes.route('/connect', methods=['POST'])
def connect_camera():
    try:
        success, error = run_async(profile_controller.connect_camera())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": error}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/status', methods=['GET'])
def get_camera_status():
    try:
        if not profile_controller.camera_connected:
            return jsonify({"connected": False})
            
        storage_info = run_async(profile_controller.camera.get_storage_info())
        camera_settings = run_async(profile_controller.camera.get_settings())
        
        return jsonify({
            "connected": True,
            "recording": profile_controller.recording_active,
            "storage": storage_info,
            "settings": camera_settings,
            "live_view": profile_controller.camera.live_view_enabled
        })
    except Exception as e:
        logger.error(f"Error getting camera status: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/stream')
def stream_video():
    """Stream video using MJPEG format."""
    try:
        if error_response := check_camera_connected():
            logger.error("Camera not connected")
            return error_response

        streamer = get_mjpeg_streamer()
        if not streamer:
            return jsonify({"error": "Failed to initialize streamer"}), 500

        def generate():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                async def frame_generator():
                    async for frame_data in streamer.get_stream():
                        yield frame_data

                gen = frame_generator()
                while True:
                    try:
                        frame = loop.run_until_complete(anext(gen))
                        yield frame
                    except StopAsyncIteration:
                        break
                    except Exception as e:
                        logger.error(f"Frame generation error: {str(e)}")
                        break
            finally:
                loop.close()

        return Response(
            generate(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/live_view')
def get_live_view():
    """Endpoint for camera live view that reuses MJPEG stream."""
    try:
        if error_response := check_camera_connected():
            logger.error("Camera not connected")
            return error_response

        return stream_video()
    except Exception as e:
        logger.error(f"Live view setup error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/capture', methods=['POST'])
def capture_photo():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        success = run_async(profile_controller.camera.capture_photo())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to capture photo"}), 500
    except Exception as e:
        logger.error(f"Error capturing photo: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/start_recording', methods=['POST'])
def start_recording():
    if not profile_controller.camera_connected:
        try:
            success, error = run_async(profile_controller.connect_camera())
            if not success:
                return jsonify({"error": f"Failed to connect camera: {error}"}), 400
        except Exception as e:
            return jsonify({"error": f"Camera connection error: {str(e)}"}), 500

    try:
        success = run_async(profile_controller.camera.start_video())
        if success:
            profile_controller.recording_active = True
            return jsonify({"success": True})
        return jsonify({"error": "Failed to start recording"}), 500
    except gp.GPhoto2Error as e:
        if e.code == -110:  # I/O in progress
            logger.warning("Camera I/O in progress, please wait a moment and try again")
            return jsonify({"error": "Camera busy, please wait a moment and try again"}), 503
        logger.error(f"GPhoto2 error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Camera error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/stop_recording', methods=['POST'])
def stop_recording():
    if not profile_controller.camera_connected:
        return jsonify({"error": "No camera connected"}), 400
        
    try:
        success = run_async(profile_controller.camera.stop_video())
        if success:
            profile_controller.recording_active = False
            return jsonify({"success": True})
        return jsonify({"error": "Failed to stop recording"}), 500
    except gp.GPhoto2Error as e:
        if e.code == -110:  # I/O in progress
            logger.warning("Camera I/O in progress, please wait a moment and try again")
            return jsonify({"error": "Camera busy, please wait a moment and try again"}), 503
        logger.error(f"GPhoto2 error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Camera error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/settings', methods=['POST'])
def update_camera_settings():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        settings = request.json
        success = run_async(profile_controller.camera.update_settings(settings))
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to update camera settings"}), 500
    except Exception as e:
        logger.error(f"Error updating camera settings: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@camera_routes.route('/live_view/toggle', methods=['POST'])
def toggle_live_view():
    if error_response := check_camera_connected():
        return error_response
    
    global mjpeg_streamer
    try:
        enable = request.json.get('enable')
        
        # If disabling, stop and reset streamer
        if not enable and mjpeg_streamer is not None:
            run_async(mjpeg_streamer.reset())
            mjpeg_streamer = None
            
        success = run_async(profile_controller.camera.toggle_live_view(enable))
        if success:
            return jsonify({
                "success": True,
                "enabled": profile_controller.camera.live_view_enabled
            })
        return jsonify({"error": "Failed to toggle live view"}), 500
    except Exception as e:
        logger.error(f"Error toggling live view: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
