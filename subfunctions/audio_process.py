import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip
import speech_recognition as sr
import os, shutil
 
 
def tts(input_text, voice, audio_file_path):
    # Function to handle the TTS
    com = edge_tts.Communicate(input_text, voice)
    com.save_sync(audio_file_path)
    return audio_file_path
 
 
def audio_output_from_video(video_input, audio_file_path):
    if not os.path.exists(video_input):
        return False
 
    video_clip = VideoFileClip(video_input)
    if video_clip.audio is None:
        print("No audio track found in the video.")
        return False
 
    audio_clip = video_clip.audio
    print(audio_clip, "audio-clipppppp")
    print(audio_file_path, "checkibgg-----")
    audio_clip.write_audiofile(audio_file_path)
 
    # Close the video and audio clip objects to free resources
    video_clip.close()
    audio_clip.close()
 
    return True
 
 
def is_speech(video_input, audio_path):
    if audio_output_from_video(video_input, audio_path):
        # Initialize recognizer
        recognizer = sr.Recognizer()
 
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        # Recognize speech using Google Web Speech API
        try:
            text = recognizer.recognize_google(audio)
            return True
        except sr.UnknownValueError:
            return False
        except sr.RequestError as e:
            return True
    else:
        return False
 
 
def empty_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
 
def is_video_audio_same(video_path, audio_path):
    # Load video and get duration
    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration
    video_clip.close()
 
    # Load audio and get duration
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()
 
    # Print durations for debugging
    print(f"Video duration: {video_duration:.2f} seconds")
    print(f"Audio duration: {audio_duration:.2f} seconds")
 
    # Check if audio duration matches the video duration criteria
    if video_duration >= audio_duration >= (video_duration - 5):
        return True, video_duration, audio_duration
 
    return False, video_duration, audio_duration
 