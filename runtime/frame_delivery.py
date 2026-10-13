"""Publish a generated frame before requesting the next one from the worker."""
import asyncio


async def deliver_frames(frames, send):
    try:
        while True:
            frame = await asyncio.to_thread(next, frames, None)
            if frame is None:
                break
            await send(frame)
    finally:
        frames.close()
