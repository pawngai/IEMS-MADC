# Dynamic Form Configuration - Field Rules Engine
# Controls visibility, editability, and immutability based on context

DYNAMIC_FORM_RULES = {
    # ==================== EMPLOYEE PROFILE FORM ====================
    "employee_profile": {
        "form_id": "employee_profile",
        "title": "Employee Profile",
        "sections": [
            {
                "section_id": "personal_info",
                "title": "Personal Information",
                "fields": [
                    {
                        "field_id": "salutation",
                        "label": "Salutation",
                        "type": "select",
                        "master_ref": "salutation_master",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["SERVICE_BOOK_PART_I_ATTESTED"]
                        }
                    },
                    {
                        "field_id": "date_of_birth",
                        "label": "Date of Birth",
                        "type": "date",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["INITIAL_APPOINTMENT"]
                        },
                        "validation": {"min_age": 18, "max_age": 65}
                    },
                    {
                        "field_id": "gender",
                        "label": "Gender",
                        "type": "select",
                        "options": ["Male", "Female", "Transgender"],
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["SERVICE_BOOK_PART_I_ATTESTED"]
                        }
                    },
                    {
                        "field_id": "caste_category_code",
                        "label": "Category",
                        "type": "select",
                        "master_ref": "caste_category_master",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["INITIAL_APPOINTMENT"]
                        }
                    }
                ]
            },
            {
                "section_id": "contact_info",
                "title": "Contact Information",
                "fields": [
                    {
                        "field_id": "mobile_number",
                        "label": "Mobile Number",
                        "type": "tel",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": True,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": []
                        },
                        "validation": {"pattern": "^[6-9]\\d{9}$"}
                    },
                    {
                        "field_id": "personal_email",
                        "label": "Personal Email",
                        "type": "email",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": True,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": []
                        }
                    },
                    {
                        "field_id": "emergency_contact_name",
                        "label": "Emergency Contact Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": True,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": []
                        }
                    },
                    {
                        "field_id": "emergency_contact_number",
                        "label": "Emergency Contact Number",
                        "type": "tel",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": True,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": []
                        }
                    }
                ]
            },
            {
                "section_id": "current_address",
                "title": "Current Address",
                "fields": [
                    {
                        "field_id": "current_address_line1",
                        "label": "Address Line 1",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": []}
                    },
                    {
                        "field_id": "current_city",
                        "label": "City",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": []}
                    },
                    {
                        "field_id": "current_state_code",
                        "label": "State",
                        "type": "select",
                        "master_ref": "state_master",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": []}
                    },
                    {
                        "field_id": "current_pincode",
                        "label": "PIN Code",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": []},
                        "validation": {"pattern": "^[1-9][0-9]{5}$"}
                    }
                ]
            }
        ]
    },
    
    # ==================== SERVICE BOOK PART I FORM ====================
    "service_book_part_i": {
        "form_id": "service_book_part_i",
        "title": "Service Book - Part I (Bio-Data)",
        "employment_type_visibility": ["REG", "CON", "ADH", "DEP", "REE"],
        "sections": [
            {
                "section_id": "basic_personal_info",
                "title": "Basic Personal Information",
                "fields": [
                    {
                        "field_id": "photograph_url",
                        "label": "Photograph",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "name_in_block_letters",
                        "label": "Name (in block letters)",
                        "type": "text",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "parent_name",
                        "label": "Parent's Name",
                        "type": "text",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "spouse_name",
                        "label": "Spouse's Name (if married)",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "nationality",
                        "label": "Nationality",
                        "type": "text",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "caste_category",
                        "label": "Caste Category (SC/ST/OBC etc.)",
                        "type": "select",
                        "master_ref": "caste_category_master",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "date_of_birth_christian",
                        "label": "Date of Birth (Christian era)",
                        "type": "date",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    },
                    {
                        "field_id": "date_of_birth_saka",
                        "label": "Date of Birth (Saka era)",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {
                            "ess": False,
                            "data_entry": True,
                            "establishment": True,
                            "locked_after": ["ATTESTED"]
                        }
                    }
                ]
            },
            {
                "section_id": "qualifications",
                "title": "Qualifications",
                "fields": [
                    {
                        "field_id": "educational_qualifications_initial",
                        "label": "Educational Qualifications (initial)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "educational_qualifications_acquired",
                        "label": "Educational Qualifications (acquired)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "professional_qualifications",
                        "label": "Professional/Technical Qualifications",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    }
                ]
            },
            {
                "section_id": "physical_identity",
                "title": "Physical & Identification Details",
                "fields": [
                    {
                        "field_id": "height_cm",
                        "label": "Exact Height (cm)",
                        "type": "number",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "identification_marks",
                        "label": "Personal Identification Marks",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    }
                ]
            },
            {
                "section_id": "permanent_address",
                "title": "Permanent Home Address",
                "fields": [
                    {
                        "field_id": "permanent_address_line1",
                        "label": "Address Line 1",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "permanent_address_line2",
                        "label": "Address Line 2",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "permanent_city",
                        "label": "City/Town",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "permanent_state_code",
                        "label": "State",
                        "type": "select",
                        "master_ref": "state_master",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "permanent_pincode",
                        "label": "PIN Code",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]},
                        "validation": {"pattern": "^[1-9][0-9]{5}$"}
                    },
                    {
                        "field_id": "permanent_country",
                        "label": "Country",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    }
                ]
            },
            {
                "section_id": "signatures_attestation",
                "title": "Signatures & Attestation",
                "fields": [
                    {
                        "field_id": "signature_url",
                        "label": "Signature of Government Servant",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "thumb_impression_url",
                        "label": "Thumb Impression of Government Servant",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "attesting_officer_name",
                        "label": "Attesting Officer Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": False, "establishment": False, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "attesting_officer_designation",
                        "label": "Attesting Officer Designation",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": False, "establishment": False, "locked_after": ["ATTESTED"]}
                    }
                ]
            }
        ]
    },
    
    # ==================== SERVICE BOOK PART II-A FORM ====================
    "service_book_part_ii_a": {
        "form_id": "service_book_part_ii_a",
        "title": "Service Book - Part II-A (Immutable Certificates)",
        "employment_type_visibility": ["REG", "CON", "ADH", "DEP", "REE"],
        "sections": [
            {
                "section_id": "medical_and_verification",
                "title": "Medical & Verification Certificates",
                "fields": [
                    {
                        "field_id": "medical_fitness_certificate",
                        "label": "Medical Fitness Certificate Available",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "medical_exam_date",
                        "label": "Medical Examination Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "medical_officer_name",
                        "label": "Medical Officer Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "medical_category",
                        "label": "Medical Category",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "character_verification_done",
                        "label": "Character Verification Completed",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "character_verification_date",
                        "label": "Character Verification Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "character_verification_authority",
                        "label": "Character Verification Authority",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "police_verification_done",
                        "label": "Police Verification Completed",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "police_verification_date",
                        "label": "Police Verification Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "oath_of_allegiance_taken",
                        "label": "Oath of Allegiance Taken",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "oath_of_allegiance_date",
                        "label": "Oath of Allegiance Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "oath_of_secrecy_taken",
                        "label": "Oath of Secrecy Taken",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "oath_of_secrecy_date",
                        "label": "Oath of Secrecy Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    }
                ]
            },
            {
                "section_id": "declarations_and_confirmation",
                "title": "Declarations & Confirmation",
                "fields": [
                    {
                        "field_id": "marital_status_declaration",
                        "label": "Marital Status Declaration Submitted",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "marital_status_declaration_date",
                        "label": "Marital Status Declaration Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "hometown_declaration",
                        "label": "Hometown Declaration Submitted",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "declared_hometown",
                        "label": "Declared Hometown",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "hometown_declaration_date",
                        "label": "Hometown Declaration Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "initial_property_return",
                        "label": "Initial Property Return Submitted",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "initial_property_return_date",
                        "label": "Initial Property Return Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "entries_confirmed",
                        "label": "Entries Confirmed",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "confirmation_date",
                        "label": "Confirmation Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    },
                    {
                        "field_id": "confirming_officer",
                        "label": "Confirming Officer",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["ATTESTED"]}
                    }
                ]
            }
        ]
    },
    # ==================== SERVICE BOOK PART II-B FORM ====================
    "service_book_part_ii_b": {
        "form_id": "service_book_part_ii_b",
        "title": "Service Book - Part II-B (Mutable Certificates)",
        "employment_type_visibility": ["REG"],
        "sections": [
            {
                "section_id": "family_and_pcf",
                "title": "Family Particulars & PCF",
                "fields": [
                    {
                        "field_id": "family_members",
                        "label": "Family Members (JSON)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "pcf_account_number",
                        "label": "PCF Account Number",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "pcf_nominee_name",
                        "label": "PCF Nominee Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "pcf_nominee_relation",
                        "label": "PCF Nominee Relationship",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "pcf_nominee_share_percent",
                        "label": "PCF Nominee Share (%)",
                        "type": "number",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    }
                ]
            },
            {
                "section_id": "insurance_nps_bank",
                "title": "Insurance, NPS & Bank Details",
                "fields": [
                    {
                        "field_id": "gratuity_nominee_name",
                        "label": "Gratuity Nominee Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "gratuity_nominee_relation",
                        "label": "Gratuity Nominee Relationship",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "gratuity_nominee_share_percent",
                        "label": "Gratuity Nominee Share (%)",
                        "type": "number",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "nps_pran_number",
                        "label": "NPS PRAN Number",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "bank_account_number",
                        "label": "Bank Account Number",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "bank_name",
                        "label": "Bank Name",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "bank_ifsc",
                        "label": "Bank IFSC",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    }
                ]
            }
        ]
    },

    # ==================== SERVICE BOOK PART III FORM ====================
    "service_book_part_iii": {
        "form_id": "service_book_part_iii",
        "title": "Service Book - Part III (Service History Outside Current Appointment)",
        "employment_type_visibility": ["REG"],
        "sections": [
            {
                "section_id": "previous_service_records",
                "title": "Previous Qualifying Service",
                "fields": [
                    {
                        "field_id": "previous_services",
                        "label": "Previous Services (JSON)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "total_previous_qualifying_service",
                        "label": "Total Previous Qualifying Service (JSON years/months/days)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    }
                ]
            },
            {
                "section_id": "foreign_service_and_verification",
                "title": "Foreign Service & Verification",
                "fields": [
                    {
                        "field_id": "foreign_services",
                        "label": "Foreign Services (JSON)",
                        "type": "textarea",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "part_iii_verified",
                        "label": "Part III Verified",
                        "type": "checkbox",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "part_iii_verified_by",
                        "label": "Verified By",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    },
                    {
                        "field_id": "part_iii_verification_date",
                        "label": "Verification Date",
                        "type": "date",
                        "required": False,
                        "visibility": {"all_employment_types": False, "REGULAR": True},
                        "editability": {"ess": False, "data_entry": True, "establishment": True, "locked_after": ["LOCKED"]}
                    }
                ]
            }
        ]
    },
    
    # ==================== LEAVE APPLICATION FORM ====================
    "leave_application": {
        "form_id": "leave_application",
        "title": "Leave Application",
        "employment_type_visibility": ["REG", "CON", "ADH", "DEP", "REE"],
        "sections": [
            {
                "section_id": "leave_details",
                "title": "Leave Details",
                "fields": [
                    {
                        "field_id": "leave_type_code",
                        "label": "Leave Type",
                        "type": "select",
                        "master_ref": "leave_type_master",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]},
                        "filter_by_employment_type": True
                    },
                    {
                        "field_id": "from_date",
                        "label": "From Date",
                        "type": "date",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]}
                    },
                    {
                        "field_id": "to_date",
                        "label": "To Date",
                        "type": "date",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]}
                    },
                    {
                        "field_id": "days_applied",
                        "label": "Number of Days",
                        "type": "number",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]},
                        "computed": True
                    },
                    {
                        "field_id": "reason",
                        "label": "Reason for Leave",
                        "type": "textarea",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]}
                    },
                    {
                        "field_id": "leave_station",
                        "label": "Station during Leave",
                        "type": "text",
                        "required": False,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]}
                    },
                    {
                        "field_id": "contact_during_leave",
                        "label": "Contact Number during Leave",
                        "type": "tel",
                        "required": True,
                        "visibility": {"all_employment_types": True},
                        "editability": {"ess": True, "data_entry": True, "establishment": True, "locked_after": ["SUBMITTED"]}
                    }
                ]
            }
        ]
    }
}

# ==================== FIELD IMMUTABILITY MILESTONES ====================

IMMUTABILITY_MILESTONES = {
    "INITIAL_APPOINTMENT": {
        "description": "After initial appointment order is finalized (locked)",
        "locks_fields": [
            "date_of_birth",
            "caste_category_code",
        ]
    },
    "SERVICE_BOOK_PART_I_ATTESTED": {
        "description": "After Part I bio-data is finalized (locked)",
        "locks_fields": [
            "name_in_block_letters",
            "parent_name",
            "spouse_name",
            "nationality",
            "caste_category",
            "date_of_birth_christian",
            "date_of_birth_saka",
            "educational_qualifications_initial",
            "educational_qualifications_acquired",
            "professional_qualifications",
            "height_cm",
            "identification_marks",
            "permanent_address_line1",
            "permanent_address_line2",
            "permanent_city",
            "permanent_state_code",
            "permanent_pincode",
            "permanent_country",
            "signature_url",
            "thumb_impression_url"
        ]
    },
    "CONFIRMATION": {
        "description": "After confirmation in service",
        "locks_fields": [
            "employment_type_code"
        ]
    },
    "FIRST_PROMOTION": {
        "description": "After first promotion",
        "locks_fields": []
    },
    "RETIREMENT_NOTIFICATION": {
        "description": "After retirement notification issued",
        "locks_fields": [
            "date_of_retirement"
        ]
    },
    "ATTESTED": {
        "description": "After any Service Book entry is finalized (locked)",
        "locks_all_fields_in_entry": True
    }
}

# ==================== HIGH AUTHORITY OVERRIDE ====================

HIGH_AUTHORITY_OVERRIDE_CONFIG = {
    "allowed_authorities": ["APPROVING_AUTHORITY", "HOD", "APPOINTING_AUTHORITY", "SYSTEM_ADMIN"],
    "requires_reason": True,
    "creates_audit_record": True,
    "creates_supersession_entry": True,
    "notification_recipients": ["AUDITOR"]
}
