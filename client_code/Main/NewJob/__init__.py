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
    self.file_name.text = "uploading..."
    upload_task = anvil.server.call_s('save_file_loaded', file)
    

  def start_transcoding_click(self, **event_args):
    """This method is called when the button is clicked"""
    profiles = self.get_profiles()
    
    pass

  def get_profiles(self):
    profiles = []
    profiles.append({"name": self.transcoding_profiles.p1_name.text, 
                     "encoder": self.transcoding_profiles.p1_codec.selected_value,
                     "width": self.transcoding_profiles.p1_width.text,
                     "height": self.transcoding_profiles.p1_height.text,
                     "fps": self.transcoding_profiles.p1_fps.text,
                     "quality": self.transcoding_profiles.p1_crf,
                     "av1Preset": self.transcoding_profiles.p1_preset.selected_value,
                     "av1Params": self.transcoding_profiles.p1_params
                    })
    profiles.append({"name": self.transcoding_profiles.p2_name.text, 
                     "encoder": self.transcoding_profiles.p2_codec.selected_value,
                     "width": self.transcoding_profiles.p2_width.text,
                     "height": self.transcoding_profiles.p2_height.text,
                     "fps": self.transcoding_profiles.p2_fps.text,
                     "quality": self.transcoding_profiles.p2_crf,
                     "av1Preset": self.transcoding_profiles.p2_preset.selected_value,
                     "av1Params": self.transcoding_profiles.p2_params
                    })
    profiles.append({"name": self.transcoding_profiles.p3_name.text, 
                     "encoder": self.transcoding_profiles.p3_codec.selected_value,
                     "width": self.transcoding_profiles.p3_width.text,
                     "height": self.transcoding_profiles.p3_height.text,
                     "fps": self.transcoding_profiles.p3_fps.text,
                     "quality": self.transcoding_profiles.p3_crf,
                     "av1Preset": self.transcoding_profiles.p3_preset.selected_value,
                     "av1Params": self.transcoding_profiles.p3_params
                    })
    profiles.append({"name": self.transcoding_profiles.p4_name.text, 
                     "encoder": self.transcoding_profiles.p4_codec.selected_value,
                     "width": self.transcoding_profiles.p4_width.text,
                     "height": self.transcoding_profiles.p4_height.text,
                     "fps": self.transcoding_profiles.p4_fps.text,
                     "quality": self.transcoding_profiles.p4_crf,
                     "av1Preset": self.transcoding_profiles.p4_preset.selected_value,
                     "av1Params": self.transcoding_profiles.p4_params
                    })
    profiles.append({"name": self.transcoding_profiles.p5_name.text, 
                     "encoder": self.transcoding_profiles.p5_codec.selected_value,
                     "width": self.transcoding_profiles.p5_width.text,
                     "height": self.transcoding_profiles.p5_height.text,
                     "fps": self.transcoding_profiles.p5_fps.text,
                     "quality": self.transcoding_profiles.p5_crf,
                     "av1Preset": self.transcoding_profiles.p5_preset.selected_value,
                     "av1Params": self.transcoding_profiles.p5_params
                    })
    return profiles
