import backoff
import requests


@backoff.on_exception(backoff.expo, (requests.exceptions.RequestException, requests.exceptions.HTTPError), max_tries=8)
def put_with_retries(url, multipart_form_data, token):
  return requests.put(url, headers={"Authorization": f"Bearer {token}"},
                      files=multipart_form_data)


@backoff.on_exception(backoff.expo, (requests.exceptions.RequestException, requests.exceptions.HTTPError), max_tries=8)
def patch_with_retries(url, multipart_form_data, token):
  return requests.patch(url, headers={"Authorization": f"Bearer {token}"},
                        files=multipart_form_data)
