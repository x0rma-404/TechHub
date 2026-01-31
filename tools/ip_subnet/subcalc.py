class SubnetCalculator:
    
    def __init__(self, ip_adres, prefix):
        self.ip_adres = ip_adres
        self.prefix = prefix
        self.oktetler = self._ip_parcala()
        # Ortaq istifadə olunan 'x' (blok ölçüsü) və 'nw_count' (tam oktetlər)
        self.x = 255 - (2**8 - 1 - (2**(8 - self.prefix % 8) - 1))
        self.nw_count = self.prefix // 8

    def _ip_parcala(self):
        """IP stringini rəqəm listinə çevirir."""
        return [int(octet) for octet in self.ip_adres.split('.')]

    def get_mask(self):
        """Alt ağ maskasını (Subnet Mask) hesablayır."""
        e = self.prefix
        mask = '255.' * (e // 8) + str(2**8 - 1 - (2**(8 - e % 8) - 1)) + '.0' * (4 - e // 8 - 1)
        return mask.strip('.')

    def get_host_bits(self):
        """Host bitlərinin sayını qaytarır."""
        return 32 - self.prefix

    def get_max_hosts(self):
        """Maksimum istifadə edilə bilən host sayını qaytarır."""
        return (2**(32 - self.prefix)) - 2

    def get_network_id(self):
        """Network ID-ni hesablayır."""
        k = 0
        while self.oktetler[self.nw_count] > k + self.x:
            k += (self.x + 1)
            
        nw_part = ".".join(map(str, self.oktetler[:self.nw_count]))
        if nw_part: nw_part += "."
        
        return nw_part + str(k) + '.0' * (4 - self.nw_count - 1)

    def get_broadcast(self):
        """Broadcast ünvanını hesablayır."""
        k = 0
        while self.oktetler[self.nw_count] > k + self.x:
            k += (self.x + 1)
        i = k + self.x
            
        nw_part = ".".join(map(str, self.oktetler[:self.nw_count]))
        if nw_part: nw_part += "."
        
        return nw_part + str(i) + '.255' * (4 - self.nw_count - 1)

    def get_first_ip(self):
        """İlk istifadə edilə bilən IP-ni qaytarır."""
        nw = self.get_network_id()
        parts = nw.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    def get_last_ip(self):
        """Son istifadə edilə bilən IP-ni qaytarır."""
        bc = self.get_broadcast()
        parts = bc.split('.')
        parts[-1] = str(int(parts[-1]) - 1)
        return ".".join(parts)

    def rapor(self):
        """Bütün metodları ayrı-ayrılıqda çağıraraq nəticəni göstərir."""
        print(f"\n--- Detallar: {self.ip_adres}/{self.prefix} ---")
        print(f"Mask:         {self.get_mask()}")
        print(f"Network:      {self.get_network_id()}")
        print(f"Broadcast:    {self.get_broadcast()}")
        print(f"First IP:     {self.get_first_ip()}")
        print(f"Last IP:      {self.get_last_ip()}")
        print(f"Host Bits:    {self.get_host_bits()}")
        print(f"Max Hosts:    {self.get_max_hosts()}")

    def get_network_details(self):
        """Bütün əsas məlumatları bir dəfəyə qaytarır."""
        return (
            self.get_network_id(),
            self.get_broadcast(),
            self.get_first_ip(),
            self.get_last_ip()
        )
