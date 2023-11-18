import pygame, sys, random, math, wave, os, json
clock = pygame.time.Clock()

# NOTE - could be made more flexible by specifying top down or side scrolling

from pygame.locals import *

# JSON is a serialization format, textual data representing a structure. It is not, itself, that structure.

# optimization algos are not guaranted to find an answer but are tolerably close enough to being complete
# HC - from a particular node
# if on my frontier there is something better, take that step

# this all relies on reepresenting our map/problem as a graph


# gonna do 30 x 20 resolution here
pygame.init() 
# WINDOW_WIDTH = 240  # 40 tiles across
WINDOW_WIDTH = 200  # 35 tiles across
WINDOW_HEIGHT = 200 # 35 tiles down
# WINDOW_HEIGHT = 160 # 30 tiles down
TILE_SIZE = 8

display_window = pygame.display.set_mode((WINDOW_WIDTH * 4, WINDOW_HEIGHT * 4), 0, 32)
raw_window = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

playing = True
# ===============================================================
# stuff i should put in a utils.py but wont :D 
# ===============================================================
BASE_PATH = './'

def load_image(path):
    img = pygame.image.load(BASE_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_dir(path) :
    images = []
    for img_name in sorted(os.listdir(BASE_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

def stringFromTuple (t : tuple) -> str:
    ret = "("
    for elt in t :
        ret += str(elt) + ","
    ret = ret[:-1]
    ret += ")"
    return ret

# base entity class - only used to contain general information about a controllable character
class Entity :
    def __init__(self, box : pygame.Rect, sprite : pygame.Surface, state : dict ) -> None:
        self.box            = box
        self.sprite         = sprite
        self.state          = state

# SPACE PARTITIONING TREE - just somewhere to put leaves an the whole tree together
class Tree:
    def __init__(self, tree : list, leaves : list) -> None:
        self.tree : list    = tree
        self.leaves: list   = leaves

# CELL USED IN SPACE PARTITIONING
class partitionCell :
    def __init__(self, topLeft : tuple, bottomRight : tuple, parent = None) -> None:
        self.topLeft                = topLeft
        self.bottomRight            = bottomRight
        self.children : list        = None
        # can use this to help merge rooms that or too small or post-processing in general
        self.parent : partitionCell = parent
        # self.isLeaf

    # returns tuple of leftmost and rightmost y-values
    def getHorizontalRange(self) -> tuple:
        return (self.topLeft[0], self.bottomRight[0])
    
    def getVerticalRange(self) -> tuple:
        return (self.topLeft[1], self.bottomRight[1])
    
    # return tuple of x, y dimensions
    def getDimensions(self) -> tuple:
        return (self.bottomRight[0] - self.topLeft[0], self.bottomRight[1] - self.topLeft[1])

    # return a list of the x,y coordinates that are contained in the cell
    def getInternalCoords(self) -> list: # given the topLeft and bottomRight coords
        ret = []
        x_start = self.topLeft[0]
        y_start = self.topLeft[1]
        x_bound = self.bottomRight[0] - x_start
        y_bound = self.bottomRight[1] - y_start

        r = 0
        while r < x_bound :
            c = 0
            while c < y_bound :
                coord = (x_start + r, y_start + c)
                ret.append(coord)
                c += 1
            r += 1

        return ret


    def isDonePartitioning(self) -> bool:
        dims : tuple = self.getDimensions()
        if dims[0] <= 5 or dims[1] <= 5:
            return True
        
        return False

    # TODO: splitvertical/horizontal functions

    def printData(self) -> None :
        print("Top left: ", self.topLeft, "Bottom right: ", self.bottomRight)
        print("Dimensions: ", self.getDimensions())
        if self.children != None :
            print("Children:", len(self.children))
            for node in self.children:
                print("topLeft:", node.topLeft, "bottomRight:", node.bottomRight)
        else:
            print("no more")
        print("==============================")


class World :
    def __init__(self) -> None:
        # can be externalized to json along with map
        # self.assets = {
        #     'blank' :   load_image("blank.png")
        # }
        # ========= OPEN FILE =========
        mapFile = open('empty.json')
        data = json.load(mapFile)
        mapFile.close()
        world = data["world"]
        # ========= HANDLE ASSETS =========
        # assets will include things like player sprite, objects, and misc entities. 
        # tiles will be reserved for tile_types
        self.assets = world["assets"]
        tiles = world["tile_assets"]
        # tile assets handled separately here
        self.tile_assets = {}
        for key in tiles :
            self.tile_assets[key] = load_image(tiles[key])
        # ========= HANDLE MAP =========
        # the absence of a coordinate in "map" in the json indicates that it's just a blank tile
        # NOTE : tile_map dict will have raw tuples as keys, while json will have strings of tuples as keys
        self.tile_map = {}
        for y in range(world["window_data"]["tiles_down"]) :
            for x in range(world["window_data"]["tiles_across"]) :
                if stringFromTuple((x, y)) not in world["map"].keys():
                    self.tile_map[(x, y)] = 0
                
        self.level_number = 0

    def getTileNeighbors(self, coord: tuple) -> dict :
        tiles = {
            "top" : {},
            "middle" : {},
            "bottom" : {}
        }
        
        tiles["top"]["left"] = (coord[0] - 1, coord[1] - 1) if coord[0] > 0 and coord[1] > 0 else None
        tiles["top"]["middle"] = (coord[0], coord[1] - 1) if coord[1] > 0 else None
        tiles["top"]["right"] = (coord[0] + 1, coord[1] - 1) if coord[0] < WINDOW_WIDTH / TILE_SIZE - 1 and coord[1] > 0 else None
       
        tiles["middle"]["left"] = (coord[0] - 1, coord[1]) if coord[0] > 0  else None
        tiles["middle"]["middle"] = None
        tiles["middle"]["right"] = (coord[0] + 1, coord[1]) if coord[0] < WINDOW_WIDTH / TILE_SIZE - 1 else None

        tiles["bottom"]["left"] = (coord[0] - 1, coord[1] + 1) if coord[0] > 0 and coord[1] < WINDOW_HEIGHT / TILE_SIZE - 1 else None
        tiles["bottom"]["middle"] = (coord[0], coord[1] + 1) if coord[1] < WINDOW_HEIGHT / TILE_SIZE - 10 else None
        tiles["bottom"]["right"] = (coord[0] + 1, coord[1] + 1) if coord[0] < WINDOW_WIDTH / TILE_SIZE - 1 and coord[1] < WINDOW_HEIGHT / TILE_SIZE - 1 else None
         
        return tiles

# TODO (maybe)
# it might make more sense to create classes in python and pickle them

    # range : area in which we allow the cut to be made
    # orientation : 0 for horizontal (cut will be vertical), 1 for vertical
    def spacePart(self, root : partitionCell) -> Tree: 
        # maintains tree structure
        tree = []
        # populated once we know the froniter is on its last expansion
        leaves = []
        # used for expansion of the tree
        frontier = []
        frontier.append(root)
        # =====================================================
        # given an arbitrary leaf node, it is the job of the frontier to create and add it's children to the
        # tree, and in turn update the array of leaf nodes
        # =====================================================
        while frontier:
            node : partitionCell = frontier[0]
            frontier.remove(frontier[0])
            if node.isDonePartitioning() :
                # skip - NOTE : no tree adding is necessary in this case bc the leaves will already exist in the children of certain nodes
                leaves.append(node)
                continue
            # otherwise keep partitioning
            orientation = 1 if random.random() >= .5 else 0
            # extract middle two quarters of space
            space = node.getVerticalRange() if orientation == 1 else node.getHorizontalRange()
            # TODO: expose to json 
            space_size = abs(space[0] - space[1])
            middle = (space[0] + math.floor(space_size / 4), space[1] - math.floor(space_size / 4))
            spliceLocation = random.randrange(middle[0], middle[1])
            
            # TODO: MOVE INTO split FUNCTION
            # split up cell into children 
            # partitionCell(topLeft, bottomRight, parent)
            node.children = [ # horizontal range -> vertical cut
                partitionCell(
                    node.topLeft, 
                    (spliceLocation, node.bottomRight[1]), 
                    node
                ), partitionCell(
                    (spliceLocation + 1, node.topLeft[1]), 
                    node.bottomRight, 
                    node
                )
            ] if orientation == 0 else [ # vertical range -> horizontal cut
                partitionCell(
                    node.topLeft, 
                    (node.bottomRight[0], spliceLocation), 
                    node
                ), partitionCell(
                    (node.topLeft[0], spliceLocation + 1), 
                    node.bottomRight, 
                    node
                )
            ]
            
            tree.append(node)

            frontier.append(node.children[0])
            frontier.append(node.children[1])

        # TODO: check the size of leaf nodes - if too skinny, merge with sister node
        # i.e. remove these leaves leaving only parents
        skinnies : list = []
        for node in leaves:
            dims : tuple = node.getDimensions()
            if dims[0] <= 2 or dims [1] <= 2:
                skinnies.append(node)
                # print("hey soul sister: VVVVVVVVVV")
                # node.parent.printData()
                # print("hey soul sister: ^^^^^^^^^^")

        for node in skinnies :
            parent = node.parent
            # NOTE: this probably fucks with the order of leaves?
            tree.remove(parent)
            # for child in parent.children:
            #     leaves.remove(child)
            parent.children = None
            leaves.append(parent)

        ret = Tree(tree, leaves)
        return ret

    # we have:
        # and n-dimensional grid
        # a set of states
        # a set of transition rules
    def cellularAutomata(self) :
        # start by sprinkling the world
        # rocks : list = []
        spawn_chance = .5
        neighbor_requirement = 4

        for key in self.tile_map.keys() :
            place_tile = 1 if random.random() <= spawn_chance else 0

            if place_tile :
                # rocks.append(key)
                self.tile_map[key] = 1

        to_remove   : list  = []
        to_add      : list  = []
        # then apply propagation rules
        # a cell turns into rock in the next time step if at least
        # T (e.g. 5) of its neighbors are rock, otherwise it will turn into free space
        # NOTE: STORE THE CHANGES THAT NEED TO BE MADE AND THEN MAKE ALL THE REPLACEMENTS
        # DONT MAKE THE CHANGES AS YOU GO - THIS AFFECTS CURRENT STATE
        # TODO: this could be made faster by chunking a bit
        for i in range(3): 
            for key in self.tile_map.keys() :
                neighbors = self.getTileNeighbors(key)
                count = 0
                # double for loop to check all neighbors
                for row in neighbors.keys():
                    for col in neighbors[row].keys() :
                        neighbor_coord = neighbors[row][col]
                        
                        if neighbor_coord != None:
                            if self.tile_map[neighbor_coord] == 1 :
                                count += 1
                if count >= neighbor_requirement :
                    to_add.append(key)
                else :
                    to_remove.append(key)

            for coord in to_add :
                self.tile_map[coord] = 1

            for coord in to_remove :
                self.tile_map[coord] = 0
            
# ===============================================================
frame_start = 0
frame_end = pygame.time.get_ticks()
dt = frame_end - frame_start
path = None

world = World()

root = partitionCell((0,0), (WINDOW_WIDTH / TILE_SIZE, WINDOW_HEIGHT / TILE_SIZE))
tree_map : Tree = world.spacePart(root)
for node in tree_map.leaves:
    node.printData()

# world.cellularAutomata()

while playing :
    frame_start = frame_end
    raw_window.fill((0,0,0))

    # event polling
    for event in pygame.event.get() :
        if event.type == QUIT: 
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN: 
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

    # space partitionining rendering
    for leaf in tree_map.leaves : # elt is a partitionNode
        box : list = leaf.getInternalCoords()
        for coord in box :
            world.tile_map[coord] = 1


    for coord in world.tile_map.keys() :
        if world.tile_map[coord] == 0:
            raw_window.blit(world.tile_assets['default'], (TILE_SIZE * coord[0], TILE_SIZE * coord[1]))
        if world.tile_map[coord] == 1:
            raw_window.blit(world.tile_assets['wall'], (TILE_SIZE * coord[0], TILE_SIZE * coord[1]))

        

    scaled_window = pygame.transform.scale(raw_window, display_window.get_size())
    display_window.blit(scaled_window, (0,0))
    pygame.display.update()

    frame_end = pygame.time.get_ticks()
    dt = frame_end - frame_start
    clock.tick(60)