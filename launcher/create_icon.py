"""
Script pour générer launcher.ico
Exécuter : python launcher/create_icon.py
"""
from PIL import Image, ImageDraw, ImageFont

# Créer une image 256x256 avec fond bleu foncé
img = Image.new('RGB', (256, 256), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# Dessiner un cercle bleu clair (représentant JARVIS)
draw.ellipse([48, 48, 208, 208], fill='#00b4d8', outline='#0096c7', width=8)

# Dessiner un éclair au centre (symbole ⚡)
try:
    font = ImageFont.truetype("seguisym.ttf", 120)
except:
    font = ImageFont.load_default()

text = "⚡"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (256 - text_width) // 2
y = (256 - text_height) // 2 - 10

draw.text((x, y), text, fill='#ffffff', font=font)

# Sauvegarder en .ico (multiples tailles)
img.save('launcher/launcher.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("✅ launcher/launcher.ico créé")
