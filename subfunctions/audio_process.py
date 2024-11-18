import edge_tts
from moviepy.editor import VideoFileClip

def tts(input_text, voice, audio_file_path):
    # Function to handle the TTS
    com = edge_tts.Communicate(input_text, voice)
    com.save_sync(audio_file_path)
    return audio_file_path

def audio_output_from_video(video_input, audio_file_path):
    video_clip = VideoFileClip(video_input)
    audio_clip = video_clip.audio

    audio_clip.write_audiofile(audio_file_path)

    # Close the video and audio clip objects to free resources
    video_clip.close()
    audio_clip.close()