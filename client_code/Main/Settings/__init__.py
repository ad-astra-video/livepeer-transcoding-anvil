from ._anvil_designer import SettingsTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..JobProfiles import JobProfiles
class Settings(SettingsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def save_settings_click(self, **event_args):
    """This method is called when the button is clicked"""
    settings = {"broadcasters":self.broadcaster_urls.text, "profiles": self.transcoding_profiles.get_profiles()}
    anvil.server.call('save_settings', settings)
    self.raise_event("x-close-alert", value=1)
    
