import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import base64
import cv2
from sam2.build_sam import build_sam2_video_predictor
from jupyter_bbox_widget import BBoxWidget

home = os.getcwd()
home

torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


checkpoint = f"{home}/segment-anything-2/checkpoints/sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"
predictor = build_sam2_video_predictor(model_cfg, checkpoint)