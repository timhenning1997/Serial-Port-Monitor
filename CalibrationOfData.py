import numpy as np


class CalibrationOfData():
    def __init__(self):
        self.port = ""
        self.configured = False
        self.config = {}
        self.coeff = [[0], [0]]
        self.udcoeff = []
        self.ndsl = 0
        self.fileName = ""
        self.pathName = ""

    def readCalibrationFile(self, filepath: str):
        try:
            self.config = np.genfromtxt(filepath, skip_header=1, delimiter=',',
                                        dtype=(np.dtype('U5'), np.dtype('U10'), float, float, float, float, float, float,
                                               float, np.dtype('U10'), int, bool, float, float, int),
                                        names='Kanal, Name, UD2, UD1, UD0, K3, K2, K1, K0, Funktion,TEkan, Geraetekal, Uref, Ra, RefTh')

            self.coeff = np.asarray([self.config['K3'], self.config['K2'], self.config['K1'], self.config['K0']]).transpose()

            self.udcoeff = np.asarray([self.config['UD2'], self.config['UD1'], self.config['UD0']]).transpose()

            self.ndsl = len(self.config['Kanal'])

            self.fileName = filepath.split('/')[len(filepath.split('/')) - 1]
            self.pathName = filepath
            self.configured = True
            return True
        except:
            print("Could not load calibration file!")
            return None

    def getName(self, index: int):
        if index < len(self.config['Name']):
            return self.config['Name'][index]
        return None

    def getKanal(self, index: int):
        if index < len(self.config['Kanal']):
            return self.config['Kanal'][index]
        return None

    def calibrate(self, data: []):
        if not self.configured:
            return None
        calData = []
        try:
            n = 0
            for element in self.config['Geraetekal']:
                if element:
                    if self.config['Funktion'][n] == 'Pol':
                        calData.append(np.polyval(self.coeff[n, :], data[n]))
                    elif self.config['Funktion'][n] == 'Ube':
                        x = data[n]/data[self.config['TEkan'][n]-2]
                        calData.append(np.polyval(self.coeff[n, :], x))
                    elif self.config['Funktion'][n] == 'NTC':
                        calData.append(self.coeff[n, 0] + self.coeff[n, 1] * np.log(data[n])
                                   + self.coeff[n, 2] * np.log(data[n]) ** 3)
                    elif self.config['Funktion'][n] == 'G12N':
                        calData.append((1/(1/298.15 + (np.log(self.coeff[n, 1]*data[24]/data[n]-self.coeff[n, 0]) +self.coeff[n, 3]*np.log(self.coeff[n, 1]*data[24]/data[n]-self.coeff[n, 0])**2)/self.coeff[n, 2])))
                    elif self.config['Funktion'][n] == 'PTC':
                        x = data[n]
                        calData.append((self.coeff[n, 0] + np.log(self.coeff[n, 1])*(1/(x-1))/self.coeff[n, 2])**-1)
                    elif self.config['Funktion'][n] == 'TE':
                        data[n] -= data[self.config['TEkan'][n]]
                        calData.append(np.polyval(self.coeff[n, :], data[n]))
                    elif self.config['Funktion'][n] == 'Pol12':
                        calData.append(np.polyval(self.coeff[n, :], data[n]))
                    elif self.config['Funktion'][n] == 'Pol8':
                        calData.append(np.polyval(self.coeff[n, :], data[n]))
                    else:
                        calData.append(data[n])
                else:
                    if self.config['Funktion'][n]== 'Pol8':
                        x = data[n] / 1023
                    elif self.config['Funktion'][n]== 'Pol12':
                        x = data[n] / 4095
                    else:
                        x = data[n] / 65535
                    if self.config['Funktion'][n] == 'Pol':
                        calData.append(np.polyval(self.coeff[n, :], x))
                    elif self.config['Funktion'][n] == 'NTC':
                        try:
                            UB = np.polyval(self.udcoeff[24, :], data[24])
                            UA = x*self.config['Uref'][n]
                            Rth = (UB / UA - 1) * self.config['Ra'][n] * 1e+3
                            calData.append(1/(1/self.coeff[n, 1] + (np.log(Rth/self.coeff[n, 0]) + self.coeff[n, 3] * np.log(Rth/self.coeff[n, 0]) ** 2)/self.coeff[n, 2]))
                        except RuntimeWarning as e:
                            print('Error occured: ' + str(e) + 'x =' + str(x))
                    elif self.config['Funktion'][n] == 'TWS':
                        try:
                            if data[self.config['TEkan'][n]-2] < 1000:
                                x7 = 42233.0 / 65535
                            else:
                                x7 = data[self.config['TEkan'][n]-2]/65535
                            Rth = (x7 * self.config['UD2'][n]/ x - 1) * self.config['Ra'][n]
                            T = (1/self.coeff[n, 1] + (np.log(Rth/self.coeff[n, 0]) + self.coeff[n, 3] * np.log(Rth/self.coeff[n, 0]) ** 2)
                                            /self.coeff[n, 2])**-1-273.15
                            calData.append(T)
                        except RuntimeWarning as e:
                            print('Error occured: ' + str(e) + 'x =' + str(x))
                    elif self.config['Funktion'][n] == 'TE':
                        x -= data[self.config['TEkan'][n]-2] / 65535
                        x = np.polyval(self.udcoeff[n, :], x)
                        calData.append(np.polyval(self.coeff[n, :], x))
                    elif self.config['Funktion'][n] == 'PTC':
                        calData.append((self.coeff[n, 0] + np.log(self.coeff[n, 1])*(1/(x-1))/self.coeff[n, 2])**-1)
                    elif self.config['Funktion'][n] == 'Pol12':
                        calData.append(np.polyval(self.coeff[n, :], x))
                    elif self.config['Funktion'][n] == 'Pol8':
                        calData.append(np.polyval(self.coeff[n, :], x))
                    elif self.config['Funktion'][n] == "RPM":
                        rpm = 147463800/(data[n] * 65536 + data[n+1])
                        calData.append(rpm)
                    elif self.config['Funktion'][n] == "HDA":
                        Uhd = 4.08*1.33
                    elif self.config['Funktion'][n] == "Volt":
                        calData.append(np.polyval(self.coeff[n, :], x*65535/data[self.config['TEkan'][n]-2]))
                    elif self.config['Funktion'][n] == "U5":
                        calData.append(2.5*1023/data[n])
                    elif self.config['Funktion'][n] == "NTCTele":
                        pass
                        #(1/(A0 + np.log(A1*(1/(mw/1023)-1))/A2))
                    elif self.config['Funktion'][n] == "NTCG12":
                        if data[n] != 0:
                            mw = data[self.config['TEkan'][n]-2]/data[n]
                        else:
                            mw = 0
                        calData.append((1/(1/298.15 + (np.log(self.coeff[n, 1]*mw-self.coeff[n,0])+self.coeff[n, 3]*np.log(self.coeff[n, 1]*mw-self.coeff[n, 0])**2)/self.coeff[n,2]))-273.15)
                    elif self.config['Funktion'][n] == "NTCBG":
                        mw = data[n]/data[self.config['TEkan'][n]-2]
                        calData.append(1/(1/298.15 + (np.log(self.coeff[n, 0]/(mw-1)-self.coeff[n, 1])+self.coeff[n, 3]*np.log(self.coeff[n, 0]/(mw-1)-self.coeff[n, 1])**2)/self.coeff[n,2])-273.15)

                    else:
                        calData.append(data[n])
                n += 1
            return np.asarray(calData)
        except ValueError:
            print("ValueError")
            return None
        except TypeError:
            print("TypeError")
            return None
        except IndexError:
            print("IndexError")
            return None
        except:
            print("Calibration failed: unknown reason")
            return None
