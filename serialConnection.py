import json
import marshal
import os
import time
import types
import serial
from PIL import Image
from struct import pack
from threading import Thread
import serial.serialutil
from constants import *
import serial.tools.list_ports


runThreads = True
devices = []
devicesIdentifier = []

devicesImagesStatus = {}
devicesIntegrationsArgs = {}
first_scan = set()
scanned_ports = set()

def serial_ports():
    global scanned_ports
    ports = set()

    devices = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(devices):
        ports.add(port)
    
    for port in scanned_ports.copy():
        if port not in ports:
            scanned_ports.remove(port) # Remove if not connected anymore
 
    ports -= scanned_ports # Don't check for known ports
    print(ports, scanned_ports)
    return ports

def updateSecondImages(i, device):
    with open(f"settings/savedData-{devicesIdentifier[i]}.json", "r") as f:
        settings = json.load(f)
    for num in settings:
        try:
            setting = settings[num]
            if setting["second_image"] != "":
                if setting["start-integration"] != "False":
                    if setting["start-integration"] not in devicesIntegrationsArgs:
                        with open(os.path.join(sitePackagesPath, setting["groupRaw"], setting["start-integration"]), "rb") as f:
                            func = types.FunctionType(marshal.loads(marshal.load(f)), globals())
                        data = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]))
                        print(data)
                        devicesIntegrationsArgs[setting["start-integration"]] = data
                with open(os.path.join(sitePackagesPath, setting["groupRaw"], setting["check-second"]), "rb") as f:
                    func = types.FunctionType(marshal.loads(marshal.load(f)), globals())
                if setting["start-integration"] in devicesIntegrationsArgs:
                    status, updatedNum = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]), devicesIntegrationsArgs[setting["start-integration"]])
                else:
                    status, updatedNum = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]))
                if status:
                    # Change so it is the same as the other one before changing it.
                    if updatedNum == 1:
                        updatedNum = 0
                    elif updatedNum == 0:
                        updatedNum = 1
                    
                    if not num in devicesImagesStatus[device] or devicesImagesStatus[device][num] != updatedNum:
                        print("updating Image")
                        device.write(f"updateImage:{num}:{updatedNum}\n".encode())
                    devicesImagesStatus[device][num] = updatedNum
        except Exception as e:
            print("E" + str(e))

def connections():
    global devices, devicesIdentifier
    while runThreads:
        oldDevices = []
        oldDevicesIdentifier = []
        for device, identifier in zip(devices, devicesIdentifier):
            try:
                device.write("connection\n".encode())
                oldDevices.append(device)
                oldDevicesIdentifier.append(identifier)
            except serial.serialutil.SerialException:
                pass # Device disconnected
        devices = oldDevices
        devicesIdentifier = oldDevicesIdentifier
        ports = serial_ports()
        for port in ports:
            try:
                initializing_device = False 
                ser = serial.Serial(port=port, baudrate=115200, bytesize=8, timeout=1)
                ser.write("uscs\n".encode())
                recived = ser.readline().decode()[:-1]
                print(recived)
                if recived.startswith("uscc"):
                    ser.write("uscsc".encode())
                    devices.append(ser)
                    devicesIdentifier.append(recived.split(":")[1])
                elif recived.startswith("uscnotready"):
                    initializing_device = True # If device is starting up
                    ser.close()
                else:
                    ser.close()
            except Exception as e:
                print(e)
            finally:
                if not initializing_device:
                    if port in first_scan:
                        scanned_ports.add(port)
                        first_scan.remove(port)
                    first_scan.add(port)
                else:
                    print("Device not ready, initializing...")
    
        print(devices)
        timeToWait = 3
        for _ in range(timeToWait):
            time.sleep(1)
            if not runThreads:
                break
    threadsRunning[0] = False

def serListener():
    while runThreads:
        for i,device in enumerate(devices):
            try:
                data = device.readline().decode()[:-1]
                if data:
                    print(data)
                    if data.startswith("uscnotready"):
                        print("closing...")
                        first_scan.remove(device.port)
                        scanned_ports.remove(device.port)
                        devices.pop(i)
                        device.close()
                    if data.startswith("btd"):
                        number = int(data[3:])
                        print(devicesIdentifier[i], number)
                        with open(f"settings/savedData-{devicesIdentifier[i]}.json", "r") as f:
                            settings = json.load(f)
                        setting = settings[str(number)]
                        print(setting)
                        if setting["start-integration"] != "False":
                            if setting["start-integration"] not in devicesIntegrationsArgs:
                                with open(os.path.join(sitePackagesPath, setting["groupRaw"], setting["start-integration"]), "rb") as f:
                                    func = types.FunctionType(marshal.loads(marshal.load(f)), globals())
                                data = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]))
                                devicesIntegrationsArgs[setting["start-integration"]] = data
                        try:
                            with open(os.path.join(sitePackagesPath, setting["groupRaw"], setting["function"]), "rb") as f:
                                func = types.FunctionType(marshal.loads(marshal.load(f)), globals())
                            if setting["start-integration"] in devicesIntegrationsArgs:
                                status, image = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]), devicesIntegrationsArgs[setting["start-integration"]])
                            else:
                                status, image = func(setting["settings"], os.path.join(sitePackagesPath, setting["groupRaw"]))
                            print(image)
                            if status:
                                device.write(f"btdok{image}\n".encode())
                                updateSecondImages(i, device)
                            else:
                                device.write(f"btderror\n".encode())
                        except Exception as e:
                            print(e)
                            device.write(f"btderror\n".encode())
            except Exception as e:
                print(e)
    threadsRunning[1] = False

def updateImage():
    while runThreads:
        for i,device in enumerate(devices):
            if not device in devicesImagesStatus:
                devicesImagesStatus[device] = {}
            updateSecondImages(i, device)
        timeToWait = 1
        for _ in range(timeToWait):
            time.sleep(1)
            if not runThreads:
                break
    threadsRunning[2] = False

def encodeImage(in_path):
    image = Image.open(in_path)
    resized = image.resize((90, 90))
    resized.convert('RGB')
    pixels = list(resized.getdata())
    with open(r"assets\icons\current-raw-image.raw", 'wb') as f:
        for pix in pixels:
            r = (pix[0] >> 3) & 0x1F
            g = (pix[1] >> 2) & 0x3F
            b = (pix[2] >> 3) & 0x1F
            f.write(pack('>H', (r << 11) + (g << 5) + b))
    return r"assets\icons\current-raw-image.raw"

def uploadImage(ser: serial.Serial, pathFile, pathSave):
    timeStart = time.time()
    pathOpen = encodeImage(pathFile)
    with open(pathOpen, "rb") as f:
        image = f.read()
    ser.write(f"imageComing:{pathSave}\n".encode())
    size = len(image)
    for i in range(0, size, 32):
        chunk_size = min(32, size - i)
        chunk = image[i : i + chunk_size]
        ser.write(chunk)
        time.sleep(.01)
    ser.write("stop\n".encode())
    timeEnd = time.time()
    return timeEnd - timeStart

def uploadJSON(ser: serial.Serial, data: str, pathSave):
    ser.write(f"jsonComing:{pathSave}\n".encode())
    data = encodeLists(data).encode()
    size = len(data)
    for i in range(0, size, 32):
        chunk_size = min(32, size - i)
        chunk = data[i : i + chunk_size]
        ser.write(chunk)
        time.sleep(.01)
    ser.write("stop\n".encode())

def start():
    global threadConnections, threadSerialListener, threadUpdateImage, threadsRunning
    threadConnections = Thread(target=connections)
    threadConnections.start()
    threadSerialListener = Thread(target=serListener)
    threadSerialListener.start()
    threadUpdateImage = Thread(target=updateImage)
    threadUpdateImage.start()
    threadsRunning = [True, True, True]

def restart():
    global runThreads, threadsRunning, first_scan, scanned_ports
    first_scan = set()
    scanned_ports = set()
    runThreads = True
    threadsRunning = [True, True, True]
    start()

def stop():
    global runThreads, threadsRunning
    runThreads = False
    while True:
        print(threadsRunning)
        if not True in threadsRunning:
            print("stop")
            break


def encodeLists(dataList: list):
    finalString = ""
    for i,data in enumerate(dataList):
        for x, subdata in enumerate(data):
            if x+1 != len(data): finalString += subdata + ";"
            else: finalString += subdata
        if i+1 != len(dataList): finalString += ","
    return finalString

def decodeString(dataString: str):
    mainList = dataString.split(",")
    finalList = []
    for subData in mainList: 
        if ";" in subData:
            finalList.append(subData.split(";"))
        else:
            finalList.append(subData)
    return finalList

def listdir(ser: serial.Serial, path="/", sizeData:bool=True):
    ser.write(f"ls:{path}:{sizeData}\n".encode())
    data = ser.readline().decode()[:-1]
    if not sizeData:
        data = decodeString(data)
    return data

def updateScreen(ser: serial.Serial):
    ser.write("updateScreen\n".encode())