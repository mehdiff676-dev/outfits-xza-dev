from flask import Flask, request, send_file, jsonify
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import time

app = Flask(__name__)
session = requests.Session()

# Keys stored in RAM with usage limits
API_KEYS = {
    "xza": 9999
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MyBot/1.0)',
}

ICON_URL = "https://ch9ayfa-100.vercel.app/freefire/icons/{}.png"

def is_valid_key(key):
    return key in API_KEYS and API_KEYS[key] > 0

def consume_key(key):
    if API_KEYS[key] > 0:
        API_KEYS[key] -= 1

def fetch_image(id_, size=None):
    if not id_:
        return None
    url = ICON_URL.format(id_)
    for attempt in range(3):
        try:
            r = session.get(url, timeout=10, headers=HEADERS)
            if r.status_code == 200 and r.content:
                img = Image.open(BytesIO(r.content)).convert("RGBA")
                if size:
                    img = img.resize(size, Image.LANCZOS)
                return img
        except Exception as e:
            print(f"⚠️ Error fetching image {id_}: {e}")
            time.sleep(1)
    return None

def filter_valid_ids(items):
    return [i for i in items if isinstance(i, int) and i > 100000000]

def create_composite_with_background(data):
    # Load background
    background_url = "https://iili.io/Kfm8fqu.png"
    try:
        response = session.get(background_url, timeout=10, headers=HEADERS)
        bg = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Error loading background: {e}")
        bg = Image.new("RGBA", (1200, 700), (25, 25, 25, 255))

    bg_w, bg_h = bg.size
    skin_size = (150, 150)

    # Extract info
    account_info = data.get("basicInfo", {})
    profile_info = data.get("profileInfo", {})
    pet_info = data.get("petInfo", {})

    # IDs
    avatar_id = profile_info.get("avatarId")
    clothes = profile_info.get("clothes", [])
    skills = profile_info.get("equipedSkills", [])
    weapons = account_info.get("weaponSkinShows", [])
    pet_id = pet_info.get("id") if pet_info.get("isSelected") else None

    all_items_raw = clothes + skills + weapons
    all_items = filter_valid_ids(all_items_raw)
    if pet_id and pet_id > 100000000:
        all_items.append(pet_id)

    positions = [
        (630, 300),
        (630, 1100),
        (350, 1000),
        (215, 710),
        (350, 425),
        (1060, 715),
        (927, 980),
        (925, 430),
    ]
    if pet_id and pet_id > 100000000:
        positions.append((600, 500))

    # Paste avatar
    avatar_img = fetch_image(avatar_id, size=(140, 140)) if avatar_id else None
    if avatar_img:
        center_pos = (bg_w // 2 - avatar_img.width // 2, 640)
        bg.paste(avatar_img, center_pos, avatar_img)

    # Paste items
    for i in range(min(len(all_items), len(positions))):
        item_id = all_items[i]
        item_img = fetch_image(item_id, size=skin_size)
        if item_img:
            x = positions[i][0] - item_img.width // 2
            y = positions[i][1] - item_img.height // 2
            bg.paste(item_img, (x, y), item_img)

    # ✅ Add watermark text at bottom
    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("arial.ttf", 36)  # لو ما عندك arial.ttf يستخدم الافتراضي
    except:
        font = ImageFont.load_default()
    
    text = "@DeV_Xzanja3"
    text_w, text_h = draw.textsize(text, font=font)
    x = (bg_w - text_w) // 2
    y = bg_h - text_h - 20
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return bg

@app.route("/")
def index():
    return "✅ Free Fire API is running with new GPL TEAM OUTFIT API!"

@app.route("/addky/<key>/<int:limit>")
def add_key(key, limit):
    API_KEYS[key] = limit
    return jsonify({"status": "✅ Key added", "key": key, "limit": limit})

@app.route("/outfit", methods=["GET"])
def render():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if not key or not is_valid_key(key):
        return jsonify({"error": "Unauthorized or invalid key"}), 403

    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    try:
        url = f"https://masry-info.vercel.app/info?uid={uid}"
        r = session.get(url, timeout=20, headers=HEADERS)
        if r.status_code != 200:
            return jsonify({"error": "Failed to fetch player info"}), 502

        data = r.json()
        if not data.get("basicInfo"):
            return jsonify({"error": "Player not found"}), 404

        img = create_composite_with_background(data)
        img_io = BytesIO()
        img.convert("RGB").save(img_io, 'JPEG', quality=80)
        img_io.seek(0)

        consume_key(key)

        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()