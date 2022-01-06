from reportlab.pdfgen import canvas
from reportlab.lib.colors import magenta, pink, blue 
from typing import Any, Dict, Iterable, Union
from pikepdf import Pdf
from enum import Enum
import io

class FieldType(Enum):
    TEXT = 'text' # Text input Field
    CHECK_BOX = 'checkbox'
    LIST_BOX = 'listbox' # allows multiple selection
    CHOICE = 'choice' # allows only one selection
    RADIO = 'radio'

class FormField:
    """A data holding class, used to easily specify how a PDF form field should be created."""
    def __init__(self, program_name:str, type_name:Union[FieldType, str], x:int, y:int, user_name:str='', configs:Dict[str, Any]=None):
        """configs is dictionary containing any keyword argument to the reportlab field functions, which
        vary depending on what type of field this is. See section 4.7 of the 
        [reportlab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)"""
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

def _create_only_fields(io_obj, fields_per_page:Iterable[Iterable[FormField]], font_name:str='Courier', font_size:int=20):
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
                form.textfield(name=field.name, x=field.x, y=field.y, tooltip=field.user_name, **field.configs)
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

def set_fields(in_file, out_file, fields_per_page:Iterable[Iterable[FormField]]):
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

    foreign_root = in_pdf.copy_foreign(temp_pdf.Root)
    in_pdf.Root.AcroForm = foreign_root.AcroForm
    for in_page, temp_page in zip(in_pdf.pages, temp_pdf.pages):
        in_page = in_pdf.pages[1]
        if not hasattr(temp_page, 'Annots'):
            continue # no fields on this page, skip
        annots = temp_pdf.make_indirect(temp_page.Annots)
        if not hasattr(in_page, 'Annots'):
            in_page['/Annots'] = in_pdf.copy_foreign(annots)
        else:
            in_page.Annots.extend(in_pdf.copy_foreign(annots))
    in_pdf.save(out_file)