
from utime import sleep_ms

class VEML6030:

    # I2C address
    ADDRESS = 0x10

    # VEML6030 command codes
    CONFIG = 0x00
    READ_DATA = 0x04


    # Constructor

    def __init__(self, bus):
        self.bus = bus

    # Low-level I2C helpers

    def write_u24(self, value):
        """
        Write 3 bytes to veml6030 using i2c.
        
        :param value: array containig the three bytes to be written.
        """
        self.bus.writeto(self.ADDRESS, bytes([value[0] & 0xFF, value[1] & 0xFF, value[2] & 0xFF]), True)

    def read_u16(self, cmd):
        """
        Read value from veml6030 using command code.
        
        :param cmd: command code to select the register where data is read.
        cmd = 0x04 : ASL register is selected.
        """
        self.bus.writeto(self.ADDRESS, bytes([cmd & 0xFF]), False)
        data = self.bus.readfrom(self.ADDRESS, 2)
        return (data[1] << 8) | data[0]
    

    # Public API (student-facing)

    def init(self):
        """
        Configure the veml6030 ambient light sensor with settings:

        Bit 12:11 = 10 (gain1/8)
        Bit 9:6 = 0000 (Integration time 100ms)
        Bit 5:4 Persisentec protect number setting (00 -> 1) 
        Bit 1 =0 INT disable
        Bit 0 = 0 Power on

        Configuration:
        0b0001 0000 0000 0000 -> =0x1000

        """ 
        config = [self.CONFIG, 0x00, 0x10]      #[command code, data(LSB), data(MSB)]
        self.write_u24(config)
        sleep_ms(10)


    def read(self):
        """
        Read veml6030 ambient light sensor value.

        returns the ambient light level in Lux (float)
        
        """
    
        bits = self.read_u16(self.READ_DATA)
        luxVal_uncorrected = bits * 0.5376      #convert read bits to lux
        if luxVal_uncorrected > 1000:
            luxVal = ((0.00000000000060135 * luxVal_uncorrected ** 4) - 
                        (0.0000000093924 * luxVal_uncorrected ** 3) + 
                        (0.000081488 * luxVal_uncorrected ** 2) + 
                        (1.0023 * luxVal_uncorrected)
                        )
            return luxVal

        return luxVal_uncorrected


    def stop(self):
        """
        Power off the veml6030 ambient light sensor.
        
        """
            #Set the bit 0 in the configuration to 1 -> power off
            # 0b0001 0000 0000 0001
        config = [self.CONFIG, 0x01, 0x10]   #[command code, data(LSB), data(MSB)]
        self.write_u24(config)
        sleep_ms(10)
