import json
from multiprocessing import Process
import subprocess, platform
import MuseTalk.inference_musetalk as musetalk
from subfunctions.audio_process import tts, audio_output_from_video
from moviepy.editor import VideoFileClip
from flask import Flask, request, jsonify, session, send_from_directory
import os
import base64


app = Flask(__name__)
app.static_folder = 'inputs'

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

def encode_images(image_paths):
    encoded_images = []
    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            encoded_images.append(encoded_image)
    return encoded_images

def encode_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")
    return encoded_audio

# Generate a random secret key
app.secret_key = os.urandom(24)

@app.route("/video_upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400
    if file:
        file.save(os.path.join(app.config["UPLOAD_FOLDER"]))
        text = request.form.get("text")
        if not text:
            session["text"] = "" 
            return jsonify({"data": UPLOAD_FOLDER, "text": False}), 200
        session["text"] = text  # Store text in session
        session.modified = True
        return jsonify({"data": UPLOAD_FOLDER, "text": text}), 200

@app.route("/gender/<gender>", methods=["GET"])
def choices(gender):
    text = session.get("text")  # Retrieve text from session
    # gender = request.json.get("gender")
    session["gender"]=gender
    if not gender:
        return jsonify({"message": "Invalid choice"}), 400
    if text:
        if gender == "male":
            return jsonify({"voices": male_voice, "images": male_images}), 200
        elif gender == "female":
            return jsonify({"voices": female_voice, "images": female_images}), 200

    if os.path.exists(UPLOAD_FOLDER):
        audio_output_from_video(UPLOAD_FOLDER,audio_file_path)
        if gender == "male":
            return jsonify({"voices": audio_file_path, "images": male_images}), 200
        elif gender == "female":
            return jsonify({"voices": audio_file_path, "images": female_images}), 200
    return jsonify({"message": "Gender Should be male or female"}), 400

@app.route("/audio_gen", methods=["POST"])
def audio_gen():
    voice = request.json.get("voice_choice")
    text = session.get("text")  # Retrieve text from session
    if voice and text:
        tts_process = Process(target=tts, args=(text, voice, audio_file_path))
        tts_process.start()
        tts_process.join()
        return jsonify({"audio": audio_file_path}), 200
    return jsonify({"message": "Text or voice choice is missing"}), 400

@app.route("/preview", methods=["POST"])
def preview_video_process():
    video_input = UPLOAD_FOLDER
    video_gen_location = request.json.get("video_gen_location")
    avatar = request.json.get("image_choice")
    if not avatar:
        return jsonify({"message": "Avatar choice is missing"}), 400
    session["video_gen_location"] = video_gen_location  # Store video generation location in session

    gender = session.get("gender")
    images = male_images if gender == "male" else female_images

    if avatar not in images:
        return jsonify({"message": "Invalid avatar choice"}), 400
    image_index = images.index(avatar) + 1
    preview_video = f"inputs/faces/{gender}{image_index}.mp4"
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

    return send_from_directory(directory=os.path.dirname(preview_output), path=os.path.basename(preview_output))

@app.route("/generate", methods=["POST"])
def generate_video_process():
        global process_running
        process_running = True
        try:
            while process_running:
                video_input = UPLOAD_FOLDER
                video_gen_location = session.get("video_gen_location")
                selected_Video = session.get("selected_image")
                outfile = "result"
                enchance_video_ouput = "result/output_out.mp4"
                final_output = "result/final_result.mp4"

                musetalk.inference(audio_file_path, selected_Video, final_output, 0)

                if video_gen_location == "Bottom Right":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                    [first][scaled]overlay=W-w--100:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                elif video_gen_location == "Bottom Left":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                    [first][scaled]overlay=-100:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                elif video_gen_location == "Top Right":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                    [first][scaled]overlay=W-w--100:0" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                elif video_gen_location == "Top Left":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/2.5:ih/2.5[scaled];
                    [first][scaled]overlay=-100:0" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                elif video_gen_location == "Right":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned]; [cleaned]scale=iw/1.5:ih/1.5[scaled];  [first][scaled]overlay=W-w/1.4:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                elif video_gen_location == "Left":
                    command = """ffmpeg -i {} -i {} -filter_complex "[0:v]scale=1920:1080[first]; [1:v]scale=1920:1080[second]; [second]colorkey=0x00FF00:0.4:0.05[cleaned];
                    [cleaned]scale=iw/1.5:ih/1.5[scaled];  [first][scaled]overlay=-W/5:H-h" -preset veryslow -map 1:a -c:a copy {} -y""".format(
                        video_input, enchance_video_ouput, final_output
                    )
                else:
                    return jsonify({"message": "Invalid choice"}), 400

                subprocess.call(command, shell=platform.system() != "Windows")
                return send_from_directory(directory=os.path.dirname(final_output), path=os.path.basename(final_output))
            
        finally:
            print("Generated Successfully")

@app.route('/kill_process', methods=['POST'])
def kill_process():
    global process_running
    process_running = False
    return jsonify({"message": "Process killed"}), 200

if __name__ == "__main__":
    app.run(debug=True)