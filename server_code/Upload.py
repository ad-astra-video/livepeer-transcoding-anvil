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
import anvil.media

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
      aws_secret_access_key=anvil.secrets.get_secret('s3_key_secret'),
      region_name="dc1",
      endpoint_url="https://inputs.transcoding.s3.ad-astra.video:3900",
  )
  r = s3_client.generate_presigned_post("inputs", filename)
  # Return the data in the format Uppy needs 
  return {
    'url': r['url'],
    'fields': r['fields'],
    'method': 'POST'
  }

@anvil.server.callable(require_user=True)
def upload_started(file_name):
  user=anvil.users.get_user()
  job = app_tables.jobs.get(user=user,local_file=file_name)
  if job != None:
    job['uploaded'] = False
    
@anvil.server.callable(require_user=True)
def upload_chunk(data, chunk_num, file_name, start, end):
  user = anvil.users.get_user()
  save_chunk(user, data, chunk_num, file_name, start, end)
  return chunk_num
  
@anvil.server.callable(require_user=True)
def upload_chunks_finished(file_name, size):
  user = anvil.users.get_user()
  combine_chunks(user, file_name, size)

@anvil.server.background_task
def save_chunk(user, data, chunk, file_name, start, end):
  app_tables.fileuploads.add_row(user=user,data=data,chunk=chunk,file_name=file_name,start=start,end=end)
  
@anvil.server.background_task
def combine_chunks(user, file_name, size):
  file = bytearray()
  chunks = app_tables.fileuploads.search(user=user,file_name=file_name)
  c_t = chunks[0]['data'].content_type
  for chunk in chunks:
    file.extend(chunk['data'].get_bytes())
    chunk.delete() #delete file part
  #save the combined file
  job = app_tables.jobs.get(user=user,local_file=file_name)
  if job == None:
    app_tables.jobs.add_row(user=user, local_file=file_name, local_media=anvil.BlobMedia(c_t, bytes(file)),uploaded=True)
    print("file combined and added to db")
  else:
    job.update(local_media=anvil.BlobMedia(c_t, bytes(file)),uploaded=True)
    
    print("file combined and updated in db")
  #with anvil.media.TempFile(chunks[0]['data']) as tmp_file:
  #  with open(tmp_file, "wb") as c_file:
  #    for c in range(1, len(chunks)):
  #      c_file.write(chunks[c]['data'].get_bytes())
  #    #add joined file to db
  #    job = app_tables.jobs.get(user=user,local_file=file_name)
  #    if job == None:
  #      app_tables.jobs.add_row(user=user, local_file=file_name, local_media=anvil.media.from_file(tmp_file))
  #    else:
  #      job['local_media'] = anvil.media.from_file(tmp_file)

@anvil.server.http_endpoint("/upload", authenticate_users=True, methods=['POST'])
def upload_chunk_api(**params):
  pass

