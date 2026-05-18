# python3 download.py
import os
import requests

import constants


def download(url: str, filename: str):
  response = requests.get(url)
  if response.status_code == 200:
    with open(filename, "wb") as f:
      f.write(response.content)
    

if __name__ == "__main__":
  for url in [
      constants.QRANK_CSV_URL, 
    ]:
    filename = url.split('/')[-1]
    if not os.path.exists(filename):
      print(f'Downloading {filename} ...')
      download(url, filename)
    else:
      print(f'{filename} already downloaded.')
