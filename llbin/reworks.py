
import logs
import string,types
import matches
import module_class as mdc

# Ninet  04-8441799

def run(db):
    db.Modules={}
    db.Components={}
    for Thing in db.Scanned:
        if Thing[0]=='entity':
            Name = Thing[1]
            if Name not in db.Modules:
                db.Modules[Name] = mdc.module_class(Name)
                Mod = db.Modules[Name]
                Params = Thing[2] 
                if (len(Params)>0)and(Params[0]=='port'):
                    for Item in Params[1]:
                        addParam(Item,Mod)

                Ports  = Thing[3]
                if (len(Ports)>0)and(Ports[0]=='port'):
                    for Item in Ports[1]:
                        addPort(Item,Mod)


        elif Thing[0]=='archi':
            Name = Thing[2]
            print(Name)
            if Name not in db.Modules:
                db.Modules[Name] = mdc.module_class(Name)
            Decls = Thing[3]
            Stuffs = Thing[4]
            workInArchStuffs(Decls,Stuffs,db,Mod)




        elif Thing[0]=='package':
            Name = Thing[1]
            db.Modules[Name] = mdc.module_class(Name,'package')
            Mod = db.Modules[Name]
            workInArchStuffs(Thing[2],[],db,Mod)

def workInArchStuffs(Decls,Stuffs,db,Mod):
    workArchDecls(Decls,db,Mod)
    print('TELL',len(Stuffs),type(Stuffs)is list)
    if type(Stuffs)is list:
        for Stuff in Stuffs:
            addStuff(db,Mod,Stuff)
    else:
        addStuff(db,Mod,Stuffs)


def workArchDecls(Decls,db,Mod):
    if type(Decls)is tuple: Decls = [Decls]
    for Item in Decls:
        good=False
        Vars = matches.matches_l(Item,'signal ?s [ ?s [ range [ ?sD ?s ?s ] ] ]')
        if Vars:
            good=True
            Mod.add_net(Vars[0],'logic',(vexpr(Vars[3]),vexpr(Vars[4])))

        Vars = matches.matches_l(Item,'signal ?s [ ?s [ ? ? ? ] ]')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'',Vars[1],(Vars[3],Vars[4]))
        Vars = matches.matches_l(Item,'signal ?s ?s')
        if Vars:
            good=True
            Type = Vars[1]
            if Type in Mod.typedefs:
                addNet(Mod,Vars[0],'logic',Mod.typedefs[Type],0)
            else:
                addNet(Mod,Vars[0],'',Vars[1],Vars[1])
        Vars = matches.matches_l(Item,'signal ?l ?s')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'',Vars[1],Vars[1])

        Vars = matches.matches_l(Item,'signal ?s [ std_logic_vector [ DOWNTO ?s ?s ] ] [ ] ?s')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'','wire',Vars[1])
        Vars = matches.matches_l(Item,'signal ?s ?s  [ ] ?s')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'','wire',0)

        Vars = matches.matches_l(Item,'signal ?l [ ?s [ ? ? ? ] ]')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'',Vars[1],(Vars[3],Vars[4]))
        Vars = matches.matches_l(Item,'alias ?s ? ?')
        if Vars:
            good=True
        Vars = matches.matches_l(Item,'typedef ?s [ ?s [ range [ ?sD ?s ?s ] ] ]')
        if Vars:
            if Vars[1] in ['natural','integer']:
                Var = Vars[0]
                if Vars[2]=='TO':
                    Big = Vars[4]
                else:
                    Big = Vars[3]
                if Big[0] in '0123456789':
                    Big = eval(Big)
                    Bits = len(bin(Big))-2
                    Mod.typedefs[Vars[0]] = ('logic',(Big-1,0))
                    good=True




        Vars = matches.matches_l(Item,'typedef ?s [ enumlist  ? ]')
        if Vars:
            good=True
            Len = len(Vars[1])
            Wid = len(bin(Len))-2
            addNet(Mod,[Vars[0]],'','wire',(Wid-1,0))
            for ind,Par in enumerate(Vars[1]):
                Mod.localparams[Par]=ind
            return
                
        Vars = matches.matches_l(Item,'typedef ?s [ record ? ]')
        if Vars:
            good=True
            missing('typedef record')
        Vars = matches.matches_l(Item,'typedef ?s [ ?s [ ?sD ?  ?sI ] ]')
        if Vars:
            if Vars[1] in ['std_logic_vector','unsigned','signed']:
                good=True
                Hi = vexpr(Vars[3])
                Lo = vexpr(Vars[4])
                if Vars[1]=='signed':
                    Mod.typedefs[Vars[0]] = ('signed',(Hi,Lo))
                else:
                    Mod.typedefs[Vars[0]] = ('logic',(Hi,Lo))

        Vars = matches.matches_l(Item,'typedef ?s [ array  [ discrete [ ? ? ] ] ? ]')
        if Vars:
             good=True
             AA = vexpr(Vars[1])
             BB = vexpr(Vars[2])
             CC = vexpr(Vars[3])
             AA = exploreKind(Mod,AA)
             BB = exploreKind(Mod,BB)
             CC = exploreKind(Mod,CC)
             Mod.typedefs[Vars[0]] = ('triple',AA,BB,CC)

        Vars = matches.matches_l(Item,'typedef ?s [ array  [ box_range  ? ] ? ?s ]')
        if Vars:
             Mod.typedefs[Vars[0]] = ('array',Vars[3])
             good=True
        Vars = matches.matches_l(Item,'typedef ?s [ array  [ ?s ? ] ?s ]')
        if Vars:
            if Vars[1] in ['discrete']:
                Vars2 = matches.matches_l(Vars[2],'?sD ?sI ?sI')
                if Vars2:
                    Sub=Vars[3]
                    if Sub in Mod.typedefs:
                        Sub = Mod.typedefs[Sub]
                        if Sub[0]=='logic': Sub=Sub[1]
                        Mod.typedefs[Vars[0]] = ('double',(Vars2[1],Vars2[2]),Sub)
                    else:
                        Mod.typedefs[Vars[0]] = ('double',(Vars2[1],Vars2[2]),Vars[3])

                    good=True
        Vars = matches.matches_l(Item,'component ?s ? ?')
        if Vars:
            Comp = Vars[0]
            Gen = Vars[1]
            Ports = Vars[2]
            db.Components[Comp]=(Gen,Ports)
            good=True
        Vars = matches.matches_l(Item,'constant ?s ?s ?')
        if Vars:
            if Vars[1] in ['integer','positive']:
                Val = vexpr(Vars[2])
                good=True
                Mod.localparams[Vars[0]]=Val

        Vars = matches.matches_l(Item,'taskhead ?s ?')
        if Vars:
            good=True
            Mod.funcheads[Vars[0]] = (Vars[1],'taskhead')
        Vars = matches.matches_l(Item,'funchead ?s ?  ?s')
        if Vars:
            good=True
            Mod.funcheads[Vars[0]] = (Vars[1],Vars[2])
        Vars = matches.matches_l(Item,'constant ?s ?s ?s')
        if Vars and not True:
            good=True
            Mod.localparams[Vars[0]]=('funccall',Vars[1],[vexpr(Vars[2])])

        Vars = matches.matches_l(Item,'constant ?s std_logic ?')
        if Vars:
            addNet(Mod,[Vars[0]],'','wire',0)
            Val = vexpr(Vars[1])
            Mod.add_hard_assign(Vars[0],Val)
            good=True
        Vars = matches.matches_l(Item,'constant ?s [ std_logic_vector [ ?sD ?sI ?sI ] ] ?')
        if Vars:
            addNet(Mod,[Vars[0]],'','wire',(Vars[2],Vars[3]))
            Val = vexpr(Vars[2])
            Mod.add_hard_assign(Vars[0],Val)
            good=True
        Vars = matches.matches_l(Item,'constant ?s natural ?')
        if Vars:
            good=True
            Mod.localparams[Vars[0]]=vexpr(Vars[1])
                
        Vars = matches.matches_l(Item,'constant ?s [ signed [ ?sD ? ? ] ] [ aggregate to_signed [ ? ?s ] ]')
        if Vars:
            good=True
            Hi = vexpr(Vars[2])
            Lo = vexpr(Vars[3])
            Val = vexpr(Vars[4])
            addNet(Mod,[Vars[0]],'','wire signed',(Hi,Lo))
            Mod.add_hard_assign(Vars[0],Val)

        Vars = matches.matches_l(Item,'constant ?s string ?s ')
        if Vars:
            good=True
        Vars = matches.matches_l(Item,'constant ?s boolean ?s ')
        if Vars:
            good=True
            addNet(Mod,Vars[0],'','wire',0)
            if Vars[1]=='true': Vars[1]=1
            if Vars[1]=='false': Vars[1]=0
            Mod.add_hard_assign(Vars[0],Vars[1])
                
        if not good: 
            logs.log_error('item in declarations failed "%s"'%str(Item))


def addParam(Item,Mod):
    printl('addParam %s'%str(Item))

DIRS = {'BUFFER':'output','IN':'input','OUT':'output','INOUT':'inout','std_logic':'logic','std_logic_vector':'logic','wire':'wire','signed':'signed','unsigned':'unsigned','logic':'logic','wire signed':'wire signed'}
def addPort(Item,Mod):
    Vars = matches.matches_l(Item,'signal ? ?s ?s [ ?s ?s ?s ]')
    if Vars:
        Sigs = Vars[0]
        Dir  = Vars[1]
        Kind = Vars[2]
        Hi = Vars[4]
        Lo = Vars[5]
        Wid = (Hi,Lo)
        addNet(Mod,Sigs,Dir,Kind,Wid)
        return
    Vars = matches.matches_l(Item,'signal ? ?s ?s [ ?s ? ?s ]')
    if Vars:
        Sigs = Vars[0]
        Dir  = Vars[1]
        Kind = Vars[2]
        Hi = Vars[4]
        Lo = Vars[5]
        Wid = (Hi,Lo)
        addNet(Mod,Sigs,Dir,Kind,Wid)
        return


    Vars = matches.matches_l(Item,'signal ? ?s ?s ')
    if Vars:
        Sigs = Vars[0]
        Dir  = Vars[1]
        Kind = Vars[2]
        Wid = 0
        addNet(Mod,Sigs,Dir,Kind,Wid)
        return
    logs.log_error('addPort failed "%s"'%(str(Item)))

def addNet(Mod,Sigs,Dir,Kind,Wid):
    if type(Sigs) is str:
        Sigs = [Sigs]
    if (type(Kind) is tuple)and(Kind[0]=='triple'):
        for Sig in Sigs:
            Mod.add_net(Sig,Dir,('triple',Kind[1],Kind[1],Kind[2]))


        return
    if (type(Kind) is tuple)and(Dir=='logic'):
        if Kind[0]=='logic':
            for Sig in Sigs:
                Mod.add_net(Sig,Dir,(vexpr(Kind[1][0]),vexpr(Kind[1][1])))
            return
            
    if Kind in Mod.typedefs:
        Kind = exploreKind(Mod,Kind)
        if Kind[0]=='array':
            if (type(Wid) is tuple)and(len(Wid)==2):
                Kind = Kind[1]
                if Kind[0]=='logic':
                    Wid0 = Kind[1]
                    for Sig in Sigs:
                        Mod.add_net(Sig,'logic',('double',Wid0,Wid))
                return 

    if (type(Kind) is tuple)and(Wid==0):
        Vars = matches.matches_l(Kind,'double [ ? ? ] [  ? ? ]')
        if Vars:
            Hi0 = vexpr(Vars[0])
            Lo0 = vexpr(Vars[1])
            Hi1 = vexpr(Vars[2])
            Lo1 = vexpr(Vars[3])
            for Sig in Sigs:
                Mod.add_net(Sig,Dir,('double',(Hi0,Lo0),(Hi1,Lo1)))
            return


    if Wid == 'std_logic':
        for Sig in Sigs: Mod.add_net(Sig,'logic',0)
        return
    if Kind==Wid:
        if Dir=='':
            Dir = Kind
        else:
            Dir = '%s %s'%(Dir,Kind)
        for Sig in Sigs:
            Mod.add_net(Sig,Dir,Kind)
        return

    if (Dir in ['IN','OUT'])and (type(Kind) is str) and(Kind not in DIRS):
        Dir = '%s %s'%(DIRS[Dir],Kind)
        Mod.extTypes.append(Kind)
        for Sig in Sigs: Mod.add_net(Sig,Dir,Wid)
        return
        


    if Dir=='':
        pass
    elif Dir in DIRS:
        Dir = DIRS[Dir]
    else:
        logs.log_error('Dir of signal %s is "%s"   %s'%(Sigs,Dir,Mod.typedefs.keys()))
    if (type(Kind) is str) and(Kind in DIRS):
        Kind = DIRS[Kind]
    else:
        logs.log_error('Kind of signal %s is "%s"  %s'%(Sigs,Kind,Mod.typedefs.keys()))
        
        
    DK = '%s %s'%(Dir,Kind)
    if Dir=='': DK=Kind
    if Wid=='std_logic': Wid=0
    for Sig in Sigs:
        Mod.add_net(Sig,DK,Wid)

def exploreKind(Mod,Kind):
    Kind = Mod.typedefs[Kind]
    if Kind[0]=='logic':
        return Kind[1]
    if Kind[0]=='array':
        Who = Kind[1]
        if Who in Mod.typedefs:
            Who = Mod.typedefs[Who]
            return ('array',Who)
    logs.log_error('exploreKind got %s'%str(Kind))
    return Kind

def addStuff(db,Mod,Stuff):
    if Stuff==[]: return
    if Stuff[0]=='process':
        addProcess(Mod,Stuff[1:])
    elif Stuff[0]=='labeled_process':
        addProcess(Mod,Stuff[2][1:])
    elif Stuff[0]=='<=':
        Dst = vexpr(Stuff[1])
        Src = vexpr(Stuff[3])
        Mod.add_hard_assign(Dst,Src)
    elif Stuff[0]=='instance':
        Mod.add_inst(Stuff[2],Stuff[1])
        if Stuff[3]!=[]: 
            addInstanceParam(Mod,Stuff[1],Stuff[3])
        if Stuff[4]!=[]: 
            addInstanceConns(db,Mod,Stuff[1],Stuff[4])
    elif Stuff[0]=='labeled_gen':
        M1 = ['named_begin',Stuff[1],Stuff[2]]
        Mod.generates.append(M1)
    else:
        logs.log_error('addStuff got  %s'%(str(Stuff[0])))

def addInstanceParam(Mod,Inst,List):
    if List[0]=='generic_map':
        addInstanceParam(Mod,Inst,List[1])
        return
    if List[0]=='arrow_or':
        Mod.add_inst_param(Inst,List[1],List[2])
        return

    for A,Prm,Val in List:
        if A=='arrow_or':
            Mod.add_inst_param(Inst,Prm,Val)
        else:
            logs.log_error('addInstanceParam of %s got %s %s %s'%str(Inst,A,Prm,Val))


def addInstanceConns(db,Mod,Inst,List):
    Type = Mod.insts[Inst].Type
    if Type in db.Components:
        Pins = db.Components[Type][1]
    else:
        Pins = False
    if List[0]=='conns':
        for ind,Con in enumerate(List[1]):
            if type(Con) is str:
                if Pins:
                    Pin = getIndPin(Type,Pins,ind)
                    Mod.add_conn(Inst,Pin,Con)
                else:
                    Mod.add_conn(Inst,ind,Con)
            elif Con[0]=='arrow_or':
                Mod.add_conn(Inst,Con[1],vexpr(Con[2]))
            else:
                logs.log_error('add conns to instance %s got %s'%(Inst,Con))
        return
    logs.log_error('add conns to instance %s %s'%(Inst,List))

pinsCaches={}
def getIndPin(Type,Pins,ind):
    if Type in pinsCaches:
        return pinsCaches[Type][ind]
    if Pins[0]=='ports':
        Res = []
        for Item in Pins[1]:
            if Item[0]=='signal':
                Res.append(Item[2])
            else:
                logs.log_error('item in pins of %s is not signal "%s"'%(Type,Item))
        pinsCaches[Type]=Res 
        return getIndPin(Type,Pins,ind)
    logs.log_error('getIndPin in pins of %s is not good "%s"'%(Type,Pins[0]))

def addProcess(Mod,Process):
    Sense = list(map(vexpr,Process[0]))
    Vars = Process[1]
    Stmt = Process[2]
    Vars2 = reworkStmt(Vars)
    if type(Vars2) is tuple: Vars2 = ['list',Vars2]
    Stmts = reworkStmt(Stmt)
    if Stmts[0]=='list': Stmts = Stmts[1:]
    Stmt2 = list(Vars2)+list(Stmts)
    Mod.alwayses.append((Sense,Stmt2,'always'))
#    logs.log_error('addProcess got  %s'%(str(Process)))
    

def reworkStmt(Stmt):
    if Stmt==[]: return []
    if type(Stmt) is list:
        Res = list(map(reworkStmt,Stmt))
        return ['list']+Res
    if Stmt[0]=='case':
        Cond = vexpr(Stmt[1])
        Cases = reworkCases(Stmt[2])
        return ('case',Cond,Cases)
    if Stmt[0]=='<=':
        A = vexpr(Stmt[1])
        B = vexpr(Stmt[2])
        return ('<=',A,B)
    if Stmt[0]=='assign':
        A = vexpr(Stmt[1])
        B = vexpr(Stmt[2])
        return ('<=',A,B)
        
    if Stmt[0]=='ifelse':
        Cond = vexpr(Stmt[1])
        Yes = reworkStmt(Stmt[2])
        if len(Stmt)==3:
            return ('if',Cond,Yes)
            
        if Stmt[3]==[]:
            No = reworkStmt(Stmt[4])
        else:
            No = reworkStmt(Stmt[3])
        return ('ifelse',Cond,Yes,No)
    if Stmt[0]=='elsif':
        Cond = vexpr(Stmt[1])
        Yes = reworkStmt(Stmt[2])
        return ('if',Cond,Yes)
    if Stmt[0]=='loop':
        Body = reworkStmt(Stmt[2])
        Vars = matches.matches_l(Stmt[1],'in ?s [ TO ?s ?s ]')
        if Vars:
            return ('for',('=',Vars[0],Vars[1]),('<',Vars[0],Vars[2]),('=',Vars[0],('+',Vars[0],1)),Body)
        Vars = matches.matches_l(Stmt[1],'in ?s ?s')
        if Vars:
            return ('for',('=',Vars[0],Vars[1]),('<',Vars[0],Vars[1]),('=',Vars[0],('+',Vars[0],1)),Body)
            
    if Stmt[0]=='aggregate':
        if (len(Stmt)==3)and(type(Stmt[2]) is list):
            return ('taskcall',Stmt[1],list(map(vexpr,Stmt[2])))
        
    if Stmt[0]=='variable':
        Vars = matches.matches_l(Stmt,'variable ?s [ natural [ range [ ?sD ?s ?s ] ] ]  ?')
        if Vars:
            return ('integer',0,Vars[0])
        Vars = matches.matches_l(Stmt,'variable ?s natural ?')
        if Vars:
            return ('integer',0,Vars[0])
        Vars = matches.matches_l(Stmt,'variable ?s std_logic  ?')
        if Vars:
            return ('logic',0,Vars[0])
        Vars = matches.matches_l(Stmt,'variable ?s [ std_logic_vector [ ?sD ?s ?s ] ]  ?')
        if Vars:
            return ('logic',('width',Vars[2],Vars[3]),Vars[0])
            
        logs.log_error('(reworks) variable %s'%str(Stmt))
        return []

    logs.log_error('reworkStmt %d "%s"'%(len(Stmt),Stmt))
    return Stmt

def reworkCases(List):
    Res = []
    for Item in List:
        good=False
        Vars = matches.matches(Item,'when ? ?')
        if Vars:
            Cond = vexpr(Vars[0])
            Stmt = reworkStmt(Vars[1])
            Res.append((Cond,Stmt))
            good=True
        Vars = matches.matches(Item,'when OTHERS')
        if Vars:
            good=True 
            Res.append(('default',[]))

        if not good:
            logs.log_error('reworkCases got "%s"'%str(Item))
            Res.append(Item)
    return Res
    



BIOPS = ('+ - * / & | ~ ^ ').split()
VHDLOPS = {'AND':'&','OR':'|','EQSym':'==','not':'~','Star':'*','Slash':'/','GTSym':'>','LTSym':'<','**':'**','GESym':'>=','/=':'!=','=>':'=>','<=':'<='}

def vexpr(Item):
    A = vexpr__(Item)
    guardExpr(A)
    return A


def guardExpr(Expr):
     Str = str(Expr)
     if 'aggregate' in Str:
        logs.log_error('guardExpr found %s'%Str)




def vexpr__(Item):
    if (type(Item) is str)and(Item!=''):
        if Item[0]=='"':
            Bin = ('bin',len(Item)-2,"%s"%(Item[1:-1]))
            return Bin
        if Item[0]=="'":
            return Item[1]
        if (Item[-1]=='"')and(Item[1]=='"'):
            if Item[0] in 'Bb':
                return ('bin',len(Item)-3,Item[2:-1])
            if Item[0] in 'Xx':
                return ('hex',len(Item)-3,Item[2:-1])
                


    if isinstance(Item,(str,int)): return Item
    
    if len(Item)==0: return ''
    if isinstance(Item[0],str)and(Item[0] in VHDLOPS):
        if len(Item)==3:
            Nitem = (VHDLOPS[Item[0]],Item[1],Item[2])
            return vexpr(Nitem)
        if len(Item)==2:
            Nitem = (VHDLOPS[Item[0]],Item[1])
            return vexpr(Nitem)


    if (type(Item[0]) is str)and(Item[0] in BIOPS):
        A = vexpr(Item[1])
        if len(Item)==3:
            B = vexpr(Item[2])
            return (Item[0],A,B)
        if len(Item)==2:
            return (Item[0],A)

    if Item[0]=='relop':
        A = Item[1][0]
        B = Item[1][1][1]
        Op = VHDLOPS[Item[1][1][0]]
        AA = vexpr(A)
        BB = vexpr(B)
        return (Op,AA,BB)

    if Item[0]=='Ampersand':
        A = vexpr(Item[1])
        B = vexpr(Item[2])
        return ('curly',A,B)

    if Item[0]=='apostrophe':
        Vars = matches.matches_l(Item,'apostrophe ?s ?s')
        if Vars:
            if Vars[1]=='event':
                return ('funccall','anyedge',[Vars[0]])
            return ('funccall',Vars[1],[Vars[0]])
    if Item[0]=='aggregate':
        Vars = matches.matches_l(Item,'aggregate ?s [ ?sD ?sI ?sI ]')
        if Vars:
            Hi = Vars[2]
            Lo = Vars[3]
            return ('subbus',Vars[0],Hi,Lo)
        Vars = matches.matches_l(Item,'aggregate [ aggregate ?s ? ] ?s')
        if Vars:
            A = vexpr(Vars[1])
            Res = [('subbit',Vars[0],('subbit',Vars[2],A))]
            return Res
        Vars = matches.matches_l(Item,'aggregate ?s ?')
        if Vars:
            if Vars[0]=='conv_integer': return vexpr(Vars[1])
            if Vars[0]=='std_logic_vector': return vexpr(Vars[1])
            if Vars[0]=='signed': return [('funccall','signed',[vexpr(Vars[1])])]
            if type(Vars[1]) is list:
                AA = list(map(vexpr,Vars[1]))
                return [('funccall',Vars[0],AA)]
                
            Ind = vexpr(Vars[1])
            if type(Ind) is list:
                return ('subbus',Vars[0],Ind)
            else:
                return ('subbit',Vars[0],Ind)
    if Item[0]=='multing':
        return vexpr((Item[2],Item[1],Item[3]))
    Vars = matches.matches_l(Item,'dstar ? [ ** ? ]')
    if Vars:
       A = vexpr(Vars[0]) 
       B = vexpr(Vars[1])
       return ('**',A,B)
        

    Vars = matches.matches_l(Item,'choice_arrow OTHERS ? ?')
    if Vars:
        return vexpr(Vars[1])

    Vars = matches.matches_l(Item,'?sD ? ?')
    if Vars: 
        A = vexpr(Vars[1])
        B = vexpr(Vars[2])
        return [A,B]
        

    Vars = matches.matches_l(Item,'choice_arrow [ apostrophe ?s ?s ] ? ? ')
    if Vars:
        if Vars[1]=='RANGE':
            Res = ('curly',('funccall','$width',[Vars[0]]),('curly',Vars[3]))
            return Res
            
        
    if type(Item) is list:
        if len(Item)==[]: return []
        if (Item[0][0]=='choice_arrow'):
            return choiceArrows(Item)

    logs.log_error('vexpr got  %s'%(str(Item)))
    return Item

def choiceArrows(List):
    Res = ['list']
    for Item in List:
        good=False
        Vars = matches.matches(Item,'choice_arrow OTHERS ? ?s')
        if Vars:
            good=True
            Res.append(('deposit','default',vexpr(Vars[1])))
        Vars = matches.matches(Item,'choice_arrow ?s ? ?s')
        if not good and Vars:
            good=True
            Res.append(('deposit',vexpr(Vars[0]),vexpr(Vars[2])))
            
    return Res
def missing(Txt):
    logs.log_error('please implement "%s"'%Txt)
def isToken(Who):
    return type(Who) is str
def printl(Txt):
    print('TELL %s'%Txt)
