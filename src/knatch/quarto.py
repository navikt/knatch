import os
import math
import argparse
import logging

from knatch import put_with_retries, patch_with_retries

logging.basicConfig(level=logging.INFO)

def get_quarto_files(files: list, dirName: str = None):
  for file in os.listdir(dirName):
      if not dirName:
          if not os.path.isfile(file):
              get_quarto_files(files, file)
          else:
              files.append(file)
      else:
          if not os.path.isfile(dirName + "/" + file):
              get_quarto_files(files, dirName + "/" + file)
          else:
              files.append(dirName + "/" + file)


def batch_upload_quarto(
    quarto_id: str,
    folder: str,
    team_token: str,
    host: str = "datamarkedsplassen.intern.nav.no",
    batch_size: int = 10
):
  if not os.getcwd().endswith(folder):
      os.chdir(folder)

  files = []
  get_quarto_files(files)
  logging.info(f"Uploading {len(files)} files in batches of {batch_size}")
  
  for batch_count in range(math.ceil(len(files) / batch_size)):
      multipart_form_data = {}
      start_batch = batch_count*batch_size
      end_batch = start_batch + batch_size
      for file_path in files[start_batch:end_batch]:
          file_name = os.path.basename(file_path)
          with open(file_path, "rb") as file:
              file_contents = file.read()
              multipart_form_data[file_path] = (file_name, file_contents)

      if batch_count == 0:
          res = put_with_retries(f"https://{host}/quarto/update/{quarto_id}", multipart_form_data, team_token)
      else:
          res = patch_with_retries(f"https://{host}/quarto/update/{quarto_id}", multipart_form_data, team_token)

      res.raise_for_status()
      
      uploaded = end_batch if end_batch < len(files) else len(files)
      logging.info(f"Uploaded {uploaded}/{len(files)} files")

def batch_update():
    parser = argparse.ArgumentParser(description="Knatch - knada batch")
    parser.add_argument("id", type=str, help="the id of the quarto to update")
    parser.add_argument("folder", type=str, help="the folder with files to upload")
    parser.add_argument("token", type=str, help="the team token for authentication")
    parser.add_argument("--host", dest="host", default="datamarkedsplassen.intern.nav.no", help="the api host")
    parser.add_argument("--batch-size", dest="batch_size", default=10, help="the desired batch size")

    args = parser.parse_args()
    batch_upload_quarto(args.id, args.folder, args.token, host=args.host, batch_size=int(args.batch_size))
