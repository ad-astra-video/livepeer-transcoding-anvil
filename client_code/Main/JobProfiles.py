from ._anvil_designer import JobProfilesTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import json

class JobProfiles(JobProfilesTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    pass
    
  def update_profiles(self, profiles):
    profiles = json.loads(profiles)
    if len(profiles) > 0:
      self.p1_name.text = profiles[0]["name"]
      self.p1_codec.selected_value = profiles[0]["encoder"]
      self.p1_width.text = profiles[0]["width"]
      self.p1_height.text = profiles[0]["height"]
      self.p1_fps.text = profiles[0]["fps"]
      self.p1_crf.text = profiles[0]["quality"]
      self.p1_preset.selected_value = profiles[0]["av1Preset"]
      self.p1_params.text = profiles[0]["av1Params"]
    if len(profiles) > 1:
      self.p2_name.text = profiles[1]["name"]
      self.p2_codec.selected_value = profiles[1]["encoder"]
      self.p2_width.text = profiles[1]["width"]
      self.p2_height.text = profiles[1]["height"]
      self.p2_fps.text = profiles[1]["fps"]
      self.p2_crf.text = profiles[1]["quality"]
      self.p2_preset.selected_value = profiles[1]["av1Preset"]
      self.p2_params.text = profiles[1]["av1Params"]
    if len(profiles) > 2:
      self.p3_name.text = profiles[2]["name"]
      self.p3_codec.selected_value = profiles[2]["encoder"]
      self.p3_width.text = profiles[2]["width"]
      self.p3_height.text = profiles[2]["height"]
      self.p3_fps.text = profiles[2]["fps"]
      self.p3_crf.text = profiles[2]["quality"]
      self.p3_preset.selected_value = profiles[2]["av1Preset"]
      self.p3_params.text = profiles[2]["av1Params"]
    if len(profiles) > 3:
      self.p4_name.text = profiles[3]["name"]
      self.p4_codec.selected_value = profiles[3]["encoder"]
      self.p4_width.text = profiles[3]["width"]
      self.p4_height.text = profiles[3]["height"]
      self.p4_fps.text = profiles[3]["fps"]
      self.p4_crf.text = profiles[3]["quality"]
      self.p4_preset.selected_value = profiles[3]["av1Preset"]
      self.p4_params.text = profiles[3]["av1Params"]
    if len(profiles) > 4:
      self.p5_name.text = profiles[4]["name"]
      self.p5_codec.selected_value = profiles[4]["encoder"]
      self.p5_width.text = profiles[4]["width"]
      self.p5_height.text = profiles[4]["height"]
      self.p5_fps.text = profiles[4]["fps"]
      self.p5_crf.text = profiles[4]["quality"]
      self.p5_preset.selected_value = profiles[4]["av1Preset"]
      self.p5_params.text = profiles[4]["av1Params"]
      
  def get_profiles(self):
    profiles = []
    profiles.append({"name": self.p1_name.text,
                     "encoder": self.p1_codec.selected_value,
                     "width": self.p1_width.text,
                     "height": self.p1_height.text,
                     "fps": self.p1_fps.text,
                     "quality": self.p1_crf.text,
                     "av1Preset": self.p1_preset.selected_value,
                     "av1Params": self.p1_params.text
                    })
    profiles.append({"name": self.p2_name.text, 
                     "encoder": self.p2_codec.selected_value,
                     "width": self.p2_width.text,
                     "height": self.p2_height.text,
                     "fps": self.p2_fps.text,
                     "quality": self.p2_crf.text,
                     "av1Preset": self.p2_preset.selected_value,
                     "av1Params": self.p2_params.text
                    })
    profiles.append({"name": self.p3_name.text, 
                     "encoder": self.p3_codec.selected_value,
                     "width": self.p3_width.text,
                     "height": self.p3_height.text,
                     "fps": self.p3_fps.text,
                     "quality": self.p3_crf.text,
                     "av1Preset": self.p3_preset.selected_value,
                     "av1Params": self.p3_params.text
                    })
    profiles.append({"name": self.p4_name.text, 
                     "encoder": self.p4_codec.selected_value,
                     "width": self.p4_width.text,
                     "height": self.p4_height.text,
                     "fps": self.p4_fps.text,
                     "quality": self.p4_crf.text,
                     "av1Preset": self.p4_preset.selected_value,
                     "av1Params": self.p4_params.text
                    })
    profiles.append({"name": self.p5_name.text, 
                     "encoder": self.p5_codec.selected_value,
                     "width": self.p5_width.text,
                     "height": self.p5_height.text,
                     "fps": self.p5_fps.text.text,
                     "quality": self.p5_crf,
                     "av1Preset": self.p5_preset.selected_value,
                     "av1Params": self.p5_params.text
                    })
    return json.dumps(profiles)
  