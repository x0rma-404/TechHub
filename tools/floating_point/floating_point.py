class FloatingPoint:
    def __init__(self):
        self.decimal_representation = ""
        self.mantissa = 0
        self.bias = 3

    def to_binary(self, decimal):
        decimal_part, fractional_part = decimal.split(".")
        decimal_part = int(decimal_part)
        fractional_part = float("0." + fractional_part)
        
        binary_decimal = bin(decimal_part)[2:]
        binary_fractional = ""
        count = 0
        while fractional_part > 0 and count < 20:  # Add limit to prevent infinite loops
            fractional_part *= 2
            binary_fractional += str(int(fractional_part))
            fractional_part -= int(fractional_part)
            count += 1
        
        return binary_decimal + "." + binary_fractional
        
    def convert_to_floating_point(self, decimal):
        # Handle negative numbers
        is_negative = decimal.startswith('-')
        decimal = decimal.lstrip('-')
        
        binary = self.to_binary(decimal)
        
        # Find position of first '1'
        binary_no_dot = binary.replace(".", "")
        first_one = binary_no_dot.index("1") if "1" in binary_no_dot else 0
        dot_position = binary.index(".")
        
        # Calculate exponent
        if dot_position <= first_one:
            # Number < 1, need to shift right
            exponent = dot_position - first_one - 1
        else:
            # Number >= 1, need to shift left
            exponent = dot_position - first_one - 1
        
        # Sign bit
        sign_bit = '1' if is_negative else '0'
        
        # Biased exponent (bias = 3)
        biased_exponent = exponent + 3
        exponent_bits = bin(biased_exponent)[2:] if biased_exponent >= 0 else bin(biased_exponent & 0b111)[2:]
        exponent_bits = exponent_bits.zfill(3)  # 3 bits for exponent
        
        # Mantissa (normalized, skip leading 1)
        binary_no_dot = binary.replace(".", "")
        mantissa_start = binary_no_dot.index("1") + 1 if "1" in binary_no_dot else 0
        mantissa = binary_no_dot[mantissa_start:mantissa_start + 4]
        mantissa = mantissa.ljust(4, '0')  # 4 bits for mantissa
        
        return sign_bit + exponent_bits + mantissa
    
    def convert_from_floating_point(self, fp_binary):
        """
        Convert from 8-bit floating point representation back to decimal
        Format: 1 sign bit + 3 exponent bits + 4 mantissa bits
        """
        if len(fp_binary) != 8:
            raise ValueError("Floating point representation must be 8 bits")
        
        # Extract components
        sign_bit = fp_binary[0]
        exponent_bits = fp_binary[1:4]
        mantissa_bits = fp_binary[4:8]
        
        # Convert exponent from biased form
        biased_exponent = int(exponent_bits, 2)
        exponent = biased_exponent - 3  # Remove bias
        
        # Reconstruct the binary number with implicit leading 1
        # (assuming normalized format)
        if biased_exponent == 0:
            # Denormalized number (no implicit 1)
            binary_mantissa = "0." + mantissa_bits
        else:
            # Normalized number (implicit leading 1)
            binary_mantissa = "1." + mantissa_bits
        
        # Apply exponent (shift the decimal point)
        mantissa_value = 0.0
        for i, bit in enumerate(binary_mantissa.replace(".", "")):
            if bit == '1':
                # Position relative to decimal point
                if binary_mantissa[0] == '1':
                    mantissa_value += 2 ** (0 - i)
                else:
                    mantissa_value += 2 ** (-1 - i)
        
        # Shift by exponent
        result = mantissa_value * (2 ** exponent)
        
        # Apply sign
        if sign_bit == '1':
            result = -result
        
        return result