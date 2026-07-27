import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List

from app.domain.models.timeline import TimelineEntry
from app.domain.video import Video
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class VideoRenderer:
    """
    Renders the final MP4 video by exporting PPTX slides to PNGs using win32com,
    and then stitching them with the audio files using FFmpeg.
    """
    
    @staticmethod
    def render(document_id: str, pptx_path: str, timeline: List[TimelineEntry], output_path: str) -> Video:
        settings = get_settings()
        ffmpeg_cmd = settings.ffmpeg_path
        
        # We will use a temporary directory for all the intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            slides_folder = temp_path / "slides"
            slides_folder.mkdir()
            
            logger.info(f"Exporting PPTX slides to images in {slides_folder}")
            # 1. Export PPTX to PNGs using win32com
            try:
                import win32com.client
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                # Open presentation in background
                presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_path), WithWindow=False)
                # ppSaveAsPNG is 18
                presentation.SaveAs(os.path.abspath(slides_folder), 18)
                presentation.Close()
                powerpoint.Quit()
            except ImportError:
                logger.error("win32com is not installed. Cannot export PPTX. Ensure pywin32 is installed.")
                raise
            except Exception as e:
                logger.error(f"Failed to export PPTX via PowerPoint: {e}")
                # Make sure to quit powerpoint if it crashed
                try:
                    powerpoint.Quit()
                except:
                    pass
                raise
                
            # 2. Build individual MP4 segments for each slide + audio
            segment_files = []
            for i, entry in enumerate(timeline):
                slide_num = i + 1
                # PowerPoint exports slides as Slide1.PNG, Slide2.PNG, etc.
                # However, local languages might change this (e.g., Diapositiva1.PNG). 
                # We'll just sort the files in the directory by creation/name and assume order.
                import re
                def extract_number(path):
                    match = re.search(r'\d+', path.name)
                    return int(match.group()) if match else 0
                    
                images_list = [p for p in slides_folder.glob("*") if p.suffix.lower() == ".png"]
                images = sorted(images_list, key=extract_number)
                
                if not images or i >= len(images):
                    raise FileNotFoundError(f"Could not find exported image for slide {slide_num}")
                    
                image_file = images[i]
                audio_file = Path(entry.audio_path)
                segment_file = temp_path / f"segment_{slide_num}.mp4"
                
                logger.info(f"Rendering segment {slide_num} from {image_file.name} and {audio_file.name}")
                
                # ffmpeg command to combine 1 image + 1 audio into a video segment
                # -loop 1 loops the single image, -shortest cuts the video when the audio ends
                cmd = [
                    ffmpeg_cmd,
                    "-y", # overwrite output
                    "-loop", "1",
                    "-i", str(image_file),
                    "-i", str(audio_file),
                    "-c:v", "libx264",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    str(segment_file)
                ]
                
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                segment_files.append(segment_file)
                
            # 3. Concatenate all segments into the final video
            concat_list_path = temp_path / "concat.txt"
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for sf in segment_files:
                    # ffmpeg concat list format: file 'path/to/file.mp4'
                    # Paths need forward slashes for ffmpeg safely
                    f.write(f"file '{sf.as_posix()}'\n")
                    
            logger.info("Concatenating all segments into final video...")
            concat_cmd = [
                ffmpeg_cmd,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-c", "copy",
                output_path
            ]
            
            subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Calculate total duration
            total_duration = sum(entry.slide_end_sec - entry.slide_start_sec for entry in timeline)
            
            logger.info(f"Video rendering complete! Saved to {output_path}")
            return Video(
                document_id=document_id,
                storage_path=output_path,
                duration_sec=total_duration
            )
