import asyncio
import logging
from typing import Optional, AsyncGenerator
import time
from queue import Queue
from threading import Event, Lock
from concurrent.futures import ThreadPoolExecutor

class MJPEGStreamer:
    """Handles MJPEG streaming from the camera with connection pooling."""
    
    def __init__(self, camera, max_connections=5, frame_buffer_size=2):
        """Initialize the MJPEG streamer.
        
        Args:
            camera: Camera instance to stream from
            max_connections: Maximum number of simultaneous stream connections
            frame_buffer_size: Size of frame buffer queue
        """
        self.camera = camera
        self.max_connections = max_connections
        self._active_streams = 0
        self._stream_lock = Lock()
        self._frame_queue = Queue(maxsize=frame_buffer_size)
        self._streaming_event = Event()
        self._logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=2)
        
    async def start_streaming(self) -> bool:
        """Start the streaming process."""
        if self._streaming_event.is_set():
            return True
            
        try:
            if not self.camera.live_view_enabled:
                success = await self.camera.toggle_live_view(True)
                if not success:
                    self._logger.error("Failed to enable live view")
                    return False
            
            self._streaming_event.set()
            asyncio.create_task(self._stream_producer())
            self._logger.info("MJPEG streaming started")
            return True
        except Exception as e:
            self._logger.error(f"Failed to start streaming: {str(e)}")
            return False
    
    async def stop_streaming(self) -> None:
        """Stop the streaming process."""
        self._streaming_event.clear()
        await asyncio.sleep(0.1)  # Give producer time to stop
        
        with self._stream_lock:
            self._active_streams = 0
            
        # Clear the frame queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except:
                pass
        
        try:
            if self.camera.live_view_enabled:
                await self.camera.toggle_live_view(False)
        except Exception as e:
            self._logger.error(f"Error disabling live view: {str(e)}")
        finally:
            self._logger.info("MJPEG streaming stopped")

    async def _stream_producer(self) -> None:
        """Continuously capture frames and add them to the queue."""
        retry_delay = 0.1
        max_retries = 3
        last_frame_time = 0
        min_frame_interval = 0.03  # ~30fps max
        
        while self._streaming_event.is_set():
            if self._active_streams > 0:
                current_time = time.time()
                if current_time - last_frame_time >= min_frame_interval:
                    for attempt in range(max_retries):
                        try:
                            frame = await self.camera.capture_preview()
                            if frame:
                                # Clear old frame if queue is full
                                if self._frame_queue.full():
                                    try:
                                        self._frame_queue.get_nowait()
                                    except:
                                        pass
                                self._frame_queue.put(frame)
                                last_frame_time = time.time()
                                break
                            else:
                                self._logger.warning(f"Empty frame (attempt {attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                        except asyncio.CancelledError:
                            self._logger.info("Stream producer cancelled")
                            return
                        except Exception as e:
                            self._logger.error(f"Frame capture error: {str(e)}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
            await asyncio.sleep(0.01)  # Shorter sleep for more responsive shutdown

    async def get_stream(self) -> AsyncGenerator[bytes, None]:
        """Get a MJPEG stream generator.
        
        Yields:
            JPEG frame data with MJPEG multipart format
        """
        if not self._streaming_event.is_set():
            if not await self.start_streaming():
                self._logger.error("Failed to start streaming")
                return
        
        with self._stream_lock:
            if self._active_streams >= self.max_connections:
                self._logger.warning("Maximum stream connections reached")
                return
            self._active_streams += 1
            self._logger.info(f"New stream connected (active: {self._active_streams})")
        
        try:
            boundary = "frame"
            # Send MJPEG header
            header = [
                '--' + boundary,
                'Content-Type: image/jpeg',
                'Content-Length: ',
            ]
            header_str = '\r\n'.join(header)
            
            while self._streaming_event.is_set():
                try:
                    frame = await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        lambda: self._frame_queue.get(timeout=1.0)
                    )
                    
                    if frame:
                        # Construct MJPEG frame
                        frame_header = (
                            f"{header_str}{len(frame)}\r\n\r\n"
                        ).encode('utf-8')
                        yield frame_header + frame + b'\r\n'
                except asyncio.CancelledError:
                    self._logger.info("Stream consumer cancelled")
                    break
                except Exception as e:
                    if not isinstance(e, TimeoutError):
                        self._logger.error(f"Frame fetch error: {str(e)}")
                    continue
        finally:
            with self._stream_lock:
                self._active_streams -= 1
                self._logger.info(f"Stream disconnected (active: {self._active_streams})")
                if self._active_streams == 0:
                    asyncio.create_task(self.stop_streaming())
    
    def __del__(self):
        """Cleanup on deletion."""
        self._executor.shutdown(wait=False)
                    
    @property
    def is_streaming(self) -> bool:
        """Check if streaming is active."""
        return self._streaming_event.is_set()
        
    @property
    def active_streams(self) -> int:
        """Get number of active streams."""
        return self._active_streams
