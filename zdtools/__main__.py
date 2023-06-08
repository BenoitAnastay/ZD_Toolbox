import sys
import re
from difflib import SequenceMatcher
from zdtools import TOTK

#Set Encoding
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

def handle_tags(test_str):
    #Just put in bold
    test_str.replace("<2 Type='35'/>", "Geofencer")
    regex = r"<0 Type='\d+'( Data='[a-fA-F0-9_]+')?\/>"
    subst = "'''"
    test_str = re.sub(regex, subst, test_str, 0, re.MULTILINE)
    regex = r"<2 Type='\d+'( Data='[a-fA-F0-9_]+')?\/>"
    subst = "_COUNTER_"
    test_str = re.sub(regex, subst, test_str, 0, re.MULTILINE)
    regex = r"<201 Type='\d+'( Data='[a-fA-F0-9_]+')?\/>"
    subst = "_INTEM_NAME_"
    test_str = re.sub(regex, subst, test_str, 0, re.MULTILINE)
    return test_str

def handle_geofence(str):
    return str.replace("<2 Type='35'/>", "Geofencer")

def write_wiki_quests(Challenges):
    for row in Challenges:
        print('== ',Challenges[row]['Name'].strip(),' ==')
        if 'RequestActor' in Challenges[row]:
            print('Quest Giver : ',handle_geofence(Challenges[row]['RequestActor'].strip()))
            print("")
        if 'RequestLocation' in Challenges[row]:
            print('Location : ',Challenges[row]['RequestLocation'].strip())
            print("")
        for step in Challenges[row]['Steps']:
            if step['Name'] != 'Ready':
                print('=== ',step['Name'].strip(),' ===')
                print(handle_tags(step['Message'].strip()))
                print("")
                for points in step['DestinationPoint']:
                    if 'AlternativePos' in points:
                        print(f"Quest Marker pos X:{points['AlternativePos']['X']}, Y:{points['AlternativePos']['Y']}, Z:{points['AlternativePos']['Z']}")
                    if 'Pos' in points:
                        print(f"Quest Marker pos X:{points['Pos']['X']}, Y:{points['Pos']['Y']}, Z:{points['Pos']['Z']}")

def print_part(part):
        print('=== ',part.Name.strip(),' ===')
        print('[[File:',part.Name.strip(),' - TotK icon.png|144x144px|right]]')
        print('{{main|',part.Name.strip(),'}}')
        print('{{quote|'+handle_tags(part.Caption.strip())+'|In-game description}}')
        print()
        #print("*'''Selling Price:''' {{R|"+str(part.SellingPrice)+"}}")
        print("*'''Buying Price:''' {{R|"+str(part.BuyingPrice)+"}}")
        if part.ArmorEffectType != '':
            print("*'''Effect:''' "+part.ArmorEffectType_Name)
        print('''
        {|class="wikitable"
        !Tier
        !Armor
        !Materials
        !Selling Price
        ''')
        print_equipment_performance(part)
        print('|}')
        print('{{clear}}')
        print()

def format_materials(material):
    result = ""
    for item in material.Items:
        result = result + str(item['Number']) + " x [[" +item['Name'].strip()+"]] <br>"
    return result+"{{R|"+str(material.Price)+"}}"

def get_set_name(part1,part2):
    match = SequenceMatcher(None, part1, part2).find_longest_match()
    return part1[match.a:match.a + match.size].strip()

def print_equipment_performance(pouch,shifted_material = ""):
    icon = ''.join(["★" for _ in range(int(pouch.ArmorRank)-1)])
    materials_str = ""
    sell_str = ""
    if pouch.CannotSell is False:
        sell_str = "{{R|"+str(pouch.SellingPrice)+"}}"
    if pouch.ArmorNextRankActor_obj:
        materials_str = format_materials(pouch.ArmorNextRankActor_Material)
    print("|-")
    print("| "+icon+" || "+str(pouch.EquipmentPerformance)+" || "+shifted_material+" || "+sell_str)
    if pouch.ArmorNextRankActor_obj:
        print_equipment_performance(pouch.ArmorNextRankActor_obj, materials_str)


def order_by_set(items):
    armor = list(filter(lambda p: p.PouchCategory == "Armor", items.values()))
    armor = list(filter(lambda p: p.ArmorRank == 1, armor))
    armor_set = {}
    for row in armor:
        ##Grouping by set
        if row.Name != row.__RowId:
            id = row.__RowId.split('_')[1]
            part = row.__RowId.split('_')[2]
            if id not in armor_set:
                armor_set[id] = {}
            armor_set[id][part] = row
    #Handle Head only
    head_only = {}
    armor_set_cleaned = armor_set.copy()
    for row in armor_set:
        if len(armor_set[row]) == 1:
            key = list(armor_set[row].keys())[0]
            head_only[armor_set[row][key].__RowId] = armor_set[row][key]
            del armor_set_cleaned[row]

    for row in armor_set_cleaned.values():
        common_substring = get_set_name(row['Lower'].Name,row['Upper'].Name)
        if 'Head' in row:
            common_substring = get_set_name(row['Head'].Name,common_substring)
        if not common_substring[0].istitle():
            common_substring = "Set "+common_substring
        print('== ',common_substring,' ==')
        for part in row.values():
            print_part(part)

    print('== Others ==')
    for part in head_only.values():
        print_part(part)

def order_by_body_part(items):
    armor = list(filter(lambda p: p.PouchCategory == "Armor", items.values()))
    armor = list(filter(lambda p: p.ArmorRank == 1, armor))
    armor_set = {}
    for row in armor:
        ##Grouping by body part
        if row.Name != row.__RowId:
            id = row.__RowId.split('_')[1]
            part = row.__RowId.split('_')[2]
            if part not in armor_set:
                armor_set[part] = {}
            armor_set[part][id] = row

    for key, row in armor_set.items():
        print('== ',key,' ==')
        for part in row.values():
            print_part(part)

def main():
    totk = TOTK(".","USes")

    if len(sys.argv) >= 1:
        if sys.argv[1] == "quests":
            Challenges = totk.load_challenge()
            write_wiki_quests(Challenges)
        if sys.argv[1] == "armor":
            items = totk.load_pouch()
            order_by_body_part(items)

if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        print(e)
