import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

from deep_q import *
import json
from types import SimpleNamespace

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# send information about bot

info = {"name": "olt", "version": "0.0.1", "author": "imcatag", "features" : []}

print(json.dumps(info))

# recieve rules
rules = input()

# if rules does not have "type" = "rules", stop
rules = json.loads(rules, object_hook=lambda d: SimpleNamespace(**d))
if rules.type != "rules":
    print("error")
    exit()

ready = {"type": "ready"}

print(json.dumps(ready))

# start structure:
"""
{"hold":null,"queue":["T","I","L","J","S","O"],"combo":0,"back_to_back":false,"b2b_counter":0,"board":[[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null],[null,null,null,null,null,null,null,null,null,null]],"type":"start"}
"""
# play structure
"""
{"type":"play","move":{"location":{"type":"I","orientation":"north","x":4,"y":0},"spin":"none"}}
"""
# new piece structure
"""
{"piece":"I","type":"new_piece"}
"""
# suggest structure
"""
{"type":"suggest"}
"""
# suggestion structure
"""
{"type":"suggestion","moves":[{"location":{"type":"L","orientation":"east","x":0,"y":1},"spin":"none"}]}
"""

def stringToPiece(piece):
    if piece == "I":
        return Piece.I
    elif piece == "O":
        return Piece.O
    elif piece == "T":
        return Piece.T
    elif piece == "S":
        return Piece.S
    elif piece == "Z":
        return Piece.Z
    elif piece == "J":
        return Piece.J
    elif piece == "L":
        return Piece.L
    else:
        return Piece.NULLPIECE

firstHold = True

agent = DQNAgent(play_mode=True, model_name='4200.hdf5')

def getNextState(agent):
        next_possible_states = agent.state.generateChildren()

        if len(next_possible_states) == 0:
            return False

        next_state = agent.get_play_best_state(next_possible_states)

        return next_state

queuepls = []

while True:
    # recieve start, play, new_piece, or suggest
    message = input()
    message = json.loads(message, object_hook=lambda d: SimpleNamespace(**d))

    if message.type == "start":
        # create board that matches the start board
        # if null => 0, else 1
        board = Board()
        for i in range(len(message.board)):
            for j in range(len(message.board[i])):
                if message.board[i][j] == None:
                    board.cells[i][j] = 0
                else:
                    board.cells[i][j] = 1

        activePiece = stringToPiece(message.queue[0])

        pieceQueue = []

        # convert to Piece enum objects
        for i in range(1, len(message.queue)):
            pieceQueue.append(stringToPiece(message.queue[i]))

        
        heldPiece = Piece.NULLPIECE
        if message.hold != None:
            heldPiece = stringToPiece(message.hold)

        agent.state = GameState(board = board, queue = deque(pieceQueue), activePiece = stringToPiece(message.queue[0]), holdPiece = heldPiece)

    if message.type == "play":
        # advance the state to the next state

        agent.state = stateToAdvanceTo

        # add queuepls to the queue
        for i in range(len(queuepls)):
            agent.state.queue.append(queuepls[i])
        
        queuepls = []

        if next_state == False:
            print("error")
            exit()
        
    if message.type == "new_piece":
        # add the new piece to the queue
        agent.state.queue.append(stringToPiece(message.piece))
        queuepls.append(stringToPiece(message.piece))

    if message.type == "suggest":
        # suggest a move
        next_state = getNextState(agent)
        move = deepcopy(next_state.lastMove)
        stateToAdvanceTo = deepcopy(next_state)
        
        Ioffsetx = 0
        Ioffsety = 0
        Ooffsetx = 0
        Ooffsety = 0
        if move["rotation"] == 0:
            move["rotation"] = "north"
            Ioffsety = 1
        elif move["rotation"] == 1:
            move["rotation"] = "east"
            Ioffsetx = 1
            Ioffsety = 1

            Ooffsety = 1
        elif move["rotation"] == 2:
            move["rotation"] = "south"
            Ioffsetx = 1

            Ooffsetx = 1
            Ooffsety = 1
        else:
            move["rotation"] = "west"
            Ooffsetx = 1

        suggestion = {"type": "suggestion", "moves": [{"location": {"type": move["piece"], "orientation": move["rotation"], "x": move["position"].x, "y": move["position"].y}, "spin": move["spin"]}]}

        # apply offset for I piece and O piece

        if move["piece"] == Piece.I:
            suggestion["moves"][0]["location"]["x"] += Ioffsetx
            suggestion["moves"][0]["location"]["y"] += Ioffsety
        elif move["piece"] == Piece.O:
            suggestion["moves"][0]["location"]["x"] += Ooffsetx
            suggestion["moves"][0]["location"]["y"] += Ooffsety

        # go from piece enum to string
        suggestion["moves"][0]["location"]["type"] = suggestion["moves"][0]["location"]["type"].name
        
        print(json.dumps(suggestion))
        continue

    # # print current board, piece, holdpiece, and queue
    # print("!!!!")
    # print(agent.state.board)
    # print(agent.state.piece)
    # print(agent.state.heldPiece)
    # print(pieceQueue)
    # print(agent.state.pieceCount)
    # print("!!!!")