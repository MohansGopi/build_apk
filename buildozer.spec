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
# kivymd removed (not used in current UI code)
# pymupdf uses the 'fitz' recipe name in p4a
requirements = python3,
    kivy==2.3.0,
    pillow,
    numpy,
    scikit-learn,
    python-docx,
    certifi,
    charset-normalizer,
    requests,
    urllib3,
    pymupdf

# -- Android permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,ACCESS_NETWORK_STATE

# -- Android API levels
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# -- Architecture (arm64-v8a = modern phones, armeabi-v7a = older)
android.archs = arm64-v8a

# -- Orientation
orientation = portrait

# -- Fullscreen
fullscreen = 0

# -- Android features
android.features = android.hardware.touchscreen

# -- p4a bootstrap
p4a.bootstrap = sdl2
p4a.branch = master

# -- Allow backup
android.allow_backup = True

# -- Build settings
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
