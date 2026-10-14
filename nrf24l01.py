from micropython import const
import time

# Comandos SPI
_RX_PAYLOAD = const(0x61)
_TX_PAYLOAD = const(0xA0)
_FLUSH_TX = const(0xE1)
_FLUSH_RX = const(0xE2)
_SETUP_AW = const(0x03)
_SETUP_RETR = const(0x04)
_RF_CH = const(0x05)
_RF_SETUP = const(0x06)
_STATUS = const(0x07)
_RX_ADDR_P0 = const(0x0A)
_TX_ADDR = const(0x10)
_RX_PW_P0 = const(0x11)
_FIFO_STATUS = const(0x17)
_CONFIG = const(0x00)
_EN_AA = const(0x01)
_EN_RXADDR = const(0x02)
_DYNPD = const(0x1C)
_FEATURE = const(0x1D)

class NRF24L01:
    def __init__(self, spi, cs, ce, payload_size=32, channel=10):
        self.spi = spi
        self.cs = cs
        self.ce = ce
        self.payload_size = payload_size
        self.cs.init(self.cs.OUT, value=1)
        self.ce.init(self.ce.OUT, value=0)
        
        self.reg_write(_CONFIG, 0x0A) # Power up, CRC 2 bytes
        time.sleep_ms(5)
        
        self.reg_write(_SETUP_AW, 0x03) # 5-byte address
        self.reg_write(_SETUP_RETR, 0x3F) # 15 retries, 1000us delay
        self.reg_write(_EN_AA, 0x01) # Auto-ACK on pipe 0
        self.reg_write(_EN_RXADDR, 0x01) # Enable data pipe 0
        self.reg_write(_RF_SETUP, 0x07) # 1Mbps, 0dBm (MAX)
        self.reg_write(_DYNPD, 0x00) # Disable dynamic payloads
        self.reg_write(_FEATURE, 0x00) # Disable features
        
        self.set_channel(channel)
        self.reg_write(_RX_PW_P0, self.payload_size)
        
        self.reg_write(_FLUSH_RX, 0)
        self.reg_write(_FLUSH_TX, 0)
        self.reg_write(_STATUS, 0x70) # Clear interrupts

    def reg_read(self, reg):
        self.cs(0)
        self.spi.read(1, reg)
        res = self.spi.read(1)
        self.cs(1)
        return res[0]

    def reg_write(self, reg, value):
        self.cs(0)
        self.spi.read(1, reg | 0x20)
        self.spi.write(bytes([value]))
        self.cs(1)

    def reg_write_bytes(self, reg, buf):
        self.cs(0)
        self.spi.read(1, reg | 0x20)
        self.spi.write(buf)
        self.cs(1)

    def set_channel(self, channel):
        self.reg_write(_RF_CH, channel)

    def set_power(self, power):
        # power: 0=-18dBm, 1=-12dBm, 2=-6dBm, 3=0dBm
        setup = self.reg_read(_RF_SETUP) & 0xF9
        self.reg_write(_RF_SETUP, setup | (power << 1) | 0x01)

    def open_tx_pipe(self, address):
        self.reg_write_bytes(_RX_ADDR_P0, address)
        self.reg_write_bytes(_TX_ADDR, address)

    def open_rx_pipe(self, pipe_id, address):
        self.reg_write_bytes(_RX_ADDR_P0, address)

    def start_listening(self):
        self.reg_write(_CONFIG, 0x0F) # RX mode
        self.reg_write(_STATUS, 0x70)
        self.ce(1)
        time.sleep_us(130)

    def stop_listening(self):
        self.ce(0)
        self.reg_write(_CONFIG, 0x0E) # TX mode

    def any(self):
        return not bool(self.reg_read(_FIFO_STATUS) & 0x01)

    def recv(self):
        self.cs(0)
        self.spi.read(1, _RX_PAYLOAD)
        buf = self.spi.read(self.payload_size)
        self.cs(1)
        self.reg_write(_STATUS, 0x40) # Clear RX_DR
        return buf

    def send(self, buf, timeout=500):
        self.stop_listening()
        self.reg_write(_FLUSH_TX, 0)
        self.reg_write(_STATUS, 0x30) # Clear TX_DS, MAX_RT
        
        self.cs(0)
        self.spi.read(1, _TX_PAYLOAD)
        self.spi.write(buf)
        if len(buf) < self.payload_size:
            self.spi.write(b'\x00' * (self.payload_size - len(buf)))
        self.cs(1)
        
        self.ce(1)
        time.sleep_us(15)
        self.ce(0)
        
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
            status = self.reg_read(_STATUS)
            if status & 0x20: # TX_DS (Success)
                self.reg_write(_STATUS, 0x20)
                return True
            if status & 0x10: # MAX_RT (Failed)
                self.reg_write(_STATUS, 0x10)
                return False
        return False