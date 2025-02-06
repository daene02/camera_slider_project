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
        """Initialize the MJPEG streamer."""
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
            return True
        except Exception as e:
            self._logger.error(f"Failed to start streaming: {str(e)}")
            return False
    
    async def reset(self) -> None:
        """Reset the streamer to initial state."""
        await self.stop_streaming()
        self._frame_queue = Queue(maxsize=self._frame_queue.maxsize)
        self._streaming_event.clear()
        with self._stream_lock:
            self._active_streams = 0

    async def stop_streaming(self) -> None:
        """Stop the streaming process."""
        self._streaming_event.clear()
        
        # Wait for active streams to disconnect
        timeout = 2.0  # 2 second timeout
        start_time = time.time()
        while self._active_streams > 0 and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
            
        with self._stream_lock:
            was_active = self._active_streams > 0
            self._active_streams = 0
            
        # Clear the frame queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except:
                pass
        
        if was_active:
            try:
                await self.camera.toggle_live_view(False)
                await asyncio.sleep(0.2)  # Give camera more time to cleanup
            except Exception as e:
                self._logger.error(f"Error disabling live view: {str(e)}")

    async def _stream_producer(self) -> None:
        """Continuously capture frames and add them to the queue."""
        retry_delay = 0.1
        max_retries = 3
        last_frame_time = 0
        min_frame_interval = 0.05  # ~30fps max
        
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
                            elif attempt == max_retries - 1:
                                self._logger.error("Failed to capture frame after multiple attempts")
                            await asyncio.sleep(retry_delay)
                        except asyncio.CancelledError:
                            return
                        except Exception as e:
                            self._logger.error(f"Frame capture error: {str(e)}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
            await asyncio.sleep(0.01)  # Shorter sleep for more responsive shutdown

    async def get_stream(self) -> AsyncGenerator[bytes, None]:
        """Get a MJPEG stream generator."""
        # First check if we can accept a new connection
        with self._stream_lock:
            if self._active_streams >= self.max_connections:
                self._logger.error("Maximum stream connections reached")
                return
        
        # Then try to start streaming if needed
        if not self._streaming_event.is_set():
            if not await self.start_streaming():
                self._logger.error("Failed to start streaming")
                return
        
        # Finally increment connection count
        with self._stream_lock:
            # Double check max connections in case of race condition
            if self._active_streams >= self.max_connections:
                self._logger.error("Maximum stream connections reached (race check)")
                return
            self._active_streams += 1
        
        try:
            boundary = "frame"
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
                        frame_header = (
                            f"{header_str}{len(frame)}\r\n\r\n"
                        ).encode('utf-8')
                        yield frame_header + frame + b'\r\n'
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if not isinstance(e, TimeoutError):
                        self._logger.error(f"Frame fetch error: {str(e)}")
                    continue
        finally:
            with self._stream_lock:
                self._active_streams -= 1
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
