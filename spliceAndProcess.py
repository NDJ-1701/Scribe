# Noah says:
# this file is currently a stub to be integrated once we know the structure of our program.
# the Current functionality is to take a video file path, and spit out slides and audio
# segments from that video file, with the intention that later we would send those
# audio segments to get transcribed prior to creating the document.
# still do to: probably overlap the audio to get better transcription.
#
# example execution of the main function is at the bottom

import os  # for file handling
# this package will have to be installed to the environment to be included.
# to get this package into conda, run from terminal: conda install -c conda-forge moviepy
# pip install moviepy also works if you use pip; added to requirements.txt
from moviepy.video.io.VideoFileClip import VideoFileClip

from typing import List
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# setup for ibm watson transcription service
authenticator = IAMAuthenticator(os.environ.get('API_KEY'))
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)
speech_to_text.set_service_url(os.environ.get('API_URL'))
speech_to_text.set_disable_ssl_verification(True)

# this is just a decimal version of the standard range function
# adapted from https://www.techbeamers.com/python-float-range/#:~:text=Python%20range%20can%20only%20generate,arguments%20are%20of%20integer%20type.
def float_range(start, stop, step):
    while start < stop:
        yield float(start)
        start += step
        start = round(start, 2)


class Segment:
    def __init__(self, start_time, end_time):
        self.startTime = start_time
        self.endTime = end_time
        self.video = None
        self.text = None
        self.audioPath = None
        self.imagePath = None


def createOrCleanOutputFolder(output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    else:
        fileList = [f for f in os.listdir(
            output_dir)]  # jacked from https://stackoverflow.com/questions/1995373/deleting-all-files-in-a-directory-with-python/1995397
        for f in fileList:
            os.remove(os.path.join(output_dir, f))


def generateSlides(clip: VideoFileClip, segments: List[Segment], output_dir):
    for seg in segments:
        slidePath = os.path.join(output_dir, '{}.png'.format(seg.startTime))
        clip.save_frame(slidePath, seg.startTime)
        seg.imagePath = slidePath


def generateAudioClips(clip: VideoFileClip, segments: List[Segment], output_dir):
    # this needs to be done in two loops to avoid assertions from the sub clipping
    for seg in segments:
        seg.video = clip.subclip(seg.startTime, seg.endTime)
    for seg in segments:
        seg.audioPath = output_dir + "/clip_" + str(seg.startTime) + ".mp3"
        seg.video.audio.write_audiofile(seg.audioPath)


def generateTranscriptions(segments: List[Segment]):
    for seg in segments:
        filename = seg.audioPath
        with open(filename, 'rb') as audio_file:
            speech_recognition_results = speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/mp3',
                word_alternatives_threshold=0.9,
				smart_formatting='true'
            ).get_result()

        transcript = []
        for portion in speech_recognition_results['results']:
            # timestamp = portion['word_alternatives'][0]['start_time']
            text = portion['alternatives'][0]['transcript']
            # text_data = dict({'timestamp': timestamp, 'text': text})
            # transcript.append(text_data)
            transcript.append(text)
        seg.text = '. '.join(transcript)
        print("Finished transcription of segment with text:\n", seg.text)


def generateDocument(segments: List[Segment], output_dir):
    # code goes here
    return "path to document would go here"
    # return the path to the generated document, presumably stored in the output_dir


# this function does all the stuff listed at the top of this file.
# based on https://stackoverflow.com/questions/43148590/extract-images-using-opencv-and-python-or-moviepy
def spliceAndProcess(video_name, video_folder, time_increment_seconds=60.0, output_dir='slides'):
    print("video name received", video_name)
    print("video folder received", video_folder)
    # ensure that slide directory exists and is empty
    # this is technically dangerous:
    #   In the finished product we may want to delete dir when we're done, and
    #   bail if dir exists when entering function.
    createOrCleanOutputFolder(output_dir)

    # get video handler and calculate segment times
    fullVideoPath = os.path.join(video_folder, video_name)
    print("full video path", fullVideoPath)
    clip = VideoFileClip(fullVideoPath)
    print("the duration is: ", clip.duration)
    times = list(float_range(0, clip.duration, time_increment_seconds))
    print("the clips are at: ", times)
    times.append(clip.duration)  # add the end time

    # create video segment list to process
    segments = []
    for i in range(0, len(times) - 1):
        segments.append(Segment(times[i], times[i+1]))

    # create image slides
    generateSlides(clip, segments, output_dir)

    # create audio clips
    generateAudioClips(clip, segments, output_dir)

    # create transcriptions of audio
    generateTranscriptions(segments)

    # create document
    pathToDocument = generateDocument(segments, output_dir)

	# clean up the temp folder of data files no longer needed.
	# code goes here

    # finally, give the document path back to calling function to be delivered to user
    return pathToDocument


# example function execution
# movieName = 'testVid.mp4'  # name of the video
# movieFolder = ''  # path to folder containing the video
# outputPath = 'slides'  # temp dir to store the files
# timeIncrement = 90.0  # time per slide in seconds
# spliceAndProcess(movieName, movieFolder, timeIncrement, outputPath)