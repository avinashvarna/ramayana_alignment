# -*- coding: utf-8 -*-
"""
Align meghaduta text with audio

Text source: text/ - proofread from GRETIL to match audio
Audio: https://archive.org/details/meghadUta-mUlam-vedabhoomi.org

@author: Avinash Varna
"""

import os
import time
import re
import sys
import csv

from urllib.parse import urlparse
from pathlib import Path

from tqdm import tqdm

base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir)

from utils import download_file
try:
    from utils.alignment import align
except ImportError:
    pass


def is_devanagari(char):
    unicode_val = ord(char)
    return unicode_val >= 0x0900 and unicode_val < 0x0980


def clean_text(text):
    lines = []
    for line in text.split('\n'):
        # Skip comments
        if line.startswith('#'):
            continue
        line = line.strip()
        # Only retain portion before । or ॥
        index = line.find(u'॥')
        # If both are present retain first
        # If neither was found, then retain entire line
        if index == -1:
            index = len(line)
        line = line[:index]

        if line != '':
            lines.append(line)

    return lines


def parse_and_clean_text(input_path, output_path):
    ''' Clean the text and write it to the output_path. Return url of audio '''
    with open(input_path, encoding='utf-8') as f:
        text = f.read()
    lines = clean_text(text)
    with open(output_path, mode='w', encoding='utf8') as f:
        f.write('\n'.join(lines))
        f.write('\n')
    m = re.search('# (.*?)\n', text, flags=re.DOTALL)
    url = m.group(1).replace('\n','')
    return url


def parse_files(text_src_dir, clean_text_dir):
    ''' Clean text source files, write them to clean_text_dir,
        and return list of (text, url) tuples

    '''
    os.makedirs(clean_text_dir, exist_ok=True)

    text_url_map = []
    for entry in os.scandir(text_src_dir):
        if not entry.is_file():
            continue
        input_path = os.path.join(text_src_dir, entry.name)
        output_path = os.path.join(clean_text_dir, entry.name)
        url = parse_and_clean_text(input_path, output_path)

        output_path = Path(output_path).as_posix()
        text_url_map.append((output_path, url))
    return text_url_map


def download_audio(text_url_map, audio_output_dir):
    ''' Download the audio using (text, url) pairs to audio_output_dir and
        return a list of (text, audio_file_path) tuples
    '''
    os.makedirs(audio_output_dir, exist_ok=True)
    text_file_map = []
    for text_path, url in tqdm(text_url_map):
        path = urlparse(url).path
        filepath = Path(path).name
        output_path = os.path.join(audio_output_dir, filepath)
        if not os.path.exists(output_path):
            download_file(url, output_path)
        output_path = Path(output_path).as_posix()
        text_file_map.append((text_path, output_path))
    return text_file_map


def create_text_audio_map():
    text_src_dir = r"text"
    clean_text_dir = "cleaned"
    audio_output_dir = "audio"

    text_url_map = parse_files(text_src_dir, clean_text_dir)
    text_audio_map = download_audio(text_url_map, audio_output_dir)

    with open('text_audio_map.csv', 'w',
              encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(text_audio_map)


def get_text_audio_map():
    map_file = 'text_audio_map.csv'

    if not os.path.exists(map_file):
        create_text_audio_map()

    text_audio_map = []
    with open(map_file, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            text_audio_map.append(row)

    return text_audio_map



def align_text(text_audio_map, align_out_dir, word_align=False):
    os.makedirs(align_out_dir, exist_ok=True)

    for text_path, audio_path in tqdm(text_audio_map):
        audio_basename = os.path.basename(audio_path)
        audio_basename = os.path.splitext(audio_basename)[0]
        align_path = os.path.join(align_out_dir, f'{audio_basename}.json')
        if not os.path.exists(align_path):
            align(text_path, audio_path, align_path, word_align)


if __name__ == "__main__":
    start_time = time.time()

    text_audio_map = get_text_audio_map()

    align_out_dir = 'sentence_alignment'
    align_text(text_audio_map, align_out_dir, word_align=False)

    align_out_dir = 'word_alignment'
    align_text(text_audio_map, align_out_dir, word_align=True)

    print(f'Finished in {time.time()-start_time:0.4f} seconds.')