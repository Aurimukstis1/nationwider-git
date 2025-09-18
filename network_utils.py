import boto3
import json
from typing import Optional, List, Tuple
import requests

"""
If you wonder about the choice of Amazon AWS services,
it's because the file sizes of the saves are so stupidly small,
and it nets a virtually ~0$ bill for being stored in the server.

The whole system could technically be rewritten by anyone willing to support a different file host.
And by how the internet works, someone could host the files on their computer and share with open ports. 
"""

_loaded_client = None
_loaded_resource = None
_app_version = None

def load_aws_clients(keys_file="server_keys.json"):
  try:
    with open(keys_file,"r") as f:
      server_key_file = json.load(f)

    aws_access_key_id = server_key_file["api_key"]
    aws_secret_access_key = server_key_file["secret_key"]

  except FileNotFoundError:
    raise RuntimeError(f"X- Keys file not found: {keys_path.resolve()}")
  except json.JSONDecodeError:
    raise RuntimeError("X- Keys file is not valid JSON.")
  except KeyError as exc:
    raise RuntimeError(f"X- Missing expected key in JSON: {exc}")

  # start clients
  s3_client = boto3.client(
    "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
  )
  s3_resource = boto3.resource(
    "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
  )

  return s3_client, s3_resource


def _ensure_clients() -> Tuple[boto3.client, boto3.resources.base.ServiceResource]:
    global _loaded_client, _loaded_resource
    if _loaded_client is None or _loaded_resource is None:
        _loaded_client, _loaded_resource = load_aws_clients()
    return _loaded_client, _loaded_resource


def list_savefiles(bucket_name: str, limit: int = 3) -> List[str]:
    """Return the last `limit` savefile keys from the given S3 bucket."""
    try:
        _, s3_resource = _ensure_clients()
        bucket = s3_resource.Bucket(bucket_name)
        files = [obj.key for obj in bucket.objects.all()]
        return files[-limit:] if files else []
    except Exception as exc:
        print(f"X- Could not fetch saves from bucket '{bucket_name}': {exc}")
        return []


def download_savefile(bucket_name: str, key: str, local_path: str) -> bool:
    """Download a savefile from S3 and store it locally."""
    try:
        s3_client, _ = _ensure_clients()
        with open(local_path, "wb") as writable_file:
            s3_client.download_fileobj(bucket_name, key, writable_file)
        return True
    except Exception as exc:
        print(f"X- Failed to download {key}: {exc}")
        return False


def upload_savefile(bucket_name: str, local_path: str, key: Optional[str] = None) -> bool:
    """Upload a file from local disk to the given S3 bucket."""
    try:
        s3_client, _ = _ensure_clients()
        key = key or Path(local_path).name
        s3_client.upload_file(local_path, bucket_name, key)
        return True
    except Exception as exc:
        print(f"X- Failed to upload {local_path} to {bucket_name}/{key}: {exc}")
        return False

try:
  api_url = f"https://api.github.com/repos/Aurimukstis1/nationwider-git/releases/latest"
  response = requests.get(api_url)
  if response.status_code == 200:
    git_data = response.json()
    _app_version = git_data['tag_name']
  else:
    print(f"X- Failed to fetch releases info, status code {response.status_code}")
except Exception as exc:
  print(exc)