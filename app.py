from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import os
import torch
from diffusers import StableDiffusionPipeline
import ffmpeg
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Carrega o modelo ReV-Animated
print("Carregando modelo ReV-Animated...")
pipe = StableDiffusionPipeline.from_pretrained(
    "s6yx/ReV_Animated",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
)
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
print("Modelo carregado com sucesso!")

# Armazena progresso
progress_dict = {}

@app.route("/")
def index():
    return render_template("index.html")

# Endpoint para progresso via SSE
@app.route("/progress/<task_id>")
def progress(task_id):
    def generate():
        last_progress = 0
        while last_progress < 100:
            progress = progress_dict.get(task_id, 0)
            if progress != last_progress:
                yield f"data: {progress}\n\n"
                last_progress = progress
        yield "data: 100\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/generate", methods=["POST"])
def generate():
    image = request.files["image"]
    prompt = request.form.get("prompt", "make the image move gently")
    duration = int(request.form.get("duration", 4))
    speed = float(request.form.get("speed", 1.0))
    task_id = request.form.get("task_id")

    filename = image.filename
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    temp_video_path = os.path.join(OUTPUT_FOLDER, "temp_" + filename.split('.')[0] + ".mp4")
    output_path = os.path.join(OUTPUT_FOLDER, filename.split('.')[0] + ".mp4")
    image.save(input_path)

    num_frames = int(duration * 10)

    # Função de callback para atualizar progresso
    def progress_callback(frame_index, total_frames):
        progress_dict[task_id] = int((frame_index / total_frames) * 100)

    # Geração de vídeo
    video = pipe(
        prompt=prompt,
        init_image=input_path,
        num_inference_steps=num_frames,
        strength=0.75,
        guidance_scale=7.5,
        callback=progress_callback
    )

    # Salva vídeo temporário
    video["sample"][0].save(temp_video_path)

    # Converte vídeo com ffmpeg para compatibilidade
    (
        ffmpeg
        .input(temp_video_path)
        .output(output_path, vcodec='libx264', pix_fmt='yuv420p', r=30)
        .overwrite_output()
        .run(quiet=True)
    )
    os.remove(temp_video_path)

    # Remove progresso
    progress_dict.pop(task_id, None)

    return jsonify({"video": f"/outputs/{os.path.basename(output_path)}"})

@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
