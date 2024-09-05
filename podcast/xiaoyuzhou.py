import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin

import click


@click.group()
def cli():
    pass


@cli.command()
@click.option("--url", required=True, help="URL of the webpage containing audio links")
@click.option("--output_path", default="downloaded_audio", help="Output directory for downloaded audio files")
def download_audio(url, output_path="downloaded_audio"):

    os.makedirs(output_path, exist_ok=True)

    # Send a GET request to the target webpage
    response = requests.get(url)
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
            audio_response = requests.get(audio_url, stream=True)
            audio_response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Download complete at {file_path}")
            output_list.append(file_path)
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {file_name}. Error: {e}")

    return output_list


@cli.command()
@click.option("--audio_path", required=True, help="Path to the audio file")
def transcribe(audio_path):
    import whisper
    model = whisper.load_model("large")
    result = model.transcribe(audio_path)
    # print(result["text"])

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
