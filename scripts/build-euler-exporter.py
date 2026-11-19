"""Add omitted original Unity Euler rotation curves to the local GLB exporter."""
from pathlib import Path
import shutil, subprocess
root = Path(__file__).resolve().parents[1]
source = root/'tools/asset-downloader/src/ba_downloader/infrastructure/extraction/assetripper/tool'
target = root/'.assets/euler-exporter-source'
shutil.copytree(source,target,ignore=shutil.ignore_patterns('bin','obj'),dirs_exist_ok=True)
file = target/'Models/PlayableGlbAnimationExporter.cs'
code = file.read_text(encoding='utf-8')
needle = '\t\tforeach (IVector3Curve curve in clip.ScaleCurves_C74)'
addition = '''
        // Unity's Euler curves are a separate channel, not Quaternion curves.
        // Sample the authored Hermite curve before converting the clip's authored rotation order.
        foreach (IVector3Curve curve in clip.EulerCurves_C74)
        {
            if (clip.RotationCurves_C74.Any(c => c.Path.String == curve.Path.String)) continue;
            if (!TryGetNode(nodes, transforms, curve.Path.String, out NodeBuilder? node)) continue;
            var keys = curve.Curve.Curve.ToArray();
            if (keys.Length == 0) continue;
            float end = keys[^1].Time;
            var times = new SortedSet<float>(keys.Select(k => k.Time));
            for (int i = 0; i <= (int)Math.Ceiling(end * 60); i++) times.Add(Math.Min(end, i / 60f));
            Quaternion? previous = null;
            foreach (float time in times)
            {
                int index = 0;
                while (index + 1 < keys.Length && keys[index + 1].Time <= time) index++;
                Vector3 angles = keys[index].Value.CastToStruct();
                if (index + 1 < keys.Length)
                {
                    var a = keys[index]; var b = keys[index + 1];
                    float span = b.Time - a.Time;
                    float t = Math.Clamp((time - a.Time) / span, 0, 1);
                    Vector3 outgoing = a.OutSlope.CastToStruct(), incoming = b.InSlope.CastToStruct();
                    if (IsFinite(outgoing) && IsFinite(incoming))
                        angles = (2*t*t*t-3*t*t+1)*a.Value.CastToStruct() + (t*t*t-2*t*t+t)*span*outgoing
                            + (-2*t*t*t+3*t*t)*b.Value.CastToStruct() + (t*t*t-t*t)*span*incoming;
                }
                angles *= MathF.PI / 180;
                string order = curve.Curve.RotationOrderE.ToString().Replace("Order", "");
                Quaternion rotation = Quaternion.Identity;
                foreach (char axis in order)
                {
                    Quaternion part = axis switch {
                        'X' => Quaternion.CreateFromAxisAngle(Vector3.UnitX, angles.X),
                        'Y' => Quaternion.CreateFromAxisAngle(Vector3.UnitY, angles.Y),
                        'Z' => Quaternion.CreateFromAxisAngle(Vector3.UnitZ, angles.Z),
                        _ => throw new InvalidOperationException("Unknown Euler rotation order: " + order)
                    };
                    rotation = part * rotation;
                }
                Quaternion value = ConvertQuaternion(rotation);
                if (previous.HasValue && Quaternion.Dot(previous.Value, value) < 0) value = Negate(value);
                node.UseRotation(track).SetPoint(time, Quaternion.Normalize(value), isLinear: true);
                previous = value;
            }
        }
'''
assert needle in code
file.write_text(code.replace(needle,addition+needle),encoding='utf-8')

# Furniture timelines bind student clips at runtime, outside their Animator
# controllers. An explicit offline export manifest supplies only those bindings
# resolved from the original timeline, never a guessed clip-name match.
code = file.read_text(encoding='utf-8')
needle = '\t\treturn bindings.Values'
addition = '''
        string? manifest = Environment.GetEnvironmentVariable("BA_FURNITURE_BINDINGS");
        if (!string.IsNullOrEmpty(manifest))
        {
            var selected = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, string[]>>(File.ReadAllText(manifest))!;
            foreach (IGameObject hierarchyRoot in roots)
            {
                var bundle = hierarchyRoot.Collection.Bundle;
                while (bundle.Parent is not null) bundle = bundle.Parent;
                var clips = bundle.FetchAssets().OfType<IAnimationClip>().ToArray();
                foreach (var animator in hierarchyRoot.FetchHierarchy().OfType<IAnimator>())
                {
                    if (animator.GameObjectP is not { } root || !selected.TryGetValue(root.Name.String, out var names)) continue;
                    foreach (var clip in clips.Where(c => names.Contains(c.Name.String)))
                    {
                        AnimationBinding binding = new(root, animator.AvatarP, clip);
                        bindings.TryAdd(GetBindingIdentity(binding), binding);
                    }
                }
            }
        }
'''
assert needle in code
file.write_text(code.replace(needle,addition+needle),encoding='utf-8')

# Some cafe controllers are first encountered on a stripped scene hierarchy.
# Their globally cached clip conversion still needs the full original avatar
# path table. Keep the opt-in used by complete body exports reproducible.
code = file.read_text(encoding='utf-8')
needle = '''cache = new PathChecksumCache(
\t\t\t\t\tassemblyManager,
\t\t\t\t\t[binding.Root],
\t\t\t\t\tbinding.Avatar is null ? [] : [binding.Avatar]);'''
replacement = '''var sourceBundle = binding.Root.Collection.Bundle;
                while (sourceBundle.Parent is not null) sourceBundle = sourceBundle.Parent;
                var pathAvatars = Environment.GetEnvironmentVariable("BA_COMPLETE_PATH_CACHE") == "1"
                    ? sourceBundle.FetchAssets().OfType<IAvatar>().ToArray()
                    : binding.Avatar is null ? [] : new[] { binding.Avatar };
                cache = new PathChecksumCache(
                    assemblyManager,
                    [binding.Root],
                    pathAvatars);'''
assert needle in code
file.write_text(code.replace(needle,replacement),encoding='utf-8')
overlay=root/'.assets/.ba-downloader/tools/AssetRipper-1ac666f47d8e-overlay-0b8c8b0c7ee62b8de8f9'
subprocess.run([str(root/'.cache/dotnet/dotnet.exe'),'publish',str(target/'AssetRipperExporter.csproj'),'-c','Release','-o',str(root/'.assets/euler-exporter'),f'-p:AssetRipperSource={overlay}'],check=True)
