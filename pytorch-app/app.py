import torch
import time
import nvsmi

try:
  nvsmi.get_gpus()
  nvsmi.get_available_gpus()
  nvsmi.get_gpu_processes()
except :
  print("No nvidia-smi (or other error)...")

x = torch.rand(5, 3)
print(x)

print("Cuda is available: " + str(torch.cuda.is_available()))

print("Sleep...")
while True:
  time.sleep(1)
