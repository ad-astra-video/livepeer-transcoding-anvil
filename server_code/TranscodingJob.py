import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users, anvil.server, anvil.http
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
  job_details = job['job_details']
  #download the file
  try:
    s3 = boto3.client(service_name='s3', 
                    aws_access_key_id=job_details["input"]["credentials"]["accessKeyId"], 
                    aws_secret_access_key=job_details["input"]["credentials"]["secretAccessKey"])
    fp = f"/srv/videos/inputs/{job['user'].get_id()}_{job_details['input']['bucket']}_{job_details['input']['path']}"
    s3.download_file(job_details["input"]["bucket"], job_details["input"]["path"], fp)
  except botocore.exceptions.ClientError as e:
    job['error'] = e.response
    if e.response['Error']['Code'] == "404":
      print("The object does not exist.")
    else:
      print("error getting file")
    return

  #start watcher that will submit segments for transcoding
  vid_path = pathlib.Path(job_details['input']['path'])
  vid_ext = vid_path.suffix
  vid_fn = f"/srv/videos/segments/{job['user'].get_id()}_{job_details['input']['bucket']}_{vid_path.stem}"
  start_transcode_requests_watcher(job, vid_fn, vid_ext)
  #segment the video
  ffmpeg.input(fp).output(f"{vid_fn}_%d{vid_ext}", f='segment', segment_time='10').run()

@anvil.server.background_task
def start_transcode_requests_watcher(job, vid_fn, vid_ext):
  #give segmenter some time to start up
  time.sleep(10)
  transcodes_in_process = []
  seg_num = 0
  while True:
    if len(transcodes_in_process) <= 5:
      seg = f"{vid_fn}_{seg_num}{vid_ext}"
      if os.path.exists(seg):
        t_proc = send_transcode_request(job, seg, 1)
        transcodes_in_process.append(t_proc)
        seg_num += 1 #move to next segment
      else:
        time.sleep(1) #let segmenter catch up
    else:
      for t in range(0,5):
        t_status = transcodes_in_process[t].get_termination_status()
        if t_status != None:
          if t_status == "completed":
            transcodes_in_process.pop(t)
          else:
            if t_status == "failed":
              transcodes_in_process[t] = send_transcode_request(transcodes_in_process[t].task_state['job'], transcodes_in_process[t].task_state['segment'], transcodes_in_process[t].task_state['attempt'])
            
      
      max_retry = 5
@anvil.server.background_task
def send_transcode_request(job, segment, attempt):
  anvil.server.task_state['segment'] = segment
  anvil.server.task_state['job'] = job
  anvil.server.task_state['attempt'] = attempt
  
  job_data = job['job_details']
  
def add_completed_segment(job, segment, attempts):
  if job['completed_segments'] != None:
    job['completed_segments'].append({"segment":segment, "attempts":attempt})
  else:
    job['completed_segments'] = [].append({"segment":segment, "attempts":attempt})

def add_error_segment(job, segment, attempts):
  if job['error_segments'] != None:
    job['error_segments'].append({"segment":segment, "attempts":attempt})
  else:
    job['error_segments'] = [].append({"segment":segment, "attempts":attempt})

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
