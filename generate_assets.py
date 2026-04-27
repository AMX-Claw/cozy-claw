import os
from PIL import Image, ImageDraw

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Categories and colors for placeholders
assets = {
    "characters": {
        "ak.png": "blue",
        "mumu.png": "brown",
        "xiaoyu.png": "pink",
        "kora.png": "coral"
    },
    "animals": {
        "cookie.png": "gold",
        "heihei.png": "black",
        "huahua.png": "orange",
        "chicken.png": "yellow",
        "duck.png": "white"
    },
    "tiles": {
        "grass.png": "green",
        "water.png": "cyan",
        "dirt.png": "saddlebrown",
        "floor.png": "wheat",
        "wall.png": "gray"
    },
    "crops": {
        "tomato.png": "red",
        "potato.png": "tan",
        "carrot.png": "orange",
        "tree.png": "darkgreen"
    }
}

for category, items in assets.items():
    cat_dir = os.path.join(base_dir, category)
    os.makedirs(cat_dir, exist_ok=True)
    for filename, color in items.items():
        filepath = os.path.join(cat_dir, filename)
        # Create a simple 16x16 sprite (or 16x64 for 4-frame animation)
        img = Image.new('RGBA', (16, 64), color=(0,0,0,0))
        draw = ImageDraw.Draw(img)
        # Draw 4 frames
        for i in range(4):
            draw.rectangle([0, i*16, 15, i*16+15], fill=color, outline="black")
        img.save(filepath)

print("Generated placeholder sprites.")
