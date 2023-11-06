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
import anvil.media

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

  
