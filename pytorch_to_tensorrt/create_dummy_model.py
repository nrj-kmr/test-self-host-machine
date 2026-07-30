import torch
from model import MyModel

model = MyModel()

# Save only the state_dict
torch.save(model.state_dict(), "model.pth")

print("Dummy model saved as model.pth")