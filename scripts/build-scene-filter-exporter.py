"""Restrict an offline export to explicitly named scene prefabs."""
import shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];source=R/'.assets/euler-exporter-source';target=R/'.assets/scene-filter-exporter-source'
shutil.copytree(source,target,ignore=shutil.ignore_patterns('bin','obj'),dirs_exist_ok=True)
p=target/'PrimaryContent/SelectivePrimaryContentExporter.cs';s=p.read_text(encoding='utf8');needle='string readableName = primary.GetBestName();'
assert needle in s
s=s.replace(needle,needle+'\n            string? sceneNames = Environment.GetEnvironmentVariable("BA_EXPORT_NAME_FILTER");\n            if (!string.IsNullOrEmpty(sceneNames) && !sceneNames.Split(\'|\').Contains(readableName)) continue;')
p.write_text(s,encoding='utf8')
overlay=R/'.assets/.ba-downloader/tools/AssetRipper-1ac666f47d8e-overlay-0b8c8b0c7ee62b8de8f9'
subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),'publish',str(target/'AssetRipperExporter.csproj'),'-c','Release','-o',str(R/'.assets/scene-filter-exporter'),f'-p:AssetRipperSource={overlay}'],check=True)
