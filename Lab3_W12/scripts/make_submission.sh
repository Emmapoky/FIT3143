#!/bin/bash
# Assembles the Moodle submission folder and zip. No AI declaration is included:
# Taabish prepares and adds that file himself.
set -e
cd "$(dirname "$0")/.."
NAME=FIT3143_Lab3_Submission
rm -rf "$NAME" "$NAME.zip"
mkdir -p "$NAME/supporting"
cp README.md Makefile wsn.h main.c node.c base_station.c common.c Presentation_Slides.pdf "$NAME/"
cp -R caas "$NAME/supporting/caas"
cp -R results scripts tests "$NAME/supporting/"
rm -f "$NAME/supporting/scripts/make_submission.sh"
mkdir -p "$NAME/supporting/graphs" "$NAME/supporting/logs"
cp -R graphs/slides "$NAME/supporting/graphs/slides"
cp graphs/graph*.png "$NAME/supporting/graphs/" 2>/dev/null || true
cp -R graphs/per_type "$NAME/supporting/graphs/per_type" 2>/dev/null || true
cp -R logs/sample logs/tests logs/e1_grid logs/e2_line logs/e3_bs logs/e4_window logs/e5_poll "$NAME/supporting/logs/"
find "$NAME" -name .DS_Store -delete
zip -qr "$NAME.zip" "$NAME"
echo "built $NAME.zip: $(du -h "$NAME.zip" | cut -f1), $(unzip -l "$NAME.zip" | tail -1)"
