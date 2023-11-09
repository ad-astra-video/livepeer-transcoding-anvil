from ._anvil_designer import NewJobTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..JobProfiles import JobProfiles
from ..Uploader import Uploader
import anvil.media
from anvil_extras.non_blocking import call_async
import time
from datetime import timedelta

class NewJob(NewJobTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    user_settings = anvil.server.call('get_settings')
    if user_settings:
      self.transcoding_profiles.update_profiles(user_settings['profiles'])
    #get user files
    self.file_names.items = anvil.server.call('get_loaded_files')
    #init tracking of uploads
    self.uploads_in_process = 0
    self.uploads_failed = 0
    self.uploads_start = {}
    self.max_uploads = 10
    self.current_uploads = {} #{file.name: {'file':file, 'bytes':bytes}
    
  def load_file_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    self.file_names.text = "uploading..."
    anvil.server.call_s('save_file_loaded', file)    
            
  def start_transcoding_click(self, **event_args):
    """This method is called when the button is clicked"""
    profiles = self.transcoding_profiles.get_profiles()
    fn = ""
    if self.load_file.file != None:
      fn = self.load_file.file.name
    else:
      fn = self.file_names.selected_value
      
    if fn != "":
      anvil.server.call('start_transcoding_job', fn, profiles)
    else:
      alert("transcoding did not start, no file selected")

  def upload_files_click(self, **event_args):
    """This method is called when the button is clicked"""
    alert(
      content=Uploader(),
      title="Update Files",
      large=True
    )

  def file_loader_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    #signal upload started
    start_upload(file)
    
    #upload the chunks
    fb = file.get_bytes()
    size = len(fb)
    end = 0
    chunk_cnt = 1
    while end < size:
      if self.uploads_in_process < self.max_uploads:
        print(f"uploading chunk {chunk_cnt}")
        chunk = self.get_chunk(file.name, chunk_cnt)
        end = chunk["end"]
        self.upload_file_chunk(chunk['data'], chunk_cnt, file.name, chunk['start'], chunk['end'], chunk['size'])
        chunk_cnt += 1
        time.sleep(.5)
      else:
        time.sleep(2)

  def chunk_upload_complete(self, res):
    print(f"chunk {res} upload complete")
    self.uploads_in_process -= 1 #let other chunks upload
    #dynamically adjust max uploads based on upload time
    took = time.time() - self.uploads_start[res]
    if took < 15:
      self.max_uploads += 2
    else:
      self.max_uploads = min(1, self.max_uploads-4)
    
    if self.uploads_in_process == 0:
      anvil.server.call_s('upload_chunks_finished', file_name, size)
      
  def chunk_upload_failed(self, res):
    print(f"chunk {res} upload failed")  #TODO: can we do a retry?
    self.uploads_in_process -= 1 #let other chunks upload
    
    fb = file.get_bytes()
    size = len(fb)
    
  def upload_file_chunk(self, data, chunk, file_name, start, end, size):
    self.uploads_start[chunk_cnt] = time.time()
    call_async('upload_chunk', data, chunk, file_name, start, end).on_result(self.chunk_upload_complete, self.chunk_upload_failed)
    self.uploads_in_process += 1
    self.upload_progress.text = f"{en/size:.0%}"

  def start_upload(self, file):
    anvil.server.call('upload_started',file.name)
    self.uploads_in_process = 0
    self.uploads_failed = 0
    self.uploads_start = {}
    self.current_uploads[file.name] = {"file":file, "bytes":file.get_bytes()}

  def get_chunk(self, file_name, chunk_num):
    if file_name in self.current_uploads:
      file = self.current_uploads[file_name]["file"]
      fb = self.current_uploads[file_name]["bytes"]
      size = len(fb)
      st = (chunk_num-1)*1024*1024*1
      en = min(chunk_num*1024*1024*1, size)
      return {"data":anvil.BlobMedia(file.content_type, fb[st:en], name=file.name), "start":st, "end":en,"size":size}
      
  

  
