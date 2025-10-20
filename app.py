from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import os, torch, ffmpeg
from diffusers import MotionAdapter, AnimateDiffPipeline, DDIMScheduler
from diffusers.utils import export_to_gif
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Inicializa MotionAdapter + AnimateDiffPipeline ===
print("Carregando MotionAdapter e modelo AnimateDiff...")
adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
model_id = "SG161222/Realistic_Vision_V5.1_noVAE"
pipe = AnimateDiffPipeline.from_pretrained(model_id, motion_adapter=adapter)
scheduler = DDIMScheduler.from_pretrained(
    model_id, subfolder="scheduler", clip_sample=False, timestep_spacing="linspace", steps_offset=1
)
pipe.scheduler = scheduler
pipe.enable_vae_slicing()
pipe.enable_model_cpu_offload()
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
    prompt = request.form.get("prompt", "masterpiece, moving water, ocean waves")
    duration = int(request.form.get("duration", 4))
    speed = float(request.form.get("speed", 1.0))
    task_id = request.form.get("task_id")

    filename = image.filename
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    temp_gif_path = os.path.join(OUTPUT_FOLDER, "temp_" + filename.split('.')[0] + ".gif")
    output_path = os.path.join(OUTPUT_FOLDER, filename.split('.')[0] + ".mp4")
    image.save(input_path)

    num_frames = int(duration * 10)

    # Callback para atualizar progresso
    def progress_callback(frame_index, total_frames):
        progress_dict[task_id] = int((frame_index / total_frames) * 100)

    # Geração da animação
    output = pipe(
        prompt=prompt,
        init_image=input_path,
        num_frames=num_frames,
        motion_field_strength=speed,
        guidance_scale=7.5,
        num_inference_steps=25,
        callback=progress_callback
    )

    frames = output.frames[0]
    export_to_gif(frames, temp_gif_path)

    # Converte GIF para MP4 com resolução 340px
    (
        ffmpeg
        .input(temp_gif_path)
        .filter('scale', -1, 340)
        .output(output_path, pix_fmt='yuv420p', r=30)
        .overwrite_output()
        .run(quiet=True)
    )
    os.remove(temp_gif_path)

    progress_dict.pop(task_id, None)

    return jsonify({"video": f"/outputs/{os.path.basename(output_path)}"})

@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
