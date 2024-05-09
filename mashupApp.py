import smtplib
import urllib
import re
import zipfile
import os
import streamlit as st
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from moviepy.editor import VideoFileClip, concatenate_audioclips
from pytube import YouTube
from pytube.exceptions import PytubeError


def download_videos_and_convert_into_audio(singer, n):
    # Search for music videos related to the singer
    url = "https://www.youtube.com/results?search_query=" + singer + " music video"
    search_query = url.replace(" ", "%20")
    html = urllib.request.urlopen(search_query)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    video_links = [
        "https://www.youtube.com/watch?v=" + video_id for video_id in video_ids
    ]
    video_links = list(set(video_links))  # Remove duplicates

    # Downloading videos and converting them into audio
    videos = []
    idx = 1
    destination = "Video_files"
    print("Downloading...")

    for video_link in video_links:
        if idx > n:
            break
        try:
            yt = YouTube(video_link)
            if yt.length / 60 < 5:
                video = yt.streams.filter(file_extension="mp4", res="360p").first()
                out_file = video.download(output_path=destination)
                basePath, extension = os.path.splitext(out_file)
                videos.append(VideoFileClip(os.path.join(basePath + ".mp4")))
                idx += 1
        except PytubeError:
            continue

    print("Downloaded")


def cut_first_y_sec(singer, n, y):
    print("Processing videos...")
    directory = "Video_files/"
    clips = []

    for filename in os.listdir(directory):
        if filename.endswith(".mp4"):
            file_path = os.path.join(directory, filename)
            clip = VideoFileClip(file_path).subclip(0, y)
            audioclip = clip.audio
            clips.append(audioclip)

    concat = concatenate_audioclips(clips)
    concat.write_audiofile("concat.mp3")
    print("Processing done")


def zipit(file):
    destination = "mashup.zip"
    zip_file = zipfile.ZipFile(destination, "w")
    zip_file.write(file, compress_type=zipfile.ZIP_DEFLATED)
    zip_file.close()
    return destination


def send_email(item, email):
    smtp_port = 587
    smtp_server = "smtp.gmail.com"
    email_from = ""
    pswd = ""
    subject = "Your customized mashup"
    body = """
    Hello!

    Your customized mashup is ready!
    """

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    filename = item
    attachment = open(filename, "rb")
    attachment_package = MIMEBase("application", "octet-stream")
    attachment_package.set_payload((attachment).read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header(
        "Content-Disposition", "attachment; filename= " + filename
    )
    msg.attach(attachment_package)
    text = msg.as_string()

    print("Connecting to server...")
    TIE_server = smtplib.SMTP(smtp_server, smtp_port)
    TIE_server.starttls()
    TIE_server.login(email_from, pswd)
    print("Successfully connected to server")
    print(f"Sending email to: {email}...")
    TIE_server.sendmail(email_from, email, text)
    print(f"Email sent to: {email}")
    TIE_server.quit()
    print("Email sent successfully!")


def create_mashup(singer, num_videos, duration, email):
    download_videos_and_convert_into_audio(singer, num_videos)
    cut_first_y_sec(singer, num_videos, duration)
    file = "concat.mp3"
    zipped_file = zipit(file)
    send_email(zipped_file, email)


with st.form(key="Mashup Form"):
    singer_name = st.text_input(label="Enter Singer's Name", value="")
    num_of_videos = st.number_input(label="Number of Videos to Include", value=0)
    video_duration = st.number_input(
        label="Duration of Each Video (in seconds)", value=0
    )
    user_email = st.text_input(label="Enter Your Email", value="")
    submit_button = st.form_submit_button(label="Create Mashup")

    if submit_button:
        if not singer_name.strip():
            st.error("Please enter the name of the singer.")
        elif int(num_of_videos) == 0:
            st.error("Please select at least one video.")
        elif int(video_duration) == 0:
            st.error("Duration cannot be zero.")
        else:
            with st.spinner(text="Processing your request..."):
                sleep(3)  # Simulating processing time
                folder = "Video_files"
                os.makedirs(folder, exist_ok=True)

                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)

            create_mashup(singer_name, num_of_videos, video_duration, user_email)
            st.success("Success! Your mashup will shortly arrive in your mailbox.")
