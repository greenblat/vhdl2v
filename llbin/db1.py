

import os,sys,string,pickle,types

import logs
import traceback
import module_class as mcl
import matches
import pprint

def main():
    load_parsed('.')
    Fout = open('modules.v','w')
    for Mod in db.Modules:
        Mod.dump_verilog(Fout)
    Fout.close()

def load_parsed(Rundir):
    db.Global = mcl.module_class('global_module')
    db.Modules = {}
    if True:
        load_db1('%s/db0.pickle'%Rundir)
        Key = ('main', 1)
        dumpDataBase(db.db)
        scan1(Key)
        dumpScanned(db,'bef_')
        for ind,LL in enumerate(db.Scanned):
            L2 = simplify(LL)
            db.Scanned[ind]=L2
        dumpScanned(db,'aft_')
    logs.log_info('total matches run %s'%matches.totalcount)
    return db


class dataBaseClass:
    def __init__(self):
        self.db = False
        self.Entities = {} 
        self.Architectures = {} 
        self.Packages = {} 
        self.Global = False
        self.Scanned = []

db = dataBaseClass()

def load_db1(Fname):
    File = open(Fname,'rb')
    db.db = pickle.load(File)
    File.close()

def scan1(Key):
    if Key not in db.db: 
        logs.log_error('scan1 failed on "%s" "%s"'%(Key,'not in db'))
        return
    List = db.db[Key]
    if List==[]: return

    if Key[0] == 'library_clause':
        return
    if (len(List)==1)and(List[0] in db.db):
        scan1(List[0])
        return

    Vars = matches.matches(List,'!clauses !clause')
    if Vars:
        scan1(Vars[0])
        scan1(Vars[1])
        return


    Vars = matches.matches(List,'ENTITY ? IS !port_clause END Semicolon')
    if Vars:
        Cell = Vars[0][0]
        LL = get_list(Vars[1])
        for Port  in LL:
            if (len(Port)==4)and(Port[0] == 'port'):
                addPin(Cell,Port[1],Port[2][0],Port[3])
            elif (len(Port)==6)and(Port[0] == 'port')and(Port[3] == 'std_logic_vector'):
                addBusPin(Cell,Port)
                
            else:
                logs.log_error('ENTITY PORT %d %s' % (len(Port),Port))

        return

    Vars = matches.matches(List,'ENTITY ? IS !generic_clause !port_clause END Semicolon')
    if Vars:
        Cell = Vars[0][0]
        Gens = get_list(Vars[1])
        Ports  = get_list(Vars[2])
        for Port in Ports:
            if (len(Port)==6)and(Port[0] == 'port')and(Port[3] == 'std_logic_vector'):
                addBusPin(Cell,Port)
            else:
                addPin(Cell,Port[1],Port[2][0],Port[3])
        for Gene in Gens:
            if len(Gene)==3: 
                addParam(Cell,Gene[1],Gene[2],1)
            else:
                addParam(Cell,Gene[1],Gene[2],Gene[3])
        return

    Vars = matches.matches(List,'ARCHITECTURE ? OF ? IS BEGIN_ !statements END Semicolon')
    if Vars:
        Name = Vars[1][0]
        Body = get_list(db.db[Vars[2]])
        db.Scanned.append(('architecture',Name,[],Body))
        addArchitecture(Name,[],Body)
        return


    Vars = matches.matches(List,'ARCHITECTURE ? OF ? IS !components BEGIN_ !statements END Semicolon')
    if Vars:
        Name = Vars[1][0]
        Decls = get_list(db.db[Vars[2]])
        Body = get_list(db.db[Vars[3]])
        db.Scanned.append(('architecture',Name,Decls,Body))
        addArchitecture(Name,Decls,Body)
        return


    Vars = matches.matches(List,'PACKAGE BODY ?t IS !package_body_declarative_part END ? ?')
    if Vars:
        Name= Vars[0]
        List = get_list(db.db[Vars[1]])
        db.Scanned.append(('package_body',Name,List))
        return

    Vars = matches.matches(List,'PACKAGE ?t IS !package_declarative_part END ? ?')
    if Vars:
        Name = Vars[0]
        List = get_list(db.db[Vars[1]])
        db.Scanned.append(('package',Name,List))
        return



    logs.log_error('scan1 failed on "%s" "%s"'%(Key,List))


def travelList(Target,Key):
    L1 = db.db[Key]
    Vars = matches.matches(L1,'? Semicolon !%s' % Target)
    if Vars:
        Item = Vars[0]
        More = travelList(Target,Vars[1])
        return [Item] + More
    if len(L1) == 1:
        return L1
    logs.log_error('ILIA ERROR travelList %s %s' % (Target, Key))
    return []


def inDb(Item):
    return (type(Item) is tuple)and(len(Item)==2)and(Item in db.db)

def dumpScanned(db,Pref=''):
    File = open('%sscanned.dump'%Pref,'w')
    for Item in db.Scanned:
        Kind = Item[0]
        if Kind=='architecture':
            Name = Item[1]
            Str = '%s lens = prm=%d stuff=%d'%(Name,len(Item[2]),len(Item[3]))
            File.write('\n\n%s\n'%Str)
            if type(Item[2]) is list:
                for X in Item[2]:
                    File.write('item2 : %s\n'%(str(X)))
            else:
                File.write('xitem2 : %s\n'%(str(Item[2])))

            if type(Item[3]) is list:
                for X in Item[3]:
                    XX = nicePrint(X)
                    File.write('item3 : %s\n'%(XX))
            else:
                File.write('xitem3 : %s\n'%(nicePrint(Item[3])))

        elif Kind=='entity':
            Lens = map(len,Item)
            Str = '%s %s lens = %s'%(Kind,Name,Lens)
            File.write('\n\n%s\n'%Str)
            for ind,Li in enumerate(Item):
                if ind>=2:
                    for X in Li:
                        File.write('item%d : %s\n'%(ind,str(X)))
            
        elif Kind in ['package','package_body']:
            Str = '%s %s lens = stuff=%d'%(Kind,Name,len(Item[2]))
            File.write('\n\n%s\n'%Str)
            for X in Item[2]:
                File.write('item2 : %s\n'%(str(X)))
        elif Kind in ['use']:
            File.write('%s %s\n'%(Item[0],Item[1]))
        else:
            File.write('ERROR ?? %s %s\n'%(Item[0],Item[1]))
            logs.log_error('SCANNED %s' % str(Item))
    File.close()

def dumpDataBase(db):
    Keys = list(db.keys())
    Keys.sort()
    Fout = open('database.dump','w')
    for Key in Keys:
        Fout.write('db %s %s\n'%(Key,db[Key]))
    Fout.close()



def get_list(Item):
#    print('GETLIST',Item)
    return get_list__(Item)
   
def get_list_db(Item,Verbose=False):
    Db = db.db[Item]
    if Verbose: logs.log_info('enter get_list_db item=%s Db=%s'%(Item,Db))
    Res = get_list(Db)
    if Verbose: logs.log_info('exit get_list_db item=%s Db=%s res=%s'%(Item,Db,Res))
    return Res

def get_iterative_list_2(Item,First,Second,Middle=''):
    Vars = matches.matches(Item,'%s %s %s'%(First,Middle,Second))
    if Vars:
        LL = []
        Vars2 = True
        Item0 = db.db[Vars[-1]]
        while Vars2:
            Vars2 = matches.matches(Item0,'%s %s %s'%(First,Middle,Second))
            if Vars2:
                L1 = get_list_db(Vars2[0])
                Item0 = db.db[Vars2[-1]]
            else:
                L1 = get_list(Item0)
            LL = LL+L1
        L2 = get_list_db(Vars[0])
        return LL+L2
    else:
        return get_list(Item)

def get_iterative_list_1(Item,First,Second,Middle=''):
    Vars = matches.matches(Item,'%s %s %s'%(First,Middle,Second))
    if Vars:
        LL = []
        Ok=True
        Vars2 = True
        Item0 = db.db[Vars[0]]
        while Vars2:
            Vars2 = matches.matches(Item0,'%s %s %s'%(First,Middle,Second))
            if Vars2:
                L1 = get_list_db(Vars2[-1])
                Item0 = db.db[Vars2[0]]
            else:
                L1 = get_list(Item0)
            LL = L1+LL
        L2 = get_list_db(Vars[-1])
        return LL+L2
    else:
        return get_list(Item)

def get_list__(Item):
    if (type(Item) is list)and(len(Item)==1):
        return get_list(Item[0])
    if (type(Item) is tuple)and(len(Item)==4):
        return [Item[0]]
    if (type(Item) is list)and(len(Item)==0):
        return []

    if inDb(Item):
        List = db.db[Item]
        if List==[]: return []
        return get_list(List)

    Vars = matches.matches(Item,'!statement !statements')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!pstatement !pstatements')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!generate_item !generates')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!pdefine !pdefines')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!Simple Bar !Simples')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!whens !one_when')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'!item !components')
    if Vars:
        Comp = get_list(Vars[0])
        More = get_list(Vars[1])
        return Comp + More

    Vars = matches.matches(Item,'PORT LeftParen !formal_port_list RightParen Semicolon')
    if Vars:
        LL = get_list(Vars[0])
        return LL

    Vars = matches.matches(Item,'COMPONENT ? PORT LeftParen !ports_list RightParen Semicolon END Semicolon')
    if Vars:
        Ports = get_list(Vars[1])
        return [('component',Vars[0][0],[],Ports)]
    Vars = matches.matches(Item,'COMPONENT ? !generic_clause PORT LeftParen !ports_list RightParen Semicolon END Semicolon')
    if Vars:
        Generics = get_list(Vars[1])
        Ports = get_list(Vars[2])
        return [('component',Vars[0][0],Generics,Ports)]

    Vars = matches.matches(Item,'!port_def Semicolon !ports_list')
    if Vars:
        Ports = get_list(Vars[1])
        Port = get_list(Vars[0])
        return Port + Ports

    Vars = matches.matches(Item,'!List Colon !Mode ?')
    if Vars:
        Mode = db.db[Vars[1]][0]
        LL = get_list(Vars[0])
        Res = []
        for Sig in LL:
            Res.append(('port',LL,Mode,Vars[2][0]))
        return  Res

    Vars = matches.matches(Item,'? Colon !Mode ?')
    if Vars:
        Mode = db.db[Vars[1]][0]
        return  [('port',Mode,Vars[0][0])]

    Vars = matches.matches(Item,'!List Colon !Mode ? !BusDef')
    if Vars:
        Mode = db.db[Vars[1]]
        HiLo = get_list(Vars[3])
        LL = get_list(Vars[0])
        Res = []
        for Sig in LL:
            Res.append(('port',Sig,Mode,Vars[2][0],HiLo[0][0],HiLo[0][1]))
        return  Res
        
    Vars = matches.matches(Item,'? Colon !Mode ? LeftParen !Expression DOWNTO !Expression RightParen')
    if Vars:
        Mode = db.db[Vars[1]]
        Hi = get_list(Vars[3])
        Lo = get_list(Vars[4])
        return [('port',Vars[0][0],Mode,Vars[2][0],Hi,Lo)]


    Vars = matches.matches(Item,'? Colon ? GENERIC MAP LeftParen !maps RightParen PORT MAP LeftParen !maps RightParen Semicolon')
    if Vars:
        Inst = Vars[0][0]
        Type = Vars[1][0]
        Gens = get_list(Vars[2])
        Cons = get_list(Vars[3])
#        add_inst(Inst,Type,Cons)
#        add_params(Inst,Gens)
        return [('instance',Vars[0][0],Vars[1][0],Cons,Gens)]

    Vars = matches.matches(Item,'? Colon ? GENERIC MAP LeftParen !maps RightParen PORT MAP LeftParen !List RightParen Semicolon')
    if Vars:
        Inst = Vars[0][0]
        Type = Vars[1][0]
        Gens = get_list(Vars[2])
        Cons = get_list(Vars[3])
#        add_inst(Inst,Type,Cons)
#        add_params(Inst,Gens)
        return [('instance',Vars[0][0],Vars[1][0],Cons,Gens)]

    Vars = matches.matches(Item,'? Colon ? PORT MAP LeftParen !maps RightParen Semicolon')
    if Vars:
        Maps = get_list(Vars[2])
#        add_inst(Vars[0][0],Vars[1][0],Maps)
        return [('instance',Vars[0][0],Vars[1][0],Maps,[])]

    Vars = matches.matches(Item,'? Colon ? PORT MAP LeftParen !List RightParen Semicolon')
    if Vars:
        Maps = get_list(Vars[2])
#        add_inst(Vars[0][0],Vars[1][0],Maps)
        return [('instance',Vars[0][0],Vars[1][0],Maps,[])]




    Vars = matches.matches(Item,'!map Comma !maps')
    if Vars:
        Maps = get_list(Vars[1])
        Map = get_list(Vars[0])
        return Map + Maps

    Vars = matches.matches(Item,'? => ?')
    if Vars:
        Con = get_list(Vars[1])
        return [('conn',Vars[0][0],Con)]

    Vars = matches.matches(Item,'? => ? LeftParen !Expression DOWNTO !Expression RightParen')
    if Vars:
        Hi = get_list(Vars[2])
        Lo = get_list(Vars[3])
        return [('conn',Vars[0][0],('subbus',Vars[1][0],Hi,Lo))]
    Vars = matches.matches(Item,'? => ? LeftParen !Expression RightParen')
    if Vars:
        Ind = get_list(Vars[2])
        return [('conn',Vars[0][0],('subbit',Vars[1][0],Ind))]

    Vars = matches.matches(Item,'? <= !Expression Semicolon')
    if Vars:
        Expr = get_list(Vars[1])
#        add_hard_assign(Vars[0][0],Expr[0])
        return [('hard_assign',Vars[0][0],Expr[0])]

    Vars = matches.matches(Item,'GENERIC LeftParen !formal_generic_list RightParen Semicolon')
    if Vars:
        LLL = get_list(Vars[0])
        return LLL

    Vars = matches.matches(Item,'!formal_generic_element Semicolon !formal_generic_list')
    if Vars:
        One = get_list(Vars[0])
        More = get_list(Vars[1])
        return One + More

    Vars = matches.matches(Item,'?  Colon ? !BusDef VarAsgn !Simple')
    if Vars:
        Bus = get_list(Vars[2])
        Val = get_list(Vars[3])
        return [('generic',Vars[0][0],Bus,Val)]

    Vars = matches.matches(Item,'?  Colon ?')
    if Vars:
        return [('generic',Vars[0][0],Vars[1][0])]

    Vars = matches.matches(Item,'?  Colon IN ?')
    if Vars:
        return [('generic',Vars[0][0],Vars[1][0])]



    Vars = matches.matches(Item,'PORT LeftParen !formal_port_list RightParen Semicolon')
    if Vars:
        return get_list(Vars[0])
    Vars = matches.matches(Item,'!formal_port_element Semicolon !formal_port_list')
    if Vars:
        return get_list(Vars[0])+get_list(Vars[1])
    Vars = matches.matches(Item,'!Expression Minus !Expression')
    if Vars:
        Exp0 = get_list(Vars[0])
        Exp1 = get_list(Vars[1])
        return [('expr','-',Exp0,Exp1)]
    Vars = matches.matches(Item,'? Colon ? VarAsgn ?')
    if Vars:
        return [('generic_map',Vars[0][0],Vars[1][0],Vars[2][0])]

    Vars = matches.matches(Item,'SIGNAL !List Colon ? Semicolon')
    if Vars:
        List = get_list(Vars[0])
        return [('signal',List,Vars[1][0])]

    Vars = matches.matches(Item,'SIGNAL !List Colon ? VarAsgn !Expression Semicolon')
    if Vars:
        List = get_list(Vars[0])
        Expr = get_list(Vars[2])
        return [('signal',List,Vars[1][0]),('assign',List[0],Expr)]

    Vars = matches.matches(Item,'SIGNAL !List Colon ? !BusDef VarAsgn !Expression Semicolon')
    if Vars:
        List = get_list(Vars[0])
        HiLo = get_list(Vars[2])
        Expr = get_list(Vars[3])
        return [('signal',List,Vars[1][0],HiLo[0]),('assign',List[0],Expr)]  # ILIA
    
    Vars = matches.matches(Item,'LeftParen !Expression !Dir !Expression RightParen')
    if Vars:
        L1 = get_list(Vars[0])
        Dir = get_list(Vars[1])
        L2 = get_list(Vars[2])
        Hi = xeval(L1[0])
        Lo = xeval(L2[0])
        return [(Hi,Lo)]


    Vars = matches.matches(Item,'SIGNAL !List Colon ? RANGE !Expression TO !Expression Semicolon')
    if Vars:
        List = get_list(Vars[0])
        Lo = get_list(Vars[2])
        Hi = get_list(Vars[3])
        return [('signal',List,Vars[1][0],('range',Lo,Hi))]

    Vars = matches.matches(Item,'SIGNAL !List Colon ? !BusDef Semicolon')
    if Vars:
        List = get_list(Vars[0])
        Kind = Vars[1][0]
        HiLo = get_list(Vars[2])

        return [('signal',List,Vars[1][0],HiLo[0])]


    Vars = matches.matches(Item,'VARIABLE !List Colon ? Semicolon')
    if Vars:
        List = get_list(Vars[0])
        return [('variable',List,Vars[1][0])]

    Vars = matches.matches(Item,'VARIABLE !List Colon ? !BusDef Semicolon')
    if Vars:
        List = get_list(Vars[0])
        Wid  = get_list(Vars[2])
        return [('variable',List,Vars[1][0],Wid)]



    Vars = matches.matches(Item,'!List Comma ?')
    if Vars:
        LL = get_list(Vars[0])
        This = get_list(Vars[1])
        return LL + This

    Vars = matches.matches(Item,'PROCESS LeftParen !List RightParen BEGIN_ !pstatements END  Semicolon')
    if Vars:
        Sense = get_list(Vars[0])
        Statements= get_list(Vars[1])
        return [('always',Sense,Statements)]

    Vars = matches.matches(Item,'? Colon PROCESS LeftParen !List RightParen BEGIN_ !pstatements END  Semicolon')
    if Vars:
        Sense = get_list(Vars[1])
        Statements= get_list(Vars[2])
        return [('always',Sense,Statements)]

    Vars = matches.matches(Item,'? Colon PROCESS LeftParen !List RightParen !pdefines BEGIN_ !pstatements END  Semicolon')
    if Vars:
        Sense = get_list(Vars[1])
        Statements= get_list(Vars[3])
        Defs= get_list(Vars[2])
        return [('always',Vars[0][0],Sense,Defs,Statements)]




    Vars = matches.matches(Item,'IF !Expression THEN !pstatements END Semicolon')
    if Vars:
        Cond = get_list(Vars[0])
        Stats = get_list(Vars[1])
        return [('if',Cond,Stats)]

    Vars = matches.matches(Item,'IF !Expression THEN !pstatements ELSE !pstatements END Semicolon')
    if Vars:
        Cond = get_list(Vars[0])
        Yes = get_list(Vars[1])
        No = get_list(Vars[2])
        return [('ifelse',Cond,Yes,No)]

    Vars = matches.matches(Item,'!elsifs !elsif')
    if Vars:
        Part0 = get_list(Vars[0])
        Part1 = get_list(Vars[1])
        return Part0 + Part1

    Vars = matches.matches(Item,'IF !Expression THEN !pstatements !elsifs END Semicolon')
    if Vars:
        Cond = get_list(Vars[0])
        Yes = get_list(Vars[1])
        No = get_list(Vars[2])
        No = list(No[0])
        No[0] = 'if'
        No = tuple(No)
        return [('ifelse',Cond,Yes,[No])]


    Vars = matches.matches(Item,'IF !Expression THEN !pstatements !elsifs ELSE !pstatements END Semicolon')
    if Vars:
        Cond = get_list(Vars[0])
        Yes = get_list(Vars[1])
        No = get_list(Vars[2])
        No = list(No[0])
        No[0] = 'ifelse'
        No2 = get_list(Vars[3])
        No = No + [No2]
        No = tuple(No)
        Result = ('ifelse',Cond,Yes,No)
        return [Result]



    Vars = matches.matches(Item,'ELSIF !Expression THEN !pstatements')
    if Vars:
        Cond = get_list(Vars[0])
        Stats = get_list(Vars[1])
        return [('elsif',Cond,Stats)]

    Vars = matches.matches(Item,'? LeftParen !Expression RightParen LESym !Expression Semicolon')
    if Vars:
        Src = get_list(Vars[2])
        Dst1 = get_list(Vars[1])
        return [('assign',('subbit',Vars[0][0],Dst1),Src)]

    Vars = matches.matches(Item,'? LeftParen !Expression DOWNTO !Expression RightParen LESym !Expression Semicolon')
    if Vars:
        Src = get_list(Vars[3])
        Hi = get_list(Vars[1])
        Lo = get_list(Vars[2])
        return [('assign',('subbus',Vars[0][0],Hi,Lo),Src)]


    Vars = matches.matches(Item,'LeftParen !Expression RightParen')
    if Vars:
        Cond = get_list(Vars[0])
        return Cond
    Vars = matches.matches(Item,'!Expression ? !Expression')
    if Vars:
        AA = get_list(Vars[0])
        BB = get_list(Vars[2])
        return [('expr',Vars[1][0],AA,BB)]

    Vars = matches.matches(Item,'!Expressions Comma !Expression')
    if Vars:
        AA = get_list(Vars[0])
        BB = get_list(Vars[1])
        return  AA+BB

    Vars = matches.matches(Item,'NOT !Expression')
    if Vars:
        AA = get_list(Vars[0])
        return  [('!',AA)]
        
    Vars = matches.matches(Item,'? LeftParen !Expressions RightParen')
    if Vars:
        AA = get_list(Vars[1])
        return [('func',Vars[0][0],AA)]

    Vars = matches.matches(Item,'? Apostrophe event')
    if Vars:
        return [('event',Vars[0][0])]
    Vars = matches.matches(Item,'? Apostrophe RANGE')
    if Vars:
        return [('range',Vars[0][0])]

    Vars = matches.matches(Item,'LeftParen ? RANGE Box RightParen')
    if Vars:
        return [('box',Vars[0][0])]

    Vars = matches.matches(Item,'!Expression WHEN !Expression ELSE !Expression')
    if Vars:
        Cond = get_list(Vars[1])
        Yes = get_list(Vars[0])
        No = get_list(Vars[2])
        return [('question',Cond,Yes,No)]

    Vars = matches.matches(Item,'LeftParen OTHERS Arrow !Expression RightParen')
    if Vars:
        AA = get_list(Vars[0])
        return [('default',AA)]

    Vars = matches.matches(Item,'LeftParen OTHERS Arrow ? RightParen')
    if Vars:
        return [Vars[0][0]]

    Vars = matches.matches(Item,'? LeftParen !Expression DOWNTO !Expression RightParen')
    if Vars:
        Hi = get_list(Vars[1])
        Lo = get_list(Vars[2])
        return [('bus',Vars[0][0],Hi,Lo)]

    Vars = matches.matches(Item,'TYPE ? IS LeftParen !List RightParen Semicolon')
    if Vars:
        AA = get_list(Vars[1])
        return [('type',Vars[0][0],AA)]

    Vars = matches.matches(Item,'TYPE ? IS ARRAY !BusDef OF ? !BusDef Semicolon')
    if Vars:
        St = get_list(Vars[1])
        En = get_list(Vars[3])
        return [('doublearray',Vars[0][0],St,En)]

    Vars = matches.matches(Item,'TYPE ? IS ARRAY !Nat OF ? !BusDef Semicolon')
    if Vars:
        En = get_list(Vars[3])
        return [('doublearray',Vars[0][0],'integer',En)]

    Vars = matches.matches(Item,'CASE !Expression IS !whens END Semicolon')
    if Vars:
        Cond = get_list(Vars[0])
        AA = get_list(Vars[1])
        return [('case',Cond,AA)]

    Vars = matches.matches(Item,'WHEN ? Arrow !pstatements')
    if Vars:
        Cond = get_list(Vars[0])
        Stats = get_list(Vars[1])
        return [('case',Cond,Stats)]

    Vars = matches.matches(Item,'WHEN OTHERS Arrow !pstatements')
    if Vars:
        Stats = get_list(Vars[0])
        return [('default',Stats)]

    Vars = matches.matches(Item,'WHEN OTHERS Arrow NULL_ Semicolon')
    if Vars:
        return [('default',[])]

    Vars = matches.matches(Item,'? VarAsgn !Expression Semicolon')
    if Vars:
        AA = get_list(Vars[1])
        return [('assign',Vars[0][0],AA)]

    Vars = matches.matches(Item,'CONSTANT ? Colon ? VarAsgn !Expression Semicolon')
    if Vars:
        Expr = get_list(Vars[2])
        return [('constant',Vars[0][0],Expr)]

    Vars = matches.matches(Item,'CONSTANT ? Colon ? !BusDef VarAsgn !Expression Semicolon')
    if Vars:
        Expr = get_list(Vars[3])
        return [('constant',Vars[0][0],Expr)]

    Vars = matches.matches(Item,'FOR ? IN !Expression TO !Expression LOOP !pstatement END Semicolon')
    if Vars:
        St = get_list(Vars[1])
        En = get_list(Vars[2])
        Stats = get_list(Vars[3])
        return [('for',Vars[0][0],St,En,Stats)]


    Vars = matches.matches(Item,'? Colon FOR ? IN !Expression TO !Expression GENERATE !generates END Semicolon')
    if Vars:
        St = get_list(Vars[1])
        En = get_list(Vars[2])
        List = get_list(Vars[3])
        return [('generate_for',Vars[0][0],St,En,List)]

    Vars = matches.matches(Item,'? Colon IF !Expression GENERATE !generates END Semicolon')
    if Vars:
        Expr = get_list(Vars[1])
        List = get_list(Vars[2])
        return [('generate_if',Vars[0][0],Expr,List)]

    Vars = matches.matches(Item,'ASSERT !Expression REPORT ? ? Semicolon')
    if Vars:
        Expr = get_list(Vars[0])
        return [('assertion',Expr,Vars[1][0],Vars[2][0])]

    Vars = matches.matches(Item,'ASSERT !Expression REPORT ? ? ? Semicolon')
    if Vars:
        Expr = get_list(Vars[0])
        return [('assertion',Expr,Vars[1][0],Vars[2][0],Vars[3][0])]

    Vars = matches.matches(Item,'? LeftParen ? Comma !List RightParen Semicolon')
    if Vars:
        List = get_list(Vars[2])
        return [('funccall',Vars[0][0],[ Vars[1][0]] + List)]




    logs.log_error('GETLIST %s' % str(Item))
    return ['error %s' % str(Item)]






############################################
    logs.log_err('get_list %s'%str(Item))
    logs.pStack()
    return []


def simplify(Item):
    if isinstance(Item,(str,int)): return Item

    if type(Item) is list:
        if len(Item)==1:
            return simplify(Item[0])
        if len(Item)==0: return Item
        LL = Item
        while LL[-1]==[]: LL.pop(-1)

        Res = list(map(simplify,LL))
        return Res

    if type(Item) is tuple:
        LL = list(map(simplify,Item))
        if LL==[]: return tuple(LL)
        while (LL!=[])and(LL[-1]==[]): LL.pop(-1)
        if len(LL)==1: return LL[0]
        return tuple(LL)

    logs.log_error('wtf! %s %s'%(type(Item),Item))
    return Item

def nicePrint(Item):
    Str = str(Item)
    if len(Str)<100: return Str
    wrds = Str.split()
    Str = ''
    Lim = 100
    while wrds!=[]:
        Str += wrds.pop(0)+' '
        if len(Str)>Lim:
            Str = Str + '\n      '
            Lim += 100
    Str += '\n'        
    return Str

def printl(Txt):
    logs.log_info('TELL %s'%(Txt))

Modules = {}
Current = False
def addParam(Cell,Param,Kind,Val):
    global Current
    Current = Cell
    if Cell not in  db.Modules:
        Mod = mcl.module_class(Cell)
        db.Modules[Cell] = Mod
    else:
        Mod = db.Modules[Cell]
    Mod.parameters[Param] = Val

def add_params(Inst,Params):
    Mod = db.Modules[Current]
    for Prm in Params:
        _,Param,Value = Prm
        Mod.add_inst_param(Inst,Param,Value)
        print('ADD_PRM',Inst,Param,Value)


def addArchitecture(Name,Decls,Body):
    Mod = startModule(Name)
    Mod.vsignals.append(Decls)
    Mod.valwayses.append(Body)

def startModule(Cell):
    global Current
    Current = Cell
    if Cell not in  db.Modules:
        Mod = mcl.module_class(Cell)
        db.Modules[Cell] = Mod
    else:
        Mod = db.Modules[Cell]
    return Mod

def pinDir(Dir):
    if type(Dir) is tuple: return pinDir(Dir[0])
    if Dir in ['input','output']: return Dir
    if Dir == 'IN': Dir = 'input'
    elif Dir == 'OUT': Dir = 'output'
    elif Dir == 'INOUT': Dir = 'inout'
    else: 
        logs.log_error('Direction from vhdl "%s"' %str(Dir))
        Dir = 'inout'
    return Dir

def addBusPin(Cell,Port):
    Mod = startModule(Cell)
    if (len(Port)==6)and(Port[0] == 'port')and(Port[3] == 'std_logic_vector'):
        Pin = Port[1]
        Dir = pinDir(Port[2][0]) 
        Hi = xeval(Port[4])
        Lo = xeval(Port[5])
        Mod.add_sig(Pin,Dir,(Hi,Lo))
        return
    logs.log_error('bad bus %s pin "%s"' % (Cell,Port))
                
def xeval(Ind):
    if type(Ind) is int: return Ind
    if type(Ind) is str:
        try:
            return eval(Ind)
        except:
            return Ind
    return Ind

def addPin(Cell,Sig,Dir,Kind):
    Mod = startModule(Cell)
    Dir = pinDir(Dir)
    if (type(Sig) is list) and (len(Sig) == 1):
        Sig = Sig[0]

    if Kind == 'std_logic': Wid = 0
    else:
#        logs.log_error('KIND %s sig=%s kind=%s Wid = 0' % (Cell,Sig,Kind))
        Wid = 0
        Dir = Dir + ' ' + Kind
    Mod.add_sig(Sig,Dir,Wid)

def add_inst(Inst,Type,Conns):
    if not Current:
        logs.log_error('ADD_INST no current for %s %s %s' % (Inst,Type,Conns))
        return
    Mod = db.Modules[Current]
    Mod.add_inst(Type,Inst)
    for ind,Conn in enumerate(Conns):
        if (len(Conn)==3)and(Conn[0] == 'conn'):
            (_,Pin,Sig) = Conn
            Mod.add_conn(Inst,Pin,Sig)
        elif (len(Conn)==1)or(type(Conn) is str):
            Mod.add_conn(Inst,ind,Conn)
        else:
            logs.log_error('CONN %s' % str(Conn))


def add_hard_assign(Dst,Src):
    Mod = db.Modules[Current]
    Mod.hard_assigns.append((Dst,Src,'',[])) 
     

if __name__=='__main__':
    main()


