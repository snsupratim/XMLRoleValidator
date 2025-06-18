# src/role_comparer.py
from typing import List, Tuple
from src.utils import normalize_role, fuzzy_match
from config.config import FUZZY_MATCH_THRESHOLD

class RoleComparer:
    def __init__(self, fuzzy_threshold=FUZZY_MATCH_THRESHOLD):
        self.fuzzy_threshold = fuzzy_threshold

    def compare_roles(self, xml_roles: List[str], pdf_roles: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Compares roles from XML and PDF and determines if PDF roles are correct.
        Returns (is_incorrect, matched_roles_normalized, incorrect_pdf_roles_original).
        """
        normalized_xml_roles = {normalize_role(role) for role in xml_roles}
        # Create a mapping from normalized PDF role to its original string
        normalized_pdf_to_original = {normalize_role(role): role for role in pdf_roles}
        normalized_pdf_roles = set(normalized_pdf_to_original.keys())

        # Find direct matches
        matched_normalized_roles = normalized_xml_roles.intersection(normalized_pdf_roles)

        # Identify roles in PDF that are not exact matches in XML
        potentially_incorrect_pdf_normalized = normalized_pdf_roles - normalized_xml_roles

        # Try fuzzy matching for potentially incorrect PDF roles against all XML roles
        still_incorrect_pdf_normalized = set()
        for pdf_norm in potentially_incorrect_pdf_normalized:
            original_pdf_role = normalized_pdf_to_original[pdf_norm]
            found_fuzzy_match = False
            for xml_orig in xml_roles: # Compare against original XML roles for fuzzy matching
                if fuzzy_match(original_pdf_role, xml_orig, self.fuzzy_threshold):
                    found_fuzzy_match = True
                    # If fuzzy match found, consider it correct and add to matched
                    matched_normalized_roles.add(normalize_role(xml_orig)) # Add normalized XML role
                    break
            if not found_fuzzy_match:
                still_incorrect_pdf_normalized.add(pdf_norm)

        is_incorrect = bool(still_incorrect_pdf_normalized)

        # Convert matched roles to their original XML strings for reporting clarity
        final_matched_xml_roles = [xml_orig for xml_orig in xml_roles if normalize_role(xml_orig) in matched_normalized_roles]
        
        # Convert incorrect PDF roles back to their original PDF strings
        final_incorrect_pdf_roles = [normalized_pdf_to_original[role_norm] for role_norm in still_incorrect_pdf_normalized]

        return is_incorrect, sorted(list(set(final_matched_xml_roles))), sorted(list(set(final_incorrect_pdf_roles)))

    def generate_report(self, is_incorrect: bool, matched_roles: List[str], incorrect_pdf_roles: List[str], xml_roles: List[str], pdf_roles: List[str]):
        """Generates a comparison report."""
        print("\n--- Role Comparison Report ---")
        print(f"Total Unique Roles in XML: {len(set(xml_roles))}")
        print(f"Total Unique Roles found in PDF: {len(set(pdf_roles))}")

        print("\n--- Roles Matched (XML to PDF) ---")
        if matched_roles:
            for role in matched_roles:
                print(f"- {role}")
        else:
            print("No direct or fuzzy matches found between XML and PDF roles.")

        if is_incorrect:
            print("\n--- INCORRECT PDF ROLES (Found in PDF but NOT matching any XML role) ---")
            for role in incorrect_pdf_roles:
                print(f"- {role}")
            print("\nCONCLUSION: Roles in the PDF are INCORRECT as there are roles that do not match the XML definitions.")
        else:
            print("\n--- PDF ROLES ARE CORRECT ---")
            print("All roles found in the PDF either directly matched or fuzzy-matched with roles defined in the XML.")

        print("\n-----------------------------\n")