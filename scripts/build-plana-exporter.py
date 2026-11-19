"""Build a local exporter with explicit binding of Plana's timeline clips."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / 'tools/asset-downloader/src/ba_downloader/infrastructure/extraction/assetripper/tool'
target = root / '.assets/plana-exporter-source'
shutil.copytree(source, target, ignore=shutil.ignore_patterns('bin', 'obj'), dirs_exist_ok=True)
file = target / 'Models/PlayableGlbAnimationExporter.cs'
code = file.read_text(encoding='utf-8')
needle = '\t\t\tforeach (IUnityObjectBase asset in hierarchyRoot.FetchHierarchy())'
addition = '''
            // Plana's original prefab is driven by a timeline, not a populated
            // animator controller. Bind only its own original clips to its rig.
            if (hierarchyRoot.Name.String == "Plana_Original_Mesh")
            {
                foreach (IAnimationClip clip in hierarchyRoot.Collection.Bundle.FetchAssetsInHierarchy().OfType<IAnimationClip>())
                {
                    string name = clip.Name_C74.String;
                    if (name == "plana_Idle" || name.StartsWith("Plana_Original_AroPla_Cacha_02_", StringComparison.Ordinal))
                    {
                        AnimationBinding binding = new(hierarchyRoot, null, clip);
                        bindings.TryAdd(GetBindingIdentity(binding), binding);
                    }
                }
            }
'''
assert needle in code
file.write_text(code.replace(needle, addition + needle), encoding='utf-8')
overlay = root / '.assets/.ba-downloader/tools/AssetRipper-1ac666f47d8e-overlay-0b8c8b0c7ee62b8de8f9'
dotnet = root / '.cache/dotnet/dotnet.exe'
subprocess.run([str(dotnet) if dotnet.exists() else 'dotnet', 'publish', str(target / 'AssetRipperExporter.csproj'), '-c', 'Release', '-o', str(root / '.assets/plana-exporter'), f'-p:AssetRipperSource={overlay}'], check=True)
