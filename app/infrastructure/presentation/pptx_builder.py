import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from app.domain.models.teaching_unit import TeachingUnit
from app.domain.models.slide import Slide
from app.domain.models.narration_segment import NarrationSegment
from app.infrastructure.presentation.slide_builder import SlideBuilder

class PptxBuilder:
    @staticmethod
    def build(
        units: list[TeachingUnit],
        narration_segments: list[NarrationSegment] | None = None,
        output_dir: str = "outputs"
    ) -> tuple[list[Slide], str]:
        os.makedirs(output_dir, exist_ok=True)
        prs = Presentation()
        
        # Set 16:9 widescreen layout
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        
        slides = []
        builder = SlideBuilder()
        
        narration_map = {}
        if narration_segments:
            for seg in narration_segments:
                narration_map[seg.unit_id] = seg.narration_text
                
        for unit in units:
            narration_text = narration_map.get(unit.unit_id)
            if not narration_text:
                raise ValueError(f"Missing NarrationSegment for TeachingUnit {unit.unit_id}")
                
            slide_model = builder.build(unit, narration_text)
            slides.append(slide_model)
            
            # Use Title and Content layout for native bullets, but we will strictly override its positions
            slide_layout = prs.slide_layouts[1] 
            slide = prs.slides.add_slide(slide_layout)
            
            # Populate speaker notes verbatim
            slide.notes_slide.notes_text_frame.text = narration_text
            
            # --- 0. BACKGROUND STYLING (Off-White) ---
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(248, 249, 250) # #F8F9FA
            
            # --- 1. ACCENT BAR (Deep Blue) ---
            bar = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.2)
            )
            bar.fill.solid()
            bar.fill.fore_color.rgb = RGBColor(0, 86, 210) # #0056D2
            bar.line.fill.background() # Remove border
            
            # --- 2. TITLE BOX (Native Placeholder) ---
            title_shape = slide.shapes.title
            title_shape.left = Inches(1.2) # Modest left gap
            title_shape.top = Inches(0.8)
            title_shape.width = Inches(11.0) # Expanded width to ensure left-alignment dominance
            title_shape.height = Inches(1.5)
            
            title_shape.text = slide_model.title
            title_tf = title_shape.text_frame
            title_tf.word_wrap = True
            title_tf.margin_left = Inches(0) # Force strict alignment
            
            p = title_tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            p.font.size = Pt(40) 
            p.font.bold = True
            p.font.name = "Segoe UI"
            p.font.color.rgb = RGBColor(43, 58, 66) # #2B3A42
            
            # --- 3. BODY BOX (Native Bullets) ---
            body_shape = slide.placeholders[1]
            body_shape.left = Inches(1.2) # Perfectly aligned with title
            body_shape.top = Inches(2.3)
            body_shape.width = Inches(11.0)
            body_shape.height = Inches(4.7)
            
            tf = body_shape.text_frame
            tf.text = "" # Clear default placeholder text
            tf.word_wrap = True
            tf.margin_left = Inches(0) # Force strict alignment with title
            
            for i, bullet in enumerate(slide_model.bullets):
                p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                p.text = bullet # Native bullets don't need manual •
                p.level = 0
                p.alignment = PP_ALIGN.LEFT
                p.font.size = Pt(24) 
                p.font.name = "Segoe UI"
                p.font.color.rgb = RGBColor(74, 85, 104) # #4A5568
                p.space_after = Pt(28) 
                p.line_spacing = 1.3
                
        output_path = os.path.join(output_dir, "output.pptx")
        prs.save(output_path)
        return slides, output_path
