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
COLORS_REF = np.array([(0,0,0), (0,0,255), (0,255,0), (0,255,255), 
                       (255,0,0), (255,0,255), (255,255,0), (255,255,255)])

TARGET_FPS = 30  # Set your desired FPS cap here
FRAME_TIME = 1.0 / TARGET_FPS
MAX_FRAME_SKIP = 5  # Maximum number of frames to skip when lagging

@lru_cache(maxsize=512)
def get_ansi_color_cached(b, g, r):
    distances = np.sqrt(np.sum((COLORS_REF - np.array([b, g, r]))**2, axis=1))
    return ANSI_COLORS[np.argmin(distances)]

def resize_frame(frame, new_width=100):
    height, width = frame.shape[:2]
    aspect_ratio = height/width
    new_height = int(new_width * aspect_ratio * 0.55)
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_NEAREST)

@lru_cache(maxsize=1024)
def process_pixel(b, g, r, char):
    color_code = get_ansi_color_cached(int(b), int(g), int(r))
    return color_code + char

def frame_to_ascii(frame):
    resized = resize_frame(frame)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    ascii_indices = (gray / 255 * ASCII_CHARS_LEN).astype(int)
    ascii_chars = np.array(list(ASCII_CHARS))[ascii_indices]
    
    return '\n'.join(''.join(process_pixel(b, g, r, char) 
                    for (b, g, r), char in zip(row, chars_row))
                    for row, chars_row in zip(resized, ascii_chars)) + "\033[0m"

def main():
    video_path = "video.mp4"
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video file")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    
    pygame.init()
    mixer.init()
    mixer.music.load("audio.mp3")
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[?25l")  # Hide cursor
    
    mixer.music.play()
    next_frame_time = time.time()
    frames_behind = 0
    
    try:
        while True:
            current_time = time.time()
            
            if current_time < next_frame_time:
                time.sleep(0.001)
                continue
            
            # Calculate how many frames we're behind
            frames_behind = int((current_time - next_frame_time) / FRAME_TIME)
            
            # Skip frames if we're falling behind
            if frames_behind > 1:
                frames_to_skip = min(frames_behind - 1, MAX_FRAME_SKIP)
                for _ in range(frames_to_skip):
                    cap.read()
                next_frame_time += FRAME_TIME * frames_to_skip
            
            ret, frame = cap.read()
            if not ret:
                break
            
            ascii_frame = frame_to_ascii(frame)
            print(f"\033[H{ascii_frame}", flush=True)
            
            next_frame_time += FRAME_TIME
            
            # Reset timing if we're too far behind
            if frames_behind > MAX_FRAME_SKIP:
                next_frame_time = current_time + FRAME_TIME
    
    finally:
        print("\033[?25h")  # Show cursor
        cap.release()
        mixer.music.stop()
        pygame.quit()

if __name__ == "__main__":
    main()
