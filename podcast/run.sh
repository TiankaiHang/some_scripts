URLS=(
    # "https://www.xiaoyuzhoufm.com/episode/66f668646c7f8177867c2b44"
    https://www.xiaoyuzhoufm.com/episode/66f5701b2adfe48b83b0a9fa
)

for url in "${URLS[@]}"; do
    python xiaoyuzhou.py download-audio --url $url --output_path "downloaded_audio" --cookies_file "cookies.txt"
done