#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from PIL import Image, ImageDraw
import io

# Create icons directory
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
if not os.path.exists(ICONS_DIR):
    os.makedirs(ICONS_DIR)

def create_sunny_icon():
    """Create a sunny weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw sun
    draw.ellipse((32, 32, 96, 96), fill=(255, 200, 0))
    
    # Draw rays
    for i in range(8):
        angle = i * 45
        if angle == 0:
            draw.rectangle((96, 58, 120, 70), fill=(255, 200, 0))
        elif angle == 45:
            draw.rectangle((88, 88, 108, 108), fill=(255, 200, 0))
        elif angle == 90:
            draw.rectangle((58, 96, 70, 120), fill=(255, 200, 0))
        elif angle == 135:
            draw.rectangle((20, 88, 40, 108), fill=(255, 200, 0))
        elif angle == 180:
            draw.rectangle((8, 58, 32, 70), fill=(255, 200, 0))
        elif angle == 225:
            draw.rectangle((20, 20, 40, 40), fill=(255, 200, 0))
        elif angle == 270:
            draw.rectangle((58, 8, 70, 32), fill=(255, 200, 0))
        elif angle == 315:
            draw.rectangle((88, 20, 108, 40), fill=(255, 200, 0))
    
    img.save(os.path.join(ICONS_DIR, "sunny.png"))

def create_cloudy_icon():
    """Create a cloudy weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw sun (partially visible)
    draw.ellipse((20, 20, 70, 70), fill=(255, 200, 0))
    
    # Draw cloud
    draw.ellipse((40, 50, 90, 100), fill=(220, 220, 220))
    draw.ellipse((60, 45, 110, 95), fill=(220, 220, 220))
    draw.ellipse((70, 60, 120, 110), fill=(220, 220, 220))
    draw.rectangle((60, 70, 100, 100), fill=(220, 220, 220))
    
    img.save(os.path.join(ICONS_DIR, "cloudy.png"))

def create_overcast_icon():
    """Create an overcast weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw clouds
    draw.ellipse((20, 40, 70, 90), fill=(180, 180, 180))
    draw.ellipse((40, 35, 90, 85), fill=(180, 180, 180))
    draw.ellipse((60, 50, 110, 100), fill=(180, 180, 180))
    draw.rectangle((40, 60, 90, 90), fill=(180, 180, 180))
    
    img.save(os.path.join(ICONS_DIR, "overcast.png"))

def create_rain_icon():
    """Create a rain weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw cloud
    draw.ellipse((20, 30, 70, 80), fill=(100, 100, 100))
    draw.ellipse((40, 25, 90, 75), fill=(100, 100, 100))
    draw.ellipse((60, 40, 110, 90), fill=(100, 100, 100))
    draw.rectangle((40, 50, 90, 80), fill=(100, 100, 100))
    
    # Draw raindrops
    for i in range(5):
        x = 30 + i * 20
        y = 90 + (i % 2) * 10
        draw.line((x, y, x - 5, y + 15), fill=(30, 144, 255), width=3)
    
    img.save(os.path.join(ICONS_DIR, "rain.png"))

def create_snow_icon():
    """Create a snow weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw cloud
    draw.ellipse((20, 30, 70, 80), fill=(180, 180, 180))
    draw.ellipse((40, 25, 90, 75), fill=(180, 180, 180))
    draw.ellipse((60, 40, 110, 90), fill=(180, 180, 180))
    draw.rectangle((40, 50, 90, 80), fill=(180, 180, 180))
    
    # Draw snowflakes
    for i in range(5):
        x = 30 + i * 20
        y = 100 + (i % 2) * 10
        
        # Draw a simple snowflake
        draw.line((x - 5, y, x + 5, y), fill=(255, 255, 255), width=2)
        draw.line((x, y - 5, x, y + 5), fill=(255, 255, 255), width=2)
        draw.line((x - 4, y - 4, x + 4, y + 4), fill=(255, 255, 255), width=2)
        draw.line((x - 4, y + 4, x + 4, y - 4), fill=(255, 255, 255), width=2)
    
    img.save(os.path.join(ICONS_DIR, "snow.png"))

def create_fog_icon():
    """Create a fog weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw fog layers
    for i in range(5):
        y = 40 + i * 15
        draw.line((20, y, 108, y), fill=(200, 200, 200), width=8)
    
    img.save(os.path.join(ICONS_DIR, "fog.png"))

def create_haze_icon():
    """Create a haze weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw sun (faded)
    draw.ellipse((32, 32, 96, 96), fill=(255, 200, 0, 128))
    
    # Draw haze layers
    for i in range(5):
        y = 60 + i * 12
        draw.line((20, y, 108, y), fill=(150, 150, 150, 180), width=6)
    
    img.save(os.path.join(ICONS_DIR, "haze.png"))

def create_unknown_icon():
    """Create an unknown weather icon"""
    img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw question mark
    draw.ellipse((32, 32, 96, 96), fill=(200, 200, 200))
    draw.text((55, 45), "?", fill=(0, 0, 0), font_size=40)
    
    img.save(os.path.join(ICONS_DIR, "unknown.png"))

if __name__ == "__main__":
    print("Creating weather icons...")
    create_sunny_icon()
    create_cloudy_icon()
    create_overcast_icon()
    create_rain_icon()
    create_snow_icon()
    create_fog_icon()
    create_haze_icon()
    create_unknown_icon()
    print(f"Icons created successfully in {ICONS_DIR}")
