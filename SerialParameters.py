import serial


class SerialParameters:
    def __init__(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False,
                 write_timeout=None, dsrdtr=False, inter_byte_timeout=None, exclusive=None,
                 local_echo=False, appendCR=False, appendLF=False):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.write_timeout = write_timeout
        self.dsrdtr = dsrdtr
        self.inter_byte_timeout = inter_byte_timeout
        self.exclusive = exclusive
        self.readTextIndex = "read_line"
        self.readBytes = 1
        self.readUntil = ''
        self.DTR = False
        self.maxSignalRate = 10  # Hz
        self.Kennbin = ""

        self.local_echo = local_echo
        self.appendCR = appendCR
        self.appendLF = appendLF
