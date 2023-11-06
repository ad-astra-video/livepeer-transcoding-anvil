import anvil.files
from anvil.files import data_files
import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users, anvil.server, anvil.http
from anvil.server import http_endpoint, request
import json, pathlib, os
import ffmpeg, boto3
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
@anvil.server.callable
def save_file_loaded(file):
  save_file(file)
  return

@anvil.server.background_task
def save_file(file):
  if not os.path.exists("/srv/videos/inputs"):
    os.makedirs("/srv/videos/inputs", exist_ok=True)
  
  user = anvil.users.get_user()
  fp = f"/srv/videos/inputs/{user.get_id()}_{file.name}"
  print(fp)
  with open(fp, 'wb') as inp:
    inp.write(file.get_bytes())
    print("source file saved for %s %s" % (user.get_id(), file.name))
  #add job to table if does not exist for file
  jobs = app_tables.jobs.search(user=user, local_file=fp)
  if len(jobs) == 0:
    job = app_tables.jobs.add_row(local_file=fp,user=user,uploaded=True)
    print("job added for: %s %s" % (user.get_id(), fp))
  else:
    print("job already exists for: %s %s" % (user.get_id(), fp))

@anvil.server.callable
def get_loaded_files():
    user = anvil.users.get_user()
    user_id = user.get_id()
    jobs = app_tables.jobs.search(user=user)
    file_list = []
    for job in jobs:
      if os.path.exists(job['local_file']):
        fn = job['local_file'].replace('/srv/videos/inputs/'+user_id+"_","")
        file_list.append(fn)
      else:
        print("file does not exist, deleting job for: "+job['local_file'])
        job.delete()
    return file_list
      
@anvil.server.callable
def start_transcoding_job(file_name, profiles):
  user = anvil.users.get_user()
  job_details = {"input": { "type": "local",
                            "filename": f"{user.get_id()}_{file_name}",
                          },
                 "storage": { "type": "local",
                            },
                 "profiles": profiles
                }
  
  job = app_tables.jobs.get(user=user, local_file=file_name, uploaded=True)
  if job != None:
    start_transcode(job)
    return "ok"
  else:
    return "file not available"

@anvil.server.callable
def get_file_info(file_name, as_json=False):
  user = anvil.users.get_user()
  job = app_tables.jobs.get(user=user, local_file=file_name, uploaded=True)
  if job != None:
    try:
      fp = f"/srv/videos/inputs/{user.get_id()}_{file_name}"
      probe = ffmpeg.probe(fp)
      if as_json:
        return probe
      else:
        return json.dumps(probe, indent=4)
    except ffmpeg.Error as e:
      return str(e.stderr)
    except Exception as ee:
      return "file not available"

@anvil.server.http_endpoint('/transcode', authenticate_users=True, methods=['POST'])
def transcode(**params):
  req_data = request.body_json
  job = app_tables.jobs.add_row(user=anvil.users.get_user(), job_details=req_data, in_progress=True, req_url=request.remote_address)
  #start transcoding job
  start_transcode(job)
  
@anvil.server.background_task
def start_transcode(job):
  job_details = job['job_details']
  #download the file
  if not os.path.exists("/srv/videos/segments"):
    os.makedirs("/srv/videos/segments", exist_ok=True)
  if not os.path.exists("/srv/videos/transcoded"):
    os.makedirs("/srv/videos/transcoded", exist_ok=True)

  vid_path = ""
  vid_ext = ""
  vid_fn = ""
  if job_details['input']['type'] == "s3":
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
    vid_path = pathlib.Path(job_details['input']['path'])
    vid_ext = vid_path.suffix
    vid_fn = f"/srv/videos/segments/{job['user'].get_id()}_{job_details['input']['bucket']}_{vid_path.stem}"
  elif job_details['input']['type'] == "local":
    fp = f"/srv/videos/inputs/{job['user'].get_id()}_{job['local_file']}"
    vid_path = pathlib.Path(job['local_file'])
    vid_ext = vid_path.suffix
    vid_fn = f"/srv/videos/segments/{job['user'].get_id()}_{vid_path.stem}"
    
  #start watcher that will submit segments for transcoding
  start_transcode_requests_watcher(job, vid_fn, vid_ext)
  #segment the video
  ffmpeg.input(fp).output(f"{vid_fn}_%d{vid_ext}", f='segment', segment_time='10').run()

@anvil.server.background_task
def start_transcode_requests_watcher(job, vid_fn, vid_ext):
  #give segmenter some time to start up
  time.sleep(10)
  #monitor for files and exit after no file available for 15 seconds
  transcodes_in_process = []
  seg_num = 0
  no_file_available_cnt = 0
  while no_file_available_cnt <= 15:
    if len(transcodes_in_process) <= 5:
      seg = f"{vid_fn}_{seg_num}{vid_ext}"
      if os.path.exists(seg):
        no_file_available_cnt = 0
        t_proc = send_transcode_request(job, seg, 1)
        transcodes_in_process.append(t_proc)
        seg_num += 1 #move to next segment
      else:
        no_file_available_cnt += 1
        time.sleep(1) #let segmenter catch up, exits at 15 seconds
    else:
      for t in range(0,5):
        t_status = transcodes_in_process[t].get_termination_status()
        t_error = transcodes_in_process[t].task_state['error']
        if t_status != None:
          if t_status == "completed":
            transcodes_in_process.pop(t)
          else:
            if t_error != '':
              transcodes_in_process[t] = send_transcode_request(transcodes_in_process[t].task_state['job'], transcodes_in_process[t].task_state['segment'], transcodes_in_process[t].task_state['attempt'] + 1)
      #short pause to allow processing
      time.sleep(1)
            
      
@anvil.server.background_task
def send_transcode_request(job, segment, attempt):
  anvil.server.task_state['segment'] = segment
  anvil.server.task_state['job'] = job
  anvil.server.task_state['attempt'] = attempt
  anvil.server.task_state['error'] = ""
  anvil.server.task_state['retry'] = True
  job_details = job['job_details']
  
  #get segment information
  try:
    probe = get_file_info(segment, as_json=True)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = video_stream['width']
    height = video_stream['height']
    duration = round(probe['format']['duration']*1000, 0)
  except ffmpeg.Error as e:
    print("Error: Could not get file information "+e.stderr)
    anvil.server.task_state['error'] = "could not get segment information"
    add_error_segment(job, segment, attempts)
    return
    
  with open(segment, 'rb') as segment_file:
    data = segment_file.read()
    name_parts = pathlib.Path(segment)
    try:
      transcode_settings = {"manifestID": name_parts.stem,
                            "profiles": job_details['profiles'],
                            "timeoutMultiplier": 4
                           }
      headers = {'Accept':'multipart/mixed','Content-Duration':str(duration),'Content-Resolution':str(width)+"x"+str(height)}
      resp = anvil.http.request("http://127.0.0.1:3935/live/"+name_parts.name, 
                               method="POST",
                               headers = {'Accept':'multipart/mixed','Content-Duration':'10000',
                                          'Content-Resolution':'1920x1080',
                                          'Livepeer-Transcode-Configuration': transcode_settings},
                               data=data,
                               timeout=60)
      #save the transcoded renditions
      if resp.headers['content-type'][:15] =='multipart/mixed':
        transcoded_segment_folder = os.path.dirname(segment.replace("/srv/videos/segments/", "/srv/videos/transcoded/"))
        decoded = MultipartDecoder.from_response(resp)
        for part in decoded.parts:
          disposition = part.headers[b'content-disposition']
          filename = parse_stream_resp_hdr(disposition)['filename']  
          rendition = part.headers[b'rendition-name']
          transcoded_file_name = transcoded_segment_folder+"/"+rendition+"/"+filename
          #make directories for transcoded segments
          if not os.path.exists(transcoded_segment_folder+"/"+rendition):
            os.makedirs(os.path.dirname(transcoded_segment_folder+"/"+rendition), exist_ok=True)
          #get the binary data of the rendition
          rendition = part.content #actual transcoded stream
          with open(transcoded_file_name,'wb') as t:
              t.write(rendition)
        
        #received completed segment add to completed segments
        add_completed_segment(job, transcoded_file_name, attempt)
    except anvil.http.HttpError as e:
      print(f"Segment Transcode Error:  {e.status} {e.content}")
      anvil.server.task_state['error'] = f"{e.status} {e.content}"
  
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
