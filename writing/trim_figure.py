"""
Trim white space from images (PNG, JPEG) or PDFs.

pip install click Pillow opencv-python PyMuPDF numpy
"""

import click
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import os
from pathlib import Path
import cv2

def detect_edges(img_array):
    """Detect edges of content in image by finding non-white pixels"""
    # Convert to grayscale if it's a color image
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array
    
    # Threshold to separate content from background
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    
    # Find non-zero points (content)
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(coords)
    return (x, y, w, h)

def trim_image(input_path, output_path):
    """Trim white space from image formats (PNG, JPEG)"""
    # Read image
    img = cv2.imread(str(input_path))
    if img is None:
        raise ValueError(f"Could not read image: {input_path}")
    
    # Detect edges
    bounds = detect_edges(img)
    if bounds is None:
        print(f"No content found in {input_path}")
        return
    
    x, y, w, h = bounds
    
    # Crop image
    cropped = img[y:y+h, x:x+w]
    
    # Save cropped image
    cv2.imwrite(str(output_path), cropped)

def trim_pdf(input_path, output_path):
    """Trim white space from PDF while maintaining PDF format"""
    # Open PDF
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Convert page to image for edge detection
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_array = np.array(img)
        
        # Detect edges
        bounds = detect_edges(img_array)
        if bounds is None:
            print(f"No content found in page {page_num+1}")
            continue
            
        x, y, w, h = bounds
        
        # Convert pixel coordinates to PDF coordinates
        rect = fitz.Rect(x, y, x+w, y+h)
        
        # Create new page with detected size
        new_page = new_doc.new_page(width=w, height=h)
        
        # Copy content from original page to new page
        new_page.show_pdf_page(
            new_page.rect,
            doc,
            page_num,
            clip=rect
        )
    
    # Save new PDF
    new_doc.save(output_path)
    new_doc.close()
    doc.close()

@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
def main(input_path, output_path):
    """
    Trim white space from images and PDFs.
    Supports PDF, PNG, and JPEG formats.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Check if output directory exists, if not create it
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process based on file extension
    ext = input_path.suffix.lower()
    
    try:
        if ext == '.pdf':
            trim_pdf(input_path, output_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            trim_image(input_path, output_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
        print(f"Successfully trimmed {input_path} to {output_path}")
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

if __name__ == '__main__':
    main()
