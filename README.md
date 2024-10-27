# Format Converter

A versatile media format converter application built with PyQt6 that supports conversion between various audio, video, and image formats. The application provides a user-friendly interface with preview capabilities for all media types.

![Application Preview](/api/placeholder/800/400)

## Features

- **Multiple Media Type Support**:
  - Audio conversion (MP3, WAV, OGG, AAC, WMA, M4A, FLAC)
  - Video conversion (MP4, AVI, MKV, MOV, WMV, FLV, WebM)
  - Image conversion (JPG, PNG, GIF, BMP, TIFF, WebP, SVG, AVIF)

- **Media Preview**:
  - Video playback with controls
  - Audio playback with volume control
  - Image preview with aspect ratio preservation

- **Real-time Progress Tracking**:
  - Progress bar for conversion status
  - Status messages for operation feedback

## Installation Requirements

1. Python 3.x
2. Required Python packages:
```bash
pip install PyQt6
pip install Pillow
pip install pydub
pip install moviepy
pip install svglib
pip install reportlab
```

3. FFmpeg Installation:
   - **Windows**: Download from [FFmpeg Official Website](https://ffmpeg.org/download.html) and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

## Usage

1. Clone the repository:
```bash
git clone https://github.com/yourusername/format-converter.git
cd format-converter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

4. Using the converter:
   - Click "EKLE" to select input file
   - Choose the appropriate media type (Audio/Video/Image)
   - Select desired output format from dropdown
   - Click "BAŞLAT" to start conversion
   - Monitor progress and wait for completion message

## Libraries Used

- **PyQt6**: GUI framework for the application interface
- **PIL (Pillow)**: Image processing and conversion
- **Pydub**: Audio file manipulation and conversion
- **MoviePy**: Video processing and format conversion
- **svglib**: SVG file handling and conversion
- **reportlab**: PDF generation and graphics processing
- **FFmpeg**: Backend for complex audio/video conversions

## Supported Formats

### Audio
- Input/Output: MP3, WAV, OGG, AAC, WMA, M4A, FLAC

### Video
- Input/Output: MP4, AVI, MKV, MOV, WMV, FLV, WebM

### Image
- Input/Output: JPG/JPEG, PNG, GIF, BMP, TIFF, WebP, SVG, AVIF

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FFmpeg for providing the core media conversion capabilities
- PyQt team for the excellent GUI framework
- All contributors and maintainers of the used libraries

## Contact

For any questions or suggestions, please open an issue in the GitHub repository.
