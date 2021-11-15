import re

def regex_norm_field(text):
    # Takes an auto-generated form field name and uses
    # regex to convert it into an Assembly Line standard field.
    # See https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/label_variables/

    regex_list = [

        # Personal info
        ## Name & Bio
        ["^(My\s)?Name$","users1_name"],
        ["^Printed Name\s?\d*$","users1_name"],
        ["^(DOB|Date of Birth|Birthday)$","users1_birthdate"],
        ## Address
        ["^(Street )?Address$","users1_address_line_one"],
        ["^City State Zip$","users1_address_line_two"],
        ["^City$","users1_address_city"],
        ["^Zip( Code)?$","users1_address_zip"],
        ## Contact
        ["^Phone$","users1_phone_number"],
        ["^Email$","users1_email"],

        # Court info
        ["^(Court\s)?Case\s?(No|Number)?\s?A?$","docket_number"],
        ["^File\s?(No|Number)?\s?A?$","docket_number"],

        # Form info
        ["^Date\s?\d*$","signature_date"],
    ]

    for regex in regex_list:
        text = re.sub(regex[0],regex[1],text, flags=re.IGNORECASE)
    return text
