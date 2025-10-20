from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import os, torch, ffmpeg
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
from tqdm import tqdm

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Inicializa modelo ReV-Animated com CPU offload para economizar memória ===
print("Carregando MotionAdapter...")
adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")

print("Carregando modelo SD finetuned...")
model_id = "SG161222/Realistic_Vision_V5.1_noVAE"
pipe = AnimateDiffPipeline.from_pretrained(model_id, motion_adapter=adapter)
scheduler = DDIMScheduler.from_pretrained(
    model_id, subfolder="scheduler", clip_sample=False, timestep_spacing="linspace", steps_offset=1
)
pipe.scheduler = scheduler

# Ativa offload para CPU e slicing VAE
pipe.enable_model_cpu_offload()
pipe.enable_vae_slicing()

device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = pipe.to(device)
print(f"Modelo carregado em {device}!")

# Armazena progresso
progress_dict = {}

@app.route("/")
def index():
    return render_template("index.html")

# SSE para progresso
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

    def progress_callback(frame_index, total_frames):
        progress_dict[task_id] = int((frame_index / total_frames) * 100)

    # Geração do vídeo (resolução reduzida para 340px)
    video = pipe(
        prompt=prompt,
        image=input_path,
        num_frames=num_frames,
        motion_field_strength=speed,
        guidance_scale=4.5,
        callback=progress_callback
    )

    # Salva temporário
    video["video"].save(temp_video_path)

    # Converte com ffmpeg para garantir compatibilidade e resolução 340
    (
        ffmpeg
        .input(temp_video_path)
        .filter("scale", 340, -1)
        .output(output_path, vcodec='libx264', pix_fmt='yuv420p', r=15)
        .overwrite_output()
        .run(quiet=True)
    )
    os.remove(temp_video_path)

    # Limpa progresso
    progress_dict.pop(task_id, None)

    return jsonify({"video": f"/outputs/{os.path.basename(output_path)}"})

@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)
