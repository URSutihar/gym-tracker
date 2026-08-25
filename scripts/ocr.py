#!/usr/bin/env python3
"""OCR a screenshot for the gym tracker.

Wraps macOS Vision framework via a Swift one-liner, falling back to tesseract.
Vision is far more accurate on Apple Watch / Xiaomi UI text than tesseract.

Usage:
    python3 scripts/ocr.py path/to/screenshot.png [--json]
"""
import json
import subprocess
import sys

SWIFT_OCR = r'''
import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("cannot load image\n".data(using: .utf8)!)
    exit(1)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([request])
let wantJSON = CommandLine.arguments.contains("--json")
var out: [Any] = []
for obs in request.results ?? [] {
    guard let top = obs.topCandidates(1).first else { continue }
    let s = top.string
    if wantJSON {
        out.append(["text": s,
                    "x": obs.boundingBox.origin.x,
                    "y": obs.boundingBox.origin.y,
                    "w": obs.boundingBox.size.width,
                    "h": obs.boundingBox.size.height,
                    "conf": top.confidence])
    } else {
        out.append(s)
    }
}
if wantJSON {
    let data = try JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted, .sortedKeys])
    print(String(data: data, encoding: .utf8)!)
} else {
    for s in out { print(s) }
}
'''

def vision_ocr(path, want_json):
    import os
    bin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_vision_bin")
    cmd = [bin_path, path] if os.path.exists(bin_path) else ["swift", "-", path]
    script = SWIFT_OCR + "\n" if not os.path.exists(bin_path) else None
    r = subprocess.run(cmd + (["--json"] if want_json else []),
                       input=script, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None, r.stderr.strip()
    if want_json:
        return json.loads(r.stdout.strip()), None
    return r.stdout.strip(), None


def tesseract_ocr(path):
    r = subprocess.run(["tesseract", path, "stdout", "--psm", "6"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, r.stderr.strip()
    return r.stdout.strip(), None


def main():
    if len(sys.argv) < 2:
        print("usage: python3 scripts/ocr.py <image> [--json]", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    want_json = "--json" in sys.argv

    text, err = vision_ocr(path, want_json)
    if text is None:
        # First swift run compiles; retry once on stale cache race.
        text, err2 = vision_ocr(path, want_json)
        if text is None:
            text, err = tesseract_ocr(path)
            if text is None:
                print(f"VISION_ERR: {err2}\nTESS_ERR: {err}", file=sys.stderr)
                sys.exit(1)
    if want_json:
        print(json.dumps(text, indent=1))
    else:
        print(text)


if __name__ == "__main__":
    main()
