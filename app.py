import json
# from multiprocessing import Process
import subprocess, platform
from inference_musetalk import inference
import subfunctions.audio_process as AP
from flask import Flask, request, jsonify, session, send_from_directory
import os, shutil
from flask_cors import CORS

app = Flask(__name__)
app.static_folder = "results"
app.static_folder = "inputs"
app.config["CORS_HEADERS"] = "Content-Type"
cors = CORS(app, resources={r"*": {"origins": ["http://localhost:3000"]}})
UPLOAD_FOLDER = "inputs/input_video/video.mp4"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
audio_file_path = "inputs/input_audio/audio.wav"
process_running = False
 
with open("inputs/voices.json", "r") as file:
    data = json.load(file)
    male_images = data["thumbnail"]["male_images"]
    female_images = data["thumbnail"]["female_images"]
    male_voice = data["voices"]["male_voice"]
    female_voice = data["voices"]["female_voice"]

app.secret_key = os.urandom(24)
 
@app.route("/inputs/<path:filename>")
def serves_static(filename):
    return app.send_static_file(filename)

@app.route("/results/<path:filename>")
def serve_static(filename):
    print(filename)
    return send_from_directory(app.root_path + "/results/", filename)

@app.route("/video_upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file part", "success": False}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file", "success": False}), 400
    if file:
        file.save(os.path.join(app.config["UPLOAD_FOLDER"]))
        if AP.is_speech(UPLOAD_FOLDER, audio_file_path):
            session["use_text"] = False
            return jsonify({"data": None, "success": True, "message": "Video has transcript", "text": True}), 200
        else:
            session["use_text"] = True
            return jsonify({"data": None, "success": True, "message": "No transcript is present", "text": False}), 200
    return jsonify({"message": "File upload failed", "success": False}), 400
 
@app.route("/text_input", methods=["POST"])
def text_input():
    text = request.json.get("text")  # Get the text from the request
    audio_flag = request.json.get("audio_flag")  # Get the audio_flag from the request
    if text and audio_flag:
        session["text"] = text  # Store the text in the session
        session["use_text"] = True
        return jsonify({"data": {"text": text}, "success": True, "message": "Text input saved successfully"}), 200
    if audio_flag == False:
        session["use_text"] = False
        AP.audio_output_from_video(UPLOAD_FOLDER, audio_file_path)
        return jsonify({"data": None, "success": True, "message": "Using Video Audio"}), 200
    return (jsonify({"message": "Text input is missing", "success": False}),)

@app.route("/gender/<gender>", methods=["GET"])  # send text
def choices(gender):
    session["gender"] = gender
    if not gender:
        return jsonify({"message": "Gender is missing", "success": False}), 400
    if gender == "male":
        return jsonify({"data": {"voices": male_voice, "images": male_images}, "success": True, "message": "Male is selected"}), 200
    elif gender == "female":
        return jsonify({"data": {"voices": female_voice, "images": female_images}, "success": True, "message": "Female is selected"}), 200
    return jsonify({"message": "Invalid gender", "success": False}), 400
 
@app.route("/audio_gen", methods=["POST"])
def audio_gen():
    voice = request.json.get("voice_choice")
    text = session.get("text")  # Retrieve text from session
    if voice and text:
        AP.tts(text, voice, audio_file_path)
        flag, video_duration, audio_duration = AP.is_video_audio_same(UPLOAD_FOLDER, audio_file_path)
        if flag:
            return jsonify({"data": {"audio": audio_file_path}, "message": "Audio from Text generated successfully", "success": True}), 200
        else:
            return (
                jsonify(
                    {
                        "data": {"video_length": video_duration, "audio_length": audio_duration},
                        "message": "length of video and audio is not same",
                        "success": False,
                    }
                ),
                400,
            )
    return jsonify({"message": "Text or voice is missing", "success": False}), 400

@app.route("/preview", methods=["POST"])
def preview_video_process():
    video_input = UPLOAD_FOLDER
    video_gen_location = request.json.get("video_gen_location")
    avatar = request.json.get("image_choice")
    if not avatar:
        return jsonify({"message": "Avatar choice is missing"}), 400
 
    # Store video generation location in session
    session["video_gen_location"] = video_gen_location
 
    # Validate and process the avatar choice
    if "inputs/faces/thumbnails/" not in avatar:
        return jsonify({"message": "Invalid avatar choice"}), 400
 
    # Extract the base file name (e.g., male1 from inputs/faces/thumbnails/male1.png)
    avatar_name = avatar.split("/")[-1].split(".")[0]
 
    # Construct the preview video path and store it in the session
    preview_video = f"inputs/faces/{avatar_name}.mp4"
    session["selected_image"] = preview_video
 
    preview_output = "temp/preview.mp4"

    if video_gen_location == "Bottom Right":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
        [first][scaled]overlay=W-w--100:H-h" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )
    elif video_gen_location == "Bottom Left":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
        [first][scaled]overlay=-100:H-h" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )
    elif video_gen_location == "Top Right":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
        [first][scaled]overlay=W-w--100:0" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )
    elif video_gen_location == "Top Left":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
        [first][scaled]overlay=-100:0" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )
    elif video_gen_location == "Right":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
        [cleaned]scale=iw/1.5:ih/1.5[scaled];  [first][scaled]overlay=W/2:H-h" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )
    elif video_gen_location == "Left":
        command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
        [cleaned]scale=iw/1.5:ih/1.5[scaled];  [first][scaled]overlay=-W/5:H-h" -c:a copy -t 10 {} -y""".format(
            video_input, preview_video, preview_output
        )

    else:
        return 0

    subprocess.call(command, shell=platform.system() != "Windows")

    return jsonify({"data": {"result": preview_output}, "message": "Preview video generated successfully", "success": True}), 200
 
@app.route("/generate", methods=["POST"])
def generate_video_process():
    global process_running
    process_running = True
    video_gen_location = request.json.get("video_gen_location")
    avatar = request.json.get("image_choice")
    if not avatar:
        return jsonify({"message": "Avatar choice is missing"}), 400
 
    # Store video generation location in session
    session["video_gen_location"] = video_gen_location
 
    # Extract the base file name (e.g., male1 from inputs/faces/thumbnails/male1.png)
    avatar_name = avatar.split("/")[-1].split(".")[0]
 
    # Construct the preview video path and store it in the session
    preview_video = f"inputs/faces/{avatar_name}.mp4"
    session["selected_image"] = preview_video
 
    try:
        video_input = UPLOAD_FOLDER
        selected_Video = session.get("selected_image")
        enchance_video_output = "inputs/input_video/outputxxx_men1_audio.mp4"
        final_output = "results/final_result.mp4"
 
        enchance_video_output = inference(selected_Video,audio_file_path, 0)
 
        if video_gen_location == "Bottom Right":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                [first][scaled]overlay=W-w--100:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Bottom Left":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                [first][scaled]overlay=-100:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Top Right":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                [first][scaled]overlay=W-w--100:0" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Top Left":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                [first][scaled]overlay=-100:0" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Right":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
                [cleaned]scale=iw:ih[scaled];  [first][scaled]overlay=W-w/1.4:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Left":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
                [cleaned]scale=iw:ih[scaled];  [first][scaled]overlay=-w/3.5:0" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
        elif video_gen_location == "Center":
            command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080:force_original_aspect_ratio=decrease[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
                [cleaned]scale=iw:ih[scaled]; [first][scaled]overlay=(W-w)/2:(H-h)/2" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                video_input, enchance_video_output, final_output
            )
 
        else:
            return jsonify({"message": "Invalid choice"}), 400
 
        subprocess.call(command, shell=platform.system() != "Windows")
 
        AP.empty_folder("inputs/wav2lip_out")
 
        return jsonify({"data": {"result": final_output}, "message": "Preview video generated successfully", "success": True}), 200
 
    except Exception as e:
        print(e)
        return jsonify({"message": "Preview video generation failed", "success": False}), 400
 
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)