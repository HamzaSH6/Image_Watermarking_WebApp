# Imports
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from pathlib import Path
from PIL import Image
from urllib.request import urlopen
from urllib.parse import urlparse

# Flask Init
app = Flask(__name__)
app.secret_key = "demo_secret_key_123"

# Processed/Output Images Folder
OUTPUT_FOLDER = Path("processed_image")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# Removing Watermark Background Function
def remove_bg(wm_image):
    new_data = []
    for item in wm_image.getdata():
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    wm_image.putdata(new_data)
    return wm_image


# Centering Watermark Function
def centering_watermark(image, watermark_image):
    img_w, img_h = image.size
    wm_w, wm_h = watermark_image.size

    c_x = (img_w - wm_w) // 2
    c_y = (img_h - wm_h) // 2
    return c_x, c_y


# Index Route
@app.route("/")
def index():
    filename = request.args.get("filename")
    return render_template("index.html", filename=filename)


# Upload Main Route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Getting Uploaded Image/Watermark/Type/Transparency Part
        file = request.files['image']
        image_url = request.form.get('image_url')

        watermark = request.files['watermark']
        watermark_url = request.form.get('watermark_url')

        image_type = request.form.get('image_type')
        watermark_transparency = int(request.form.get('watermark_transparency'))

        # Error Handling
        if not file and not image_url:
            flash("Upload an Image First", "error")
            return redirect(url_for("index"))
        if file and image_url:
            flash("Cannot Upload an Image and a Link at the same time", "error")
            return redirect(url_for("index"))
        if not watermark and not watermark_url:
            flash("Upload a Watermark First", "error")
            return redirect(url_for("index"))
        if watermark and watermark_url:
            flash("Cannot Upload a Watermark and a Link at the same time", "error")
            return redirect(url_for("index"))

        # Logic Handling
        if not image_url:
            image = Image.open(file)
        else:
            image = Image.open(urlopen(image_url))
            if image_type in [".jpg", ".jpeg"]:
                image = image.convert("RGB")

        if not watermark_url:
            watermark_image = Image.open(watermark).convert("RGBA")
        else:
            watermark_image = Image.open(urlopen(watermark_url))

        # Main Logic Handling
        if (file or image_url) and (watermark or watermark_url):
            if file:
                if image_type == "automatic":
                    filename = file.filename
                else:
                    filename = Path(file.filename).stem + image_type
            else:
                path = urlparse(image_url).path
                if image_type == "automatic":
                    ext = Path(path).suffix or ".jpg"
                else:
                    ext = image_type
                filename = "downloaded" + ext
            # filename = file.filename
            # watermark_name = watermark.filename

            watermark_image.putalpha(watermark_transparency)
            watermark_image_no_bg = remove_bg(watermark_image)
            c_x, c_y = centering_watermark(image, watermark_image)
            image.paste(watermark_image_no_bg, (c_x, c_y), watermark_image_no_bg)
            image.save(OUTPUT_FOLDER / filename)
            flash("Image Watermarked Successfully!", "success")
            return redirect(url_for("index", filename=filename, file=file))
    return redirect(url_for("index"))


# Show Processed/Output Image Route
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('processed_image', filename)


if __name__ == "__main__":
    app.run(debug=True)
