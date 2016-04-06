'''
    Simple MJPEG streaming server + FIR
'''
import time, sensor, pyb, network, usocket, fir

SSID=''         # Network SSID
KEY=''          # Network key
HOST = ''       # Use first available interface
PORT = 8000     # Arbitrary non-privileged port

led_r = pyb.LED(1)
led_b = pyb.LED(2)
led_g = pyb.LED(3)

# Reset sensor
sensor.reset()

# Set sensor settings
sensor.set_contrast(1)
sensor.set_brightness(1)
sensor.set_saturation(1)
sensor.set_gainceiling(16)
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.GRAYSCALE)

# Initialize the thermal sensor
fir.init()

# Init wlan module and connect to network
wlan = network.WINC()
wlan.connect(SSID, key=KEY, security=wlan.WPA_PSK)

# We should have a valid IP now via DHCP
print(wlan.ifconfig())

# Create server socket
s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

# Bind and listen
s.bind((HOST, PORT))
s.listen(5)

# Set timeout to 1s
s.settimeout(1.0)

print ('Waiting for connections..')
client, addr = s.accept()
print ('Connected to ' + addr[0] + ':' + str(addr[1]))

# Read request from client
data = client.recv(1024)

# Should parse client request here

# Send multipart header
client.send("HTTP/1.1 200 OK\r\n"   \
            "Server: OpenMV\r\n"    \
            "Content-Type: multipart/x-mixed-replace;boundary=openmv\r\n" \
            "Cache-Control: no-cache\r\n" \
            "Pragma: no-cache\r\n\r\n")

# Start streaming images
while (True):
    image = sensor.snapshot()
    # Capture FIR data
    #   ta: Ambient temperature
    #   ir: Object temperatures (IR array)
    #   to_min: Minimum object temperature
    #   to_max: Maximum object temperature
    ta, ir, to_min, to_max = fir.read_ir()

    # Scale the image and belnd it with the framebuffer
    fir.draw_ir(image, ir)

    # Draw ambient, min and max temperatures.
    image.draw_string(0, 0, "Ta: %0.2f"%ta, color = (0xFF, 0x00, 0x00))
    image.draw_string(0, 8, "To min: %0.2f"%(to_min+ta), color = (0xFF, 0x00, 0x00))
    image.draw_string(0, 16, "To max: %0.2f"%(to_max+ta), color = (0xFF, 0x00, 0x00))

    
    client.send("\r\n--openmv\r\n"  \
                "Content-Type: image/jpeg\r\n"\
                "Content-Length:"+str(image.size())+"\r\n\r\n")
    client.send(image.compress(35))
    
client.close()
