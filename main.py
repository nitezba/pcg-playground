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
WINDOW_WIDTH = 240  # 40 tiles across
WINDOW_HEIGHT = 160 # 30 tiles down
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

# expects string (_ , ... , _)
def tupleFromString(s : str) :
    new_s = s.replace('(', '')
    new_s = new_s.replace(')', '')
    return tuple(map(int, new_s.split(',')))

def stringFromTuple (t : tuple) -> str:
    ret = "("
    for elt in t :
        ret += str(elt) + ","
    ret = ret[:-1]
    ret += ")"
    return ret

class Entity :
    def __init__(self, box : pygame.Rect, sprite : pygame.Surface, state : dict ) -> None:
        self.box            = box
        self.sprite         = sprite
        self.state          = state

class Tree:
    def __init__(self, tree : list, leaves : list) -> None:
        self.tree : list    = tree
        self.leaves: list   = leaves

class partitionCell :
    def __init__(self, topLeft : tuple, bottomRight : tuple) -> None:
        self.topLeft        = topLeft
        self.bottomRight    = bottomRight
        self.children : list= None
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

# TODO (maybe)
# it might make more sense to create classes in python and pickle them

# question : what's the point of the json if we can just manage it in a dictionary here in python?
    # maybe json might not be the best for pcg, as we need to generate it, not load it in
    
    # maybe we just use json to hold data about obstacles/nontrivial tile types and keep a dict or tiles here
    
    # does it make more sense to generate a map from nothing or to overlay the space partitioning on the empty map

    # range : area in which we allow the cut to be made
    # orientation : 0 for horizontal (cut will be vertical), 1 for vertical
    def spacePart(self, root : partitionCell) -> Tree: 
        # might be better to do this as a dictionary instead?
        tree = []
        leaves = []
        frontier = []
        frontier.append(root)
        # ==========================================
        # given an arbitrary leaf node, it is the job of the frontier to create and add it's children to the
        # tree, and in turn update the array of leaf nodes
        # ==========================================
        while frontier:
            node : partitionCell = frontier[0]
            frontier.remove(frontier[0])
            # if reached smallest size
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
            node.children = [ # horizontal range -> vertical cut
                partitionCell(node.topLeft, (spliceLocation, node.bottomRight[1])),
                partitionCell((spliceLocation + 1, node.topLeft[1]), node.bottomRight)
            ] if orientation == 0 else [ # vertical range -> horizontal cut
                partitionCell(node.topLeft, (node.bottomRight[0], spliceLocation)),
                partitionCell((node.topLeft[0], spliceLocation + 1), node.bottomRight)
            ]
            # node.printData()
            tree.append(node)

            frontier.append(node.children[0])
            frontier.append(node.children[1])

            # I THINK THE ISSUE IS HERE, WITH WHAT WE CONSIDER AND HOW WE HANDLE THE BASE CASE
            # for elt in node.children:
            #     dims : tuple = elt.getDimensions()
            #     if dims[0] <= 5 or dims[1] <= 5:
            #         print("SKIPPPPPPPP")
            #     else :
            #         leaves.append(elt)

        ret = Tree(tree, leaves)
        return ret


    def spacePartition(self, cell : partitionCell, orientation : bool) :
        space = (0,0)
        # RECURSIVE APPROACH DOES NOT WORK BECAUSE OF HOW IT'LL POPULATE SHIT AS IT WORKS IT'S WAY BACK UP
        # WE WANT IT TO DO EACH LEVEL OF THE TREE TO COMPLETION AND THEN MOVE DOWN

        # TODO: there's gotta be a simple way to only check orientation once at the start
            # or not at all
        if orientation == 0 :
            space = cell.getHorizontalRange()
        elif orientation == 1 : 
            space = cell.getVerticalRange()
        
    # extract middle quarter
        space_size = abs(space[0] - space[1])
        print(space)
        # TODO: SECOND CONDITION FEELS V SILLY and i dont fully get why it's needed to begin with tbh
        # ALSO TODO: BASE THIS ON ONLY ONE OF THE DIMENSIONS (THE SMALLER ONE) INSTEAD
        if space_size <= 4 or space[0] < space[1]:
            # self.tile_map[cell.topLeft] = 1
            # self.tile_map[cell.bottomRight] = 1
            return
        else :
            middle = (space[0] + math.floor(space_size / 4), space[1] - math.floor(space_size / 4))
            # we'll make the left/top cell inclusive of this, and ofc the bottom one exclusive
            # print(middle, "h" if not orientation else "v")
            spliceLocation = random.randrange(middle[0], middle[1])
            if orientation == 0 : # vertical cut
                cell1 = partitionCell(cell.topLeft, (spliceLocation, cell.bottomRight[1]))
                cell2 = partitionCell((spliceLocation + 1, cell.topLeft[1]), cell.bottomRight)
            elif orientation == 1: # horizontal cut
                cell1 = partitionCell(cell.topLeft, (cell.bottomRight[0], spliceLocation))
                cell2 = partitionCell((cell.topLeft[0], spliceLocation + 1), cell.bottomRight)

            # TODO : this is just alternating but it might be better to have random orientation
            self.spacePartition(cell1, not orientation)
            self.spacePartition(cell2, not orientation)

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