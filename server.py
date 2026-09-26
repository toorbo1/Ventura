import os
import requests
from flask import Flask, request, redirect, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

CLIENT_KEY = "ВАШ_CLIENT_KEY"
CLIENT_SECRET = "ВАШ_CLIENT_SECRET"
REDIRECT_URI = "https://toorbo1.github.io/Ventura/"

@app.route('/auth')
def auth():
    url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={CLIENT_KEY}"
        f"&scope=user.info.basic,video.publish"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state=xyz"
    )
    return redirect(url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    res = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    })
    data = res.json()
    session['access_token'] = data.get('access_token')
    session['open_id'] = data.get('open_id')
    return redirect("/")

@app.route('/check')
def check():
    if 'access_token' in session:
        return jsonify({"authorized": True, "username": session.get('open_id')})
    return jsonify({"authorized": False})

@app.route('/upload', methods=['POST'])
def upload():
    if 'access_token' not in session:
        return jsonify({"message": "Не авторизован"}), 401

    video = request.files['video']
    desc = request.form.get('description', '')

    # Инициализация загрузки в TikTok
    init_res = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {session['access_token']}",
            "Content-Type": "application/json"
        },
        json={
            "post_info": {"title": desc, "privacy_level": "PUBLIC_TO_EVERYONE"},
            "source_info": {"source": "FILE_UPLOAD", "video_size": len(video.read()), "chunk_size": len(video.read()), "total_chunk_count": 1}
        }
    )
    video.seek(0)
    upload_url = init_res.json()['data']['upload_url']

    # Загрузка файла
    requests.put(upload_url, data=video.read(), headers={
        "Content-Range": f"bytes 0-{len(video.read())-1}/{len(video.read())}",
        "Content-Type": "video/mp4"
    })
    return jsonify({"message": "Видео опубликовано!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
