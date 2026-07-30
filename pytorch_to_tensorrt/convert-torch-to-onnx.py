import torch
import onnx
import os

# ============================================================
# CHANGE THIS: Import your model
# Example:
# from model import MyModel
# ============================================================
from model import MyModel


# ============================================================
# CHANGE THIS: Path to your PyTorch checkpoint
# ============================================================
CHECKPOINT_PATH = "model.pth"

# ============================================================
# Output ONNX file
# ============================================================
ONNX_OUTPUT = "model.onnx"

# ============================================================
# CHANGE THIS: Create your model
# ============================================================
model = MyModel()

print("Checkpoint:", os.path.abspath(CHECKPOINT_PATH))
print("Exists:", os.path.exists(CHECKPOINT_PATH))
print("Size:", os.path.getsize(CHECKPOINT_PATH))

with open(CHECKPOINT_PATH, "rb") as f:
    print("First 100 bytes:", f.read(100))

# Load weights
checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)

# If checkpoint contains state_dict
if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    model.load_state_dict(checkpoint["state_dict"])
else:
    model.load_state_dict(checkpoint)

model.eval()

# ============================================================
# CHANGE THIS: Dummy input shape
# Example:
# Image Classification -> (1,3,224,224)
# YOLO -> (1,3,640,640)
# ============================================================
dummy_input = torch.randn(1, 3, 224, 224)

# Export
torch.onnx.export(
    model,
    dummy_input,
    ONNX_OUTPUT,
    export_params=True,
    opset_version=17,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={
        "input": {0: "batch_size"},
        "output": {0: "batch_size"},
    },
)

print(f"ONNX model saved to {ONNX_OUTPUT}")

# Verify
onnx_model = onnx.load(ONNX_OUTPUT)
onnx.checker.check_model(onnx_model)

print("ONNX model verified successfully!")