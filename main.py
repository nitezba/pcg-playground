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

    # delta will be how long we want a step to take
    def gridMove(self, grid : dict, delta_time : int, direction : list = [0,0]) : 
        valid_move = True
        next_x = self.box.x + direction[0] * TILE_SIZE
        next_y = self.box.y + direction[1] * TILE_SIZE

        # bounds check
        if next_x >= WINDOW_WIDTH or next_x < 0 :
            valid_move = False
        if next_y >= WINDOW_HEIGHT or next_y < 0 :
            valid_move = False

        # wall check
        # TODO : PROBLEM - EXPOSE THIS TO THE MAP FOR ACCESS
        next_key = (next_x / TILE_SIZE, next_y / TILE_SIZE)

        if grid[next_key] == 2:
            valid_move = False

        if valid_move:
            self.box.x = next_x
            self.box.y = next_y
            # TODO : SMOOTH OUT THIS MOVEMENT
            # start = pygame.time.get_ticks()
            # end = start + delta_time
            # # smooth the transition from one to the next
            # delta_pos_x = next_x - self.box.x
            # step_length_x = delta_pos_x / delta_time

            # delta_pos_y = next_x - self.box.y
            # step_length_y = delta_pos_y / delta_time

            # # question - how much do we need to add each frame so that it'll take exactly delta_time to traverse
            # # delta_pos_X
            # if self.box.x != next_x :
            #     while pygame.time.get_ticks() < end :
            #         self.box.x += step_length_x

            # if self.box.y != next_y :
            #     while pygame.time.get_ticks() < end :
            #         self.box.y += step_length_y


        
    # the main purpose of handleAnimation will be to set the animation flag which dictates if we can take in more
    # input or not
    # start_time will get input from getTicks, thus being time in ms
    def handleAnimation(self, animaton : list, start_time : int, anim_duration : int) :
        if start_time < 0 :
            return
        
        delta = pygame.time.get_ticks() - start_time
        if delta < anim_duration :
            self.state['is_animating'] = True
        else :
            self.state['is_animating'] = False



# SPACE PARTITIONING TREE - just somewhere to put leaves an the whole tree together
class Tree:
    def __init__(self, tree : list, leaves : list) -> None:
        self.tree : list    = tree
        self.leaves: list   = leaves

    # should go through the tree and put connections where necessary/possible
    def connect(self) -> None:
        # treat it almost like frontier
        tree_dup : list = self.tree.copy()
        frontier : list = self.leaves.copy()


        # NOTE: WHEN WE FINISH THE BOTTOM LAYER AND CYCLE BACK
        # AROUND TO FORMER PARENT NODES, THOSE PARENT NODES
        # DONT HAVE ANY CHILDREN, WHICH IS WHY I THINK THIS FAILS
        while frontier :
            node : partitionCell = frontier[0]

            if node.parent == None:
                break
            # remove node we're checking, as well as its sibling!!

            # now that we know this node has a parent
                # obtain the parent
            parent : partitionCell = node.parent
                # remove its children from the frontier
            children : list = parent.children

            for child in children :
                if child in frontier :
                    frontier.remove(child)
                # add the former parent to the frontier
            frontier.append(parent)
            print(frontier)
        

            # identify siblings

            
            # pop siblings from frontier, add the former parent, establish bridge


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
        print("Parent Node (topLeft & dimension):" , self.topLeft, self.getDimensions())
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
        tiles = world["tile_assets"]
        assets = world["assets"]
        # tile assets handled separately here
        self.tile_assets = {}
        self.assets = {}
        for key in tiles :
            self.tile_assets[key] = load_image(tiles[key])

        for key in assets :
            self.assets[key] = load_image(assets[key])
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
    def spacePartition(self, root : partitionCell) -> Tree: 
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

        for node in skinnies :
            parent = node.parent
            # NOTE: this probably fucks with the order of leaves?
            for child in parent.children:
                if child in leaves:
                    leaves.remove(child)
            tree.remove(parent)
            parent.children = None
            leaves.append(parent)

        ret = Tree(tree, leaves)
        return ret

    # we have:
        # and n-dimensional grid
        # a set of states
        # a set of transition rules
    # area - partitionCell to use the topLeft and bottomRight of the area on which to apply this
    # asset_place - which kind of cell will get placed by the automata
    # asset_place - which kind of cell will get left behind by the automata when it decides to kill or ignore something
    def cellularAutomata(self, area : partitionCell, asset_place : int = 1, asset_ignore : int = 0, spawn_chance : int = .5) :
        # start by sprinkling the world
        # rocks : list = []
        num_iterations = 2
        neighbor_requirement = 4

        # for key in self.tile_map.keys() :
        for key in area.getInternalCoords() :
            place_tile = 1 if random.random() <= spawn_chance else 0

            if place_tile :
                # rocks.append(key)
                self.tile_map[key] = asset_place

        to_remove   : list  = []
        to_add      : list  = []
        # then apply propagation rules
        # a cell turns into rock in the next time step if at least
        # T (e.g. 5) of its neighbors are rock, otherwise it will turn into free space
        # NOTE: STORE THE CHANGES THAT NEED TO BE MADE AND THEN MAKE ALL THE REPLACEMENTS
        # DONT MAKE THE CHANGES AS YOU GO - THIS AFFECTS CURRENT STATE
        # TODO: this could be made faster by chunking a bit
        for i in range(num_iterations): # number of iterations that we want to apply
            # for key in self.tile_map.keys() :
            for key in area.getInternalCoords() :
                neighbors = self.getTileNeighbors(key)
                count = 0
                # double for loop to check all neighbors
                for row in neighbors.keys():
                    for col in neighbors[row].keys() :
                        neighbor_coord = neighbors[row][col]
                        
                        if neighbor_coord != None:
                            if self.tile_map[neighbor_coord] == asset_place :
                                count += 1
                if count >= neighbor_requirement :
                    to_add.append(key)
                else :
                    to_remove.append(key)

            for coord in to_add :
                self.tile_map[coord] = asset_place

            for coord in to_remove :
                self.tile_map[coord] = asset_ignore
            
# ===============================================================
frame_start = 0
frame_end = pygame.time.get_ticks()
dt = frame_end - frame_start
path = None

world = World()

root = partitionCell((0,0), (WINDOW_WIDTH / TILE_SIZE, WINDOW_HEIGHT / TILE_SIZE))
tree_map : Tree = world.spacePartition(root)
# for node in tree_map.leaves:
#     node.printData()

# TODO: DOOINNG THIS - MIX CA WITH BSP
# space partitionining rendering
for leaf in tree_map.leaves : # leaf is a partitionNode
    box : list = leaf.getInternalCoords()
    for coord in box :
        world.tile_map[coord] = 1

    world.cellularAutomata(leaf, 2, 1)

# tree_map.connect()
# world.cellularAutomata(root)

player = Entity(
    pygame.Rect(0,0,TILE_SIZE,TILE_SIZE),
    world.assets['player'],
    {
        'is_animating' : False
    }
)
input_time = -1

while playing :
    frame_start = frame_end
    raw_window.fill((0,0,0))
    player_move_v = [0, 0]


    # single keypress event polling
    for event in pygame.event.get() :
        if event.type == QUIT: 
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN: 
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            # if event.key == K_w:
            #     player_move_v = [0,-1]
            # if event.key == K_a:
            #     player_move_v = [-1,0]
            # if event.key == K_s:
            #     player_move_v = [0,1]
            # if event.key == K_d:
            #     player_move_v = [1,0]

    # key held down event polling
    keys = pygame.key.get_pressed()
    # IGNORE THIS INPUT IF MOVEMENT ANIMATION IS TAKING PLACE

    if not player.state['is_animating'] :
        if keys[pygame.K_w]:
            input_time = pygame.time.get_ticks()
            player_move_v = [0,-1]
            player.sprite = world.assets['walk_up']
        if keys[pygame.K_a]:
            input_time = pygame.time.get_ticks()
            player_move_v = [-1,0]
            player.sprite = world.assets['walk_left']
        if keys[pygame.K_s]:
            input_time = pygame.time.get_ticks()
            player_move_v = [0,1]
            player.sprite = world.assets['walk_down']
        if keys[pygame.K_d]:
            input_time = pygame.time.get_ticks()
            player_move_v = [1,0]
            player.sprite = world.assets['walk_right']

    step_duration = 300
    player.gridMove(world.tile_map, step_duration, player_move_v)
    player.handleAnimation(None, input_time, step_duration)

    # world rendering
    for coord in world.tile_map.keys() :
        if world.tile_map[coord] == 0:
            raw_window.blit(world.tile_assets['default'], (TILE_SIZE * coord[0], TILE_SIZE * coord[1]))
        if world.tile_map[coord] == 1:
            raw_window.blit(world.tile_assets['wall'], (TILE_SIZE * coord[0], TILE_SIZE * coord[1]))
        if world.tile_map[coord] == 2:
            raw_window.blit(world.tile_assets['mountain'], (TILE_SIZE * coord[0], TILE_SIZE * coord[1]))

    # player rendering
    if not player.state['is_animating'] :
        player.sprite = world.assets['player']
        
    raw_window.blit(player.sprite, player.box)

    scaled_window = pygame.transform.scale(raw_window, display_window.get_size())
    display_window.blit(scaled_window, (0,0))
    pygame.display.update()

    frame_end = pygame.time.get_ticks()
    dt = frame_end - frame_start
    clock.tick(60)