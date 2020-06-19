import os
from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from credentials import API_KEY, API_URL
import json

UPLOAD_FOLDER='./static/media'
ALLOWED_EXTENSIONS = {'wav', 'mp4', 'avi'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'6\x9eL~l\xbb2\xed\xe0&\x08\xbf\xa4@\xc2\x9e'


authenticator = IAMAuthenticator(API_KEY)
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)
speech_to_text.set_service_url(API_URL)
speech_to_text.set_disable_ssl_verification(True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        print(request)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print(file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('processFile',
                                    filename=filename))
    else:
        return render_template("upload.html")

@app.route('/processFile')
def process_file(filename):
    return "file added :)"

@app.route('/getTranscription')
def get_scribe():
    #hardcoded for testing purposes, this will be a parameter of get_scribe and will follow the process file route
    filename = 'clip_0.1.mp3'
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as audio_file:
        speech_recognition_results = speech_to_text.recognize(
            audio=audio_file,
            content_type='audio/mp3',
            word_alternatives_threshold=0.9,
        ).get_result()
    print(json.dumps(speech_recognition_results, indent=2))
    return speech_recognition_results

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def not_found(error):
    return render_template('500.html'), 404

if __name__ == '__main__':
    app.run()
