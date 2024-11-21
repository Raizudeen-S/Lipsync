import edge_tts
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import os

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
            return False
    else:
        return False
