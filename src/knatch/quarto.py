import os
import math
import argparse
import logging

from knatch import put_with_retries, patch_with_retries

logging.basicConfig(level=logging.INFO)

SIZE_10_MB = 10 * 1024 * 1024


def should_be_ignored(file: str, ignore_extensions: list) -> bool:
  for ext in ignore_extensions:
    if file.endswith(ext):
        return True

  return False

def get_quarto_files(files: dict, dirName: str = None, ignore_extensions: list=[]):
  for file in os.listdir(dirName):
      if should_be_ignored(file, ignore_extensions):
        continue

      if not dirName:
          if not os.path.isfile(file):
              get_quarto_files(files, file, ignore_extensions)
          else:
              if os.path.getsize(file) < SIZE_10_MB:
                files["regular_files"].append(file)
              else:
                files["large_files"].append(file)
      else:
          if not os.path.isfile(dirName + "/" + file):
              get_quarto_files(files, dirName + "/" + file, ignore_extensions)
          else:
              if os.path.getsize(dirName + "/" + file) < SIZE_10_MB:
                files["regular_files"].append(dirName + "/" + file)
              else:
                files["large_files"].append(dirName + "/" + file)


def batch_upload_quarto(
    quarto_id: str,
    folder: str,
    team_token: str,
    host: str = "datamarkedsplassen.intern.nav.no",
    path: str = "quarto/update",
    batch_size: int = 10,
    ignore_extensions: list = [],
):
  if not os.getcwd().endswith(folder):
      os.chdir(folder)

  files = {
    "regular_files": [],
    "large_files": []
  }
  get_quarto_files(files, None, ignore_extensions)

  if len(files["regular_files"]) > 0:
    logging.info(f"Uploading {len(files['regular_files'])} regular files in batches of {batch_size}")
    for batch_count in range(math.ceil(len(files["regular_files"]) / batch_size)):
        multipart_form_data = {}
        start_batch = batch_count*batch_size
        end_batch = start_batch + batch_size
        for file_path in files["regular_files"][start_batch:end_batch]:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                file_contents = file.read()
                multipart_form_data[file_path] = (file_name, file_contents)

        if batch_count == 0:
            res = put_with_retries(f"https://{host}/{path}/{quarto_id}", multipart_form_data, team_token)
        else:
            res = patch_with_retries(f"https://{host}/{path}/{quarto_id}", multipart_form_data, team_token)

        res.raise_for_status()

        uploaded = end_batch if end_batch < len(files["regular_files"]) else len(files["regular_files"])
        logging.info(f"Uploaded {uploaded}/{len(files['regular_files'])} regular files")

  if len(files["large_files"]) > 0:
    logging.info(f"Uploading {len(files['large_files'])} files larger than {SIZE_10_MB} bytes separately")
    for idx, file_path in enumerate(files["large_files"]):
      multipart_form_data = {}
      with open(file_path, "rb") as file:
        file_contents = file.read()
        multipart_form_data[file_path] = (file_name, file_contents)

        if len(files["regular_files"]) == 0 and idx == 0:
            res = put_with_retries(f"https://{host}/{path}/{quarto_id}", multipart_form_data, team_token)
        else:
            res = patch_with_retries(f"https://{host}/{path}/{quarto_id}", multipart_form_data, team_token)

        res.raise_for_status()

        logging.info(f"Uploaded {idx+1}/{len(files['large_files'])} large files")


def batch_update():
    parser = argparse.ArgumentParser(description="Knatch - knada batch")
    parser.add_argument("id", type=str, help="the id of the quarto to update")
    parser.add_argument("folder", type=str, help="the folder with files to upload")
    parser.add_argument("token", type=str, help="the team token for authentication")
    parser.add_argument("--host", dest="host", default="datamarkedsplassen.intern.nav.no", help="the api host")
    parser.add_argument("--path", dest="path", default="quarto/update", help="the api host path")
    parser.add_argument("--batch-size", dest="batch_size", default=10, help="the desired batch size")
    parser.add_argument("--ignore-extensions", dest="ignore_extensions", default=None, help="ignore files with these extensions")

    args = parser.parse_args()
    batch_upload_quarto(
        args.id, 
        args.folder, 
        args.token, 
        host=args.host, 
        path=args.path, 
        batch_size=int(args.batch_size), 
        ignore_extensions=[] if not args.ignore_extensions else args.ignore_extensions.split(",")
    )
