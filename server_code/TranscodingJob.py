import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from anvil.server import http_endpoint, request
import json, boto3
import ffmpeg, pathlib

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
@anvil.server.callable
@anvil.server.background_task
def save_file_loaded(file):
  user = anvil.users.get_user()
  fn = "%s_%s" % (user.get_id(), file.name)
  app_tables.jobs.add_row(file_name=file.name,user=user, file=file)
  print("source file saved for %s %s" % (user.get_id(), file.name))


@anvil.server.http_endpoint('/transcode', authenticate_users=True)
def transcode():
  req_data = request.body_json
  job = {"requester":request.remote_address,"job_data":req_data}
  start_transcode(job)
  job = app_tables.jobs.add_row(user=anvil.users.get_user(), job_details=req_data, in_progress=True)
  #start transcoding job
  start_transcode(job)
  

@anvil.server.background_task
def start_transcode(job):
  job_data = job['job_details']
  #download the file
  try:
    s3 = boto3.client(service_name='s3', 
                    aws_access_key_id=job_data["input"]["credentials"]["accessKeyId"], 
                    aws_secret_access_key=job_data["input"]["credentials"]["secretAccessKey"])
    fp = f"/srv/videos/inputs/{job['user'].get_id()}_{job_data['input']['bucket']}_{job_data['input']['path']}"
    s3.download_file(job_data["input"]["bucket"], job_data["input"]["path"], fp)
  except botocore.exceptions.ClientError as e:
    job['error'] = e.response
    if e.response['Error']['Code'] == "404":
      print("The object does not exist.")
    else:
      print("error getting file")
    return

  #segment the video
  out_seg = f"/srv/videos/segments/{job['user'].get_id()}_{job_data['input']['bucket']}_{job_data['input']['path']}_%d{video_ext}"
  video_ext = pathlib.Path(fp).suffix
  ffmpeg.input(fp).output(out_seg, f='segment', segment_time='10').run()

@anvil.server.background_task
def send_transcode_requests(user, bucket, path):
  

#  livepeer.transcode({
#  input: {
#    type: "s3",
#    endpoint: "https://gateway.storjshare.io",
#    credentials: {
#      accessKeyId: "$ACCESS_KEY_ID",
#      secretAccessKey: "$SECRET_ACCESS_KEY"
#    },
#    bucket: "mybucket",
#    path: "/video/source.mp4"
#  },
#  storage: {
#    type: "s3",
#    endpoint: "https://gateway.storjshare.io",
#    credentials: {
#      accessKeyId: "$ACCESS_KEY_ID",
#      secretAccessKey: "$SECRET_ACCESS_KEY"
#    },
#    bucket: "mybucket"
#  },
#  outputs: {
#    hls: {
#      path: "/samplevideo/hls"
#    },
#    mp4: {
#      path: "/samplevideo/mp4"
#    }
#  },
#  profiles: [
#    {
#      name: "480p",
#      bitrate: 1000000,
#      fps: 30,
#      width: 854,
#      height: 480
#    },
#    {
#      name: "360p",
#      bitrate: 500000,
#      fps: 30,
#      width: 640,
#      height: 360
#    }
#  ]
#});
