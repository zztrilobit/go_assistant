﻿from Tkinter import *
from ttk import *
from sys import exit as sysexit
from os.path import splitext
import os

############### Сама доска - холст с нарисованной сеткой, обработчиком событий клик-а 
class go_board:
    def __init__(self, root, linedist, boardsize, engine):
        self.undo_stack=[]  # Стэк для отката ходов
        self.root_widg=root #корневой виджет
        self.stones_figs={} #списки камней (элементы канвы)
        self.handicap=""
        self.stones_figs["black"]=[]
        self.stones_figs["white"]=[]
        self.coords_by_names={} #координаты узлов для прорисовки овалов
        self.engine=engine     #объект дляобщения с енжином
        self.gobansize = linedist * (boardsize + 1) #размер доски
        self.linedist=linedist #шаг сетки
        self.boardsize=boardsize # логический размер поля
        self.goban = Canvas(self.root_widg,width=self.gobansize,height=self.gobansize,bg="#eebb77")
        self.useHintCallback = lambda  :  1==0
        self.showInfoCallback =  lambda i : 1
        
    def newGame(self) :
        self.stones_figs["black"]=[]
        self.stones_figs["white"]=[]
        self.undo_stack=[]  # Стэк для отката ходов
        self.drawBoard()
        
        if self.handicap<>"" :
            # нарисуем камни гандикапа
            self.drawListStones("black", self.engine.list_stones("black"))
            # и передадим ход белым
            self.move_pass()
        
    def top_move(self) : 
        if (len(self.undo_stack)>0) :
            return self.undo_stack[len(self.undo_stack)-1]
        else :
            r={}
            r["black"]="PASS"
            r["white"]="PASS"
            return r
    
    def Resize(self):
        self.gobansize = self.linedist * (self.boardsize + 1) #размер доски
        self.goban.config(width=self.gobansize,height=self.gobansize)
        
    def  xToLetter (self, x):
        return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'][x]
      
    def createFieldname (self, x, y):
        return ""+self.xToLetter(x)+str(y + 1)
    
    def redrawStones(self):
        self.drawListStones("black", self.engine.list_stones("black"))
        self.drawListStones("white", self.engine.list_stones("white"))
    
    def gobanClicker(self, s) : 
        self.engine.play("black",s)
        mv_info={}
        mv_info["black"]=s
        mv_info["white"]=self.top_move()["white"]
        self.undo_stack.append(mv_info)
        self.redrawStones()
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        self.showInfoCallback("White moved "+wh)
        if (self.useHintCallback()) : 
            hint=self.engine.genmove("black")
            self.engine.undo()
            mv_info["hint"]=hint
        self.redrawStones()
    
    def undo(self):
        oldm=self.undo_stack.pop()
        if (oldm["black"]<>"PASS") : self.engine.undo()
        if (oldm["white"]<>"PASS") : self.engine.undo()
        self.redrawStones()
        
    #сделать ход за игрока    
    def help(self):
        s=self.engine.genmove("black")
        mv_info={}
        mv_info["black"]=s
        mv_info["white"]=self.top_move()["white"]
        self.undo_stack.append(mv_info)
        self.redrawStones()
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        self.redrawStones()

    #черные спасовали
    def move_pass(self):
        mv_info={}
        mv_info["black"]="PASS"
        self.undo_stack.append(mv_info)
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        self.redrawStones()
        
    # функциональная обертка для клика по гобану
    def makeCliker(self, s) : return lambda _: self.gobanClicker(s)
        
    def drawListStones(self, color, list):
        for stone in self.stones_figs[color] : 
            self.goban.delete(stone)
        
        newList=[]
        for stone in list : 
            c=self.coords_by_names[stone]
            newList.append(self.goban.create_oval(c[0],c[1],c[2],c[3],fill=color))
        
        # точки на последних камнях
        if (color=="black"): 
            ocolor="white" 
        else: 
            ocolor="black"
        mw=self.top_move()
        # помечаем последний ход маркером 
        if ((mw[color]<>"PASS") ):
            c=self.coords_by_names[mw[color]]
            d=self.linedist/3
            newList.append(self.goban.create_oval(c[0]+d,c[1]+d,c[2]-d,c[3]-d,fill=ocolor, outline=ocolor))
        # рисуем подсказку
        if (color=="black" and mw.has_key("hint") ):
            if mw["hint"]<>"PASS":
                c=self.coords_by_names[mw["hint"]]
                newList.append(self.goban.create_oval(c[0],c[1],c[2],c[3], outline="red"))

        self.stones_figs[color]=newList
        
    def drawBoard (self) : 
        self.goban.delete("all")
        max=self.boardsize * self.linedist
        self.Resize()
        
        for i in range(self.boardsize): 
            start=self.linedist * (i+1)
            self.goban.create_line(self.linedist,start,max,start, width=1)
            self.goban.create_line(start,self.linedist,start,max,width=1, fill="black")
        for i in range(self.boardsize):
            for j in range(self.boardsize):
                x1 =  ((self.linedist * i) + (self.linedist / 2)) + 2
                y1 =  ((self.linedist * j) + (self.linedist / 2)) + 2
                x2 =  (x1 + self.linedist) - 4
                y2 =  (y1 + self.linedist) - 4
                fieldname= self.createFieldname (i,j)
                self.coords_by_names[fieldname] = [x1,y1,x2,y2]
                r=self.goban.create_rectangle (x1, y1, x2, y2, tags="fieldname" , outline="" , fill="")
                self.goban.tag_bind(r,'<Button-1>',self.makeCliker(fieldname))

# интерактив с энжином
class GoEngine:
    def __init__(self):
        self._gtpnr = 1 
    
    def StartEngin(self,cmd):
        self.to_gnugo, self.from_gnugo = os.popen2(cmd)
    
    def gtp(self, command):
        verbose = True
        cmd = str(self._gtpnr) + " " + command
        if verbose:
            print cmd
        self.to_gnugo.write(cmd + "\n")
        self.to_gnugo.flush()
        status = self.from_gnugo.read(1)
        value = status
        while not status == "\n":
            status = self.from_gnugo.read(1)
            value += status
        assert(self.from_gnugo.read(1) == "\n")
        if verbose:
            print value
        self._gtpnr += 1
        return value[1 + len(str(self._gtpnr)):]
        
    def time_by_move(self, seconds) :
        # всю партию машина играет в режиме байоми, по нужному числу секунд на ход
        return self.gtp("time_settings 1 "+str(seconds)+" 1")
        
    def handicap(self, stones) :
        # всю партию машина играет в режиме байоми, по нужному числу секунд на ход
        return self.gtp("fixed_handicap "+str(stones))
        
    def boardsize(self, size):
        return self.gtp('boardsize {0}'.format(size)).strip()
    
    def clear_board(self):
        return self.gtp('clear_board').strip()
    def estimate_score(self):
        return self.gtp('estimate_score').strip()
    
    def genmove(self, color):
        return self.gtp('genmove {0}'.format(color)).strip()
    
    def play(self, color, position):
        return self.gtp('play {0} {1}'.format(color, position)).strip()
    
    def list_stones(self, color):
        return self.gtp('list_stones {0}'.format(color)).strip().split()
    
    def showboard(self):
        return self.gtp('showboard')

    def final_score(self):
        return self.gtp('final_score')
    
    def undo(self):
        return self.gtp('undo')
        
class gameInterface :
    #кнопка на фрейм кнопок, вертикально
    def newBtn_1(self,caption, action):
        res=Button(self.buttonFrame,text=caption)
        res.bind( "<Button-1>", action )
        res.pack(side="top", padx=5, pady=5 )
        
    def __init__(self,root):
        self.engine=GoEngine()
        self.engine.StartEngin("gnugo.exe --mode gtp")
        self.linedist= 20
        self.boardsize= 19
        self.canvasFrame=Frame(root)
        self.canvasFrame.pack( side="left", fill="y")
        self.buttonFrame=Frame(root)
        self.buttonFrame.pack( side="left", fill="y")
        
        self.btnNewGame=self.newBtn_1("New Game", lambda _ : self.newGame() )
        self.gridSize=StringVar()
        self.cbGridSize=Combobox(self.buttonFrame, width=4, values=[9,13,19], textvariable=self.gridSize)
        self.cbGridSize.pack(side="top", padx=5, pady=5 )

        hlabel=Label(self.buttonFrame,text="  Handicap  ")
        hlabel.pack(side="top", padx=5, pady=5 )
        self.handicap=StringVar()
        self.handicap.set("")
        self.cbHandicap=Combobox(self.buttonFrame, width=4, values=["",2,3,4,5,6,7,8,9], textvariable=self.handicap)
        self.cbHandicap.pack(side="top", padx=5, pady=5 )
        self.btnUndo=self.newBtn_1("Pass", lambda _ : self.goban.move_pass() )
        self.btnUndo=self.newBtn_1("Undo", lambda _ : self.goban.undo() )
        self.btnHelp=self.newBtn_1("Help", lambda _ : self.goban.help() )
                
        self.goban=go_board(self.canvasFrame,self.linedist, self.boardsize, self.engine)
        self.goban.goban.pack(side="top", padx=5, pady=5 )
        self.lblInfo=Label(self.canvasFrame,text=" ")
        self.lblInfo.pack(side="top", padx=5, pady=5)
        
        #чек бокс подсказки хода
        self.makeHint=IntVar()
        self.cbHint=Checkbutton(self.buttonFrame,variable=self.makeHint,text="Make hint")
        self.cbHint.pack()
        self.goban.useHintCallback=lambda  : self.makeHint.get() == 1 
        self.goban.newGame()
        self.btnScore=self.newBtn_1("Calc score", lambda _ : self.score() )
        self.goban.showInfoCallback=lambda i : self.showInfo(i)
    
    def showInfo(self,i):
        self.lblInfo.config(text=i)
    
    def score(self):
        s = self.engine.final_score()
        self.showInfo("Score: "+s)
        
    def newGame(self):
        self.engine.time_by_move(15)
        
        if (self.gridSize.get()=="") : self.gridSize.set(13)
        self.boardsize=int(self.gridSize.get())
        
        self.engine.boardsize(self.boardsize)
        self.engine.clear_board()
        
        self.goban.boardsize=self.boardsize 
        self.goban.linedist=self.linedist        
        self.goban.drawBoard()
        h=self.handicap.get()
        if h<>"" :
            self.engine.handicap(h)
        self.goban.handicap=h
        self.goban.newGame()
            
        
root=Tk()
style=Style()
style.configure("TButton",  background="gray")
style.configure("TFrame",  background="gray")
style.configure("TCheckbutton",  background="gray")

root.config()
gi=gameInterface(root) 
gi.newGame()      
root.mainloop()

gi.engine.gtp("quit")