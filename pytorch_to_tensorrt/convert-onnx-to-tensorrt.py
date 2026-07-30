import tensorrt as trt
import os

# ======================================================
# Configuration
# ======================================================
ONNX_MODEL = "model.onnx"
ENGINE_FILE = "model.engine"

LOGGER = trt.Logger(trt.Logger.INFO)

# ======================================================
# Build TensorRT Engine
# ======================================================
builder = trt.Builder(LOGGER)
if hasattr(trt, "NetworkDefinitionCreationFlag") and hasattr(trt.NetworkDefinitionCreationFlag, "EXPLICIT_BATCH"):
    network_flags = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(network_flags)
else:
    # Newer TensorRT versions
    network = builder.create_network(0)

parser = trt.OnnxParser(network, LOGGER)

print(f"Loading ONNX model: {ONNX_MODEL}")

with open(ONNX_MODEL, "rb") as model:
    if not parser.parse(model.read()):
        print("Failed to parse ONNX model.")
        for i in range(parser.num_errors):
            print(parser.get_error(i))
        exit(1)

print("ONNX parsed successfully.")

config = builder.create_builder_config()

# Allocate workspace (4 GB)
config.set_memory_pool_limit(
    trt.MemoryPoolType.WORKSPACE,
    4 << 30
)

# Enable FP16 if supported
if builder.platform_has_fast_fp16:
    print("FP16 supported -> enabling FP16")
    config.set_flag(trt.BuilderFlag.FP16)

# Create optimization profile (required if model has dynamic shapes)
profile = builder.create_optimization_profile()

for i in range(network.num_inputs):
    inp = network.get_input(i)
    shape = list(inp.shape)

    if -1 in shape:
        print(f"Dynamic input detected: {inp.name}")

        min_shape = [1 if x == -1 else x for x in shape]
        opt_shape = [4 if x == -1 else x for x in shape]
        max_shape = [8 if x == -1 else x for x in shape]

        profile.set_shape(
            inp.name,
            min=min_shape,
            opt=opt_shape,
            max=max_shape,
        )

config.add_optimization_profile(profile)

print("Building TensorRT engine...")

serialized_engine = builder.build_serialized_network(network, config)

if serialized_engine is None:
    raise RuntimeError("Engine build failed!")

with open(ENGINE_FILE, "wb") as f:
    f.write(serialized_engine)

print(f"\nTensorRT engine saved to: {ENGINE_FILE}")