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
    self.uploads_in_process = 0
    
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
    anvil.server.call('upload_started',file.name)
    #upload the chunks
    fb = file.get_bytes()
    size = len(fb)
    st = 0
    en = 0
    chunk_cnt = 1
    while en < size:
      if self.uploads_in_process < 5:
        print(f"uploading chunk {chunk_cnt}")
        st = en
        en = min(en+1024*1024*2, size)
        self.upload_file_chunk(anvil.BlobMedia(file.content_type, fb[st:en], name=file.name), chunk_cnt, file.name, st, en)
        self.upload_progress.text = f"{en/size:.0%}"
        chunk_cnt += 1
        self.uploads_in_process += 1
        time.sleep(1)
      else:
        time.sleep(2)
    #signal the chunks are all uploaded and server can combine them
    print(f"upload finished chunks: {chunk_cnt} end: {en} size: {size}")
    anvil.server.call_s('upload_chunk_finished', file.name, size)

  def chunk_upload_complete(self, res):
    print(f"chunk {res} upload complete")
    self.uploads_in_process -= 1 #let other chunks upload
  def chunk_upload_failed(self, res):
    print(f"chunk {res} upload failed")  #TODO: can we do a retry?
    self.uploads_in_process -= 1 #let other chunks upload
  def upload_file_chunk(self, data, chunk, file_name, start, end):
    call_async('upload_chunk', data, chunk, file_name, start, end).on_result(self.chunk_upload_complete, self.chunk_upload_failed)
    
  

  
