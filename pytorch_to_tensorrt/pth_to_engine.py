#!/usr/bin/env python3

import os
import sys

import torch
import onnx
import tensorrt as trt

# ==========================================================
# CHANGE THESE
# ==========================================================

from model import MyModel

CHECKPOINT_PATH = "model.pth"
ONNX_PATH = "model.onnx"
ENGINE_PATH = "model.engine"

# Create your model
model = MyModel()

# Dummy input (CHANGE THIS TO YOUR MODEL INPUT SHAPE)
dummy_input = torch.randn(1, 3, 224, 224)

# ==========================================================
# Load PyTorch weights
# ==========================================================

print("=" * 60)
print("Loading PyTorch checkpoint...")

checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu")

if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    model.load_state_dict(checkpoint["state_dict"])
else:
    model.load_state_dict(checkpoint)

model.eval()

print("Checkpoint loaded successfully.")

# ==========================================================
# Export ONNX
# ==========================================================

print("=" * 60)
print("Exporting ONNX...")

torch.onnx.export(
    model,
    dummy_input,
    ONNX_PATH,
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

print(f"ONNX exported: {ONNX_PATH}")

# ==========================================================
# Verify ONNX
# ==========================================================

print("=" * 60)
print("Verifying ONNX model...")

onnx_model = onnx.load(ONNX_PATH)
onnx.checker.check_model(onnx_model)

print("ONNX verification successful.")

# ==========================================================
# Build TensorRT Engine
# ==========================================================

print("=" * 60)
print("Building TensorRT engine...")

LOGGER = trt.Logger(trt.Logger.INFO)

builder = trt.Builder(LOGGER)

network = builder.create_network(
    1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
)

parser = trt.OnnxParser(network, LOGGER)

with open(ONNX_PATH, "rb") as f:
    if not parser.parse(f.read()):
        print("\nFailed to parse ONNX model.\n")

        for i in range(parser.num_errors):
            print(parser.get_error(i))

        sys.exit(1)

print("ONNX parsed successfully.")

config = builder.create_builder_config()

# Workspace = 4 GB
config.set_memory_pool_limit(
    trt.MemoryPoolType.WORKSPACE,
    4 << 30,
)

# Enable FP16
if builder.platform_has_fast_fp16:
    print("FP16 supported. Enabling FP16.")
    config.set_flag(trt.BuilderFlag.FP16)

# Dynamic input profile
profile = builder.create_optimization_profile()

has_dynamic = False

for i in range(network.num_inputs):

    inp = network.get_input(i)
    shape = list(inp.shape)

    if -1 in shape:

        has_dynamic = True

        min_shape = [1 if x == -1 else x for x in shape]
        opt_shape = [4 if x == -1 else x for x in shape]
        max_shape = [8 if x == -1 else x for x in shape]

        print(f"Dynamic input: {inp.name}")
        print(" Min :", min_shape)
        print(" Opt :", opt_shape)
        print(" Max :", max_shape)

        profile.set_shape(
            inp.name,
            min=min_shape,
            opt=opt_shape,
            max=max_shape,
        )

if has_dynamic:
    config.add_optimization_profile(profile)

serialized_engine = builder.build_serialized_network(
    network,
    config,
)

if serialized_engine is None:
    raise RuntimeError("TensorRT engine build failed.")

with open(ENGINE_PATH, "wb") as f:
    f.write(serialized_engine)

print("=" * 60)
print("SUCCESS!")
print(f"PyTorch : {CHECKPOINT_PATH}")
print(f"ONNX    : {ONNX_PATH}")
print(f"Engine  : {ENGINE_PATH}")
print("=" * 60)