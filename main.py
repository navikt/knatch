import requests
import os
import math
import backoff

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def put_with_retries(url, multipart_form_data, token):
  return requests.put(url, headers={"Authorization": f"Bearer {token}"},
                      files=multipart_form_data)

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def patch_with_retries(url, multipart_form_data, token):
  return requests.patch(url, headers={"Authorization": f"Bearer {token}"},
                        files=multipart_form_data)

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
    folder: str,
    quarto_id: str,
    team_token: str,
    host: str = "datamarkedsplassen.intern.nav.no",
    batch_size: int = 10
):
  if not os.getcwd().endswith(folder):
      os.chdir(folder)

  files = []
  get_quarto_files(files)
  print(f"uploading {len(files)} files in batches of {batch_size}")
  
  for batch_count in range(math.ceil(len(files) / batch_size)):
      multipart_form_data = {}
      start_batch = batch_count*batch_size
      end_batch = start_batch + batch_size
      for file_path in files[start_batch:end_batch]:
          file_name = os.path.basename(file_path)
          with open(file_path, 'rb') as file:
              file_contents = file.read()
              multipart_form_data[file_path] = (file_name, file_contents)

      if batch_count == 0:
          res = put_with_retries(f"https://{host}/quarto/update/{quarto_id}", multipart_form_data, team_token)
      else:
          res = patch_with_retries(f"https://{host}/quarto/update/{quarto_id}", multipart_form_data, team_token)

      res.raise_for_status()
      
      uploaded = end_batch if end_batch < len(files) else len(files)
      print(f"uploaded {uploaded}/{len(files)}")

if __name__ == "__main__":
  batch_upload_quarto("_book", "d7fae699-9852-4367-a136-e6b787e2a5bd", "<token>")
  
