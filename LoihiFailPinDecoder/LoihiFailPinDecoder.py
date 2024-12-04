import sys
import os

passReturnCodes = {
    "35626200": 0x00,
    "35626210": 0x00,
    "35626201": 0x01,
    "35626211": 0x01,
    "35626202": 0x02,
    "35626212": 0x02,
    "35626203": 0x03,
    "35626213": 0x03,
    "35626204": 0x04,
    "35626214": 0x04,
    "35626205": 0x05,
    "35626215": 0x05
}

failReturnCodes = {
    "35626200": 0x10,
    "35626210": 0x10,
    "35626201": 0x11,
    "35626211": 0x11,
    "35626202": 0x12,
    "35626212": 0x12,
    "35626203": 0x13,
    "35626213": 0x13,
    "35626204": 0x14,
    "35626214": 0x14,
    "35626205": 0x15,
    "35626215": 0x15
}

failpins = {
    "0003071": 0x01,
    "0003063": 0x02,
    "0003057": 0x04,
    "0003064": 0x08,
    "0003069": 0x10,
    "0003061": 0x20,
    "0003056": 0x40,
    "0003068": 0x80
}

failPinsNamesMap = {
    "0003071": "TC_GPIO_WR_D0_TSOM",
    "0003063": "TC_GPIO_WR_D1_TSOM",
    "0003057": "TC_GPIO_WR_D2_TSOM",
    "0003064": "TC_GPIO_WR_D3_TSOM",
    "0003069": "TC_GPIO_WR_D4_TSOM",
    "0003061": "TC_GPIO_WR_D5_TSOM",
    "0003056": "TC_GPIO_WR_D6_TSOM",
    "0003068": "TC_GPIO_WR_D7_TSOM"
}

class Fail:
    def __init__(self, time, lot, wafer, x, y, faildata, bin):
        self.time = time
        self.lot = lot
        self.wafer = wafer
        self.x = x
        self.y = y
        self.bin = bin
        if bin.startswith("35"):
            self.faildata = faildata
            self.errorCode = self.getErrorCode(bin, faildata)
            self.failPinsNames = self.getFailPinsNames(faildata)

    def getErrorCode(self, bin, faildata):
        faildata = faildata.strip("{").strip("}")
        errorCode = passReturnCodes[bin]
        for failpin in faildata.split(","):
            if failpin not in failpins:
                raise Exception("Unexpected fail pin: " + failpin)
            errorCode ^= failpins[failpin]
        return errorCode

    def getFailPinsNames(self, faildata):
        failPinsNames = faildata.strip("{").strip("}")
        for pin, name in failPinsNamesMap.items():
            failPinsNames = failPinsNames.replace(pin, name)
        return failPinsNames

def getItuffFiles(directory):
    filesToDecode = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ITF"):
                print(f"Found .ITF named {os.path.join(root, file)}")
                filesToDecode.append(os.path.join(root, file))
    return filesToDecode

def getFailUnits(ituffsToDecode):
    fails = []
    faildata = ""
    for ituffFile in ituffsToDecode:
        with open(ituffFile, 'r') as ituff:
            for line in ituff:
                line = line.strip()
                if "6_lotid_" in line:
                    lot = line[len("6_lotid_"):]
                elif "4_wafid_" in line:
                    wafer = line[len("4_wafid_"):]
                elif "3_wafxloc_" in line:
                    x = line[len("3_wafxloc_"):]
                elif "3_wafyloc_" in line:
                    y = line[len("3_wafyloc_"):]
                elif "3_dvtststdt_" in line:
                    time = line[len("3_dvtststdt_"):]
                elif "2_faildata_" in line:
                    faildata = line[len("2_faildata_"):]
                elif "3_binn_" in line:
                    bin = line[len("3_binn_"):]
                    fails.append(Fail(time, lot, wafer, x, y, faildata, bin))
    return fails

def decode(directory_path):
    ituffsToDecode = getItuffFiles(directory_path)
    failUnits = getFailUnits(ituffsToDecode)
    incorrectErrorCodes = 0
    correctErrorCodes = 0
    with open("LoihiData.csv", 'w') as csv:
        csv.write("Time,Lot,Wafer,X,Y,Bin,Expected Pass (0x),Expected Pass (0b),Expected Fail (0x),Expected Fail (0b),Actual Return Code (0x),Measured Return Code (0b),Failing Pins\n")
        for fail in failUnits:
            if fail.bin.startswith("35"):
                csv.write(f"{fail.time},{fail.lot},{fail.wafer},{fail.x},{fail.y},{fail.bin},{passReturnCodes[fail.bin]:#04x},{passReturnCodes[fail.bin]:#010b}, " \
                          f"{failReturnCodes[fail.bin]:#04x},{failReturnCodes[fail.bin]:#010b},{fail.errorCode:#04x},{fail.errorCode:#010b},{fail.failPinsNames.replace(',', ' ')}\n")
                if failReturnCodes[fail.bin] == fail.errorCode:
                    correctErrorCodes += 1
                else:
                    incorrectErrorCodes += 1
                print(f"Bin {fail.bin}, Expected Fail {failReturnCodes[fail.bin]:#04x} ({failReturnCodes[fail.bin]:#010b}), Expected Pass {passReturnCodes[fail.bin]:#04x} " \
                      f"({passReturnCodes[fail.bin]:#010b}), Got {fail.errorCode:#04x} ({fail.errorCode:#010b}), FailPins {fail.failPinsNames}")
            else:
                csv.write(f"{fail.time},{fail.lot},{fail.wafer},{fail.x},{fail.y},{fail.bin},,,,,,,\n")
    print(f"{len(failUnits)} in total")
    print("Correct Error Codes = " + str(correctErrorCodes))
    print("Incorrect Error Codes = " + str(incorrectErrorCodes))

if __name__=="__main__":
    decode(sys.argv[1])