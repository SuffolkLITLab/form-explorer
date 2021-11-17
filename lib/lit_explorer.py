import re

def regex_norm_field(text):
    # Takes an auto-generated form field name and uses
    # regex to convert it into an Assembly Line standard field.
    # See https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/label_variables/

    regex_list = [

        # Personal info
        ## Name & Bio
        ["^((My|Full( legal)?) )?Name$","users1_name"],
        ["^(Typed or )?Printed Name\s?\d*$","users1_name"],
        ["^(DOB|Date of Birth|Birthday)$","users1_birthdate"],
        ## Address
        ["^(Street )?Address$","users1_address_line_one"],
        ["^City State Zip$","users1_address_line_two"],
        ["^City$","users1_address_city"],
        ["^Zip( Code)?$","users1_address_zip"],
        ## Contact
        ["^(Phone|Telephone)$","users1_phone_number"],
        ["^Email( Adress)$","users1_email"],

        # Parties
        ["plaintiff","plantiff1_name"],
        ["defendant","defendant1_name"],
        ["petitioners","petitioners1_name"],
        ["respondents","respondents1_name"],

        # Court info
        ["^(Court\s)?Case\s?(No|Number)?\s?A?$","docket_number"],
        ["^File\s?(No|Number)?\s?A?$","docket_number"],

        # Form info
        ["^(Signature|Sign( here)?)\s?\d*$","users1_signature"],
        ["^Date\s?\d*$","signature_date"],
    ]

    for regex in regex_list:
        text = re.sub(regex[0],regex[1],text, flags=re.IGNORECASE)
    return text
