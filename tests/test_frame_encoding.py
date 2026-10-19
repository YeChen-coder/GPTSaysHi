import sys,unittest
from pathlib import Path
from types import SimpleNamespace
try:
    import cv2,numpy as np
except ImportError:
    cv2=np=None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))

@unittest.skipIf(cv2 is None,'NumPy/OpenCV required')
class FrameEncoding(unittest.TestCase):
    def test_native_png_preserves_rgb_and_has_only_mouth_support(self):
        from frame_encoding import encode_frame,frame_metadata
        frame=np.arange(20*30*3,dtype=np.uint8).reshape(20,30,3)
        alpha=np.zeros((8,10,1),np.float32);alpha[2:6,3:8]=.4
        e=SimpleNamespace(source_indices=np.array([0]),bboxes=np.array([[5,4,15,12]]),prepared=[{'alpha':alpha}],manifest={'width':30,'height':20})
        payload=encode_frame(e,0,frame,True)
        decoded=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_UNCHANGED)
        self.assertEqual(decoded.shape,(8,10,4))
        np.testing.assert_array_equal(decoded[:,:,:3],frame[4:12,5:15])
        np.testing.assert_array_equal(decoded[:,:,3],np.where(alpha[:,:,0]>0,255,0))
        self.assertEqual(frame_metadata(e,0,True),{'type':'frame','index':0,'format':'mouth_png','bbox':[5,4,15,12],'canvas':[30,20]})

    def test_gentleman_stays_full_frame_jpeg(self):
        from frame_encoding import encode_frame,frame_metadata
        frame=np.full((20,30,3),100,np.uint8)
        payload=encode_frame(None,0,frame,False)
        self.assertEqual(payload[:2],b'\xff\xd8')
        self.assertEqual(cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_COLOR).shape,frame.shape)
        self.assertEqual(frame_metadata(None,7,False),{'type':'frame','index':7,'format':'full_jpeg'})
