[app]

# -- App metadata
title = DocAssist
package.name = docassist
package.domain = org.docassist
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

# -- Version
version = 1.0.0

# -- Requirements
requirements = python3,
    kivy==2.3.0,
    kivymd,
    pymupdf,
    python-docx,
    numpy,
    scikit-learn,
    pillow,
    certifi,
    charset-normalizer,
    requests,
    urllib3

# -- Android permissions
android.permissions = READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    INTERNET,
    ACCESS_NETWORK_STATE

# -- Android API levels
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# -- Architecture
android.archs = arm64-v8a

# -- Orientation
orientation = portrait

# -- Icons / presplash (add your own assets)
# icon.filename = assets/icon.png
# presplash.filename = assets/presplash.png

# -- Fullscreen
fullscreen = 0

# -- Android features
android.features = android.hardware.touchscreen

# -- Build settings
p4a.branch = master
android.gradle_dependencies = 
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
