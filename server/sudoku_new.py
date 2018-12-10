# -*- coding: utf-8 -*-
import numpy as np
import random
import copy


#Responces for the set nr function.
WRONG_ANSWER = 0
RIGHT_ANSWER = 1
NUMBER_EXISTS = 2
#GLOBAL variable for the difficulty of the sudoku, the amount of numbers removed.
LEVEL = 2


#Function for checking if the input meets the requierments of a sudoku.
def check_sudoku(sud):
    row = np.zeros(10, dtype=np.int)
    col = np.zeros(10, dtype=np.int)
    box = np.zeros(10, dtype=np.int)
    for i in range(9):
        for j in range(9):
            row[sud[i,j]] += 1
            col[sud[j,i]] += 1
            x = j%3 + (i%3*3)
            y = j//3 + (i//3*3)
            #print([x,y])
            box[sud[x,y]] += 1
        if np.max(row[1:])>1 or np.max(col[1:])>1 or np.max(box[1:])>1:
            return False
        else:
            row = np.zeros(10, dtype=np.int)
            col = np.zeros(10, dtype=np.int)
            box = np.zeros(10, dtype=np.int)
    return True

#Solves the sudoku and returns a solved sudoku, if there are multible solutions (mul) , if the sudoku provided is solveable (sol).
def solve_sudoku(sud,mul = False,sol=False):
    tmp = sud.copy()
    for i in range(9):
        for j in range(9):
            if sud[i,j]==0:
                for k in range(9):
                    tmp[i,j]=k+1
                    if check_sudoku(tmp):
                        tmp,mul,sol = solve_sudoku(tmp,mul,sol)
                        #print(tmp)
                        if np.min(tmp)>0:
                            if mul:
                                return sud, False, True
                            return tmp, mul, True
                return sud, mul, sol
    if check_sudoku(tmp):
        return sud, mul, True

#An old sudoku maker that is not used.
def make_sudoku2():
    sud = np.zeros((9,9), dtype=np.int)
    mul = False
    while(not mul):
        while True:
            tmp = sud.copy()
            tmp[int(random.random()*9),int(random.random()*9)] = int(random.random()*9)
            if check_sudoku(tmp):
                break

        _, mul, sol = solve_sudoku(tmp,True)
        if (sol):
            sud=tmp.copy()
    return sud

#Sudoku maker that creates a new sudoku board, solves it and starts removing
#numbers until it satisfies the 'rem' variable, returns a sudoku and its solution.
def make_sudoku(rem = 2):
    sud = np.zeros((9,9), dtype=np.int)
    a = np.array(range(9))+1
    np.random.shuffle(a)
    removed = 0
    while(True):

        for i in range(2):
            np.random.shuffle(a)
            sud[i]=a
        if check_sudoku(sud):
            break
    sud,mul,sol = solve_sudoku(sud)
    solved = copy.deepcopy(sud)
    while(True):
        temp = sud
        a = random.randint(0,8)
        b = random.randint(0,8)
        if(sud[a,b] == 0):
            a = random.randint(0, 9)
            b = random.randint(0, 9)
        else:
            sud[a,b]=0
            _, mul, sol = solve_sudoku(sud)
            if(mul== True | sol == False):
                sud = temp
            else:
                removed +=1
        if(rem == removed): break


    return sud, solved

#Sudoku class that creates a sudoku and has the functions it needs.
class Sudoku():
    def __init__(self,level):
        self.current,self.solved=make_sudoku(level)

#Set_nr checks if the number given suits the solution, if it does,
# it replaces a zero with the right number, else it returns the corresponding.
    def set_nr(self,a,b,c):
        if self.current[b,a]!=self.solved[b,a]:
            self.current[b, a] = c;
            if self.solved[b,a] == c:
                return RIGHT_ANSWER
            else:
                return WRONG_ANSWER
        else:
            return NUMBER_EXISTS

#Checks if the curent table has any zeros left, if not, the game must be over.
    def is_game_over(self):
        ans=False
        if ((self.current == self.solved).all()):
            ans = True
        else:
            ans = False
        return ans

#Incorporates the design created in the 'Sudoku_design.txt'
# returns the designed current game table.
    def sudoku_to_string(self):
        design = """ x-1-2-3---4-5-6---7-8-9
y╔═══════╦═══════╦═══════╗
1║ * * * ║ * * * ║ * * * ║
2║ * * * ║ * * * ║ * * * ║
3║ * * * ║ * * * ║ * * * ║
|╠═══════╬═══════╬═══════╣
4║ * * * ║ * * * ║ * * * ║
5║ * * * ║ * * * ║ * * * ║
6║ * * * ║ * * * ║ * * * ║
|╠═══════╬═══════╬═══════╣
7║ * * * ║ * * * ║ * * * ║
8║ * * * ║ * * * ║ * * * ║
9║ * * * ║ * * * ║ * * * ║
 ╚═══════╩═══════╩═══════╝"""
        design = list(design)

        out_str = ''
        for i in self.current:
            for j in i:
                out_str += str(j)
        x = 0
        for i in range(len(design)):

            if design[i]=='*':
                design[i]= out_str[x]
                x +=1;

        design= ''.join(design)

        return design

    def sudoku_to_string_without_table(self):
        out_str = ''
        for i in self.current:
            for j in i:
                out_str +=(str(j))
        return out_str

#If main, then do this:
if __name__ == '__main__':

    sudokus = Sudoku(70)
    print sudokus.sudoku_to_string()
    while True:
        inp = raw_input("nr:" )
        inp = list(inp)
        print sudokus.set_nr(inp[0],inp[1],inp[2])
