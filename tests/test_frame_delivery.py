import asyncio
import threading
import unittest
from runtime.frame_delivery import deliver_frames


class IncrementalDelivery(unittest.IsolatedAsyncioTestCase):
    async def test_first_frame_does_not_wait_for_later_frames(self):
        second_started = threading.Event()
        allow_second = threading.Event()
        received = []

        def generate():
            yield 'first'
            second_started.set()
            if not allow_second.wait(3):
                raise TimeoutError('Second frame was never released')
            yield 'second'

        async def send(frame):
            received.append(frame)

        task = asyncio.create_task(deliver_frames(generate(), send))
        try:
            self.assertTrue(await asyncio.to_thread(second_started.wait, 2))
            self.assertEqual(received, ['first'])
            # The event loop remains available while inference is blocked.
            await asyncio.sleep(0)
            self.assertFalse(task.done())
        finally:
            allow_second.set()
            await asyncio.wait_for(task, 3)
        self.assertEqual(received, ['first', 'second'])

    async def test_send_failure_closes_generator_without_rendering_tail(self):
        rendered = []
        closed = []

        def generate():
            try:
                rendered.append('first')
                yield 'first'
                rendered.append('second')
                yield 'second'
            finally:
                closed.append(True)

        async def send(frame):
            raise ConnectionError('Viewer disconnected')

        with self.assertRaises(ConnectionError):
            await deliver_frames(generate(), send)
        self.assertEqual(rendered, ['first'])
        self.assertEqual(closed, [True])

    async def test_inference_failure_is_reported_after_earlier_frame(self):
        received = []

        def generate():
            yield 'first'
            raise RuntimeError('Inference failed')

        async def send(frame):
            received.append(frame)

        with self.assertRaisesRegex(RuntimeError, 'Inference failed'):
            await deliver_frames(generate(), send)
        self.assertEqual(received, ['first'])


if __name__ == '__main__':
    unittest.main()
