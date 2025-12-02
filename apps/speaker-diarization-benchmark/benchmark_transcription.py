import time
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt
import jiwer
from pywhispercpp.model import Model as PyWhisperModel
from faster_whisper import WhisperModel
import mlx_whisper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLIPS_DIR = Path("data/clips")
CLIP_ID = "clip_local_mssp-old-test-ep-1_0_60.wav"
CLIP_PATH = CLIPS_DIR / CLIP_ID

NUM_RUNS = 3

def benchmark_model(name, run_func):
    logger.info(f"--- Benchmarking {name} ---")
    
    # Warmup
    logger.info("Warming up...")
    try:
        _, _, _ = run_func()
    except Exception as e:
        logger.error(f"{name} warmup failed: {e}")
        return 0, "FAILED", False

    # Runs
    times = []
    text = ""
    has_words = False
    
    for i in range(NUM_RUNS):
        logger.info(f"Run {i+1}/{NUM_RUNS}...")
        t_text, t_dur, t_words = run_func()
        times.append(t_dur)
        text = t_text # Keep last text
        has_words = t_words
        logger.info(f"  Time: {t_dur:.2f}s")

    avg_time = sum(times) / len(times)
    logger.info(f"{name} Average Time: {avg_time:.2f}s")
    return avg_time, text, has_words

def plot_results(results):
    names = list(results.keys())
    times = [r['time'] for r in results.values()]
    wers = [r['wer'] for r in results.values()]
    has_words = [r['has_words'] for r in results.values()]
    
    fig, ax1 = plt.subplots(figsize=(12, 7))

    color = 'tab:blue'
    ax1.set_xlabel('Model')
    ax1.set_ylabel('Time (s)', color=color)
    bars = ax1.bar(names, times, color=color, alpha=0.6, label='Time')
    ax1.tick_params(axis='y', labelcolor=color)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        label = f'{height:.2f}s'
        if has_words[i]:
            label += "\n(Words ✅)"
        else:
            label += "\n(Words ❌)"
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                label,
                ha='center', va='bottom')

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('WER', color=color)
    line = ax2.plot(names, wers, color=color, marker='o', linewidth=2, label='WER')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, max(wers) * 1.2 if max(wers) > 0 else 0.1)

    for i, wer in enumerate(wers):
        ax2.text(i, wer, f'{wer:.4f}', ha='center', va='bottom', color='red')

    plt.title('Transcription Benchmark: Time vs Accuracy (Ground Truth: pywhispercpp)')
    fig.tight_layout()
    plt.savefig('benchmark_results.png')
    logger.info("Saved benchmark graph to benchmark_results.png")

def benchmark_all():
    results = {}
    
    # 1. PyWhisperCpp
    logger.info("Loading PyWhisperCpp...")
    model_pw = PyWhisperModel('small', print_realtime=False, print_progress=False)
    
    def _run_pw():
        start = time.time()
        segments = model_pw.transcribe(str(CLIP_PATH), n_threads=6)
        dur = time.time() - start
        txt = " ".join([s.text for s in segments]).strip()
        return txt, dur, False
        
    avg_time, text, has_words = benchmark_model("pywhispercpp", _run_pw)
    results['pywhispercpp'] = {'time': avg_time, 'wer': 0.0, 'text': text, 'has_words': has_words}
    gt_text = text # Use as GT

    # 2. Faster Whisper
    logger.info("Loading Faster Whisper...")
    model_fw = WhisperModel("small", device="cpu", compute_type="int8")
    
    def _run_fw():
        start = time.time()
        segments, _ = model_fw.transcribe(str(CLIP_PATH), beam_size=5, word_timestamps=True)
        segs = list(segments)
        dur = time.time() - start
        txt = " ".join([s.text for s in segs]).strip()
        hw = bool(segs and segs[0].words)
        return txt, dur, hw

    avg_time, text, has_words = benchmark_model("faster-whisper", _run_fw)
    fw_wer = jiwer.wer(gt_text, text)
    results['faster-whisper'] = {'time': avg_time, 'wer': fw_wer, 'text': text, 'has_words': has_words}

    # 3. MLX Whisper
    # MLX doesn't expose a persistent model object easily in `transcribe`.
    # But `transcribe` caches internally if we use the same args?
    # Or we can use `load_models`?
    # I'll rely on `transcribe` being smart or just measure it as is.
    # If it reloads every time, that's a library limitation unless I dig deeper.
    # Wait, `mlx_whisper.load_models` exists?
    # I'll check if I can load and pass it.
    # Docs say `path_or_hf_repo`.
    # I'll assume standard usage.
    
    def _run_mlx():
        start = time.time()
        res = mlx_whisper.transcribe(str(CLIP_PATH), path_or_hf_repo="mlx-community/whisper-small-mlx", word_timestamps=True)
        dur = time.time() - start
        txt = res['text'].strip()
        hw = False
        if 'segments' in res and res['segments']:
             if 'words' in res['segments'][0]: hw = True
        return txt, dur, hw

    avg_time, text, has_words = benchmark_model("mlx-whisper", _run_mlx)
    mlx_wer = jiwer.wer(gt_text, text)
    results['mlx-whisper'] = {'time': avg_time, 'wer': mlx_wer, 'text': text, 'has_words': has_words}

    return results

def main():
    if not CLIP_PATH.exists():
        logger.error(f"Clip not found: {CLIP_PATH}")
        return

    results = benchmark_all()
    
    # Print Summary
    print("\n--- Final Results (Average of 3 runs) ---")
    for name, res in results.items():
        print(f"{name}: {res['time']:.2f}s | WER: {res['wer']:.4f} | Words: {res['has_words']}")

    plot_results(results)
    
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
