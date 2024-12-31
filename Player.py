import cv2
import numpy as np
import pygame
from pygame import mixer
import time
import os
from functools import lru_cache

ANSI_COLORS = [
    "\033[30m", "\033[31m", "\033[32m", "\033[33m",
    "\033[34m", "\033[35m", "\033[36m", "\033[37m",
]

ASCII_CHARS = " ░▒▓█"
ASCII_CHARS_LEN = len(ASCII_CHARS) - 1

# Pre-calculate color reference arrays
COLORS_REF = np.array([(0,0,0), (0,0,255), (0,255,0), (0,255,255), 
                       (255,0,0), (255,0,255), (255,255,0), (255,255,255)])

@lru_cache(maxsize=256)
def get_ansi_color_cached(b, g, r):
    distances = np.sqrt(np.sum((COLORS_REF - np.array([b, g, r]))**2, axis=1))
    return ANSI_COLORS[np.argmin(distances)]

def resize_frame(frame, new_width=120):
    height, width = frame.shape[:2]
    aspect_ratio = height/width
    new_height = int(new_width * aspect_ratio * 0.55)
    return cv2.resize(frame, (new_width, new_height))

def frame_to_ascii(frame):
    resized = resize_frame(frame)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # Vectorized ASCII conversion
    ascii_indices = (gray / 255 * ASCII_CHARS_LEN).astype(int)
    ascii_chars = np.array(list(ASCII_CHARS))[ascii_indices]
    
    # Process colors in a vectorized way
    ascii_frame = []
    for i, row in enumerate(resized):
        row_chars = []
        for j, pixel in enumerate(row):
            b, g, r = pixel
            color_code = get_ansi_color_cached(int(b), int(g), int(r))
            row_chars.append(color_code + ascii_chars[i][j])
        ascii_frame.append(''.join(row_chars))
    
    return '\n'.join(ascii_frame) + "\033[0m"

def main():
    video_path = "video.mp4"
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video file")
        return

    pygame.init()
    mixer.init()
    mixer.music.load("audio.mp3")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 0.98/fps
    
    mixer.music.play()
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        start_time = time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
            
        ascii_frame = frame_to_ascii(frame)
        print("\033[H" + ascii_frame)
        
        processing_time = time.time() - start_time
        if processing_time < frame_time:
            time.sleep(frame_time - processing_time)
    
    cap.release()
    mixer.music.stop()
    pygame.quit()

if __name__ == "__main__":
    main()
