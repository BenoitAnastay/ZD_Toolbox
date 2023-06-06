#!/usr/bin/env python
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
import os
import re
import sys
from difflib import SequenceMatcher

class Actor(object):
    ActorName = None 

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        # Avoid Mangling
        self.RowId = data['__RowId']

class EnhancementMaterial(object):

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        # Avoid Mangling
        self.RowId = data['__RowId']

class Pouch(object):
    ArmorEffectType = "" 
    ArmorNextRankActor = ""
    ArmorNextRankActor_obj = None
    ArmorRank = int 
    EquipmentPerformance = int
    BundleActorNum = int
    BuyingPrice = int
    CannotSell = bool
    HitPointRecover = int
    IsUsable = bool
    PouchCategory = ""
    PouchGetType: ""
    PouchSortKey: int
    PouchSpecialDeal = None
    PouchStockable = bool
    PouchUseType = ""
    SellingPrice = int

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        # Avoid Mangling
        self.RowId = data['__RowId']


class TOTK:
    translate_class = {}
    Actor = {}
    Challenge = {}
    Pouch = {}
    EnhancementMaterial = {}

    def __init__(self, romfs, language):
        self._romfs = romfs
        self._language = language
        self.load_Actor()

    def get_translation_directory(self, name):
        return self._romfs+"/Mals/"+self._language+".Product.100/"+name+"Msg/"

    def load_file(self, file):
        with open(file, "r") as stream:
            try:
                return yaml.load(stream, Loader=Loader)
            except yaml.YAMLError as exc:
                print(exc)
            except UnicodeDecodeError:
                return
    
    def load_simple_array(self, name):
        directory = self.get_translation_directory(name)
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                if f.endswith("yml"):
                    data = self.load_file(f)
                    if data != None:
                        self.translate_class[name].update(data)
    
    def load_challange_language(self, name):
        directory = self.get_translation_directory(name)
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                if f.endswith("yml"):
                    key = os.path.splitext(os.path.basename(f))[0][5:]
                    data = self.load_file(f)
                    self.translate_class[name][key] = data
    
    def load_translate_class(self, name):
        if name in self.translate_class:
            return
        self.translate_class[name] = {}
        match name:
            case "Static":
                self.load_simple_array(name)
            case "Actor":
                self.load_simple_array(name)
            case "Location":
                self.load_simple_array(name)
            case 'Challenge':
                self.load_challange_language(name)

    def key_from_gymlstr(self, path):
        if '.' not in path:
            return path.split("/")[2]
        return path.split("/")[2].split('.')[0] 

    def translate(self, path, sub_key = None):
        class_name = path.split("/")[1]
        name = self.key_from_gymlstr(path)
        self.load_translate_class(class_name)

        try:
            match class_name:
                case "Static":
                    return self.translate_class[class_name][name]
                case "Actor":
                    if self.Actor[name].ActorName:
                        name = self.Actor[name].ActorName
                    if sub_key:
                        return self.translate_class[class_name][name+'_'+sub_key]
                    return self.translate_class[class_name][name+'_Name']
                case "Location":
                    return self.translate_class[class_name][name]
                case 'Challenge':
                    if sub_key:
                        return self.translate_class[class_name][name][sub_key]
                    else:
                        return self.translate_class[class_name][name]['Name']
        except KeyError:
            return name
    
    def load_challenge(self):
        raw = self.load_file(self._romfs+"/RSDB/Challenge.Product.100.rstbl.yml")
        #This bloc organise challanges with keys
        for challenge in raw:
            key = self.key_from_gymlstr(challenge['__RowId'])
            self.Challenge[key] = challenge
            #Here we make it human readlable
            self.Challenge[key]['Name'] = self.translate(challenge['__RowId'])
            if 'RequestActor' in self.Challenge[key]:
                self.Challenge[key]['RequestActor'] = self.translate(challenge['RequestActor'])
            if 'RequestLocation' in self.Challenge[key]:
                self.Challenge[key]['RequestLocation'] = self.translate(challenge['RequestLocation'])
            n_step = 0
            for step in challenge['Steps']:
                if step['Name'] != 'Ready':
                    self.Challenge[key]['Steps'][n_step]['Message'] = self.translate(challenge['__RowId'], step['Name'])
                n_step = n_step + 1

        return self.Challenge
    
    def load_pouch(self):
        self.load_EnhancementMaterial()
        raw = self.load_file(self._romfs+"/RSDB/PouchActorInfo.Product.100.rstbl.yml")
        for pouch in raw:
            self.Pouch[pouch['__RowId']] = Pouch(pouch)
            self.Pouch[pouch['__RowId']].Name = self.translate('Work/Actor/'+pouch['__RowId'], 'Name')
            self.Pouch[pouch['__RowId']].Caption = self.translate('Work/Actor/'+pouch['__RowId'], 'Caption')
            if 'ArmorNextRankActor' in pouch:
                self.Pouch[pouch['__RowId']].ArmorNextRankActor_Name = self.translate(pouch['ArmorNextRankActor'])
                self.Pouch[pouch['__RowId']].ArmorNextRankActor_Material = self.EnhancementMaterial[pouch['__RowId']]
            if 'ArmorEffectType' in pouch:
                self.Pouch[pouch['__RowId']].ArmorEffectType_Name = self.translate('Work/Static/'+pouch['ArmorEffectType'])
        self.armor_next_rank()
        return self.Pouch
    
    def load_EnhancementMaterial(self):
        raw = self.load_file(self._romfs+"/RSDB/EnhancementMaterialInfo.Product.100.rstbl.yml")
        for material in raw:
            material['__RowId'] = self.key_from_gymlstr(material['__RowId'])
            self.EnhancementMaterial[material['__RowId']] = EnhancementMaterial(material)
            for item in self.EnhancementMaterial[material['__RowId']].Items:
                item['Name'] = self.translate(item['Actor'])

    def load_Actor(self):
        raw = self.load_file(self._romfs+"/RSDB/ActorInfo.Product.100.rstbl.yml")
        for actor in raw:
            self.Actor[actor['__RowId']] = Actor(actor)


    
    def armor_next_rank(self):
        # Loop through the keys and values of the sorted dictionary
        for key, armor in self.Pouch.items():
            if armor.ArmorNextRankActor != "":
                # Truncate ArmorNextRankActor
                nexRowId = self.key_from_gymlstr(armor.ArmorNextRankActor)
                next_rank_object = [obj for obj in self.Pouch.values() if obj.RowId == nexRowId][0]
                self.Pouch[armor.RowId].ArmorNextRankActor_obj = next_rank_object