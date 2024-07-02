from time import sleep
from typing import List, Tuple
from collections import deque
from random import shuffle, choice, uniform, randint
from copy import deepcopy
from data import *

spawnPosition = Vector2Int(4, 20)
globalWidth = 10
globalHeight = 40

weights = {'lineClears' : [0, -2, -2, -2, 15], 'TSpin' : [0, 5, 15, 25] , 'TSpinMini' : [0, 0, 0], 'wellKnown' : 6, 'perfectClear' : 30, 'height': 0, 'overHalf': -0.12, 'spikiness' : -0.5, 'covered' : -1, 'gaps' : -2, 'wastedT' : -2}


class Placement:
    def __init__(self, piece: Piece, rotation: int, position: Vector2Int, spin: int = 0) -> None:
        self.piece = piece
        self.rotation = rotation
        self.position = position
        self.spin = spin

# cell 0, 0 is at bottom left
class Board:
    def __init__(self, cells: List[List[bool]] = [[False] * globalWidth for i in range(globalHeight)]) -> None:
        # if cells width does not match global width, raise error
        if len(cells[0]) != globalWidth:
            raise ValueError(f"Width of cells is not {globalWidth}")
        
        # if cells height does not match global height, add empty rows to the top
        if len(cells) < globalHeight:
            cells.extend([[False] * globalWidth for _ in range(globalHeight - len(cells))])

        self.cells = cells

    def __str__(self) -> str:
        # upside down
        result = ""
        for row in reversed(self.cells):
            for cell in row:
                result += "#" if cell else "_"
            result += "\n"
        return result
    
    def occupiedOrOutOfBounds(self, position: Vector2Int) -> bool:
        return position.x < 0 or position.x >= globalWidth or position.y < 0 or position.y >= globalHeight or self.cells[position.y][position.x]
    
    def maxHeight(self) -> int:
        for i in range(globalHeight - 1, -1, -1):
            if any(self.cells[i]):
                return i
        return 0
    
    def getHeights(self) -> List[int]:
        ans = [-1] * globalWidth
        for i in range(globalWidth):
            for j in range(globalHeight):
                if self.cells[j][i]:
                    ans[i] = j
                    break
        return ans
    
    def isValid(self, placement: Placement) -> bool:
        for cell in Cells[placement.piece][placement.rotation]:
            if self.occupiedOrOutOfBounds(placement.position + cell):
                return False
        return True
    
    def isFinalPlacement(self, placement: Placement) -> bool:
        # if piece cannot go down, return true
        return not self.isValid(Placement(placement.piece, placement.rotation, placement.position + Vector2Int(0, -1)))
    
    def TSpinCheck(self, placement: Placement, offsetIndex : int) -> int:
        if placement.piece == Piece.T:
            # check for fin and overhang T-Spin
            if (placement.rotation == 3 or placement.rotation == 1) and offsetIndex == 4:
                return 2
            else:
                # get number of corners filled
                corners = 0
                facingCorners = 0

                for offset in Diagonals:
                    # check if corners are filled
                    if self.occupiedOrOutOfBounds(placement.position + offset):
                        corners += 1

                for offset in TSpinFacingCorners[placement.rotation]:
                    # check if facing corners are filled
                    if self.occupiedOrOutOfBounds(placement.position + offset):
                        facingCorners += 1
                
                if corners >= 3:
                    if facingCorners >= 2:
                        return 2
                    else:
                        return 1
        return 0
    
    def TSpinCheckFlip(self, placement: Placement) -> int:
        corners = 0
        facingCorners = 0

        for offset in Diagonals:
            # check if corners are filled
            if self.occupiedOrOutOfBounds(placement.position + offset):
                corners += 1

        for offset in TSpinFacingCorners[placement.rotation]:
            # check if facing corners are filled
            if self.occupiedOrOutOfBounds(placement.position + offset):
                facingCorners += 1
        
        if corners >= 3:
            if facingCorners >= 2:
                return 2
            else:
                return 1
        return 0


    def findPlacements(self, piece: Piece) -> List[Placement]:
        finalPlacements = []

        if piece == Piece.NULLPIECE:
            print("Just tried to find placements for a null piece")
            return []
        
        # spawn obstructed
        if not self.isValid(Placement(piece, 0, spawnPosition)):
            return []
        
        maxHeight = self.maxHeight()

        optimalSpawnPosition = Vector2Int(spawnPosition.x, min(spawnPosition.y, maxHeight + 2))

        # visit matrix for rotation, x, y, with offset to avoid negative indices
        offsetM = 2
        visited = [[[False for _ in range(globalHeight + 4)] for _ in range(globalWidth + 4)] for _ in range(4)]

        queue = deque([Placement(piece, 0, optimalSpawnPosition)])

        while queue:
            placement = queue.popleft()
            if visited[placement.rotation][placement.position.x + offsetM][placement.position.y + offsetM]:
                continue
            visited[placement.rotation][placement.position.x + offsetM][placement.position.y + offsetM] = True


            # FOR DEBUGGING, PRINT BOARD WITH CURRENT PLACEMENT ON IT
            
            # debugBoard = deepcopy(self)

            # for cell in Cells[placement.piece][placement.rotation]:
            #     debugBoard.cells[placement.position.y + cell.y][placement.position.x + cell.x] = True
            
            # print(debugBoard)


            if self.isFinalPlacement(placement):
                # add to list of placements
                finalPlacements.append(placement)

            # move down
            down = Placement(placement.piece, placement.rotation, placement.position + Vector2Int(0, -1))
            if self.isValid(down) and not visited[down.rotation][down.position.x + offsetM][down.position.y + offsetM]:
                queue.append(down)

            # move left
            left = Placement(placement.piece, placement.rotation, placement.position + Vector2Int(-1, 0))
            if self.isValid(left) and not visited[left.rotation][left.position.x + offsetM][left.position.y + offsetM]:
                queue.append(left)

            # move right
            right = Placement(placement.piece, placement.rotation, placement.position + Vector2Int(1, 0))
            if self.isValid(right) and not visited[right.rotation][right.position.x + offsetM][right.position.y + offsetM]:
                queue.append(right)

            # rotate clockwise, using kick tables
            newRotation = (placement.rotation + 1) % 4
            offsetList = WallKicksI[placement.rotation] if placement.piece == Piece.I else WallKicksJLOSTZ[placement.rotation]

            for offsetIndex, offset in enumerate(offsetList):
                newPlacement = Placement(placement.piece, newRotation, placement.position + offset)
                if self.isValid(newPlacement):
                    if not visited[newPlacement.rotation][newPlacement.position.x + offsetM][newPlacement.position.y + offsetM]:
                        # check for T-Spin
                        if placement.piece == Piece.T:
                            newPlacement.spin = self.TSpinCheck(newPlacement, offsetIndex)
                        queue.append(newPlacement)
                    break
            
            # rotate counterclockwise, using kick tables
            newRotation = (placement.rotation - 1) % 4
            offsetList = WallKicksI[placement.rotation] if placement.piece == Piece.I else WallKicksJLOSTZ[placement.rotation]

            for offsetIndex, offset in enumerate(offsetList):
                newPlacement = Placement(placement.piece, newRotation, placement.position + offset)
                if self.isValid(newPlacement):
                    if not visited[newPlacement.rotation][newPlacement.position.x + offsetM][newPlacement.position.y + offsetM]:
                        # check for T-Spin
                        if placement.piece == Piece.T:
                            newPlacement.spin = self.TSpinCheck(newPlacement, offsetIndex)
                        queue.append(newPlacement)
                    break

            # flip, using kick tables
            newRotation = (placement.rotation + 2) % 4
            offsetList = Flips[placement.rotation]

            for offsetIndex, offset in enumerate(offsetList):
                newPlacement = Placement(placement.piece, newRotation, placement.position + offset)
                if self.isValid(newPlacement):
                    if not visited[newPlacement.rotation][newPlacement.position.x + offsetM][newPlacement.position.y + offsetM]:
                        # check for T-Spin, specifically for flips
                        if placement.piece == Piece.T:
                            newPlacement.spin = self.TSpinCheckFlip(newPlacement)
                        queue.append(newPlacement)
                    break
                
        return finalPlacements


def PlacePieceAndEvaluate(board: Board, placement: Placement) -> Tuple[Board, float, bool, bool]:
    newBoard = deepcopy(board)
    
    # place piece
    for cell in Cells[placement.piece][placement.rotation]:
        newBoard.cells[placement.position.y + cell.y][placement.position.x + cell.x] = True

    shouldClear = [False] * globalHeight
    linesCleared = 0

    # check for lines to clear

    maxHeight = newBoard.maxHeight()

    for i in range(maxHeight):
        if all(newBoard.cells[i]):
            shouldClear[i] = True
            linesCleared += 1

    for i in range(maxHeight - 1, -1, -1):
        if shouldClear[i]:
            newBoard.cells.pop(i)
    
    # add new lines
    newBoard.cells.extend([[False] * globalWidth for _ in range(linesCleared)])

    maxHeight = newBoard.maxHeight()

    # check for perfect clear (if bottom row is empty)
    perfectClear = False
    if all(not cell for cell in newBoard.cells[0]):
        perfectClear = True

    # calculate spikiness
        
    spikiness = 0
    heights = newBoard.getHeights()
    for i in range(globalWidth - 1):
        spikiness += max(abs(heights[i] - heights[i + 1]) - 1, 0)

    # calculate 0s covered by 1s
    found1 = [False for _ in range(globalWidth)]
    covered = 0

    for i in range(maxHeight - 1, -1, -1):
        for j in range(globalWidth):
            if newBoard.cells[i][j] == 1:
                found1[j] = True
            elif found1[j]:
                covered += 1

    gaps = 0
    # calculate 0s with 1s right above
    for i in range(maxHeight - 2, -1, -1):
        for j in range(globalWidth):
            gaps += (newBoard.cells[i][j] == 0) and (newBoard.cells[i+1][j] == 1)

    # calculate 1s over half height
    overHalf = 0
    for i in range(globalWidth):
        overHalf += max(0, heights[i] - maxHeight//2)

    # look for well knows T spin setups
    # 101
    # 000
    # 100
    # OR
    # 101
    # 000
    # 001
    wellKnown = False
    for i in range(maxHeight - 2, -1, -1):
        for j in range(globalWidth - 2):
            # do the 9 checks
            if newBoard.cells[i][j] == 1 and newBoard.cells[i][j+1] == 0 and newBoard.cells[i][j+2] == 1 and newBoard.cells[i+1][j] == 0 and newBoard.cells[i+1][j+1] == 0 and newBoard.cells[i+1][j+2] == 0 and newBoard.cells[i+2][j] == 1 and newBoard.cells[i+2][j+1] == 0 and newBoard.cells[i+2][j+2] == 0:
                wellKnown = True
                break
            if newBoard.cells[i][j] == 1 and newBoard.cells[i][j+1] == 0 and newBoard.cells[i][j+2] == 1 and newBoard.cells[i+1][j] == 0 and newBoard.cells[i+1][j+1] == 0 and newBoard.cells[i+1][j+2] == 0 and newBoard.cells[i+2][j] == 0 and newBoard.cells[i+2][j+1] == 0 and newBoard.cells[i+2][j+2] == 1:
                wellKnown = True
                break

    score = weights['spikiness'] * spikiness + weights['covered'] * covered + weights['height'] * maxHeight + weights['overHalf'] * overHalf + perfectClear * weights['perfectClear'] + gaps * weights['gaps'] + wellKnown * weights['wellKnown']
    
    if placement.spin == 2:
        score += weights['TSpin'][linesCleared]
    elif placement.spin == 1:
        score += weights['TSpinMini'][linesCleared]
    else:
        score += linesCleared * weights['lineClears'][linesCleared]
    
    if placement.piece == Piece.T and placement.spin == 0:
        score += weights['wastedT']

    continueB2B = (placement.spin != 0) or (linesCleared == 4)
    continueCombo = (linesCleared > 0)

    return newBoard, score, continueB2B, continueCombo

class GameState:
    def __init__(self, board: Board = Board(), activePiece: Piece = Piece.NULLPIECE, holdPiece: Piece = Piece.NULLPIECE, queue: deque = deque(), evalutaion: float = 0, b2b: int = 0, combo: int = 0, lastMove = None, pieceCount = 0) -> None:
        self.board = board
        self.activePiece = activePiece
        self.holdPiece = holdPiece
        self.queue = queue
        self.evaluation = evalutaion
        self.b2b = b2b
        self.combo = combo
        self.lastMove = lastMove

        self.pieceCount = pieceCount

    def get_game_repr(self):
        square_width = globalHeight//2 # hard lock to 20 right now
        game_state_repr = [[0 for _ in range(square_width)] for _ in range(square_width)]

        for i in range(square_width):
            for j in range(globalWidth):
                game_state_repr[i][j] = self.board.cells[i][j]

        # place active piece then 5 queue pieces to the right of the board, each piece should have 3 rows
        queueCol = globalWidth + 3
        
        piece = self.activePiece
        for i in range(min(5, len(self.queue))):
            position = Vector2Int(globalWidth + 5, i * 2 + 1)
            for cell in Cells[piece][0]:
                game_state_repr[position.y + cell.y][position.x + cell.x] = 1
            piece = self.queue[i]
        
        
        # add hold piece to the bottom of the board
        if self.holdPiece != Piece.NULLPIECE:
            position = Vector2Int(globalWidth + 5, square_width - 2)
            piece = self.holdPiece
            for cell in Cells[piece][0]:
                game_state_repr[position.y + cell.y][position.x + cell.x] = 1
        
        # make sure everything is 0 or 1
        for i in range(square_width):
            for j in range(square_width):
                game_state_repr[i][j] = int(game_state_repr[i][j])
        return game_state_repr

    def generateChildren(self) -> List['GameState']:
        children = []

        # 3 cases:
        # 1. place active piece, hold does not change
        # 2. use hold while hold empty and place
        # 3. use hold while hold not empty and place

        # case 1

        placements = self.board.findPlacements(self.activePiece)

        for placement in placements:
            newBoard, score, continueB2B, continueCombo = PlacePieceAndEvaluate(self.board, placement)
            newQueue = deepcopy(self.queue)
            newActivePiece = newQueue.popleft() if newQueue else Piece.NULLPIECE
            lastMove = {"piece": self.activePiece, "rotation": placement.rotation, "position": placement.position, "spin": "none"}
            if placement.spin == 2:
                lastMove["spin"] = "full"
            elif placement.spin == 1:
                lastMove["spin"] = "mini"
            children.append(GameState(newBoard, newActivePiece, self.holdPiece, newQueue, self.evaluation + score, self.b2b + continueB2B, self.combo + continueCombo, lastMove, self.pieceCount + 1))

        # case 2
        
        if self.holdPiece == Piece.NULLPIECE:
            
            # activePiece goes to hold
            # activePiece is first in queue
            # place activePiece, then pop queue again

            newQueue = deepcopy(self.queue)
            newHoldPiece = self.activePiece
            newActivePiece = newQueue.popleft() if newQueue else Piece.NULLPIECE
            
            newState = GameState(self.board, newActivePiece, newHoldPiece, newQueue, self.evaluation, self.b2b, self.combo)
            placements = newState.board.findPlacements(newActivePiece)

            for placement in placements:
                newBoard, score, continueB2B, continueCombo = PlacePieceAndEvaluate(self.board, placement)
                newQueue = deepcopy(newState.queue)
                newActivePiece = newQueue.popleft() if newQueue else Piece.NULLPIECE

                lastMove = {"piece": newState.activePiece, "rotation": placement.rotation, "position": placement.position, "spin": "none"}
                if placement.spin == 2:
                    lastMove["spin"] = "full"
                elif placement.spin == 1:
                    lastMove["spin"] = "mini"
                children.append(GameState(newBoard, newActivePiece, newHoldPiece, newQueue, self.evaluation + score, self.b2b + continueB2B, self.combo + continueCombo, lastMove, self.pieceCount + 1))
        
        # case 3
                
        else:

            # swap activePiece and holdPiece, then place activePiece

            newState = GameState(self.board, self.holdPiece, self.activePiece, self.queue, self.evaluation, self.b2b, self.combo)
            placements = newState.board.findPlacements(newState.activePiece)

            for placement in placements:
                newBoard, score, continueB2B, continueCombo = PlacePieceAndEvaluate(self.board, placement)
                newQueue = deepcopy(newState.queue)
                newActivePiece = newQueue.popleft() if newQueue else Piece.NULLPIECE
                
                lastMove = {"piece": newState.activePiece, "rotation": placement.rotation, "position": placement.position, "spin": "none"}
                if placement.spin == 2:
                    lastMove["spin"] = "full"
                elif placement.spin == 1:
                    lastMove["spin"] = "mini"
                children.append(GameState(newBoard, newActivePiece, newState.holdPiece, newQueue, self.evaluation + score, self.b2b + continueB2B, self.combo + continueCombo, lastMove, self.pieceCount + 1))
        
        return children

    def __str__(self) -> str:
        result = self.board.__str__()
        result += f"Piece: {self.activePiece}\n"
        result += f"Held Piece: {self.holdPiece}\n"
        visibleQueue = list(self.queue)[:5]
        result += f"Queue: {visibleQueue}\n"

        return result
    
# gs = GameState(queue = deque([Piece.J]), activePiece = Piece.Z, holdPiece=Piece.O)

# for gs1 in gs.generateChildren():


#     print(gs1)