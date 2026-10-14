from machine import Pin, I2C, SPI
import time
from ssd1306 import SSD1306_I2C
from nrf24l01 import NRF24L01

# Configuración de Hardware
led_tx = Pin(21, Pin.OUT) # Verde (Parpadea al enviar)
led_rx = Pin(20, Pin.OUT) # Rojo
btn_canal = Pin(12, Pin.IN, Pin.PULL_UP)
btn_potencia = Pin(13, Pin.IN, Pin.PULL_UP)

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
csn = Pin(17, mode=Pin.OUT, value=1)
ce = Pin(15, mode=Pin.OUT, value=0)

# Pantalla de inicio
oled.fill(0)
oled.text("NODO A (TX)", 20, 20)
oled.text("Iniciando...", 20, 40)
oled.show()
time.sleep(2)

# Iniciar Radio
nrf = NRF24L01(spi, csn, ce, payload_size=32)
canales = [10, 50, 100]
idx_canal = 0
pot_nom = ["MIN", "LOW", "HIGH", "MAX"]
pot_val = [0, 1, 2, 3]
idx_potencia = 3
direccion = b"UMNG1" # El "nombre" del túnel de comunicación

nrf.set_channel(canales[idx_canal])
nrf.set_power(pot_val[idx_potencia])
nrf.open_tx_pipe(direccion)
nrf.stop_listening() # Modo transmisor

def actualizar_pantalla(mensaje_enviado=""):
    oled.fill(0)
    oled.text("--- NODO A (TX) ---", 0, 0)
    oled.text(f"CH:{canales[idx_canal]} PT:{pot_nom[idx_potencia]}", 0, 15)
    oled.text("Vel: 1 Mbps", 0, 30)
    oled.text("Enviando:", 0, 45)
    oled.text(mensaje_enviado[:16], 0, 55)
    oled.show()

actualizar_pantalla()
ultimo_envio = time.ticks_ms()
contador = 0

# Lista de mensajes que pide la guía (Nombres y alfabetos)
mensajes = ["Fransua y Freddy", "ABCDEFGHIJKLM", "Prueba UMNG"]

while True:
    # Botón Canal
    if btn_canal.value() == 0:
        idx_canal = (idx_canal + 1) % len(canales)
        nrf.set_channel(canales[idx_canal])
        actualizar_pantalla()
        time.sleep(0.3)
        
    # Botón Potencia
    if btn_potencia.value() == 0:
        idx_potencia = (idx_potencia + 1) % len(pot_val)
        nrf.set_power(pot_val[idx_potencia])
        actualizar_pantalla()
        time.sleep(0.3)

    # Enviar mensaje automáticamente cada 2 segundos
    if time.ticks_diff(time.ticks_ms(), ultimo_envio) > 2000:
        # Armar mensaje (ej: "Jose Rugeles 1")
        msg_str = f"{mensajes[contador % 3]} {contador}" 
        actualizar_pantalla(msg_str)
        
        try:
            nrf.send(msg_str.encode('utf-8')) # Se envía por el aire
            # Destello Verde de éxito
            led_tx.value(1)
            time.sleep(0.05)
            led_tx.value(0)
        except:
            pass
            
        contador += 1
        ultimo_envio = time.ticks_ms()
