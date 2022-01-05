from reportlab.pdfgen import canvas
from reportlab.lib.colors import magenta, pink, blue, green
from typing import List
from pikepdf import Pdf
import io

class FormField:
    """A data holding class, used to easily specify how a PDF form field should be created."""
    def __init__(self, program_name, type_name, x, y, user_name=''):
        self.type = type_name
        self.name = program_name
        self.x = x
        self.y = y
        self.user_name = user_name

def _create_only_fields(io_obj, fields_per_page:List[List[FormField]]):
    """Creates a PDF that contains only AcroForm fields. This PDF is then merged into an existing PDF to add fields to it.
    We're adding fields to a PDF this way because reportlab isn't able to read PDFs, but is the best feature library for
    writing them.

    TODO: add the rest of the fields, including nesting multiple fields as one like a radio button,
    using https://www.reportlab.com/docs/reportlab-reference.pdf
    """
    c = canvas.Canvas(io_obj)
    c.setFont('Courier', 20)
    form = c.acroForm
    for fields in fields_per_page:
        for field in fields:
            if field.type == 'Tx': # Text input Field
                # TODO(brycew): just **kwargs the FormField attributes?
                form.textfield(name=field.name, x=field.x, y=field.y)
            elif field.type == 'Ch': # Check box
                form.checkbox(name=field.name, tooltip='Field cb1',
                              x=field.x, y=field.y, buttonStyle='check',
                              borderColor=magenta, fillColor=pink,
                              textColor=blue, forceBorder=True)
        c.showPage() # Goes to the next page
    c.save()

def set_fields(in_file, out_file, fields_per_page:List[List[FormField]]):
    """Adds fields per page to the in_file PDF, writing the new PDF to out_file."""
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

## Example use
## set_fields('no_fields.pdf', 'single_field_on_second_page.pdf', [[], [FormField('new_field', 'Tx', 110, 105)]])