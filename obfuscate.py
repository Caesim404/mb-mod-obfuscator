#!/bin/python2

# The location of the text files are found from (in that order):
#   1. First argument when calling the script
#   2. module_info.py file
#   3. Current directory
try:
    import sys
    DIRECTORY = sys.argv[1] + "/"
except IndexError:
    try:
        from module_info import export_dir as DIRECTORY
    except ImportError:
        DIRECTORY = "./"


###########
# OPTIONS #
###########
# Must be only whitespace characters (" ", "\t", "\n", "\r", "\v", "\x0C"). Used to separate values in the text files.
SEPARATOR      = "\v"
# Replace IDs? Setting to False should fix any in-game errors.
REPLACE_IDS    = True
# Use unique IDs rather than ID_PLACEHOLDER.
UNIQUE_IDS     = True
# Export ID map to here. If it's an empty string, don't export. Used for debugging.
ID_MAP_FILE    = "./id_map.txt"
# IDs will be replaced with this, unless UNIQUE_IDS is True.
ID_PLACEHOLDER = "0"
# Gets appended to non-empty files. Doesn't affect the functionality in any way. Must start with a whitespace character.
SIGNATURE      = SEPARATOR + "0\r\n\r\Hello!"

class Compress(object):
    # Compression is achieved by:
    #   1. Collapsing whitespace to 1 character. (SEPARATOR)
    #   2. Compressing floating point numbers. (e.g. 1.00000 => 1; -0.12000 => -0.12)
    #   3. Replacing unneeded IDs with 1 character. (ID_PLACEHOLDER)
    #   4. Clearing unneeded files.
    #   5. Removing excess data at the end of the files.
    
    def __init__(self, path, pattern=[], replace=False):
        if hasattr(replace, "__call__"):
            self.replace = replace
        else:
            self.replace = lambda x:replace
        
        self.name = path
        self.path = DIRECTORY + path
        self.id = 0
        self.id_map = []
        
        if pattern == False:
            self.data = []
            self.pattern = []
        else:
            self.pattern = pattern
            try:
                file = open(self.path, "r")
                self.data = file.read().split()
                file.close()
            except IOError:
                print "WARNING:", self.name, "could not be found"
                return
        self.compress()
    
    def process(self, pattern=None, i=0):
        lens = []
        data = self.data
        j = 0
        if pattern == None:
            pattern = self.pattern
        for value in pattern:
            # if type(value) != list and value != 1:
                # print "::", value, "->", data[i]
            if value == 1:
                # print "||", value, "->", data[i]
                lens.append(int(data[i]))
            elif type(value) == list:
                if len(lens) == 0:
                    # print "||", data[i]
                    l = int(data[i])
                    i += 1
                else:
                    l = lens.pop(0)
                for x in xrange(l):
                    i = self.process(pattern[j], i)
                i -= 1
            elif value == 2 and REPLACE_IDS:
                res = self.replace(data[i])
                if type(res) == str:
                    data[i] = res
                elif res:
                    if UNIQUE_IDS:
                        id = self.get_id()
                        self.id_map.append((id, data[i]))
                        data[i] = id
                    else:
                        data[i] = ID_PLACEHOLDER
            elif value == -1:
                try:
                    while True:
                        i = self.process(pattern[j+1], i)
                except IndexError:
                    break
            elif value == -2:
                if data[i] == "-1":
                    lens.append(0)
                else:
                    i -= 1
                    lens.append(1)
            i += 1
            j += 1
        return i
    
    def compress(self):
        print "Compressing", self.name, "..."
        
        self.compress_floats()
        if self.pattern != []:
            end_i = self.process()
            del self.data[end_i:]
            if id_map_file_open and self.id_map:
                id_map_file.write(self.name + ":\n" + "\n".join([x + "=" + y for x, y in self.id_map]) + "\n\n")
        
        file = open(self.path, "wb")
        output = SEPARATOR.join(self.data)
        if self.pattern != []:
            output += SIGNATURE
        file.write(output)
        file.close()
    
    def compress_floats(self):
        for i in xrange(len(self.data)):
            try:
                n = self.data[i]
                if "." in n:
                    float(n) # Checking if it is a valid float
                    self.data[i] = n.rstrip("0").rstrip(".")
            except ValueError:
                continue
    
    def get_id(self, i=None):
        if i == None:
            i = self.id
        chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_" # TO DO: check working chars
        char_count = len(chars)
        if i // char_count == 0:
            self.id += 1
            return chars[i]
        else:
            return self.get_id(i // char_count - 1) + chars[i % char_count]

if ID_MAP_FILE:
    id_map_file = open(ID_MAP_FILE, "w")
    id_map_file_open = True
else:
    id_map_file_open = False

#####################
# COMPRESSION RULES #
#####################
# Arguments to Compress:
# 1) Path to a file relative to DIRECTORY.
# 2) Pattern of the file. If set to False, the file contents are cleared. (default [])
#   [...] - A block. Used to group patterns.
#      -2 - If the value is "-1", the following block is ignored, else the block will be in it's place.
#      -1 - Next block is repeated until the end. Doesn't take actual space in the text file.
#       0 - Just takes space.
#       1 - Times the next block is repeated. Can be omitted, if the block follows immediately.
#       2 - ID. These are subject to replacement.
# 3) A function (1st parameter is string of the ID) or a value. If it evaluates to True, the ID is replaced with ID_PLACEHOLDER.
#                                                               But if it evaluates to a string, that string is used insead. (default False)

operations = [
    [0, [0]]
]

simple_triggers = [
    [0] + operations
]

triggers = [
    [0, 0, 0] + operations + operations
]

Compress("actions.txt", [ [2, 0, 0, [0]*10] ], True)
Compress("conversation.txt", [0, 0, 0, [2, 0, 0] + operations + [0, 0] + operations + [0]]) # IDs used in language files.
Compress("dialog_states.txt", False)
Compress("factions.txt") # TODO: figure out the format # NW: [0, 0, 0, [2] + [0]*25 + [[0]]])  # IDs used in language files and dedicated server.
Compress("info_pages.txt", [0, 0, 0, [2, 0, 0]]) # IDs used in language files.
Compress("item_kinds1.txt", [0, 0, 0, [2, 0, 0, [0, 0]] + [0]*17 + [[0]] + simple_triggers]) # IDs used in language files.
Compress("map.txt", [[0, 0, 0], [0, 0, [0]]])
Compress("map_icons.txt", [0, 0, 0, [2] + [0]*7 + simple_triggers], True)
Compress("menus.txt", [0, 0, 0, [2, 0, 0, 0] + operations + [[2] + operations + [0] + operations + [0]]])  # IDs used in language files.
Compress("meshes.txt", [[2] + [0]*11], True)
Compress("mission_templates.txt", [0, 0, 0, [2, 0, 0, 0, 0, [0, 0, 0, 0, 0, [0]]] + triggers], True)
Compress("music.txt", [ [0, 0, 0] ])
Compress("particle_systems.txt", [0, 0, 0, [2] + [0]*37], True)
Compress("parties.txt", [0, 0, 0, 1, 0, [0, 0, 0, 2] + [0]*17 + [[0]*4, 0]]) # IDs used in language files.
Compress("party_templates.txt", [0, 0, 0, [2] + [0]*5 + [-2,[0]*4]*6]) # IDs used in language files.
Compress("postfx.txt", [0, 0, 0, [2] + [0]*14], True)
Compress("presentations.txt", [0, 0, 0, [2, 0, 0] + simple_triggers], lambda x: not x.startswith("prsnt_game_"))
Compress("quests.txt", [0, 0, 0, [2, 0, 0, 0]]) # IDs used in language files.
Compress("quick_strings.txt", [[2,0]]) # IDs used in language files.
Compress("scene_props.txt", [0, 0, 0, [2, 0, 0, 0, 0] + simple_triggers]) # IDs are required to work.
Compress("scenes.txt", [0, 0, 0, [2] + [0]*10 + [[0], [0], 0]]) # IDs used in server hosting.
Compress("scripts.txt", [0, 0, 0, [2, 0] + operations], lambda x: not x.startswith("game_"))
Compress("simple_triggers.txt", [0, 0, 0, simple_triggers[0]])
Compress("skills.txt", [[2, 0, 0, 0, 0]]) # IDs used in language files.
Compress("skins.txt", [0, 0, 0, [2] + [0]*5 + [[0]*6] + [[0]]*4 + [[0, 0, 1, 1, [0], [0]], [0, 0]] + [0]*4 + [[0, 0, [0, 0]]]], True)
Compress("sounds.txt", [0, 0, 0, [0, 0], [2, 0, [0, 0]]]) # TO DO: Find the hardcoded sounds
Compress("strings.txt", [0, 0, 0, [2, 0]]) # IDs used in language files.
Compress("tableau_materials.txt", [[2] + [0]*8 + operations], lambda x: not x.startswith("tab_game_"))
Compress("tag_uses.txt", False)
Compress("triggers.txt", [0, 0, 0, triggers[0]])
Compress("troops.txt", [0, 0, 0, [2] + [0]*9 + [0, 0]*64 + [0]*26]) # IDs used in language files.
Compress("variable_uses.txt", False)
Compress("variables.txt", False)

# TO DO: Make work properly.
# Compress("Data/flora_kinds.txt") # TO DO: make the pattern.
# Compress("Data/ground_specs.txt", [-1, [2] + [0]*7],) # IDs used in map editor.
# Compress("Data/skyboxes.txt", [[2] + [0]*16]) # IDs required to work.

if id_map_file_open: id_map_file.close()
