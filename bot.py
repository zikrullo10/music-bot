import os
import time
import telebot
from yt_dlp import YoutubeDL

TOKEN = "8709224739:AAEUDkTN_rSAx_1nk3U07poj0t87jIjWuW"
bot = telebot.TeleBot(TOKEN, threaded=True)

media_cache = {}

YTDL_OPTIONS = {
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'concurrent_fragment_downloads': 30,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}


@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, "Salom! Bot tayyor va ishlamoqda 🚀")


@bot.message_handler(content_types=['text'])
def handle_text(message):
  text = message.text.strip()
  if text.startswith('/'):
    return

  if text in media_cache:
    vid_id, aud_id, title = media_cache[text]
    if vid_id and aud_id:
      bot.send_video(message.chat.id, vid_id, caption=f"🎬 {title}")
      bot.send_audio(message.chat.id, aud_id)
    return

  msg = bot.reply_to(
      message, "⚡️ Qabul qilindi, video va toza audio tayyorlanmoqda..."
  )

  try:
    if "http://" in text or "https://" in text:
      ydl_video_opts = YTDL_OPTIONS.copy()
      ydl_video_opts['format'] = 'best[ext=mp4]/best'

      with YoutubeDL(ydl_video_opts) as ydl:
        info = ydl.extract_info(text, download=True)
        video_path = ydl.prepare_filename(info)
        title = info.get('title', 'Media')
        video_id = info['id']

      audio_path = f"downloads/{video_id}.mp3"
      os.system(f'ffmpeg -y -i "{video_path}" -q:a 0 -map a "{audio_path}"')

      with open(video_path, 'rb') as vid:
        sent_video = bot.send_video(message.chat.id, vid, caption=f"🎬 {title}")

      with open(audio_path, 'rb') as aud:
        sent_audio = bot.send_audio(message.chat.id, aud, title=title)

      media_cache[text] = (
          sent_video.video.file_id,
          sent_audio.audio.file_id,
          title,
      )
      bot.delete_message(message.chat.id, msg.message_id)
    else:
      ydl_opts = YTDL_OPTIONS.copy()
      ydl_opts['format'] = 'ba/b'
      ydl_opts['postprocessors'] = [{
          'key': 'FFmpegExtractAudio',
          'preferredcodec': 'mp3',
          'preferredquality': '192',
      }]

      with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{text}", download=True)
        if 'entries' in info:
          video_info = info['entries'][0]
        else:
          video_info = info

        file_id_path = f"downloads/{video_info['id']}.mp3"
        title = video_info.get('title', text)

        with open(file_id_path, 'rb') as audio:
          sent_msg = bot.send_audio(
              message.chat.id,
              audio,
              title=title,
              performer=video_info.get('uploader'),
          )
          media_cache[text] = (None, sent_msg.audio.file_id, title)

      bot.delete_message(message.chat.id, msg.message_id)

  except Exception as e:
    bot.edit_message_text(f"Xatolik yuz berdi: {e}", message.chat.id, msg.message_id)


while True:
  try:
    print("Bot ishlamoqda...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
  except Exception as e:
    print(f"Xatolik: {e}")
    time.sleep(3)

