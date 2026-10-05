"""One model and lock owned only by the ChatGPT Live avatar server."""
import threading
import sys
# Script directory /lab precedes PYTHONPATH; select the new engine explicitly.
sys.path.insert(0, '/engine')
from loop_core import LoopEngine

engine=LoopEngine()
lock=threading.Lock()
