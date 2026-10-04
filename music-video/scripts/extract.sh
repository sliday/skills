#!/bin/sh
# prefer h3 plate, else lip-sync / kling clip; resample to 24 fps, 1920x1080 (crop-fill)
for sid in $(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('docs/shots.json'))))"); do
  src=clips/${sid}_h3.mp4; [ -f $src ] || src=clips/$sid.mp4; [ -f $src ] || continue
  [ -f frames/$sid/.done ] && [ frames/$sid/.done -nt $src ] && continue
  rm -f frames/$sid/*.jpg 2>/dev/null; mkdir -p frames/$sid
  ffmpeg -v error -y -i $src -vf "fps=24,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" -q:v 2 frames/$sid/%04d.jpg && touch frames/$sid/.done && echo "extracted $sid <- $src"
done
