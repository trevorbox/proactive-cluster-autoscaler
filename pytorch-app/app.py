import torch
import time

while True:

  print(torch.rand(5, 3))

  try:
    os.system('nvidia-smi')
  except :
    print("No nvidia-smi (or other error)...")
  
  print("Cuda is available: " + str(torch.cuda.is_available()))
  
  print("Sleep for 60 seconds...")
  time.sleep(60)
