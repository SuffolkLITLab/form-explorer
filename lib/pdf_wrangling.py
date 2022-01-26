import io
from enum import Enum
import tempfile
from typing import Any, Dict, Iterable, Union, List, Tuple, BinaryIO
from numbers import Number
from pathlib import Path

import cv2
from boxdetect import config
from boxdetect.pipelines import get_checkboxes
import numpy as np
from pdf2image import convert_from_path, convert_from_bytes
from pikepdf import Pdf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import magenta, pink, blue 

######## PDF internals related funcitons ##########

class FieldType(Enum):
    TEXT = 'text' # Text input Field
    CHECK_BOX = 'checkbox'
    LIST_BOX = 'listbox' # allows multiple selection
    CHOICE = 'choice' # allows only one selection
    RADIO = 'radio'

class FormField:
    """A data holding class, used to easily specify how a PDF form field should be created."""
    def __init__(self, program_name:str, type_name:Union[FieldType, str], x:int, y:int, 
                 user_name:str='', configs:Dict[str, Any]=None):
        """
        Constructor
        
        Args:
            x: the x position of the lower left corner of the field. Should be in X,Y coordinates,
                where (0, 0) is the lower left of the page, x goes to the right, and units are in
                points (1/72th of an inch)
            y: the y position of the lower left corner of the field. Should be in X,Y coordinates,
                where (0, 0) is the lower left of the page, y goes up, and units are in points 
                (1/72th of an inch)
            config: a dictionary containing any keyword argument to the reportlab field functions,
                which will vary depending on what type of field this is. See section 4.7 of the 
                [reportlab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
        
        """
        if isinstance(type_name, str):
            self.type = FieldType(type_name.lower()) # throws a ValueError, keeping in for now
        else:
            self.type = type_name
        self.name = program_name
        self.x = x
        self.y = y
        self.user_name = user_name
        # TODO(brycew): If we aren't given options, make our own depending on self.type
        if self.type == FieldType.CHECK_BOX:
            self.configs= {
                'buttonStyle': 'check',
                'borderColor': magenta,
                'fillColor' :pink,
                'textColor':blue,
                'forceBorder':True
            }
        elif self.type == FieldType.TEXT:
            self.configs = {
                'fieldFlags': 'doNotScroll'
            }
        else:
            self.configs = {}
        if configs:
            self.configs.update(configs)
    def __str__(self):
        return f'Type: {self.type}, Name: {self.name}, User name: {self.user_name}, X: {self.x}, Y: {self.y}, Configs: {self.configs}'

    def __repr__(self):
        return str(self)

def _create_only_fields(io_obj:BinaryIO, fields_per_page:Iterable[Iterable[FormField]], font_name:str='Courier', font_size:int=20):
    """Creates a PDF that contains only AcroForm fields. This PDF is then merged into an existing PDF to add fields to it.
    We're adding fields to a PDF this way because reportlab isn't able to read PDFs, but is the best feature library for
    writing them.
    """
    c = canvas.Canvas(io_obj)
    c.setFont(font_name, font_size)
    form = c.acroForm
    for fields in fields_per_page:
        for field in fields:
            if field.type == FieldType.TEXT: 
                form.textfield(name=field.name, tooltip=field.user_name, 
                              x=field.x, y=field.y, **field.configs)
            elif field.type == FieldType.CHECK_BOX: 
                form.checkbox(name=field.name, tooltip=field.user_name,
                              x=field.x, y=field.y, **field.configs) 
            elif field.type == FieldType.LIST_BOX: 
                form.listbox(name=field.name, tooltip=field.user_name,
                              x=field.x, y=field.y, **field.configs)
            elif field.type == FieldType.CHOICE: 
                form.choice(name=field.name, tooltip=field.user_name,
                            x=field.x, y=field.y, **field.configs)
            elif field.type == FieldType.RADIO: 
                form.radio(name=field.name, tooltip=field.user_name,
                            x=field.x, y=field.y, **field.configs)
            else:
                pass
        c.showPage() # Goes to the next page
    c.save()

def set_fields(in_file:Union[str, Path, BinaryIO], 
        out_file:Union[str, Path, BinaryIO], 
        fields_per_page:Iterable[Iterable[FormField]]):
    """Adds fields per page to the in_file PDF, writing the new PDF to out_file.

    Example usage:
    ```
    set_fields('no_fields.pdf', 'single_field_on_second_page.pdf', 
      [
        [],  # nothing on the first page
        [ # Second page
          FormField('new_field', 'text', 110, 105, configs={'width': 200, 'height': 30}),
          # Choice needs value to be one of the possible options, and options to be a list of strings or tuples
          FormField('new_choices', 'choice', 110, 400, configs={'value': 'Option 1', 'options': ['Option 1', 'Option 2']}),
          # Radios need to have the same name, with different values
          FormField('new_radio1', 'radio', 110, 600, configs={'value': 'option a'}),
          FormField('new_radio1', 'radio', 110, 500, configs={'value': 'option b'})
        ] 
      ]
    )
    ```
    """
    if not fields_per_page:
        # Nothing to do, lol
        return
    in_pdf = Pdf.open(in_file)
    if hasattr(in_pdf.Root, 'AcroForm'):
        print('Not going to overwrite the existing AcroForm!')
        return None
    # Make an in-memory PDF with the fields
    io_obj = io.BytesIO()
    _create_only_fields(io_obj, fields_per_page)
    temp_pdf = Pdf.open(io_obj)

    in_pdf = swap_pdf_page(formed_pdf=temp_pdf, blank_pdf=in_pdf)
    in_pdf.save(out_file)

def swap_pdf_page(*, formed_pdf:Union[str, Path, Pdf], blank_pdf:Union[str, Path, Pdf]) -> Pdf:
    """Copies the AcroForm fields from one PDF to another blank PDF form"""
    if isinstance(formed_pdf, (str, Path)):
        formed_pdf = Pdf.open(formed_pdf)
    if isinstance(blank_pdf, (str, Path)):
        blank_pdf = Pdf.open(blank_pdf)

    if not hasattr(formed_pdf.Root, 'AcroForm'):
      # if the given PDF doesn't have any fields, don't copy them!
      return blank_pdf

    foreign_root = blank_pdf.copy_foreign(formed_pdf.Root)
    blank_pdf.Root.AcroForm = foreign_root.AcroForm
    for blank_page, formed_page in zip(blank_pdf.pages, formed_pdf.pages):
        if not hasattr(formed_page, 'Annots'):
            continue # no fields on this page, skip
        annots = formed_pdf.make_indirect(formed_page.Annots)
        if not hasattr(blank_page, 'Annots'):
            blank_page['/Annots'] = blank_pdf.copy_foreign(annots)
        else:
            blank_page.Annots.extend(blank_pdf.copy_foreign(annots))
    return blank_pdf


####### OpenCV related functions #########

BoundingBox = Tuple[Number, Number, Number, Number]
XYPair = Tuple[Number, Number]

def get_possible_fields(in_file:Union[str, Path, bytes]) -> List[List[FormField]]:
    dpi = 200
    if isinstance(in_file, str) or isinstance(in_file, Path):
        images = convert_from_path(in_file, dpi=dpi)
    else:
        images = convert_from_bytes(in_file, dpi=dpi)

    tmp_files = [tempfile.NamedTemporaryFile() for i in range(len(images))]
    for file_obj, img in zip(tmp_files, images):
        img.save(file_obj, 'JPEG')
        file_obj.flush()
    text_bboxes_per_page = [get_possible_text_fields(tmp_file.name) for tmp_file in tmp_files]
    checkbox_bboxes_per_page =[get_possible_checkboxes(tmp_file.name) for tmp_file in tmp_files]

    pts_in_inch = 72
    unit_convert = lambda pix: pix / dpi * pts_in_inch

    def img2pdf_coords(img, max_height):
        # If bbox: X, Y, width, height, and whatever else you want (we won't return it)
        if len(img) >= 4:
            return (unit_convert(img[0]), unit_convert(max_height - img[1]), unit_convert(img[2]), unit_convert(img[3]))
        # If just X and Y
        elif len(img) >= 2:
            return (unit_convert(img[0]), unit_convert(max_height - img[1]))
        else:
            return (unit_convert(img[0]))

    text_pdf_bboxes = [ [img2pdf_coords(bbox, images[i].height) for bbox in bboxes_in_page] 
                  for i, bboxes_in_page in enumerate(text_bboxes_per_page)]
    checkbox_pdf_bboxes = [ [img2pdf_coords(bbox, images[i].height) for bbox, _, _ in bboxes_in_page]
                  for i, bboxes_in_page in enumerate(checkbox_bboxes_per_page)]

    fields = []
    i = 0
    for bboxes_in_page, checkboxes_in_page in zip(text_pdf_bboxes, checkbox_pdf_bboxes):
      page_fields = [FormField(f'page_{i}_field_{j}', FieldType.TEXT, bbox[0], bbox[1], configs={'width': bbox[2], 'height': 20})
                for j, bbox in enumerate(bboxes_in_page)]
      # We're given the top left corner of the checkbox, but reportlab expects the bottom left
      page_fields += [FormField(f'page_{i}_check_{j}', FieldType.CHECK_BOX, bbox[0] + bbox[2]/4, bbox[1] - bbox[3], 
                      configs={'size': min(bbox[2], bbox[3])})
                for j, bbox in enumerate(checkboxes_in_page)]
      i += 1

    return fields

def intersect_bbox(bbox_a, bbox_b, dialation=2) -> bool:
    a_left, a_right = bbox_a[0] - dialation, bbox_a[0] + bbox_a[2] + dialation
    a_bottom, a_top = bbox_a[1] - dialation, bbox_a[1] + bbox_a[3] + dialation
    b_left, b_right = bbox_b[0], bbox_b[0] + bbox_b[2]
    b_bottom, b_top = bbox_b[1], bbox_b[1] + bbox_b[3]
    if a_bottom > b_top or a_top < b_bottom:
        return False
    if a_left > b_right or a_right < b_left:
        return False
    return True
    
def get_possible_checkboxes(img:Union[str, cv2.Mat]) -> np.ndarray:
    # Just using the boxdetect library
    cfg = config.PipelinesConfig()
    # TODO(brycew): adjust per state?
    cfg.width_range = (32,65)
    cfg.height_range = (25,40)
    cfg.scaling_factors = [0.6]
    cfg.wh_ratio_range = (0.6, 2.2)
    cfg.group_size_range = (2, 100)
    cfg.dilation_iterations = 0
    checkboxes = get_checkboxes(img, cfg=cfg, px_threshold=0.1, plot=False, verbose=False)
    return checkboxes

def get_possible_radios(img:Union[str, BinaryIO, cv2.Mat]):
    if isinstance(img, str):
        # 0 is for the flags: means nothing special is being used
        img = cv2.imread(img, 0)
    if isinstance(img, BinaryIO):
        img = cv2.imdecode(np.frombuffer(img.read(), np.uint8), 0)
    
    # TODO(brycew): need to support radio buttons further down the Weaver pipeline as well
    pass

def get_possible_text_fields(img:Union[str, BinaryIO, cv2.Mat]) -> List[List[BoundingBox]]:
    """
    Caveats so far: only considers straight, normal horizonal lines that don't touch any vertical lines as fields
    Won't find field inputs as boxes
    """
    if isinstance(img, str):
        # 0 is for the flags: means nothing special is being used
        img = cv2.imread(img, 0)
    if isinstance(img, BinaryIO):
        img = cv2.imdecode(np.frombuffer(img.read(), np.uint8), 0)

    # fixed level thresholding, turning a gray scale / multichannel img to a black and white one.
    # OTSU = optimum global thresholding: minimizes the variance of each Thresh "class"
    # for each possible thresh value between 128 and 255, split up pixels, get the within-class variance,
    # and minimize that
    (thresh, img_bin) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)

    img_bin = 255 - img_bin
    cv2.imwrite("Image_bin.png", img_bin)

    # Detect horizontal lines and vertical lines
    kernel_length = np.array(img).shape[1]//40
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    vertical_lines_img = cv2.dilate(cv2.erode(img_bin, vert_kernel, iterations=3), vert_kernel, iterations=3)
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    horizontal_lines_img = cv2.dilate(cv2.erode(img_bin, horiz_kernel, iterations=3), horiz_kernel, iterations=3)

    alpha = 0.5
    img_final_bin = cv2.addWeighted(vertical_lines_img, alpha, horizontal_lines_img, 1.0 - alpha, 0.0)

    contours, _ = cv2.findContours(img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    def sort_contours(cnts, method="left-to-right"):
        reverse = False
        coord = 0
        if method == "right-to-left" or method == "bottom-to-top":
            reverse = True
        # handle sorting against the y-coord rather than the x-coord of the bounding box
        if method == "top-to-bottom" or method == "bottom-to-top":
            coord = 1
        # construct list of bounding boxes and sort them top to bottom
        boundingBoxes = [cv2.boundingRect(c) for c in cnts]
        (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
            key=lambda b:b[1][coord], reverse=reverse))
        # return the list of sorted contours and bounding boxes
        return (cnts, boundingBoxes)
    (contours, boundingBoxes) = sort_contours(contours, method='top-to-bottom')
    vert_contours, _ = cv2.findContours(vertical_lines_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # TODO(brycew): also consider checking that the PDF is really blank ~ 1 line space above the horiz line
    if vert_contours:
        # Don't consider horizontal lines that meet up against vertical lines as text fields
        (vert_contours, vert_bounding_boxes) = sort_contours(vert_contours, method='top-to-bottom')
        to_return = []
        for bbox in boundingBoxes:
            inters = [intersect_bbox(vbbox, bbox) for vbbox in vert_bounding_boxes]
            if not any(inters):
                to_return.append(bbox)
        return to_return
    else:
        return boundingBoxes

def auto_add_fields(in_file:Union[str, Path, BinaryIO], out_filename):
    fields = get_possible_fields(in_file)
    print(fields)
    set_fields(in_file, out_filename, fields)