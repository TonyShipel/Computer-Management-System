from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create a new image with a white background
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a blue rectangle as background
    draw.rectangle([(0, 0), (size, size)], fill='#007bff')
    
    # Add text
    text = "CMS"
    # Calculate font size based on image size
    font_size = int(size * 0.4)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate text position to center it
    x = (size - text_width) / 2
    y = (size - text_height) / 2
    
    # Draw text
    draw.text((x, y), text, fill='white', font=font)
    
    # Ensure the icons directory exists
    os.makedirs('static/icons', exist_ok=True)
    
    # Save the image
    image.save(f'static/icons/{filename}')

# Create icons of different sizes
icons = [
    (16, 'favicon-16x16.png'),
    (32, 'favicon-32x32.png'),
    (180, 'apple-touch-icon.png'),
    (192, 'android-chrome-192x192.png'),
    (512, 'android-chrome-512x512.png')
]

for size, filename in icons:
    create_icon(size, filename)

print("Icons created successfully!") 