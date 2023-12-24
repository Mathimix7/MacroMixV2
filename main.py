import wx
import wx.adv
import wx.grid
import serialConnection
import os
import logging
from constants import *
import json
import subprocess
import time
import pygame
import pygame_gui
from PIL import Image
from tkinter import filedialog
import marshal
import types
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from constants import *
from serial.serialutil import SerialException
import pypresence
import requests
import ctypes
import flask
import webbrowser
import socket
import sys

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('app')

run = True
stoppedSuccesfully = False

def app():
    global run, applicationRunning, stoppedSuccesfully
    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, pygame.NOFRAME)
    pygame.display.set_caption(APP_NAME)
    pygame.display.set_icon(pygame.image.load(APP_ICON))
    pygame.init()

    numberOfBoxesLength = 3
    numberOfBoxesHeight = 2
    arrowImage = pygame.image.load(r"assets/assets/arrow.png")

    phase = "devices" # This is used to know what to display/show

    with open("actionsList.json", "r") as f:
        actionsList = json.load(f)

    allTextInputConfig = [] # This is used to hide all the text input on changing the config item and then just showing the right one
    images = {}
    imagesGroup = {}
    for group in actionsList:
        path = os.path.join("assets", "iconsSideBar", group["image"])
        images[group["image"]] = pygame.image.load(path).convert_alpha()
        for item in group["objectsImages"]:
            path = os.path.join("assets", "iconsSideBar", item)
            imagesGroup[item] = pygame.image.load(path).convert_alpha()

    icons = {}
    for group in actionsList:
        for item in group["itemsImages"]:
            image = Image.open(os.path.join(pathIconsImages, item)).resize((90, 90))
            image.save(os.path.join(pathIconsImages, "current-image.png"))
            icons[item] = pygame.image.load(os.path.join(pathIconsImages, "current-image.png")).convert_alpha()

    currentItems = {}
    currentItemsImages = {}
    currentItemsGroup = {}
    currentItemsSettings = {}
    currentItemsSettingsNameValue = {}
    currentItemsSettingsData = {}
    currentItemsSettingsOptions = {}
    number = 0
    for i in range(numberOfBoxesLength):
        for x in range(numberOfBoxesHeight):
            currentItems[number] = None
            currentItemsImages[number] = None
            currentItemsSettings[number] = None
            currentItemsGroup[number] = None
            currentItemsSettingsData[number] = None
            currentItemsSettingsOptions[number] = {}
            currentItemsSettingsNameValue[number] = {}
            number += 1

    def marshal_to_func(path):
        with open(path, 'rb') as f:
            function_data = marshal.loads(marshal.load(f))
        func = types.FunctionType(function_data, globals())
        return func

    def appendIcon(iconName):
        image = Image.open(os.path.join(pathIconsImages, iconName)).resize((90, 90))
        image.save(os.path.join(pathIconsImages, "current-image.png"))
        icons[iconName] = pygame.image.load(os.path.join(pathIconsImages, "current-image.png")).convert_alpha()

    def returnFormatedIcon(iconName):
        image = Image.open(os.path.join(pathIconsImages, iconName)).resize((90,90))
        image.save(os.path.join(pathIconsImages, "current-image.png"))
        return pygame.image.load(os.path.join(pathIconsImages, "current-image.png")).convert_alpha()

    def decodeSettings():
        macroData = {}
        for i in range(len(currentItems)):
            group, item, image, settingsNotFormated = currentItemsGroup[i], currentItems[i], currentItemsImages[i], currentItemsSettings[i]
            if item is not None:
                currentData = {"group": group["name"], "groupRaw": group["rawName"], "item": item, "image": image, "start-integration": group["start-integration"], "second_image":"", "check-second": ""}
                for y, groupItem in enumerate(group["objects"]):
                    if groupItem == item:
                        itemNum = y
                        break
                currentData["function"] = group["functions"][itemNum]
                settingsToSave = {}
                for x,setting in enumerate(group["objectSettings"][itemNum]):
                    if setting["name"] == "second-image":
                        if currentItemsSettingsData[i]["edited"] == "":
                            image = currentItemsSettingsData[i]["original"]
                        else:
                            image = currentItemsSettingsData[i]["edited"]
                        currentData["second_image"] = image
                        currentData["check-second"] = setting["settingsData"]["check-second"]
                    elif setting["name"] == "text-input":
                        settingsToSave[setting["settingsData"]["name"]] = settingsNotFormated[x].text
                    elif setting["name"] == "slider":
                        settingsToSave[setting["settingsData"]["name"]] = settingsNotFormated[x].value()
                    elif setting["name"] == "drop-menu":
                        settingsToSave[setting["settingsData"]["name"]] = settingsNotFormated[x].value()
                currentData["settings"] = settingsToSave
                macroData[i] = currentData
            else:
                macroData[i] = None
        with open(os.path.join("settings", f"savedData-{devicesIdentifier[selectedDevice]}.json"), "w") as f:
            json.dump(macroData,f)
        
    def encodeSettings():
        with open(os.path.join("settings", f"savedData-{devicesIdentifier[selectedDevice]}.json"), "r") as f:
            data = json.load(f)
        for i in range(len(data)):
            item = data[str(i)]
            if item:
                for group in actionsList:
                    if group["name"] == item["group"]:
                        currentItemsGroup[i] = group
                for group in actionsList:
                    if group["name"] == item["group"]:
                        for itemNum, itemGroup in enumerate(group["objects"]):
                            if item["item"] == itemGroup:
                                num = itemNum
                currentItems[i] = item["item"]
                appendIcon(item["image"])
                currentItemsImages[i] = item["image"]
                config = {}
                widthConfig = window.get_width()/3+20
                heightConfig = window.get_height()-window.get_height()/3+20
                diferenceSpaceConfig = 20
                maxHeight = 0
                for x,setting in enumerate(currentItemsGroup[i]["objectSettings"][num]):
                    if setting["name"] != "":
                        settingData = setting["settingsData"]
                        try:
                            if int(setting["settingsData"]["width"]) + widthConfig > window.get_width()-225:
                                heightConfig += maxHeight + diferenceSpaceConfig
                                widthConfig = window.get_width()/3+20
                        except KeyError: # if the setting has no specific width 
                            pass 
                        if setting["name"] == "second-image":
                            currentItemsSettingsData[i] = {"original": settingData["defaultImage"], "edited":item["second_image"]}
                            config[x] = {"original": returnFormatedIcon(settingData["defaultImage"]), "edited":returnFormatedIcon(item["second_image"])}
                        elif setting["name"] == "text-input":
                            config[x] = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((widthConfig, heightConfig), (int(settingData["width"]), int(settingData["height"]))), manager=manager, object_id='#main_text_entry', initial_text=item["settings"][setting["settingsData"]["name"]])
                            allTextInputConfig.append(config[x])
                            widthConfig += int(settingData["width"]) + diferenceSpaceConfig
                        elif setting["name"] == "slider":
                            config[x] = Slider(window, (59, 59, 59), (150,150,150), (30,30,30), (widthConfig, heightConfig, int(settingData["width"]), int(settingData["height"])), pygame.font.SysFont(None, 25), maxValue=int(settingData["max"]), minValue=int(settingData["min"]), startedWidth=int(item["settings"][setting["settingsData"]["name"]]))
                            widthConfig += int(settingData["width"]) + diferenceSpaceConfig
                        elif setting["name"] == "drop-menu":
                            config[x] = DropDown([(59, 59, 59), (30, 30, 30)],[(59, 59, 59), (30, 30, 30)], 100, heightConfig, int(settingData["width"]), int(settingData["height"]), pygame.font.SysFont(None, 25), item["settings"][setting["settingsData"]["name"]], settingData["options"])
                            widthConfig += int(settingData["width"]) + diferenceSpaceConfig
                    else:
                        pass # Return None
                currentItemsSettings[i] = config
            else:
                currentItemsGroup[i] = None
                currentItems[i] = None
                currentItemsImages[i] = None
                currentItemsSettingsData[i] = None
        return currentItemsGroup, currentItems, currentItemsImages, currentItemsSettings

    def calculateHeight(list, titleHeight=50, objectHeight=40):
        y = 0
        for group in list:
            y += titleHeight
            if group["hidden"] == "False":
                for _ in group["objects"]:
                    y += objectHeight
        return y

    def allItems(list):
        clearList = []
        for group in list:
            for item in group["objects"]:
                clearList.append(item)
        return clearList

    def getHeightImage(list, imageSize=90, space=20):
        imagesPerLength = round(window.get_width() / (imageSize+space))
        imagesPerHeight = round(len(list) / imagesPerLength)
        return imagesPerHeight*110

    class DropDown:
        def __init__(self, color_menu, color_option, x, y, w, h, font, main, options):
            self.color_menu = color_menu
            self.color_option = color_option
            self.rect = pygame.Rect(x, y, w, h)
            self.font = font
            self.main = main
            self.options = options
            self.draw_menu = False
            self.menu_active = False
            self.active_option = -1
            self.clicked = False 

        def updateOptions(self, options):
            self.options = options

        def draw(self, surf):
            pygame.draw.rect(surf, self.color_menu[self.menu_active], self.rect, 0)
            msg = self.font.render(self.main, 1, (150,150,150))
            surf.blit(msg, msg.get_rect(center = self.rect.center))
            if self.draw_menu:
                for i, text in enumerate(self.options):
                    rect = self.rect.copy()
                    rect.y += (i+1) * self.rect.height
                    pygame.draw.rect(surf, self.color_option[1 if i == self.active_option else 0], rect, 0)
                    msg = self.font.render(text, 1, (150,150,150))
                    surf.blit(msg, msg.get_rect(center = rect.center))

        def update(self):
            mpos = pygame.mouse.get_pos()
            self.menu_active = self.rect.collidepoint(mpos) 
            self.active_option = -1
            for i in range(len(self.options)):
                rect = self.rect.copy()
                rect.y += (i+1) * self.rect.height
                if rect.collidepoint(mpos):
                    self.active_option = i
                    break
            if not self.menu_active and self.active_option == -1:
                self.draw_menu = False

            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.draw_menu = False
                    self.main = self.options[self.active_option]
                    return self.active_option
            if pygame.mouse.get_pressed()[0] == 0:
                self.clicked = False
            return -1
        
        def value(self):
            return self.main

    class Slider:
        def __init__(self, display:str, fillColor:tuple, backgroundColor:tuple, outlineColor:tuple, position:int,font,startedWidth:int = 0,maxValue:int=100, minValue:int=20):
            self.position = position[0], position[1]
            self.outlineSize = position[2], position[3]
            self.minValue = minValue
            self.upperValue = maxValue
            self.display = display
            self.fillColor = fillColor
            self.backgroundColor = backgroundColor
            self.outlineColor = outlineColor
            self.sliderWidth = self.outlineSize[0] * startedWidth // self.upperValue
            self.pressed = False
            self.font = font
        def value(self):
            try:
                value = int(self.sliderWidth // (self.outlineSize[0] / (self.upperValue-self.minValue)) + self.minValue)
            except ZeroDivisionError:
                value = self.minValue
            if self.sliderWidth == self.outlineSize[0]:
                value = self.upperValue
            return value
        def draw(self):
            if self.outlineSize[0] - self.sliderWidth == 5: self.finalradius = 4
            elif self.outlineSize[0] - self.sliderWidth == 4: self.finalradius = 5
            elif self.outlineSize[0] - self.sliderWidth == 3: self.finalradius = 6
            elif self.outlineSize[0] - self.sliderWidth == 2: self.finalradius = 7
            elif self.outlineSize[0] - self.sliderWidth <= 1: self.finalradius = 8
            else: self.finalradius = 0
            if self.sliderWidth <= 3: self.initialHeight, self.positionFix = self.outlineSize[1] - 6, self.position[1]+3
            else: self.initialHeight, self.positionFix = self.outlineSize[1], self.position[1]
            pygame.draw.rect(self.display, self.fillColor, (self.position[0], self.position[1], self.outlineSize[0], self.outlineSize[1]), 0, 8)
            pygame.draw.rect(self.display, self.backgroundColor, (self.position[0],self.positionFix, self.sliderWidth, self.initialHeight), 0, self.finalradius,8,self.finalradius,8)
            pygame.draw.rect(self.display, self.outlineColor, (self.position[0]-2, self.position[1]-2, self.outlineSize[0]+4, self.outlineSize[1]+4), 2, 10, -1)
            text = self.font.render(f"{self.value()}%", 1, self.backgroundColor)
            self.display.blit(text, (self.position[0] + self.outlineSize[0] + 8, self.position[1]))
        def changeValue(self):
            mousePos = pygame.mouse.get_pos()
            if mousePos[0] > self.position[0] and mousePos[0] < self.position[0]  + self.outlineSize[0]:
                if mousePos[1] > self.position[1] and mousePos[1] < self.position[1] + self.outlineSize[1]:
                    if pygame.mouse.get_pressed()[0] == 1:
                        self.pressed = True
            if pygame.mouse.get_pressed()[0] == 0:
                self.pressed = False
            if self.pressed:
                self.sliderWidth = mousePos[0] - self.position[0]
                if self.sliderWidth < 1:
                    self.sliderWidth = 0
                if self.sliderWidth > self.outlineSize[0]:
                    self.sliderWidth = self.outlineSize[0]

    class Scroll:
        def __init__(self, win: pygame.Surface, width, height, x, scrollPower=15, colorBG=(0,0,0), initial_scroll=0):
            self.surface = pygame.surface.Surface((x,height))
            self.colorBG = colorBG
            pygame.Surface.fill(self.surface, self.colorBG)
            self.width = width
            self.height = win.get_height()-height
            self.y = height
            self.x = x
            self.win = win
            self.initial_scroll = initial_scroll
            self.scroll_y = self.initial_scroll
            self.scrollPower = scrollPower
            self.allItems = allItems(actionsList)
        
        def draw(self):
            self.y = max(calculateHeight(actionsList)+self.initial_scroll, self.win.get_height())
            y = 0
            pygame.Surface.fill(self.surface, self.colorBG)
            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 20)
            font2 = pygame.font.Font(r"C:\Windows\Fonts\calibri.ttf", 18)
            self.buttonsCloseCategory = []
            self.itemsInCategory = []
            self.shownItems = []
            self.groupsAdded = []
            if not text_input.text:
                for group in actionsList:
                    self.groupsAdded.append(group)
                    pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), y+50))
                    rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 50)
                    self.surface.blit(images[group["image"]], (35,y+25-images[group["image"]].get_height()/2))
                    self.buttonsCloseCategory.append(rect)
                    text = font.render(group["name"], True, (230, 230, 230))
                    self.surface.blit(text, (58, y+25-text.get_height()/2+1))
                    oldY = y
                    pygame.draw.line(self.surface, (34,34,34), (0, y), (self.win.get_width(), y))
                    pygame.draw.line(self.surface, (34,34,34), (25, y), (25, y+50))
                    y += 50
                    if group["hidden"] == "False":
                        arrow = font.render("-", True, (230, 230, 230))
                        self.surface.blit(arrow, (10, oldY+25-text.get_height()/2))
                        for item, image in zip(group["objects"], group["objectsImages"]):
                            pygame.draw.rect(self.surface, (34,34,34), pygame.Rect(0, y, self.surface.get_width(), y+40))
                            self.surface.blit(imagesGroup[image], (7,y+25-imagesGroup[image].get_height()/2-4))
                            rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 40)
                            self.itemsInCategory.append(rect)
                            self.shownItems.append(item)
                            text2 = font2.render(item, True, (180, 180, 180))
                            self.surface.blit(text2, (35, y+20-text2.get_height()/2))
                            y += 40
                    else:
                        arrow = font.render("+", True, (230, 230, 230))
                        self.surface.blit(arrow, (8, oldY+25-text.get_height()/2+1))
                    pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), self.surface.get_height()))
                    pygame.draw.line(self.surface, (34,34,34), (0, 0), (self.win.get_width(), 0))
                    pygame.draw.line(self.surface, (34,34,34), (0, oldY+50), (self.win.get_width(), oldY+50))
            else:
                for group in actionsList: 
                    if text_input.text.lower() in group["name"].lower():
                        pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), y+50))
                        rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 50)
                        self.surface.blit(images[group["image"]], (35,y+25-images[group["image"]].get_height()/2))
                        self.buttonsCloseCategory.append(rect)
                        text = font.render(group["name"], True, (230, 230, 230))
                        self.surface.blit(text, (58, y+25-text.get_height()/2+1))
                        oldY = y
                        pygame.draw.line(self.surface, (34,34,34), (0, y), (self.win.get_width(), y))
                        pygame.draw.line(self.surface, (34,34,34), (25, y), (25, y+50))
                        y += 50
                        if group["hidden"] == "False":
                            arrow = font.render("-", True, (230, 230, 230))
                            self.surface.blit(arrow, (10, oldY+25-text.get_height()/2))
                            for item, image in zip(group["objects"], group["objectsImages"]):
                                pygame.draw.rect(self.surface, (34,34,34), pygame.Rect(0, y, self.surface.get_width(), y+40))
                                self.surface.blit(imagesGroup[image], (7,y+25-imagesGroup[image].get_height()/2-4))
                                rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 40)
                                self.itemsInCategory.append(rect)
                                self.shownItems.append(item)
                                text2 = font2.render(item, True, (180, 180, 180))
                                self.surface.blit(text2, (35, y+20-text2.get_height()/2))
                                y += 40
                        else:
                            arrow = font.render("+", True, (230, 230, 230))
                            self.surface.blit(arrow, (8, oldY+25-text.get_height()/2+1))
                        pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), self.surface.get_height()))
                        pygame.draw.line(self.surface, (34,34,34), (0, 0), (self.win.get_width(), 0))
                        pygame.draw.line(self.surface, (34,34,34), (0, oldY+50), (self.win.get_width(), oldY+50))
                        self.groupsAdded.append(group)
                for group in actionsList:
                    added = False
                    for groupname in self.groupsAdded:
                        if group["name"] == groupname["name"]:
                            added = True
                    if not added:
                        groupDrew = False
                        for item, image in zip(group["objects"], group["objectsImages"]):
                            if text_input.text.lower() in item.lower():
                                if not groupDrew:
                                    pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), y+50))
                                    rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 50)
                                    self.surface.blit(images[group["image"]], (35,y+25-images[group["image"]].get_height()/2))
                                    self.buttonsCloseCategory.append(rect)
                                    text = font.render(group["name"], True, (230, 230, 230))
                                    self.surface.blit(text, (58, y+25-text.get_height()/2+1))
                                    pygame.draw.line(self.surface, (34,34,34), (0, y), (self.win.get_width(), y))
                                    pygame.draw.line(self.surface, (34,34,34), (25, y), (25, y+50))
                                    oldY = y
                                    y += 50
                                    groupDrew = True
                                    if group["hidden"] == "False":
                                        arrow = font.render("-", True, (230, 230, 230))
                                        self.surface.blit(arrow, (10, oldY+25-text.get_height()/2))
                                    else:
                                        arrow = font.render("+", True, (230, 230, 230))
                                        self.surface.blit(arrow, (8, oldY+25-text.get_height()/2+1))
                                    pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), self.surface.get_height()))
                                    pygame.draw.line(self.surface, (34,34,34), (0, 0), (self.win.get_width(), 0))
                                    pygame.draw.line(self.surface, (34,34,34), (0, oldY+50), (self.win.get_width(), oldY+50))
                                    self.groupsAdded.append(group)
                                if group["hidden"] == "False":
                                    pygame.draw.rect(self.surface, (34,34,34), pygame.Rect(0, y, self.surface.get_width(), y+40))
                                    self.surface.blit(imagesGroup[image], (7,y+25-imagesGroup[image].get_height()/2-4))
                                    rect = pygame.Rect(self.width, y+self.scroll_y, self.surface.get_width(), 40)
                                    self.itemsInCategory.append(rect)
                                    self.shownItems.append(item)
                                    text2 = font2.render(item, True, (180, 180, 180))
                                    self.surface.blit(text2, (35, y+20-text2.get_height()/2))
                                    y += 40
                pygame.draw.rect(self.surface, (41,41,41), pygame.Rect(0, y, self.surface.get_width(), self.surface.get_height()))
            self.win.blit(self.surface, (self.width, self.scroll_y))

        def checkMouseClick(self, pos):
            for i, rect in enumerate(self.buttonsCloseCategory):
                if rect.collidepoint(pos):
                    if self.groupsAdded[i]["hidden"] == "False":
                        self.groupsAdded[i]["hidden"] = "True"
                    elif self.groupsAdded[i]["hidden"] == "True":
                        self.groupsAdded[i]["hidden"] = "False"
            for i, rect in enumerate(self.itemsInCategory):
                if rect.collidepoint(pos):
                    if selected is not None:
                        currentItems[selected] = self.shownItems[i]
                        for group in actionsList:
                            for item, image in zip(group["objects"], group["itemsImages"]):
                                if item == self.shownItems[i]:
                                    imageNow = image
                                    groupNow = group
                        currentItemsImages[selected] = imageNow
                        currentItemsSettings[selected] = None
                        currentItemsGroup[selected] = groupNow

        def down(self):
            if self.y > self.win.get_height():
                self.scroll_y = min(self.scroll_y + self.scrollPower, self.initial_scroll)
            elif self.scroll_y != self.initial_scroll:
                self.scroll_y = min(self.scroll_y + self.scrollPower, self.initial_scroll)
                
        def up(self):
            if self.y > self.win.get_height():
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)
            elif self.scroll_y != self.initial_scroll:
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)

        def resize(self, window: pygame.Surface):
            self.win = window
            self.width = window.get_width()-225
            self.x = self.win.get_width()
            self.height = self.win.get_height()-self.y
            if self.y > self.win.get_height():
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)
            else:
                self.scroll_y = self.initial_scroll

    class ScrollImage:
        def __init__(self, win: pygame.Surface, width, height, x, list,scrollPower=15, colorBG=(0,0,0), initial_scroll=0):
            self.surface = pygame.surface.Surface((x,height))
            self.colorBG = colorBG
            self.images = list
            pygame.Surface.fill(self.surface, self.colorBG)
            self.width = width
            self.height = win.get_height()-height
            self.y = height
            self.x = x
            self.win = win
            self.initial_scroll = initial_scroll
            self.scroll_y = self.initial_scroll
            self.scrollPower = scrollPower
        
        def draw(self):
            imageSize = 90
            space = 20
            imagesPerLength = round(self.win.get_width() / (imageSize+space))
            imagesPerHeight = round(len(self.images) / imagesPerLength)
            times = 0
            margin = 10
            self.imagesRect = []
            for i in range(imagesPerLength):
                for x in range(imagesPerHeight):
                    if times < len(self.images):
                        rect = self.surface.blit(self.images[times], (margin + imageSize*i+space*i, imageSize*x+space*x+self.win.get_height()/8-35))
                        pygame.draw.rect(self.surface, (71,71,71), pygame.Rect(margin-3+imageSize*i+space*i, imageSize*x+space*x+self.win.get_height()/8-3-35, imageSize+6, imageSize+6), 4, 15)
                        pygame.draw.rect(self.surface, self.colorBG, pygame.Rect(margin-4+imageSize*i+space*i, imageSize*x+space*x+self.win.get_height()/8-4-35, imageSize+8, imageSize+8), 2, 15) 
                        pygame.draw.rect(self.surface, self.colorBG, pygame.Rect(margin-5+imageSize*i+space*i, imageSize*x+space*x+self.win.get_height()/8-5-35, imageSize+10, imageSize+10), 2, 15) 
                        times += 1
                        rect[0] += self.width
                        rect[1] += self.scroll_y
                        self.imagesRect.append(rect)
            self.win.blit(self.surface, (self.width, self.scroll_y))

        def down(self):
            if self.y > self.win.get_height():
                self.scroll_y = min(self.scroll_y + self.scrollPower, self.initial_scroll)
            elif self.scroll_y != self.initial_scroll:
                self.scroll_y = min(self.scroll_y + self.scrollPower, self.initial_scroll)
                
        def up(self):
            if self.y > self.win.get_height():
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)
            elif self.scroll_y != self.initial_scroll:
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)

        def resize(self, window: pygame.Surface):
            self.win = window
            self.width = window.get_width()-225
            self.x = self.win.get_width()
            self.height = self.win.get_height()-self.y
            if self.y > self.win.get_height():
                self.scroll_y = max(self.scroll_y - self.scrollPower, self.height)
            else:
                self.scroll_y = self.initial_scroll

    class RightClickPopup:
        def __init__(self, win: pygame.Surface):
            self.win = win
            self.active = False
        
        def draw(self):
            y = 20
            self.objectsRects = []
            if self.active:
                font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 17)
                font2 = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 20)
                self.rect = pygame.draw.rect(self.win, (80,80,80), (self.x, self.y, self.width, self.height+20))
                text = font2.render("Menu:", False, (220, 220, 220))
                self.win.blit(text, (self.x+2, self.y+2))
                for option in self.options:
                    rect = pygame.draw.rect(self.win, (80,80,80), (self.x, self.y+y, self.width, 20))
                    self.objectsRects.append(rect) 
                    text = font.render(option, False, (220, 220, 220))
                    self.win.blit(text, (self.x+3, self.y+y+3))
                    y += 20
                pygame.draw.line(self.win, (50,50,50), (self.x, self.y+20), (self.x+self.width-1, self.y+20))
                pygame.draw.rect(self.win, (50,50,50), pygame.Rect(self.x, self.y, self.width, self.height+20), 1)

        def updateActive(self, pos, options):
            self.x = pos[0]
            self.y = pos[1]
            self.height = len(options)*20
            self.width = 0
            self.options = options
            for data in options:
                if len(data) > self.width:
                    self.width = len(data)*9
            self.active = True
        
        def stop(self):
            self.active = False

    class Loadbar:
        def __init__(self, win: pygame.Surface, bgx, bgy, bgw, bgh, bgcolor, barx, bary, barw, barh, barcolor, maxFill=100, fill=0):
            self.win = win
            self.bgX = bgx
            self.bgY = bgy
            self.bgW = bgw
            self.bgH = bgh
            self.bgColor = bgcolor
            self.barX = barx
            self.barY = bary
            self.barW = barw
            self.barH = barh
            self.barColor = barcolor
            self.fill = fill
            self.totalFill = maxFill
        
        def getPercent(self, percent):
            self.fill = self.barW / self.totalFill * percent
            print(self.fill)
            return self.fill

        def draw(self, percent, estimatedTime):
            pygame.draw.rect(self.win, self.bgColor, (self.bgX, self.bgY, self.bgW, self.bgH))
            pygame.draw.rect(self.win, self.barColor, (self.barX-1, self.barY-1, self.barW+2, self.barH+2), 2)
            pygame.draw.rect(self.win, self.barColor, (self.barX, self.barY, self.getPercent(percent), self.barH))
            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 20)
            text = font.render(str(percent)+"%", True, (230, 230, 230))
            text2 = font.render(str(estimatedTime), True, (230, 230, 230))
            self.win.blit(text, (self.barX+self.barW+text.get_width()/2-5, self.barY+text.get_height()/2-5))
            self.win.blit(text2, (self.barX+self.barW/2-text2.get_width()/2, self.barY-text2.get_height()))

    def changeIcon(win: pygame.Surface, selected):
        width = win.get_width()
        height = win.get_height()
        imageName, _ = imageMenuChangeWindow()
        if imageName:
            appendIcon(imageName)
            currentItemsImages[selected] = imageName
        win = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(APP_NAME)

    def imageMenuChangeWindow():
        window = pygame.display.set_mode((550, 700))
        pygame.display.set_caption("Icon List")
        imagesIcons = []
        imagesName = []
        for item in os.listdir(pathIconsImages):
            if item.endswith(".png") and item != "current-image.png" and not item.startswith("-manual"):
                image = Image.open(os.path.join(pathIconsImages, item)).resize((90, 90))
                image.save(os.path.join(pathIconsImages, "current-image.png"))
                imagesIcons.append(pygame.image.load(os.path.join(pathIconsImages, "current-image.png")).convert_alpha())
                imagesName.append(item)
        imageScroll = ScrollImage(window, 0, getHeightImage(imagesIcons), window.get_width(), imagesIcons, scrollPower=50, colorBG=(41,41,41))
        choosingImage = True
        imageSelected = None
        imagePath = None
        while choosingImage:
            for event2 in pygame.event.get():
                if event2.type == pygame.QUIT:
                    choosingImage = False
                if event2.type == pygame.MOUSEBUTTONDOWN:
                    if event2.button == 4: 
                        imageScroll.down()
                    if event2.button == 5:
                        imageScroll.up()
                    if event2.button == 1:
                        pos = pygame.mouse.get_pos()
                        for i, rect in enumerate(imageScroll.imagesRect):
                            if rect.collidepoint(pos):
                                imageNum = i
                                choosingImage = False
                                imageSelected = imagesName[imageNum]
                        if openFolderRect.collidepoint(pos):
                            image_formats= [("PNG Files", "*.png"), ("JPG Files" , ".jpeg")]
                            image_selected = filedialog.askopenfile(filetypes=image_formats)
                            imagePath = image_selected.name
                            image = Image.open(image_selected.name).resize((90, 90))
                            image.save(os.path.join(pathIconsImages, f"-manual-{os.path.basename(image_selected.name)}"))
                            choosingImage = False
                            imageSelected = f"-manual-{os.path.basename(image_selected.name)}"
            imageScroll.draw()
            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 40)
            font2 = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 25)
            pygame.draw.rect(window, (41,41,41), pygame.Rect(0,0, window.get_width(), 50))
            text = font.render("Icons Menu:", True, (230, 230, 230))
            window.blit(text, (7,5))
            text = font2.render("Open Folder", True, (220,220,220))
            openFolderRect = pygame.draw.rect(window, (100,100,100), pygame.Rect(410-5, 12-3, text.get_width()+10, text.get_height()+6),border_radius=15)
            window.blit(text, (410,12))
            pygame.display.update()
            pygame.display.update()
        return imageSelected, imagePath

    def draw_window(win: pygame.Surface):
        global phase
        win.fill(BACKGROUND_COLOR)
        pygame.draw.rect(win, (41,41,41), pygame.Rect(window.get_width()-225, 0, win.get_width(), win.get_height()))
        box, spaceBetweenBox = 90, 20
        margin = ((win.get_width()-225) - (box*numberOfBoxesLength+spaceBetweenBox*(numberOfBoxesLength-1)))/2
        boxes = []
        times = 0
        for i in range(numberOfBoxesLength):
            for x in range(numberOfBoxesHeight):
                rect = pygame.draw.rect(win, (34,34,34), pygame.Rect(margin+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8, box, box), border_radius=15)
                if currentItems[times] is not None:
                    win.blit(icons[currentItemsImages[times]], (margin+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8))
                if times == selected:
                    pygame.draw.rect(win, (0,120,255), pygame.Rect(margin-3+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8-3, box+6, box+6), 4, 14)
                else:
                    pygame.draw.rect(win, (71,71,71), pygame.Rect(margin-3+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8-3, box+6, box+6), 4, 15)
                # Images are squares so we delete the extra border
                pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(margin-4+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8-4, box+8, box+8), 2, 15) 
                pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(margin-5+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+win.get_height()/8-5, box+10, box+10), 2, 15) 
                boxes.append(rect)
                times += 1
        font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 30)
        try:
            text = font.render(f"<   {devicesIdentifier[selectedDevice]}", True, (230, 230, 230))
            rectGoBack = win.blit(text, (15, 15))
        except: # The device was unplug in the device settings
            phase = "devices"
            return boxes, None, None
        scroll.draw()
        pygame.draw.rect(win, (41,41,41), pygame.Rect(window.get_width()-225, 0, window.get_width(), 50))
        manager.update(clock.tick(FPS)/1000)
        manager.draw_ui(win)
        rightClick.draw()
        #Lines
        pygame.draw.line(win, (34,34,34), (win.get_width()-225, 0), (win.get_width()-225, win.get_height()))
        pygame.draw.line(win, (34,34,34), (0, win.get_height()-win.get_height()/3), (win.get_width()-225, win.get_height()-win.get_height()/3))
        saveButton = pygame.draw.rect(win, (59, 59, 59), (window.get_width()-225+145, 14, 71, 22), border_radius=2)
        return boxes, saveButton, rectGoBack

    def settings(win: pygame.Surface):
        for textInput in allTextInputConfig:
            textInput.hide()
        if selected is not None:
            if currentItems[selected] is not None:
                pygame.draw.line(win, (34,34,34), (win.get_width()/3, win.get_height()-win.get_height()/3), (win.get_width()/3, win.get_height()))
                win.blit(icons[currentItemsImages[selected]], (win.get_width()/3-140-110, win.get_height()-win.get_height()/3+50, 90, 90))
                pygame.draw.rect(win, (71,71,71), pygame.Rect(win.get_width()/3-140-3-110, win.get_height()-win.get_height()/3-3+50, 90+6, 90+6), 4, 14)
                # Images are squares so we delete the extra border
                pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(win.get_width()/3-140-4-110, win.get_height()-win.get_height()/3-4+50, 90+8, 90+8), 2, 15) 
                pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(win.get_width()/3-140-5-110, win.get_height()-win.get_height()/3-5+50, 90+10, 90+10), 2, 15)
                rect = pygame.draw.circle(win, (41,41,41), (win.get_width()/3-63-110, win.get_height()-win.get_height()/3-3+66), 10)
                pos = pygame.mouse.get_pos()
                if rect.collidepoint(pos):
                    if pygame.mouse.get_pressed()[0]:
                        changeIcon(win, selected)
                font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 25)
                text = font.render("Icon", True, (230, 230, 230))
                win.blit(text, (win.get_width()/3-140-110+(text.get_width()/2), win.get_height()-win.get_height()/3+20))
                itemGroup = None
                for group in actionsList:
                    for i, item in enumerate(group["objects"]):
                        if item == currentItems[selected]:
                            itemGroup = group
                            itemNum = i
                if itemGroup is not None:
                    config = {}
                    configData = {}
                    settings = itemGroup["objectSettings"][itemNum]
                    configCreated = True
                    if currentItemsSettings[selected] is None:
                        configCreated = False
                    widthConfig = win.get_width()/3+20
                    heightConfig = win.get_height()-win.get_height()/3+20
                    diferenceSpaceConfig = 20
                    maxHeight = 0
                    font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 25)
                    text = font.render(itemGroup["name"]+" - " + itemGroup["objects"][itemNum], True, (230, 230, 230))
                    win.blit(text, ((win.get_width()-255)/2-text.get_width()/2, win.get_height()-win.get_height()/3-30))
                    for i,setting in enumerate(settings):
                        try:
                            if int(setting["settingsData"]["width"]) + widthConfig > win.get_width()-225:
                                heightConfig += maxHeight + diferenceSpaceConfig
                                widthConfig = win.get_width()/3+20
                        except KeyError: # if the setting has no specific width 
                            pass 

                        if setting["name"] == "second-image":
                            data = setting["settingsData"]
                            if not configCreated:
                                configData[i] = {"original": data["defaultImage"], "edited":""}
                                config[i] = {"original": returnFormatedIcon(data["defaultImage"]), "edited":""}
                                image = config[i]["original"]
                            else:
                                config[i] = currentItemsSettings[selected][i]
                                configData[i] = currentItemsSettingsData[selected]
                                if config[i]["edited"] == "":
                                    image = config[i]["original"]
                                else:
                                    image = config[i]["edited"]
                            currentItemsSettingsData[selected] = configData[i]
                            
                            win.blit(image, (win.get_width()/3-140, win.get_height()-win.get_height()/3+50, 90, 90))
                            pygame.draw.rect(win, (71,71,71), pygame.Rect(win.get_width()/3-140-3, win.get_height()-win.get_height()/3-3+50, 90+6, 90+6), 4, 14)
                            # Images are squares so we delete the extra border
                            pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(win.get_width()/3-140-4, win.get_height()-win.get_height()/3-4+50, 90+8, 90+8), 2, 15) 
                            pygame.draw.rect(win, BACKGROUND_COLOR, pygame.Rect(win.get_width()/3-140-5, win.get_height()-win.get_height()/3-5+50, 90+10, 90+10), 2, 15) 
                            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 25)
                            text = font.render(data["name"], True, (230, 230, 230))
                            win.blit(text, (win.get_width()/3-140+45-text.get_width()/2, win.get_height()-win.get_height()/3+20))
                            rect = pygame.draw.circle(win, (41,41,41), (win.get_width()/3-63, win.get_height()-win.get_height()/3-3+66), 10)
                            pos = pygame.mouse.get_pos()
                            if rect.collidepoint(pos):
                                if pygame.mouse.get_pressed()[0]:
                                    width = win.get_width()
                                    height = win.get_height()
                                    imageName, path = imageMenuChangeWindow()
                                    if imageName:
                                        if path:
                                            configData[i] = {"original": data["defaultImage"], "edited": imageName, "path": path}
                                        else:
                                            configData[i] = {"original": data["defaultImage"], "edited": imageName}
                                        currentItemsSettingsData[selected] = configData[i]
                                        config[i] = {"original": returnFormatedIcon(data["defaultImage"]), "edited": returnFormatedIcon(imageName)}
                                    win = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                                    pygame.display.set_caption(APP_NAME)

                        if setting["name"] == "text-input":
                            data = setting["settingsData"]
                            if not configCreated:
                                config[i] = None
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                                config[i] = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((widthConfig, heightConfig), (int(data["width"]), int(data["height"]))), manager=manager, object_id='#main_text_entry')
                                allTextInputConfig.append(config[i])
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                            else:
                                config[i] = currentItemsSettings[selected][i]
                                currentItemsSettings[selected][i].set_position(pygame.Rect((widthConfig, heightConfig), (0, 0)))
                                currentItemsSettings[selected][i].show()
                                currentItemsSettingsNameValue[selected][data["name"]] = currentItemsSettings[selected][i].text
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                            if maxHeight < int(data["height"]):
                                maxHeight = int(data["height"])
                                
                        elif setting["name"] == "drop-menu":
                            data = setting["settingsData"]
                            def checkForOptions():
                                options = data["options"]
                                if data["func"] != "False":
                                    func = marshal_to_func(os.path.join(sitePackagesPath, itemGroup["rawName"], data["func"]))
                                    pathArg = os.path.join(sitePackagesPath, itemGroup["rawName"])
                                    if data["funcOptionsRelative"] != "False":
                                        try:
                                            args = []
                                            for arg in data["funcOptionsRelative"]:
                                                args.append(currentItemsSettingsNameValue[selected][arg])
                                            options = func(args, pathArg)
                                        except Exception as e:
                                            print(e)
                                    else:
                                        try:
                                            options = func([], pathArg)
                                        except Exception as e:
                                            print(e)
                                return options
                            if not configCreated:
                                options = checkForOptions()
                                currentItemsSettingsOptions[selected][i] = options
                                config[i] = DropDown([(59, 59, 59), (30, 30, 30)],[(59, 59, 59), (30, 30, 30)], 100, heightConfig, int(data["width"]), int(data["height"]), pygame.font.SysFont(None, 25), "None", options)
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                            else:
                                try:
                                    if currentItemsSettingsNameValue[selected][data["name"]] != currentItemsSettings[selected][i].value():
                                        currentItemsSettingsOptions[selected] = {}
                                except: 
                                    pass
                                currentItemsSettingsNameValue[selected][data["name"]] = currentItemsSettings[selected][i].value()
                                try: 
                                    options = currentItemsSettingsOptions[selected][i]
                                except:
                                    currentItemsSettingsOptions[selected][i] = checkForOptions()
                                    if currentItemsSettingsNameValue[selected][data["name"]] not in currentItemsSettingsOptions[selected][i]:
                                        currentItemsSettings[selected][i].main = "None"
                                    options = currentItemsSettingsOptions[selected][i]
                                config[i] = currentItemsSettings[selected][i]
                                currentItemsSettings[selected][i].updateOptions(options)
                                currentItemsSettings[selected][i].rect[0], currentItemsSettings[selected][i].rect[1]  = widthConfig, heightConfig
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                                currentItemsSettings[selected][i].draw(window)
                                currentItemsSettings[selected][i].update()
                                if data["lastOptionProccess"] != "False":
                                    if currentItemsSettings[selected][i].value() == options[-1]:
                                        if data["lastOptionProccessStarted"] == "False":
                                            subprocess.Popen([os.path.join(sitePackagesPath, itemGroup["rawName"], data["lastOptionProccess"])], shell=True)
                                            data["lastOptionProccessStarted"] = "True"
                                            currentItemsSettings[selected][i].main = "None"
                                    
                            if maxHeight < int(data["height"]):
                                maxHeight = int(data["height"])
                        elif setting["name"] == "slider":
                            data = setting["settingsData"]
                            if not configCreated:
                                config[i] = Slider(window, (59, 59, 59), (150,150,150), (30,30,30), (widthConfig, heightConfig, int(data["width"]), int(data["height"])), pygame.font.SysFont(None, 25), maxValue=int(data["max"]), minValue=int(data["min"]), startedWidth=int(data["starting"]))
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                            else:
                                config[i] = currentItemsSettings[selected][i]
                                currentItemsSettingsNameValue[selected][data["name"]] = currentItemsSettings[selected][i].value()
                                currentItemsSettings[selected][i].position = widthConfig, heightConfig
                                currentItemsSettings[selected][i].draw()
                                currentItemsSettings[selected][i].changeValue()
                                widthConfig += int(data["width"]) + diferenceSpaceConfig
                            if maxHeight < int(data["height"]):
                                maxHeight = int(data["height"])

                    currentItemsSettings[selected] = config

    def displaydevices(win: pygame.Surface):
        win.fill(BACKGROUND_COLOR)
        rectangleWidth = 450
        rectangleHeight = 300
        marginTop = win.get_height()/2-rectangleHeight/2+25
        xScroll = win.get_width()/2-rectangleWidth/2
        rectLeft, rectRight, rectMain = None, None, None
        if devices:
            rectMain = pygame.draw.rect(win, (59,59,59), pygame.Rect(xScroll, marginTop, rectangleWidth, rectangleHeight), border_radius=10)
            arrowLeftImage = pygame.transform.flip(arrowImage, True, False)
            rectLeft = win.blit(arrowLeftImage, (10, win.get_height()/2-arrowImage.get_height()/2+25))
            rectRight = win.blit(arrowImage, (win.get_width()-arrowImage.get_width()-10, win.get_height()/2-arrowImage.get_height()/2+25))
            box, spaceBetweenBox = 90, 20
            margin = ((win.get_width()) - (box*numberOfBoxesLength+spaceBetweenBox*(numberOfBoxesLength-1)))/2
            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 30)
            text = font.render(devicesIdentifier[selectedDevice], True, (230, 230, 230))
            win.blit(text, (xScroll+5, marginTop+5))
            for i in range(numberOfBoxesLength):
                for x in range(numberOfBoxesHeight):
                    pygame.draw.rect(win, (34,34,34), pygame.Rect(margin+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+marginTop+48, box, box), border_radius=15)
                    pygame.draw.rect(win, (71,71,71), pygame.Rect(margin-3+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+marginTop+48-3, box+6, box+6), 4, 15)
                    # Images are squares so we delete the extra border
                    pygame.draw.rect(win, (59,59,59), pygame.Rect(margin-4+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+marginTop+48-4, box+8, box+8), 2, 15) 
                    pygame.draw.rect(win, (59,59,59), pygame.Rect(margin-5+box*i+spaceBetweenBox*i, box*x+spaceBetweenBox*x+marginTop+48-5, box+10, box+10), 2, 15) 
        else:
            pygame.draw.rect(win, (59,59,59), pygame.Rect(xScroll, marginTop, rectangleWidth, rectangleHeight), border_radius=10)
            font = pygame.font.Font(r"C:\Windows\Fonts\calibrib.ttf", 30)
            text = font.render("Connect your MIX gear!", True, (230, 230, 230))
            win.blit(text, (xScroll+rectangleWidth/2-text.get_width()/2, marginTop+rectangleHeight/2+text.get_height()/2-25))
        return rectLeft, rectRight, rectMain

    def loadSettings():
        with open(os.path.join("settings", f"savedData-{devicesIdentifier[selectedDevice]}.json"), "r") as f:
            data = json.load(f)
        images = []
        informationImage = []
        for i in data:
            item = data[str(i)]
            if item:
                if item["image"] not in images:
                    images.append(item["image"])
                if item["second_image"] and not item["second_image"] in images:
                    images.append(item["second_image"])
                image1 = item["image"].replace("png", "raw")
                image2 = item["second_image"].replace("png", "raw")
            else:
                image1 = "None"
                image2 = "None"
            informationImage.append([image1,image2])
        imagesToLoadList = []
        overallTime = 0
        def updatePercent(percent, estimatedTime):
            if isinstance(estimatedTime, (int, float)):
                estimatedTime = "Remaining: " + str(round(estimatedTime))
            else: 
                estimatedTime = "Remaining: " + estimatedTime
            events = pygame.event.get() # Listen for events so the window "revives"
            loadbar = Loadbar(window, window.get_width()/2-300/2, window.get_height()/2-175/2, 300, 175, (40,40,40), window.get_width()/2-150/2, window.get_height()/2-30/2, 150, 30, (255,255,255), 100)
            loadbar.draw(round(percent), estimatedTime)
            pygame.display.update()

        imagesToLoadNum = len(images)
        percent = 0
        estimatedTime = "Calculating..."
        updatePercent(percent, estimatedTime)
        serialConnection.stop()
        percent += 5
        updatePercent(percent, estimatedTime)
        ls = serialConnection.listdir(devices[selectedDevice], "/sd", False)
        for image in images:
            if not "/sd/" + image.replace("png", "raw") in ls:
                imagesToLoadList.append(image)
            else:
                imagesToLoadNum -= 1
        percent += 7
        updatePercent(percent, estimatedTime)
        if imagesToLoadNum != 0:
            imagesPercent = (100-percent-3)/imagesToLoadNum
            print(imagesPercent)
        else:
            percent += 60
            estimatedTime = 3
        oldPercent = percent
        for i,image in enumerate(imagesToLoadList):
            imagePath = os.path.join(pathIconsImages, image)
            timeToload = serialConnection.uploadImage(devices[selectedDevice], imagePath, f"/sd/{image.replace('.png', '.raw')}")
            percent = oldPercent+imagesPercent*i 
            imagesToLoadNum -= 1
            estimatedTime = imagesToLoadNum*timeToload+3
            overallTime += timeToload
            updatePercent(percent, estimatedTime)
            time.sleep(.1)
        serialConnection.uploadJSON(devices[selectedDevice], informationImage, "imagesJSON.json") 
        percent = 99
        updatePercent(percent, estimatedTime)
        serialConnection.updateScreen(devices[selectedDevice])   
        percent = 100
        updatePercent(percent, estimatedTime)
        serialConnection.restart()

    selected = None
    scroll = Scroll(window, window.get_width()-225, max(calculateHeight(actionsList), window.get_height()), window.get_width(), scrollPower=50, colorBG=(41,41,41), initial_scroll=50)
    manager = pygame_gui.UIManager((WIDTH, HEIGHT), os.path.join(os.getcwd(), 'theme.json'))
    text_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(((window.get_width()-225)+10, 14), (255-125, 22)), manager=manager, object_id='#main_text_entry', placeholder_text="Search")
    clock = pygame.time.Clock()
    rightClick = RightClickPopup(window)
    selectedDevice = 0
    oldRun = False
    serialConnection.start()
    width, height = WIDTH, HEIGHT
    while applicationRunning:
        if oldRun != run:
            if run:
                window = pygame.display.set_mode((width, height), flags=pygame.SHOWN|pygame.RESIZABLE)
            else:
                window = pygame.display.set_mode((width, height), flags=pygame.HIDDEN|pygame.RESIZABLE)
        oldRun = run
        if run:
            from serialConnection import devices, devicesIdentifier
            clock.tick(FPS)
            events = pygame.event.get()
            if phase == "devices":
                rectLeft, rectRight, rectMain = displaydevices(window)
                for event in events:
                    if event.type == pygame.QUIT:
                        run = False
                    elif event.type == pygame.VIDEORESIZE:
                        width, height = event.size
                        if width < WIDTH:
                            width = WIDTH
                        if height < HEIGHT:
                            height = HEIGHT
                        window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                        scroll.resize(window)
                        manager.set_window_resolution((width, height))
                        text_input.set_position(pygame.Rect(((window.get_width()-225)+10, 14), (255-50, 22)))
                        text_input.set_dimensions(pygame.Rect(((255-125, 22), ((window.get_width()-225)+10, 14))))
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1: 
                            pos = pygame.mouse.get_pos()
                            if rectLeft:
                                if rectLeft.collidepoint(pos):
                                    selectedDevice -= 1
                            if rectRight:
                                if rectRight.collidepoint(pos):
                                    selectedDevice += 1
                            if selectedDevice < 0:
                                selectedDevice = 0
                            if selectedDevice > len(devicesIdentifier)-1:
                                selectedDevice = len(devicesIdentifier)-1
                            if rectMain:
                                if rectMain.collidepoint(pos):
                                    phase = "deviceSelected"
                                    currentItemsGroup, currentItems, currentItemsImages, currentItemsSettings = encodeSettings()

            elif phase == "deviceSelected":
                boxes, saveButton, rectGoBack = draw_window(window)
                for event in events:
                    manager.process_events(event)
                    if event.type == pygame.QUIT:
                        run = False
                    elif event.type == pygame.VIDEORESIZE:
                        width, height = event.size
                        if width < WIDTH:
                            width = WIDTH
                        if height < HEIGHT:
                            height = HEIGHT
                        window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                        scroll.resize(window)
                        manager.set_window_resolution((width, height))
                        text_input.set_position(pygame.Rect(((window.get_width()-225)+10, 14), (255-50, 22)))
                        text_input.set_dimensions(pygame.Rect(((255-125, 22), ((window.get_width()-225)+10, 14))))
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 4: 
                            scroll.down()
                        if event.button == 5:
                            scroll.up()
                        if event.button == 1:
                            pos = pygame.mouse.get_pos()
                            if rightClick.active == True:
                                if rightClick.rect.collidepoint(pos):
                                    for i,rect in enumerate(rightClick.objectsRects):
                                        if rect.collidepoint(pos):
                                            if rightClick.options[i] == "Delete":
                                                currentItems[selected] = None
                                                currentItemsImages[selected] = None
                                                currentItemsSettings[selected] = None
                                                currentItemsGroup[selected] = None
                                                rightClick.stop()
                                            elif rightClick.options[i] == "Update Image":
                                                changeIcon(window, selected)
                                                rightClick.stop()
                                else:
                                    rightClick.stop()
                            else:
                                rectLeft = pygame.Rect(0, 0, window.get_width()-225, window.get_height()-window.get_height()/3)
                                if rectLeft.collidepoint(pos):
                                    selected = None
                                    for i, box in enumerate(boxes):
                                        if box.collidepoint(pos):
                                            selected = i
                                else:
                                    scroll.checkMouseClick(pos)
                            if saveButton.collidepoint(pos):
                                decodeSettings()
                                try:
                                    loadSettings()
                                except SerialException:
                                    phase = "devices"
                                    serialConnection.restart()
                            if rectGoBack.collidepoint(pos):
                                phase = "devices"
                        if event.button == 3:
                            pos = pygame.mouse.get_pos()
                            rectLeft = pygame.Rect(0, 0, window.get_width()-225, window.get_height()-window.get_height()/3)
                            if rectLeft.collidepoint(pos):
                                selected = None
                                for i, box in enumerate(boxes):
                                    if box.collidepoint(pos) and currentItems[i] != None:
                                        selected = i
                                        rightClick.updateActive(pygame.mouse.get_pos(), ["Update Image", "Delete"])
            settings(window)
            pygame.display.update() 

    stoppedSuccesfully = True

def stop():
    global applicationRunning
    applicationRunning = False

def start():
    global run
    run = True

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame: wx.Frame):
        super(TaskBarIcon, self).__init__()
        self.set_icon(APP_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, f'Open', self.launch)
        debugMenu = wx.Menu() 
        create_menu_item(debugMenu, f'Serial', self.reloadSerial)
        menu.Append(wx.ID_ANY, "Debug", debugMenu)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(wx.Bitmap(path))
        self.SetIcon(icon, APP_NAME)

    def on_left_down(self, event):
        global run
        if run:
            run = False
        else:
            start()

    def launch(self, event):
        start()

    def reloadSerial(self, event):
        serialConnection.stop()
        serialConnection.restart()
        print("debug done")

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        stop()
        wx.Exit()
        serialConnection.stop()

class Frame(wx.Frame):
    def __init__(self, *args, **kw):
        super(Frame, self).__init__(*args, **kw)

def main():
    app = wx.App()
    frame = Frame(None)
    TaskBarIcon(frame)
    app.MainLoop()

if __name__ == '__main__':
    logger.info('Program started!')
    from threading import Thread
    global applicationRunning
    applicationRunning = True
    application = Thread(target=app)
    application.start()
    main()
    