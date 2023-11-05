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

  def load_file_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    self.file_name.text = file.name
    upload_task = anvil.server.call_s('save_file_loaded', file)

