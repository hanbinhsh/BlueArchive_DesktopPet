"""Plot measured process working sets and live Three.js resource counts."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
report = json.loads((root / 'test-results/release030-final-soak.json').read_text('utf8'))
assert report['complete'] and report['elapsedSeconds'] >= 1800
samples = report['samples']
minutes = [item['seconds'] / 60 for item in samples]
memory = [sum(process['memoryMiB'] for process in item['metrics']) for item in samples]
gpu_process = [sum(process['memoryMiB'] for process in item['metrics'] if process['type'] == 'GPU') for item in samples]
heap = [(item['diagnostics'].get('heap') or 0) / 2**20 for item in samples]
geometries = [item['diagnostics']['memory']['geometries'] for item in samples]
textures = [item['diagnostics']['memory']['textures'] for item in samples]

fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True, layout='constrained')
fig.suptitle(f'BA Desktop Pet 0.2.10 | Offline 30-minute run | {report["fps"]:.2f} FPS')
axes[0].plot(minutes, memory, label='All Electron processes', color='#2878b5', lw=1.5)
axes[0].plot(minutes, gpu_process, label='GPU process working set (not VRAM)', color='#6f4e9c', lw=1)
axes[0].set_ylabel('Working set / MiB')
axes[1].plot(minutes, heap, label='Renderer JS heap', color='#2c997c', lw=1.5)
axes[1].set_ylabel('Heap / MiB')
axes[2].step(minutes, geometries, label='Geometries', color='#2878b5', lw=1.2, where='post')
axes[2].step(minutes, textures, label='Textures', color='#d97919', lw=1.2, where='post')
axes[2].set_ylabel('Three.js resource count')
axes[2].set_xlabel('Elapsed minutes')
for ax in axes:
    ax.legend(loc='upper right', framealpha=.9)
    ax.grid(alpha=.2)
    ax.set_ylim(bottom=0)
    ax.set_xlim(0, 30)
fig.savefig(root / 'test-results/release030-stability.png', dpi=150)
plt.close(fig)

summary = {
    'seconds': report['elapsedSeconds'], 'fps': report['fps'],
    'cycles': report['cycles'], 'errors': report['errors'],
    'workingSetMiB': report['memoryMiB'],
    'geometryCountRange': [min(geometries), max(geometries)],
    'textureCountRange': [min(textures), max(textures)],
    'rendererHeapMiBRange': [min(heap), max(heap)],
    'note': 'Process working sets are not dedicated GPU VRAM measurements. Resource counts include scene caching.',
}
(root / 'test-results/release030-stability-summary.json').write_text(json.dumps(summary, indent=2), 'utf8')
print(json.dumps(summary, indent=2))
