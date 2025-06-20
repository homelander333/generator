# Create the corrected requirements.txt with proper versions
requirements_content = """# Web Framework
Flask==3.0.3
gunicorn==22.0.0

# Lightweight Text-to-Speech (using gTTS instead of heavy coqui-tts)
gTTS==2.5.3
pyttsx3==2.90

# Video Processing (lightweight alternatives)
opencv-python-headless==4.10.0.84
Pillow==10.4.0

# Audio Processing
pydub==0.25.1

# Web Scraping and Content Processing
requests==2.32.3
beautifulsoup4==4.12.3
newspaper3k==0.2.8
lxml==5.2.2

# Natural Language Processing
nltk==3.8.1

# Utilities
python-dotenv==1.0.1
python-dateutil==2.9.0.post0

# Data handling
PyYAML==6.0.1
"""

# Save to file
with open('requirements.txt', 'w') as f:
    f.write(requirements_content)

print("✅ Updated requirements.txt created with compatible versions")
print("Key changes:")
print("- Replaced coqui-tts==0.17.8 with gTTS==2.5.3 (lightweight, cloud-based)")
print("- Removed moviepy (causes broken pipe errors on Render)")
print("- Added opencv-python-headless for video processing")
print("- Updated all packages to latest stable versions")