from Tkinter import *
from ttk import *
from sys import exit as sysexit
from os.path import splitext
import os
import pickle
import copy
import shelve
from subprocess import *
import time
import popen2

## модель игры - расчет содержимого доски после цепочки ходов
class boardModel:
    def __init__(self, boardsize):
        self.GTP_LETTERS=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
        self.board=[] # поле - двумерный массив, каждая ячейка - хэш, в к отором как минимум координаты поля - х,y и id группы куда входит поле
        self.white_groups={} # хэш - ид группы - массив узлов узел {x: y:}
        self.black_groups={}
        self.groups={"black":self.black_groups, "white" : self.white_groups}

        #захвачено камней
        self.captured={"black":0 , "white" : 0}
        self.boardsize=boardsize
        self.id_g_new=1
        self.verbose=False
    
    #пустой узел
    def emptyNode(self,x,y):
        res={}
        res["x"]=x
        res["y"]=y
        res["state"]="empty"
        res["id_grp"]=-1
        return res
        
    #пустая доска
    def init(self):
        self.board=[]
        for i in range(self.boardsize):
            row=[]
            for j in range(self.boardsize):
                row.append(self.emptyNode(j,i))
            self.board.append(row)
        self.white_groups={} # хэш - ид группы - массив узлов узел {x: y:}
        self.black_groups={}
        self.groups={"black":self.black_groups, "white" : self.white_groups}

    def clone(self):
        res=boardModel(self.boardsize)
        res.init()
        res.board=copy.deepcopy(self.board)
        res.white_groups=copy.deepcopy(self.white_groups)
        res.black_groups=copy.deepcopy(self.black_groups)
        res.groups["white"]=res.white_groups
        res.groups["black"]=res.black_groups
        res.id_g_new=self.id_g_new
        return res
    
    #соседние узлы
    def nearNodesXY(self,x,y): 
        res=[]
        for dx in [-1,1]:
            x1=x+dx
            if x1>=0 and x1<self.boardsize:
                res.append({"x" : x1, "y": y})
        for dy in [-1,1]:
            y1=y+dy
            if y1>=0 and y1<self.boardsize:
                res.append({"x":x, "y":y1})
        return res
        
    def nearNodesCrd(self,c): 
        return self.nearNodesXY(c["x"],c["y"])
    
    def doMove(self,color,posGtp):
        c=self.gtp2crd(posGtp)
        stone=self.nodeByCrd(c)
        stone["state"]=color
        # сделаем новую группу, внесем ее в список, занесем в нее новый камень
        self.id_g_new=self.id_g_new+1
        new_id=self.id_g_new
        new_group=[  {"x" : stone["x"], "y": stone["y"]}  ] #пока в новой группе 1 камень
        groupset=self.groups[color]
        
        groupset[new_id]=new_group
        
        # и проставим у нового камня ид-шник группы
        stone["id_grp"]=new_id
        
        #проверяемые соседние узлы
        for c in self.nearNodesCrd(c):
            node=self.nodeByCrd(c)
            old_g=node["id_grp"]
            if (node["state"]==color) and (old_g!=new_id):
                # цвет соседа совпал с моим. Вольем группу соседа в мою
                for nn in groupset[old_g]:
                    nnn=self.nodeByCrd(nn)
                    nnn["id_grp"]=new_id
                    new_group.append({"x":nnn["x"],"y":nnn["y"]})
                # и удаляем группу из списка
                del groupset[old_g]
                
            ocolor=self.ocolor(color)    
            if node["state"]==ocolor :
                # камень другого цвета. Проверим, жива ли содержащая его группа?
                iig=node["id_grp"]
                ogrset=self.groups[ocolor]
                if not self.groupAlive(ocolor,iig) :
                    for ocr in ogrset[iig] :
                        # на доске пометим поля как пустые
                        onode = self.nodeByCrd(ocr) 
                        onode["state"]="empty"
                        onode["id_grp"]=-1
                        self.captured[color]=self.captured[color]+1
                    #и удалим группу из списка
                    del ogrset[iig]
                
    def groupAlive(self,color,id):
        # цикл по узлам группы
        groupset=self.groups[color]
        for c in groupset[id]:
            # цикл по соседям узла
            for cc in self.nearNodesCrd(c) :
                node=self.nodeByCrd(cc)
                if node["state"]=="empty": 
                    return True
        return False
    
    def ocolor(self, color): 
        if color=="black" :
            return "white"
        else :
            return "black"
    #вернем узел с координатами     
    def nodeByCrd(self, c): return self.board[c["y"]][c["x"]]

    
    # возвращает новую доску. для простоты отката
    def move(self, color, posGTP):  
        res=self.clone()
        res.doMove(color, posGTP)
        return res
    
    # возвращает список камней нужного цвета в gtp-формате
    def list(self, color):
        res=[]
        for i in range(self.boardsize):
            for j in range(self.boardsize):
                if self.board[i][j]["state"]==color:
                    res.append(self.toGtp(j,i))
        return res

    #индекс массива->gtp
    def toGtp(self,x,y) : return self.GTP_LETTERS[x]+str(y+1)
    
    #координаты GTP -> {x: y:}
    def gtp2crd(self,posGtp):
        x=self.GTP_LETTERS.index(posGtp[0])
        y=int(posGtp[1:])-1
        return {"x":x , "y":y}
        
    def getNodeState(self,posGtp):
        return self.nodeByCrd(self.gtp2crd(posGtp))["state"]

    #узел пуст?
    def isNodeEmpty(self,posGtp):
        return self.nodeByCrd(self.gtp2crd(posGtp))["state"]=="empty"

    # может ли камень дышать
    def isNodeAlive(self,posGtp):
        n=self.nodeByCrd(self.gtp2crd(posGtp))
        return self.groupAlive(n["state"],n["id_grp"])

    # можно ли делать этот ход
    def movePossible(self,color,posGtp):
        n=self.nodeByCrd(self.gtp2crd(posGtp))
        if n["state"]<>"empty" : return False
        nb=self.clone()
        nb.doMove(color,posGtp)
        #сможет ли камень после хода дышать?
        return nb.isNodeAlive(posGtp)

    # может ли камень дышать
    def nearNodesGTP(self,posGtp):
        n=self.nodeByCrd(self.gtp2crd(posGtp))
        return [self.toGtp(n["x"],n["y"]) for n in self.nearNodesXY(n["x"],n["y"])]
        
############### Сама доска - холст с нарисованной сеткой, обработчиком событий клик-а 
class go_board:
    def __init__(self, root, linedist, boardsize, engine):
        # удивительно, но протокол GTP почему-то пропустил букво I????? но так почему-то работает ......
        self.GTP_LETTERS=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
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
        self.hintRithm="y"
        # стэк в котором будет накапливаться информация для sgf-файла
        self.for_sgf=[]
        
    
    # приведение координатных обозначений GTP->SGF
    def toSGF(self,s):
        letters=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
        i1=self.GTP_LETTERS.index(s[0])
        i2=self.boardsize-int(s[1:])
        return (""+letters[i1]+letters[i2]).lower()
        
    def newGame(self) :
        self.stones_figs["black"]=[]
        self.stones_figs["white"]=[]
        self.drawBoard()
        sgf=";AP[GO_ASSISTENT:0.0.1]"
        sgf=sgf+"FF[4]GM[1]" #формат 4 игра го
        sgf=sgf+"SZ["+str(self.boardsize)+"]KM[0.0]" #размер доски и коми
        
        self.undo_stack=[]  
        u={}
        handi_info={}
        party_info={}
        # в первый узел добавим информацию о партии. Чтобы при восстановлении все это накатить
        party_info["boardsize"]=self.boardsize
        party_info["komi"]=0
        
        #доска
        bm=boardModel(self.boardsize)
        bm.init()
        
        if self.handicap<>"" :
            # нарисуем камни гандикапа
            blacklist=self.engine.handicap(self.handicap)
            handi_info["count"]=self.handicap
            
            #blacklist=self.engine.list_stones("black")
            handi_info["list"]=blacklist

            sgf=sgf+"PL[W]RU[Japanese]"#играют белые, правила японские
            sgf=sgf+"HA["+str(self.handicap)+"]"+"AB"# дальше список позиций камней гандикапа[dd][jd][gg][dj][jj]"
            for i in blacklist :
                sgf=sgf+"["+self.toSGF(i)+"]"
                bm.doMove("black",i)
            # и передадим ход белым
        else:
            sgf=sgf+"PL[B]RU[Japanese]"
        
        #может еще чего приписываем в SGF
        #sgf=sgf+"DT[2015-04-06]GN[06.04.2015_18_43.sgf]"
        
            
        if self.handicap<>"":
            #делаем первый ход за белых
            u["black"]="PASS"
            u["white"]="PASS"
            wh=self.engine.genmove("white")
            bm.doMove("white",wh)
            handi_info["white"]=wh
            party_info["handicap"]=handi_info
            sgf=sgf+";W["+self.toSGF(wh)+"]"
        else:
            # Стэк для отката ходов закинем пустой ход для showHint
            u["black"]="PASS"
            u["white"]="PASS"
        
        #первый, неоткатываемый узел партии содержит информацию о ней, размере доски, гандикапе
        u["party_info"]=party_info
        u["model"]=bm
        #и там же в точности будем хранить фрагменты текста для SGF, будем сериализовать стек ходов в пикле или шелве
        u["sgf"]=sgf
        self.undo_stack.append(u)
        
        self.showHint()
        self.redrawStones()
        
        
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
        
    
    def redrawStones(self):
        #todo может мы в дальнейшем будем хранить списки камней на стеке отката и рисовать с него, пока - с доски
        bm=self.top_move()["model"]
        self.drawListStones("black", bm.list("black"))
        self.drawListStones("white", bm.list("white"))
        #self.drawListStones("black", self.engine.list_stones("black"))
        #self.drawListStones("white", self.engine.list_stones("white"))
    
    def showHint(self):
        if len(self.hintRithm)>0 :
            ch=self.hintRithm[0]
            #циклически вращаем строку
            self.hintRithm=self.hintRithm[1:len(self.hintRithm)]+ch
            doHint=ch=="y"
        else:
            doHint=self.useHintCallback()
        if doHint:
            hint=self.engine.genmove("black")
            if ( hint<>"PASS" ) and ( hint<> "RESIGN" ) :
                self.engine.undo()
                self.top_move()["hint"]=hint
            
    def gobanClicker(self, s) :
        bm=self.top_move()["model"]
        if not bm.movePossible("black",s) :
            messagebox.showinfo("Error move", "Error move")
            return
        was_hint= self.top_move().has_key("hint") #Ход сделан с подсказкой
        self.engine.play("black",s)
        bm=bm.clone()
        
        bm.doMove("black",s)
        
        mv_info={}
        mv_info["model"]=bm
        
        mv_info["black"]=s
        mv_info["white"]=self.top_move()["white"] #пока  нужно это хотя по сути, камни все равно с доски
        self.undo_stack.append(mv_info)
        self.redrawStones()
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        sgf=";B["+self.toSGF(s)+"]"
        if was_hint: 
            sgf=sgf+"C[with hint]"
        else:
            sgf=sgf+"C[without hint]"
        if (wh<>"PASS") and (wh<>"RESIGN") :
            sgf=sgf+";W["+self.toSGF(wh)+"]"
            bm.doMove("white",wh)
        else:
            sgf=sgf+";W[]"
        
        self.showInfoCallback("White moved "+wh)
        self.showHint() 
        self.redrawStones()
        mv_info["sgf"]=sgf
    
    def undo(self):
        oldm=self.undo_stack.pop()
        
        #todo тут бы еще реду стэк организовать и и для сгф тоже, дабы создавать ветки партий
        if (oldm["black"]<>"PASS") : self.engine.undo()
        if (oldm["white"]<>"PASS") and (oldm["white"]<>"RESIGN") : self.engine.undo()
        self.redrawStones()
        
    #сделать ход за игрока    
    def help(self):
        bm=self.top_move()["model"].clone()
        s=self.engine.genmove("black")
        bm.doMove[s]
        mv_info={}
        mv_info["model"]=bm
        mv_info["black"]=s
        mv_info["white"]=self.top_move()["white"]
        self.undo_stack.append(mv_info)
        self.redrawStones()
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        sgf=";B["+self.toSGF(s)+"]"
        sgf=sgf+"C[with help]"
        if (wh<>"PASS") and (wh<>"RESIGN") :
            sgf=sgf+";W["+self.toSGF(wh)+"]"
            bm.doMove("white",wh)
        else:
            sgf=sgf+";W[]"
        mv_info["sgf"]=sgf
        self.redrawStones()
        
        mv_info["sgf"]=sgf
    
    #черные спасовали
    def move_pass(self):
        bm=self.top_move()["model"].clone()
        mv_info={}
        mv_info["black"]="PASS"
        mv_info["model"]=bm
        self.undo_stack.append(mv_info)
        wh=self.engine.genmove("white")
        mv_info["white"]=wh
        if (wh<>"PASS") and (wh<>"RESIGN"):
            bm.doMove(wh)
            sgf=";B[];W["+self.toSGF(wh)+"]"
        else:
            sgf=";B[];W[]"
        mv_info["sgf"]=sgf
    
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
        #todo - тут бы сделать поиск последнего непасованного камня в глубину
        
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
        root.update()
        
    def  xToLetter (self, x):
        return self.GTP_LETTERS[x]
    
    def createFieldname (self, x, y):
        return ""+self.xToLetter(x)+str(self.boardsize-y)
    
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
        self.running=False
    
    def StartEngin(self,cmd):
        print "starting ", cmd
        # GnuGo через Popen работает. Leela - нет. даже с задержкой.
        p=Popen(cmd, bufsize=-1, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        self.to_gnugo=p.stdin
        self.from_gnugo=p.stdout
        self.process=p
        #time.sleep(10)
        #self.to_gnugo, self.from_gnugo = os.popen2(cmd)
        #self.from_gnugo, self.to_gnugo = popen2.popen2(cmd)
        self.running=True
    
    def gtp(self, command):
        if not self.running : 
            # raise BasicError("OOOOPS..... NO GTP ENGINE!!!!")
            print ("OOOOPS..... NO GTP ENGINE!!!!")
            return
        verbose = True
        cmd = str(self._gtpnr) + " " + command
        if verbose:
            print cmd
            sys.stdout.flush()
        self.to_gnugo.write(cmd + "\n")
        self.to_gnugo.flush()
        
        #ждем начало ответа - "=" - окей "?" - ошибка
        status = self.from_gnugo.read(1)
        while status<>"=" and status<>"?" :
            status = self.from_gnugo.read(1)
        self.is_ok=status=="="
        
        #ждем id команды
        value = self.from_gnugo.read(1)
        while value<>str(self._gtpnr):
            status = self.from_gnugo.read(1)
            value+=status
        
        value=""
        is_break=False
        status = self.from_gnugo.read(1)
        
        # ждем двух переводов строки
        while not (is_break and status=="\n" ):
            if status<>"\r":
                is_break=(status=="\n")
            if status<>"\n" and status<>"\r" :
                value += status
            else :
                value +=" "
            status = self.from_gnugo.read(1)
            
        #assert(self.from_gnugo.read(1) == "\n")
        if verbose:
            print value
        #retval=value[1 + len(str(self._gtpnr)):]
        retval=value
        #todo - тут надо бы вылавливать ошибки хотя бы так
        
        if not self.is_ok:
            print "gtp error!!! "+retval
        self._gtpnr += 1
        return retval
        
    def time_by_move(self, seconds) :
        # всю партию машина играет в режиме байоми, по нужному числу секунд на ход
        return self.gtp("time_settings 1 "+str(seconds)+" 1")
        
    def handicap(self, stones) :
        s=self.gtp("fixed_handicap "+str(stones))
        return s.upper().strip().split()
        
    def boardsize(self, size):
        return self.gtp('boardsize {0}'.format(size)).strip()
    
    def clear_board(self):
        return self.gtp('clear_board').strip()
        
    def estimate_score(self):
        return self.gtp('estimate_score').strip()
    
    def genmove(self, color):
        return self.gtp('genmove {0}'.format(color)).upper().strip()
    
    def play(self, color, position):
        return self.gtp('play {0} {1}'.format(color, position)).strip()
    
    def list_stones(self, color):
        return self.gtp('list_stones {0}'.format(color)).upper().strip().split()
    
    def showboard(self):
        return self.gtp('showboard')

    def final_score(self):
        return self.gtp('final_score')
    
    def quit(self):
        r=self.gtp('quit')
        self.running=False
        return r
        
    def undo(self):
        return self.gtp('undo')

# форма с настройками игры
class optDialog :
    def __init__(self,root):
        self.w=Toplevel(root)
        hlabel=Label(self.w,text="  Board size  ")
        hlabel.pack(side="top", padx=5, pady=5 )
        
        self.gridSize=StringVar()
        self.cbGridSize=Combobox(self.w, width=4, values=[9,13,19], textvariable=self.gridSize)    
        self.cbGridSize.pack(side="top", padx=5, pady=5 )
        
        hlabel=Label(self.w,text="  Handicap  ")
        hlabel.pack(side="top", padx=5, pady=5 )
        
        self.handicap=StringVar()
        self.cbHandicap=Combobox(self.w, width=4, values=["",2,3,4,5,6,7,8,9], textvariable=self.handicap)
        self.cbHandicap.pack(side="top", padx=5, pady=5 )
        
        hlabel=Label(self.w,text="  Hint rithm  ")        
        hlabel.pack(side="top", padx=5, pady=5 )
        
        self.hintRithm=StringVar()
        self.entHintRithm=Entry(self.w,textvariable=self.hintRithm)
        self.entHintRithm.pack(side="top", padx=5, pady=5)

        hlabel=Label(self.w,text="  Game engine  ")        
        hlabel.pack(side="top", padx=5, pady=5 )
        self.gameEnginePath=StringVar()
        self.entGameEngine=Entry(self.w,textvariable=self.gameEnginePath)
        self.entGameEngine.pack(side="top", padx=5, pady=5)
        
        self.okBtn=Button(self.w,text="OK")
        self.okBtn.bind("<Button-1>",lambda _ : self.doOk() )
        self.okBtn.pack(side="top", padx=5, pady=5 )
        self.is_ok=False
        
    def doOk(self):
        self.w.destroy()
        self.is_ok=True
        
    def ShowModal(self, params):
        self.w.grab_set()
        self.w.focus_set()
        
        self.gridSize.set(params["boardsize"])
        self.handicap.set(params["handicap"])
        self.hintRithm.set(params["hintrithm"])
        self.gameEnginePath.set(params["gameengine"])

        self.w.wait_window()
        if self.is_ok:
            params["boardsize"]=int(self.gridSize.get())
            params["handicap"]=self.handicap.get()
            params["hintrithm"]=self.hintRithm.get()
            params["gameengine"]=self.gameEnginePath.get()

class gameInterface :
    #кнопка на фрейм кнопок, вертикально
    def newBtn_1(self,caption, action):
        res=Button(self.buttonFrame,text=caption)
        res.bind( "<Button-1>", action )
        res.pack(side="top", padx=5, pady=5 )
    def newBtn_GF(self,caption, action):
        res=Button(self.gameFrame,text=caption)
        res.bind( "<Button-1>", action )
        res.pack(side="top", padx=5, pady=5 )
        
    def __init__(self,root):
        self.root=root
        self.linedist= 20
        self.boardsize= 19
        self.engine=GoEngine()
        
        self.canvasFrame=Frame(root)
        self.canvasFrame.pack( side="left", fill="y")
        self.buttonFrame=Frame(root)
        self.buttonFrame.pack(side="left",fill="y")
        
        self.btnNewGame=self.newBtn_1("Options", lambda _ : self.showoptions() )
        self.btnNewGame=self.newBtn_1("New Game", lambda _ : self.newGame() )
        
        self.handicap=""

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
        self.cbHint.pack(side="top", padx=5, pady=5)

        self.hintRithm='y'
        
        self.goban.useHintCallback=lambda  : self.makeHint.get() == 1 
        self.btnScore=self.newBtn_1("Calc score", lambda _ : self.score() )
        self.goban.showInfoCallback=lambda i : self.showInfo(i)
        
        self.btnStoreGame=self.newBtn_1("Store game", lambda _ : self.storeGame() )
        self.gameEnginePath="gnugo.exe --mode gtp"
        self.read_settings()
        self.engine=GoEngine()
        
    
    def showoptions(self):
        p={}
        p["boardsize"]=self.boardsize
        p["hintrithm"]=self.hintRithm
        p["handicap"]=self.handicap
        p["gameengine"]=self.gameEnginePath
        
        f=optDialog(self.root)
        f.ShowModal(p)
        self.boardsize=p["boardsize"]
        self.handicap=p["handicap"]
        self.hintRithm=p["hintrithm"]
        self.gameEnginePath=p["gameengine"] 
        self.store_settings()
        
    # читаем файл настроек
    def read_settings(self):
        db = shelve.open("my_settings")
        
        if db.has_key("boardsize") : 
            self.boardsize=int(db["boardsize"])
        else: 
            self.boardsize=13
        
        if db.has_key("handicap"): 
            self.handicap=db["handicap"]
        else:
            self.handicap=""
            
        if db.has_key("hintrithm") :  
            self.hintRithm=db["hintrithm"] 
        else: self.hintRithm = "y"
        
        if db.has_key("gameengine"):
            self.gameEnginePath=db["gameengine"]
        else:
            self.gameEnginePath="gnugo.exe --mode gtp"
            
        db.close()
    
    # пишем файл настроек
    def store_settings(self):
        db = shelve.open("my_settings")
        
        db["boardsize"]=self.boardsize
        db["handicap"]=self.handicap
        db["hintrithm"]=self.hintRithm
        db["gameengine"]=self.gameEnginePath
            
        db.close()
    
    #сохранение игры
    def storeGame(self):
        for_sgf=[ x["sgf"] for x in self.goban.undo_stack ]
        f = open('my_sgf.txt', 'w')
        s="("+"\n".join(for_sgf)+")"
        f.write(s)
        f.close()
        
        s2=pickle.dumps(self.goban.undo_stack)
        f = open('my_picle.txt', 'w')
        f.write(s2)
        f.close()
        
    def showInfo(self,i):
        self.lblInfo.config(text=i)
    
    def score(self):
        s = self.engine.final_score()
        self.showInfo("Score: "+s)
        
    def newGame(self):
        if self.engine.running :
            self.engine.quit()
        self.engine.StartEngin(self.gameEnginePath)
        
        #self.engine.StartEngin("leela080.exe --gtp")
        #self.engine.StartEngin("gnugo.exe --mode gtp")
        self.engine.time_by_move(7)
        
        self.engine.boardsize(self.boardsize)
        self.engine.clear_board()
        
        self.goban.boardsize=self.boardsize 
        self.goban.linedist=self.linedist
        self.goban.hintRithm=self.hintRithm
        self.goban.engine=self.engine
        
        self.goban.drawBoard()
        
        self.goban.handicap=self.handicap
        self.goban.newGame()
            
        
root=Tk()
style=Style()
style.configure("TNotebook",  background="gray")
style.configure("TNotebook.Tab",  background="gray", lightcolor="gray", foregroung="gray")
style.map("TNotebook.Tab",background=[('active','gray')])

style.configure("TFrame",  background="gray")
style.configure("TCheckbutton",  background="gray")

root.config()
gi=gameInterface(root) 
gi.newGame()
root.mainloop()

gi.engine.quit()