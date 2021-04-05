import torch
import time
import os

while True:

  try:
    os.system('nvidia-smi')
    print("Cuda is available: " + str(torch.cuda.is_available()))
    print(torch.randn(10240, 10240, dtype=torch.double, device='cuda'))
  except :
    print("No nvidia-smi (or other error)...")
    
  print("Sleep for 60 seconds...")
  time.sleep(60)
