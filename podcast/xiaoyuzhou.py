import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin

import click
import json


@click.group()
def cli():
    pass


def load_cookies_from_file(file_path):
    cookies = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if '=' in line:
                    name, value = line.strip().split('=', 1)
                    cookies[name] = value
        return cookies
    except FileNotFoundError:
        print(f"Cookie file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error loading cookies from file: {e}")
        return None


@cli.command()
@click.option("--url", required=True, help="URL of the webpage containing audio links")
@click.option("--output_path", default="downloaded_audio", help="Output directory for downloaded audio files")
@click.option("--cookies_file", help="Path to JSON file containing cookies")
def download_audio(url, output_path="downloaded_audio", cookies_file=None):

    os.makedirs(output_path, exist_ok=True)

    # Load cookies from file if provided
    cookies = load_cookies_from_file(cookies_file) if cookies_file else None

    # Set up headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Send a GET request to the target webpage
    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the webpage: {e}")
        return

    # Send a GET request to the target webpage
    # response = requests.get(url, cookies=cookies)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Define common audio file extensions
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.aac')

    # Find all links
    links = soup.find_all('a', href=True)
    audio_links = set()  # Use a set to avoid duplicates
    for link in links:
        href = link['href']
        if href.lower().endswith(audio_extensions):
            full_url = urljoin(url, href)
            audio_links.add(full_url)

    # If no explicit audio links found, search the entire HTML
    if not audio_links:
        pattern = r'https?://[^\s<>"\']+(?:{})'.format('|'.join(audio_extensions))
        audio_links = set(re.findall(pattern, str(soup), re.IGNORECASE))

    if not audio_links:
        print("No audio file links found")
        return

    output_list = []
    for audio_url in audio_links:
        # Extract filename from URL
        file_name = os.path.basename(audio_url)
        file_path = os.path.join(output_path, file_name)

        # Check if file already exists
        if os.path.exists(file_path):
            print(f"File already exists, skipping: {file_path}")
            continue

        print(f"Downloading: {file_name}")
        
        # Download audio file
        try:
            audio_response = requests.get(audio_url, stream=True, cookies=cookies)
            audio_response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Download complete at {file_path}")
            output_list.append(file_path)
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {file_name}. Error: {e}")

        # transcribe
        import whisper
        model = whisper.load_model("large")
        result = model.transcribe(file_path)
        print(result["text"])

        # write to file, replace audio extension with .txt
        output_path = os.path.splitext(file_path)[0] + ".txt"
        with open(output_path, "w") as f:
            f.write(result["text"])

    return output_list


@cli.command()
@click.option("--audio_path", required=True, help="Path to the audio file")
def transcribe(audio_path):
    # import whisper
    # model = whisper.load_model("large")
    # result = model.transcribe(audio_path)
    # print(result["text"])

    # # write to file, replace audio extension with .txt
    # output_path = os.path.splitext(audio_path)[0] + ".txt"
    # with open(output_path, "w") as f:
    #     f.write(result["text"])

    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
    from datasets import load_dataset


    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True,
        # attn_implementation="flash_attention_2",
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    # dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
    # sample = dataset[0]["audio"]

    # result = pipe(sample)
    result = pipe(audio_path)
    print(result["text"])

    # write to file, replace audio extension with .txt
    output_path = os.path.splitext(audio_path)[0] + ".txt"
    with open(output_path, "w") as f:
        f.write(result["text"])



if __name__ == "__main__":
    r"""
    demo usage:
        python xiaoyuzhou.py download-audio --url "https://www.xiaoyuzhoufm.com/episode/66d7b5fa4a0f950f845a2a2e" --output_path "downloaded_audio"
        python xiaoyuzhou.py transcribe --audio_path "downloaded_audio/ltwjjENqEP3IRbUOoYOD2s01Yi2x.m4a"
    """
    cli()
