import torch
import omegaconf
import sys

try:
    print(f"Torch version: {torch.__version__}")
    print(f"OmegaConf version: {omegaconf.__version__}")
    
    # Check if we can access the classes
    print(f"TorchVersion: {torch.torch_version.TorchVersion}")
    print(f"ListConfig: {omegaconf.listconfig.ListConfig}")
    print(f"DictConfig: {omegaconf.dictconfig.DictConfig}")
    
    print("Imports successful.")
    
    # Check if safe_globals exists (PyTorch 2.6+)
    if hasattr(torch.serialization, 'safe_globals'):
        print("torch.serialization.safe_globals exists.")
    else:
        print("torch.serialization.safe_globals DOES NOT exist.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
