import torch
import time
import nvsmi

while True:

  print(torch.rand(5, 3))

  try:
    nvsmi.get_gpus()
    nvsmi.get_available_gpus()
    nvsmi.get_gpu_processes()
  except :
    print("No nvidia-smi (or other error)...")
  
  print("Cuda is available: " + str(torch.cuda.is_available()))
  
  print("Sleep for 60 seconds...")
  time.sleep(60)
