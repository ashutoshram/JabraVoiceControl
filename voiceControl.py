import speech_recognition as sr
from wit import Wit
import webcamPy as wpy
import cv2
import sys
from threading import Thread
from porcupine import Porcupine
import pyaudio
import struct
import soundfile
from datetime import datetime


def recognizeSpeech():
    r = sr.Recognizer()
    m = sr.Microphone()
    try:
        print("A moment of silence, please...")
        with m as source: r.adjust_for_ambient_noise(source)
        print("Set minimum energy threshold to {}".format(r.energy_threshold))
        while True:
            print("Say something!")
            with m as source: audio = r.listen(source)
            print("Got it! Now to recognize it...")
            try:
                # recognize speech using Google Speech Recognition
                value = r.recognize_google(audio)
                #value = "increase the brightness"

                # we need some special handling here to correctly print unicode characters to standard output
                if str is bytes:  # this version of Python uses bytes for strings (Python 2)
                    print(u"You said {}".format(value).encode("utf-8"))
                    return value
                else:  # this version of Python uses unicode for strings (Python 3+)
                    print("You said {}".format(value))
                    return value
            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
            except sr.RequestError as e:
                print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
    except KeyboardInterrupt:
        pass

def requestWit(value):
    w = Wit('W2KZKKR5XRNVB6ZBRN7KH7J5NQK5YQDN')
    resp = w.message(value)
    return resp

def parseResponse(response, cam):
    if response['entities']:
        entities = response['entities']
        property_ = entities['controlProperty']
        print(entities)
        print(property_)
        try:
            action = entities['direction'][0]['value']
            print(action)
            property_ = entities['controlProperty'][0]['value']
            print(property_)
            execute(action, property_, cam)
        except KeyError:
            print("Property cannot be obtained through STT!")
            print("Here was what Wit got:", response)

def execute(action, property_, cam):

    if property_ == 'zoom': 
        if action == 'in':
            current = cam.getCameraControlProperty(property_)[0]
            print(current)
            max_ = cam.getCameraControlProperty(property_)[2]
            new = current + 100
            if new > max_:
                new = max_
            cam.setCameraControlProperty(property_, new)
            print("increased ", property_)

        if action == 'out':
            current = cam.getCameraControlProperty(property_)[0]
            print(current)
            min_ = cam.getCameraControlProperty(property_)[1]
            new = current - 100
            if new < min_:
                new = min_
            cam.setCameraControlProperty(property_, new)
            print("increased ", property_)

    if property_ == 'pan' or property_ == 'tilt':
        print(cam.getCameraControlProperty('zoom'))
        zoom_factor = cam.getCameraControlProperty('zoom')[0]
        if zoom_factor < cam.getCameraControlProperty('zoom')[3]:
            zoom = zoom_factor + 100
            max_ = cam.getCameraControlProperty('zoom')[2]
            if zoom > max_:
                zoom = max_
            cam.setCameraControlProperty('zoom', zoom)

        if property_ == 'tilt':
            if action == 'up':
                print('up')
            if action == 'down':
                print('down')
        if property_ == 'pan':
            if action == 'left':
                print('left')
            if action == 'right':
                print('right')


    if action == 'increase' or action == 'raise':
        current = cam.getCameraControlProperty(property_)[0]
        print(current)
        max_ = cam.getCameraControlProperty(property_)[2]
        new = current + 100
        if new > max_:
            new = max_
        cam.setCameraControlProperty(property_, new)
        print("increased ", property_)
            
    if action == 'decrease' or action == 'lower':
        current = cam.getCameraControlProperty(property_)[0]
        print(current)
        min_ = cam.getCameraControlProperty(property_)[1]
        new = current - 100
        if new < min_:
            new = min_
        cam.setCameraControlProperty(property_, new)
        print("decreased ", property_)

    
def getCam():
    cam = wpy.Webcam()
    if not cam.open(3840, 1080, 30.0, "YUY2"):
        print("PanaCast could not be opened")
        sys.exit(1)
    print("opened Panacast interface!")
    return cam

def showStream(cam):
    while True:
        f = cam.getFrame()
        f = cv2.cvtColor(f, cv2.COLOR_YUV2BGR_YUY2)
        cv2.imshow('whoa', f)
        k = cv2.waitKey(30)
        if k == 27 or k == ord('q'):
            break

def wakeWord(library_path, keyword_file_paths, model_file_path):
        try:
            if not keyword_file_paths:
                raise ValueError('keyword file paths are missing')

            num_keywords = len(keyword_file_paths)

            sensitivities = 0.5
            keyword_file_paths = [x.strip() for x in keyword_file_paths.split(',')]

            if isinstance(sensitivities, float):
                sensitivities = [sensitivities] * len(keyword_file_paths)
            else:
                sensitivities = [float(x) for x in sensitivities.split(',')]
            porcupine = Porcupine(
                library_path=library_path,
                model_file_path=model_file_path,
                keyword_file_paths=keyword_file_paths,
                sensitivities=sensitivities)

            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
                input_device_index=None)

            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)


                result = porcupine.process(pcm)
                if num_keywords == 1 and result:
                    print('[%s] detected keyword' % str(datetime.now()))
                    audio_stream.close()
                    value = recognizeSpeech()
                    response = requestWit(value)
                    parseResponse(response, cam)
                elif num_keywords > 1 and result >= 0:
                    print("0")

        except KeyboardInterrupt:
            print('stopping ...')

if __name__ == "__main__":
    cam = getCam()
    thread = Thread(target=showStream, args=(cam,))
    thread.start()
    value = recognizeSpeech()
    response = requestWit(value)
    parseResponse(response, cam)
    #wakeWord('.\dependz\libpv_porcupine.dll', ".\Jabra_windows.ppn", ".\dependz\porcupine_params.pv")
    
    