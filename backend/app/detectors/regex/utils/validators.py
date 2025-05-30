import re
from datetime import datetime

class Validators:
    @staticmethod
    def is_luhn_valid(card_number: str) -> bool:
        card_number = re.sub(r"\D", "", card_number)
        total = 0
        reverse_digits = card_number[::-1]
        for i, digit in enumerate(map(int, reverse_digits)):
            if i % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit
        return total % 10 == 0

    @staticmethod
    def is_verhoeff_valid(aadhaar: str) -> bool:
        d = [[0,1,2,3,4,5,6,7,8,9], [1,2,3,4,0,6,7,8,9,5], [2,3,4,0,1,7,8,9,5,6], [3,4,0,1,2,8,9,5,6,7],
             [4,0,1,2,3,9,5,6,7,8], [5,9,8,7,6,0,4,3,2,1], [6,5,9,8,7,1,0,4,3,2], [7,6,5,9,8,2,1,0,4,3],
             [8,7,6,5,9,3,2,1,0,4], [9,8,7,6,5,4,3,2,1,0]]
        p = [[0,1,2,3,4,5,6,7,8,9], [1,5,7,6,2,8,3,0,9,4], [5,8,0,3,7,9,6,1,4,2], [8,9,1,6,0,4,3,5,2,7],
             [9,4,5,3,1,2,6,8,7,0], [4,2,8,6,5,7,3,9,0,1], [2,7,9,3,8,0,6,4,1,5], [7,0,4,6,9,1,3,2,5,8]]
        inv = [0,4,3,2,1,5,6,7,8,9]

        aadhaar = re.sub(r"\s", "", aadhaar)
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            return False

        c = 0
        for i, digit in enumerate(reversed(aadhaar)):
            c = d[c][p[i % 8][int(digit)]]
        return c == 0

    @staticmethod
    def is_valid_dob(dob: str) -> bool:
        for fmt in ("%m/%d/%Y", "%d-%m-%Y"):
            try:
                date_obj = datetime.strptime(dob, fmt)
                age = (datetime.today() - date_obj).days // 365
                return 0 < age < 120
            except ValueError:
                continue
        return False
    @staticmethod
    def is_canadian_sin_valid(sin: str) -> bool:
        sin = re.sub(r"\D", "", sin)
        if len(sin) != 9:
            return False
        return HelperAlgorithms.is_luhn_valid(sin)

    @staticmethod
    def is_us_routing_number_valid(routing: str) -> bool:
        routing = re.sub(r"\D", "", routing)
        if len(routing) != 9:
            return False
        weights = [3, 7, 1] * 3
        total = sum(int(d) * w for d, w in zip(routing, weights))
        return total % 10 == 0

    @staticmethod
    def is_india_gstin_valid(gstin: str) -> bool:
        gstin = gstin.strip().upper()
        if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}", gstin):
            return False

        def char_to_value(c):
            return int(c) if c.isdigit() else ord(c) - 55  # A=10

        factor = [1, 2] * 7 + [1]  # alternating multipliers
        total = 0
        for i in range(14):
            code_point = char_to_value(gstin[i])
            product = code_point * factor[i]
            total += product // 36 + product % 36

        check_digit = (36 - total % 36) % 36
        return gstin[-1] == (str(check_digit) if check_digit < 10 else chr(55 + check_digit))


    @staticmethod
    def is_iban_valid(iban: str) -> bool:
        iban = re.sub(r"\s+", "", iban).upper()
        if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{1,30}", iban):
            return False
        # Move first four characters to end
        rearranged = iban[4:] + iban[:4]
        # Replace letters with numbers
        numerical = ''.join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
        return int(numerical) % 97 == 1
