class FloatingPoint:
    def __init__(self):
        self.bias = 3

    def to_binary(self, decimal_str):
        """Onluq ədədi binary stringə çevirir (nöqtə ilə)."""
        if "." not in decimal_str:
            decimal_str += ".0"
            
        decimal_part_str, fractional_part_str = decimal_str.split(".")
        decimal_part = int(decimal_part_str)
        fractional_part = float("0." + fractional_part_str)
        
        binary_decimal = bin(decimal_part)[2:]
        binary_fractional = ""
        
        count = 0
        while fractional_part > 0 and count < 20:
            fractional_part *= 2
            binary_fractional += str(int(fractional_part))
            fractional_part -= int(fractional_part)
            count += 1
            
        return binary_decimal + "." + binary_fractional
        
    def convert_to_floating_point(self, decimal):
        """8-bit formatına çevirir: 1 İşarə, 3 Exponent, 4 Mantissa."""
        is_negative = decimal.startswith('-')
        decimal_val_str = decimal.lstrip('-')
        
        # Sıfır halı
        if float(decimal_val_str) == 0:
            return "00000000"
        
        binary = self.to_binary(decimal_val_str)
        
        # Nöqtəni çıxarıb ilk '1'-in yerini tapırıq (Normalizasiya üçün)
        binary_no_dot = binary.replace(".", "")
        if "1" not in binary_no_dot:
            return "00000000"
            
        first_one_idx = binary_no_dot.index("1")
        dot_idx = binary.index(".")
        
        # Exponent hesabla: nöqtənin ilk '1'-ə görə mövqeyi
        exponent = dot_idx - first_one_idx - 1
        biased_exponent = exponent + self.bias
        
        # --- SOLDAN SİLMƏ (Exponent Overflow) ---
        # 3 bit yerimiz var (0-7 arası). 8-dən böyükdürsə, soldan bitlər atılır.
        biased_exponent = biased_exponent & 0b111 
        exponent_bits = bin(biased_exponent)[2:].zfill(3)
        
        # --- SAĞDAN SİLMƏ (Mantissa Truncation) ---
        # İlk '1'-dən sonrakı bitləri götürürük
        mantissa_start = first_one_idx + 1
        # Cəmi 4 bit götürürük, qalanı (sağdakılar) silinir
        mantissa_bits = binary_no_dot[mantissa_start : mantissa_start + 4]
        # Əgər 4 bitdən azdırsa, sağdan sıfırla doldururuq
        mantissa_bits = mantissa_bits.ljust(4, '0')
        
        sign_bit = '1' if is_negative else '0'
        
        return sign_bit + exponent_bits + mantissa_bits
    
    def convert_from_floating_point(self, fp_binary):
        """8-bit binary-ni onluq ədədə qaytarır."""
        if len(fp_binary) != 8:
            raise ValueError("Floating point 8 bit olmalıdır!")
        
        sign_bit = fp_binary[0]
        exponent_bits = fp_binary[1:4]
        mantissa_bits = fp_binary[4:8]
        
        biased_exponent = int(exponent_bits, 2)
        exponent = biased_exponent - self.bias
        
        # Normalizasiya olunmuş formatda gizli 1-i bərpa edirik
        # Qeyd: biased_exponent 0 olduqda IEEE-də fərqlidir, 
        # lakin sənin 'silmə' məntiqinə görə birbaşa bərpa edirik.
        mantissa_val = 1.0
        for i, bit in enumerate(mantissa_bits):
            if bit == '1':
                mantissa_val += 2 ** -(i + 1)
        
        result = mantissa_val * (2 ** exponent)
        return -result if sign_bit == '1' else result
