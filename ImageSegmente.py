import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor, SAM2VideoPredictor
import cv2

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
print(f"using device: {device}")

if device.type == "cuda":
    torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
    if torch.cuda.get_device_properties(0).major >= 8:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
elif device.type == "mps":
    print(
        "\nSupport for MPS devices is preliminary. SAM 2 is trained with CUDA and might "
        "give numerically different outputs and sometimes degraded performance on MPS. "
        "See e.g. https://github.com/pytorch/pytorch/issues/84936 for a discussion."
    )

np.random.seed(3)

def show_mask(mask, ax, random_color=False, borders = True):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30/255, 144/255, 255/255, 0.6])
    h, w = mask.shape[-2:]
    mask = mask.astype(np.uint8)
    mask_image =  mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    if borders:
        import cv2
        contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
        contours = [cv2.approxPolyDP(contour, epsilon=0.01, closed=True) for contour in contours]
        mask_image = cv2.drawContours(mask_image, contours, -1, (1, 1, 1, 0.5), thickness=2) 
    ax.imshow(mask_image)

def show_points(coords, labels, ax, marker_size=375):
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)   

def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0, 0, 0, 0), lw=2))    

def show_masks(image, masks, scores, point_coords=None, box_coords=None, input_labels=None, borders=True):
    for i, (mask, score) in enumerate(zip(masks, scores)):
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        show_mask(mask, plt.gca(), borders=borders)
        if point_coords is not None:
            assert input_labels is not None
            show_points(point_coords, input_labels, plt.gca())
        if box_coords is not None:
            show_box(box_coords, plt.gca())
        if len(scores) > 1:
            plt.title(f"Mask {i+1}, Score: {score:.3f}", fontsize=18)
        plt.axis('off')
        plt.show()

def show_masks_on_frame(frame, masks, scores, point_coords=None, box_coords=None, input_labels=None, borders=True):
    for i, (mask, score) in enumerate(zip(masks, scores)):
        # Create a new figure and axis
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Display the frame
        ax.imshow(frame)
        
        # Show the mask on the frame
        show_mask(mask, ax, borders=borders)
        
        # Optionally show points and boxes
        if point_coords is not None:
            assert input_labels is not None
            show_points(point_coords, input_labels, ax)
        if box_coords is not None:
            show_box(box_coords, ax)
        
        # Add title if there are multiple masks
        if len(scores) > 1:
            ax.set_title(f"Mask {i+1}, Score: {score:.3f}", fontsize=18)
        
        # Hide axes
        ax.axis('off')
        
        # Draw the updated frame with masks
        fig.canvas.draw()
        
        # Convert canvas to an image
        frame_with_mask = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        frame_with_mask = frame_with_mask.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        # Close the figure to avoid memory issues
        plt.close(fig)
        
        return frame_with_mask
    

# Load the image and model configuration
sam2_checkpoint = r'D:\OSC\MirwearInterface\sam2\sam2_hiera_large.pt'
model_cfg = r'D:\OSC\MirwearInterface\sam2\sam2_hiera_l.yaml'

predictor = SAM2VideoPredictor.from_pretrained("facebook/sam2-hiera-large")

# Load your video
video_path = r'D:\OSC\MirwearInterface\segmentation\sav_000001.mp4'
cap = cv2.VideoCapture(video_path)

# Define the output video
output_video_path = 'output_segmented_video.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(output_video_path, fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

# Initialize state for video prediction
with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
    state = predictor.init_state(video_path)

    # Process each frame
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Add new prompts and get the output for the current frame
        frame_idx, object_ids, masks = predictor.add_new_points_or_box(state, 'find the boy on the image')

        # Display the masks on the current frame
        frame_with_masks = show_masks_on_frame(frame, masks, scores=[1.0] * len(masks))  # Assuming all scores are 1.0 for simplicity

        # Write the processed frame to the output video
        out.write(frame_with_masks)

        # Optionally show the frame
        # cv2.imshow('Segmented Frame', frame_with_masks)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        frame_idx += 1

    # Propagate prompts throughout the video
    for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
        # Apply masks to the frame
        frame_with_masks = show_masks_on_frame(frame, masks, scores=[1.0] * len(masks))  # Assuming all scores are 1.0 for simplicity
        
        # Write the processed frame to the output video
        out.write(frame_with_masks)

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()