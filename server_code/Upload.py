import anvil.secrets
import anvil.files
from anvil.files import data_files
import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import os, boto3

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#
@anvil.server.callable(require_user=True)
def get_upload_file_url(filename, content_type):
  s3_client = boto3.client(
      's3',
      aws_access_key_id=anvil.secrets.get_secret('s3_key_id'),
      aws_secret_access_key=anvil.secrets.get_secret('s3_secret_key'),
      region_name="dc1",
      endpoint_url="https://inputs.transcoding.s3.ad-astra.video",
  )
  r = s3_client.generate_presigned_post("inputs", filename)
  # Return the data in the format Uppy needs 
  return {
    'url': r['url'],
    'fields': r['fields'],
    'method': 'POST'
  }
  
@anvil.server.http_endpoint("/upload", authenticate_users=True, methods=['POST'])
def upload_chunk(**params):
  pass

@anvil.server.background_task()
def combine_chunks(user, file):
  pass
