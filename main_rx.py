from machine import Pin, I2C, SPI
import time
from ssd1306 import SSD1306_I2C
from nrf24l01 import NRF24L01

# Configuración de Hardware
led_tx = Pin(21, Pin.OUT) # Azul
led_rx = Pin(20, Pin.OUT) # Amarillo (Parpadea al recibir)
btn_canal = Pin(12, Pin.IN, Pin.PULL_UP)
btn_potencia = Pin(13, Pin.IN, Pin.PULL_UP)

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
csn = Pin(17, mode=Pin.OUT, value=1)
ce = Pin(15, mode=Pin.OUT, value=0)

# Pantalla de inicio
oled.fill(0)
oled.text("NODO B (RX)", 20, 20)
oled.text("Iniciando...", 20, 40)
oled.show()
time.sleep(2)

nrf = NRF24L01(spi, csn, ce, payload_size=32)
canales = [10, 50, 100]
idx_canal = 0
pot_nom = ["MIN", "LOW", "HIGH", "MAX"]
pot_val = [0, 1, 2, 3]
idx_potencia = 3
direccion = b"UMNG1"

def iniciar_radio_rx():
    nrf.set_channel(canales[idx_canal])
    nrf.set_power(pot_val[idx_potencia])
    nrf.open_rx_pipe(0, direccion)
    