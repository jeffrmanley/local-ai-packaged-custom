import threading
import uuid
import os
import traceback
from flask import Flask, request, jsonify, send_file

# Explicit imports for better compatibility
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

app = Flask(__name__)

# Track jobs in memory: {job_id: {"status": "in-progress"|"done"|"error", "output_path": "..."}}
jobs = {}

def download_file(url, out_path):
    """Simple helper to download a file from `url` to `out_path`."""
    import requests
    print(f"Downloading: {url}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def process_loop_video(job_id, background_url, media_list, duration):
    try:
        jobs[job_id]["status"] = "in-progress"
        work_dir = f"/app/tmp/{job_id}"
        os.makedirs(work_dir, exist_ok=True)

        # 1) Download background music if provided
        bg_music_path = None
        if background_url:
            bg_music_path = os.path.join(work_dir, "background.mp3")
            download_file(background_url, bg_music_path)

        # 2) Download each media in media_list
        clips = []
        for i, media_url in enumerate(media_list):
            local_path = os.path.join(work_dir, f"clip_{i}.mp4")
            download_file(media_url, local_path)
            clip = VideoFileClip(local_path)
            clips.append(clip)

        # 3) Concatenate or loop the clips to match the requested duration
        final_clip = concatenate_videoclips(clips, method="compose")
        if duration:
            looped_clips = []
            current_time = 0
            while current_time < duration:
                looped_clips.append(final_clip.copy())
                current_time += final_clip.duration
            final_clip = concatenate_videoclips(looped_clips, method="compose")
            if final_clip.duration > duration:
                # Precompute frames and create an ImageSequenceClip at a set fps.
                import numpy as np
                fps = 24
                num_frames = int(duration * fps)
                times = np.linspace(0, duration, num_frames)
                frames = [final_clip.get_frame(t) for t in times]
                new_clip = ImageSequenceClip(frames, fps=fps)
                if final_clip.audio:
                    new_clip = new_clip.set_audio(final_clip.audio.subclipped(0, duration))
                final_clip = new_clip


        # 4) Overlay background music if provided
        if bg_music_path:
            audio = AudioFileClip(bg_music_path)
            # If the audio is shorter than the video, loop it
            if audio.duration < final_clip.duration:
                loop_count = int(final_clip.duration // audio.duration) + 1
                audio = concatenate_audioclips([audio] * loop_count)
            # Trim the audio to exactly match the video's duration
            audio = audio.subclipped(0, final_clip.duration)
            final_clip.audio = audio

        # 5) Write the final video (specify fps)
        output_path = os.path.join(work_dir, "final_output.mp4")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

        final_clip.close()
        for clip in clips:
            clip.close()

        jobs[job_id]["status"] = "done"
        jobs[job_id]["output_path"] = output_path

    except Exception as e:
        print("❌ Error processing video:", e)
        traceback.print_exc()
        jobs[job_id]["status"] = "error"
        jobs[job_id]["output_path"] = None

@app.route("/api/function/video-generation/loop-video", methods=["POST"])
def loop_video():
    """
    Receives JSON like:
    {
      "type": "LoopVideo",
      "data": {
        "background_url": "string",
        "media_list": ["url1", "url2", ...],
        "duration": 20
      }
    }
    """
    payload = request.json
    video_type = payload.get("type")
    data = payload.get("data", {})
    if video_type != "LoopVideo":
        return jsonify({"error": "Invalid type"}), 400

    background_url = data.get("background_url")
    media_list = data.get("media_list", [])
    duration = data.get("duration")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "output_path": None}

    worker = threading.Thread(
        target=process_loop_video,
        args=(job_id, background_url, media_list, duration)
    )
    worker.start()

    return jsonify({"data": {"id": job_id}}), 200

@app.route("/api/function/video-generation/progress/<job_id>", methods=["GET"])
def progress(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Invalid job ID"}), 404
    return jsonify({"data": {"id": job_id, "status": jobs[job_id]["status"]}}), 200

@app.route("/api/function/video-generation/download/<job_id>", methods=["GET"])
def download(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Invalid job ID"}), 404
    if jobs[job_id]["status"] != "done":
        return jsonify({"error": "Video not ready"}), 400

    output_path = jobs[job_id]["output_path"]
    if not output_path or not os.path.exists(output_path):
        return jsonify({"error": "No output found"}), 404

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=False)
