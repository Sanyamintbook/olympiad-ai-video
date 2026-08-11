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
        # Look for the template in the project's 'templates' or 'template' directory
        project_root = Path(os.getcwd())
        template_dir_plural = project_root / "templates"
        template_dir_singular = project_root / "template"
        
        # Check a few possible names the user might use
        possible_names = [
            "Vydia_Mintbook_TemplateSystem - Copy.pptx",
            "Vydia_Mintbook_TemplateSystem.pptx",
            "template.pptx"
        ]
        
        template_path = ""
        for template_dir in [template_dir_plural, template_dir_singular]:
            if not template_dir.exists():
                continue
            for name in possible_names:
                candidate = template_dir / name
                if candidate.exists():
                    template_path = str(candidate)
                    break
            if template_path:
                break
                
        # Fallback to the old Downloads path just in case they haven't moved it yet
        if not template_path:
            template_path = r"C:\Users\Sanyami Jain\Downloads\Vydia_Mintbook_TemplateSystem - Copy.pptx"
        if os.path.exists(template_path):
            prs = Presentation(template_path)
            slide_layout = prs.slide_layouts[0] # The only layout in this template
        else:
            prs = Presentation()
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)
            slide_layout = prs.slide_layouts[1]
            
        initial_slide_count = len(prs.slides) if os.path.exists(template_path) else 0
        
        slides = []
        builder = SlideBuilder()
        
        narration_map = {}
        if narration_segments:
            for seg in narration_segments:
                narration_map[seg.unit_id] = seg.narration_text
                
        for unit_idx, unit in enumerate(units):
            narration_text = narration_map.get(unit.unit_id)
            if not narration_text:
                raise ValueError(f"Missing NarrationSegment for TeachingUnit {unit.unit_id}")
                
            slide_model = builder.build(unit, narration_text)
            slides.append(slide_model)
            
            # Add new slide using the layout
            slide = prs.slides.add_slide(slide_layout)
            
            # 0. Restore the Mintbook Vydia Dark Teal Background 
            # (Deepcopy does not copy slide-level background formatting, only shapes)
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(11, 52, 54) # #0B3436 Deep Teal/Green
            
            # PERFECT TEMPLATE CLONING HACK
            # Since python-pptx doesn't have a duplicate_slide() method, and the user's graphics 
            # are on Slide 0 (not the Master Layout), we deeply copy all shapes from Slide 0 to the new slide!
            if os.path.exists(template_path) and initial_slide_count > 0:
                import copy
                import io
                source_slide = prs.slides[0]
                for shp in source_slide.shapes:
                    # Fix for broken pictures: Deepcopying XML breaks image relationships (rIds)
                    # Instead, extract the raw image bytes and officially re-insert them.
                    if getattr(shp, "shape_type", None) == 13: # 13 is MSO_SHAPE_TYPE.PICTURE
                        try:
                            image_stream = io.BytesIO(shp.image.blob)
                            slide.shapes.add_picture(image_stream, shp.left, shp.top, shp.width, shp.height)
                            continue
                        except Exception:
                            pass
                            
                    el = shp.element
                    newel = copy.deepcopy(el)
                    slide.shapes._spTree.append(newel)
            else:
                pass # Fallback background is now handled at the top
            
            # Populate speaker notes verbatim if the template supports it
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                slide.notes_slide.notes_text_frame.text = narration_text
                
            # --- 2. DYNAMIC BINDING TO TEMPLATE SHAPES ---
            # Instead of creating new text boxes which ruins the user's alignment, we find their existing
            # "Click to add title" shapes and replace the text while preserving their exact positioning!
            
            title_shape = None
            body_shape = None
            seq_shape = None
            
            for shape in slide.shapes:
                if not hasattr(shape, "text_frame"):
                    continue
                text = shape.text_frame.text.lower().strip()
                if "click to add title" in text or "layout — title" in text:
                    title_shape = shape
                elif "click to add subtitle" in text:
                    body_shape = shape
                elif text == "01":
                    seq_shape = shape
                    
            if seq_shape:
                seq_shape.text = f"{unit_idx + 1:02d}"
                    
            if title_shape:
                title_shape.text = slide_model.title
                title_shape.text_frame.word_wrap = True
                # Auto-scale font size if needed
                title_len = len(slide_model.title)
                if title_len > 40:
                    for p in title_shape.text_frame.paragraphs:
                        try:
                            p.font.size = Pt(28 if title_len < 60 else 24)
                        except Exception:
                            pass
            else:
                # Fallback if the user's template doesn't have the "Click to add title" text box
                title_shape = slide.shapes.add_textbox(Inches(0.75), Inches(0.65), Inches(11.833), Inches(1.2))
                title_shape.text = slide_model.title
                title_shape.text_frame.word_wrap = True
                try:
                    title_shape.text_frame.paragraphs[0].font.size = Pt(32)
                    title_shape.text_frame.paragraphs[0].font.bold = True
                    title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
                except Exception:
                    pass
                
            if body_shape:
                tf = body_shape.text_frame
                tf.word_wrap = True
                tf.clear() # Clear the "Click to add subtitle" text
                for i, bullet in enumerate(slide_model.bullets):
                    p = tf.add_paragraph() if i > 0 else (tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph())
                    p.text = "•  " + bullet
                    p.level = 0
                    try:
                        p.space_after = Pt(18)
                    except Exception:
                        pass
            else:
                # Fallback body box
                body_shape = slide.shapes.add_textbox(Inches(0.75), Inches(2.1), Inches(11.833), Inches(4.8))
                tf = body_shape.text_frame
                tf.word_wrap = True
                for i, bullet in enumerate(slide_model.bullets):
                    p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                    p.text = "•  " + bullet
                    p.level = 0
                    try:
                        p.font.size = Pt(24) 
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.space_after = Pt(24)
                    except Exception:
                        pass
                
        # Delete the original dummy slides from the template
        if os.path.exists(template_path) and initial_slide_count > 0:
            xml_slides = prs.slides._sldIdLst
            slides_to_keep = list(xml_slides)[initial_slide_count:] # Keep all newly added slides, drop original template slides
            xml_slides.clear()
            for s in slides_to_keep:
                xml_slides.append(s)
                
        output_path = os.path.join(output_dir, "output.pptx")
        prs.save(output_path)
        return slides, output_path
