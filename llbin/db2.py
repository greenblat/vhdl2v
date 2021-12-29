


import logs
import module_class
import matches


Types = {}
def run(dbscan):
    dealVsignals(dbscan)
    dealValwayses(dbscan)
COMPONENTS = {}
def dealVsignals(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        ind = 0
        if Mod.vsignals == []: return
        Vsignals = Mod.vsignals[0]
        while ind<len(Vsignals):
            Item = Vsignals[ind]
            if Item[0] == 'component':
                COMPONENTS[Item[1]] = []
                for Port in Item[3]:
                    COMPONENTS[Item[1]].append(Port[1])
                Vsignals.pop(ind)
            elif Item[0] == 'type':
                Name = Item[1]
                print('ENUMS',Item[2])
                Mod.enums[Name] = ('singles',Item[2])
                Vsignals.pop(ind)
            elif Item[0] == 'doublearray':
                AA = getWid(Item[2])
                BB = getWid(Item[3])
                Types[Item[1]] = ('double',BB,AA)
                Vsignals.pop(ind)

            elif Item[0] == 'constant':
                Mod.localparams[Item[1]] = Item[2]
                Vsignals.pop(ind)
            elif Item[0].lower() == 'signal':
                Vsignals.pop(ind)
                for Sig in Item[1]:
                    if Item[2] == 'std_logic':
                        Mod.add_sig(Sig,'logic',0)
                    elif Item[2] == 'std_logic_vector':
                        Wid = getWid(Item[3])
                        Mod.add_sig(Sig,'logic',Wid)
                    elif Item[2]  in ['integer','unsigned','natural']:
                        Mod.add_sig(Sig,'logic',(31,0))
                    elif Item[2] in Types:
                        Def = Types[Item[2]]
                        if Def[0] == 'double':
                            Mod.add_sig(Sig,'logic',('packed',AA,BB))
                    else:
                        Mod.add_sig(Sig,Item[2],0)
            elif Item[0] == 'assign':
                Vsignals.pop(ind)
                logs.log_warning('INIT ASSIGN not used %s' % str(Item))
            else:
                logs.log_error('VSIGNALS %s' % str(Item))
                ind += 1
            
def getWid(Item):
    if (type(Item) is list)and(len(Item)==1):
        return getWid(Item[0])
    Bus = Item
    if (type(Bus) is tuple) and (Bus[0] == 'busdef'):
        Hi = seq_expr(Bus[1])
        Lo = seq_expr(Bus[2])
        return (Hi,Lo)
    if (type(Bus) is tuple) and (len(Bus) == 2):
        return Bus

    logs.log_error('getWid got "%s"' % str(Item))
    return 0

def dealValwayses(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        ind = 0
        if Mod.valwayses == []: return
        Valwayses = Mod.valwayses[0]
        while ind<len(Valwayses):
            Item = Valwayses[ind]
            if Item[0] == 'instance':
                Inst = Item[1]
                Type = Item[2]
                Obj = Mod.add_inst(Type,Inst)
                for xind,Conn in enumerate(Item[3]):
                    if (type(Conn) is tuple) and (Conn[0] == 'conn'):
                        Pin = Conn[1]
                        Sig = seq_expr(Conn[2])
                        Mod.add_conn(Inst,Pin,Sig)
                    elif (Type in COMPONENTS) and (xind < len(COMPONENTS[Type])):
                        Pin = COMPONENTS[Type][xind]
                        Sig = seq_expr(Conn)
                        Mod.add_conn(Inst,Pin,Sig)
                    else:
                        logs.log_error('ADD CONN %s %s %s   %s' % (Inst,Type,Conn,Item))
                for xind,Prm in enumerate(Item[4]):
                    if (type(Prm) is tuple) and (len(Prm)==3)and(Prm[0] == 'conn'):
                        Prmx = Prm[1]
                        Val = seq_expr(Prm[2])
                        Mod.add_inst_param(Inst,Prmx,Val)
                    else:
                        logs.log_error('BAD PARAM "%s" ' % str(Prm))
                Valwayses.pop(ind)
            elif Item[0] in ['assign','hard_assign']:
                Valwayses.pop(ind)
                Dst = seq_expr(Item[1])
                Src = seq_expr(Item[2])
                Mod.hard_assigns.append((Dst,Src,'',''))
            elif Item[0] == 'always':
                Valwayses.pop(ind)
                Code = seqCode(Item[-1],Mod)
                if len(Item)==5:
                    Renames = dealWithMores(Mod,Item[1],Item[3])
                    Code = renameDeep(Code,Renames)
                    Mod.alwayses.append((Item[2],Code,'always'))
                else:
                    Mod.alwayses.append((Item[1],Code,'always'))
            else:
                logs.log_error('dealValwayses %s' % str(Item))
                Valwayses.pop(ind)

def dealWithMores(Mod,Proc,List):
    Renames = {}
    for Item in List:
        if Item[0] == 'variable':
            if Item[2] == 'std_logic':
                for Sig in Item[1]:
                    Mod.add_sig(Proc+'_'+Sig,'logic',0)
                    Renames[Sig] = Proc+'_'+Sig
            elif Item[2] in Mod.enums:
                for Sig in Item[1]:
                    Mod.add_sig(Proc+'_'+Sig,Item[2],0)
                    Renames[Sig] = Proc+'_'+Sig
            else:
                logs.log_error('deal with variables of type "%s" ' % str(Item[2]))
        elif Item[0] == 'type':
            Name = Item[1]
            if Name in Mod.enums:
                Was = Mod.enums[Name]
                print('ENUM2',Was,Item[2])
                for X in Item[2]:
                    if X not in Was[1]:
                        Was[1].append(X)
                Mod.enums[Name] = ('singles',Was[1])
            else:
                Mod.enums[Name] = ('singles',Item[2])
        else:
            logs.log_error('deal with moreList of kind "%s" ' % str(Item))
    return Renames
        
def seqCode(Code,Mod):
    if Code[0] in ['ifelse','if']:
        return seqCode([Code],Mod)
    Res = []
    for Item in Code:
        if type(Item) is list:
            if len(Item) == 1:
                Res.append(seqCode(Item[0],Mod))
            elif (Item[0] == 'if'):
                return seqCode(tuple(Item),Mod)
            else:
                Mid = []
                for X in Item:
                    Mid.append(seqCode(X,Mod))
                Res.append(['list',Mid])
        elif Item[0] in ['assign','hard_assign']:
            Res.append(('=',seq_expr(Item[1]),seq_expr(Item[2])))
        elif Item[0] == 'if':
            Cond = seq_expr(Item[1])
            More = seqCode(Item[2],Mod)
            Less,Else = splitElsif(More)
            if Else != []:
                Res.append(('ifelse',Cond,Less,Else))
            else:
                Res.append(('if',Cond,More))
        elif Item[0] == 'ifelse':
            Cond = seq_expr(Item[1])
            Yes = seqCode(Item[2],Mod)
            No = seqCode(Item[3],Mod)
            Res.append( ('ifelse',Cond,Yes,No))
        elif Item[0] == 'elsif':
            Cond = seq_expr(Item[1])
            More = seqCode(Item[2],Mod)
            Less,Else = splitElsif(More)
            if Else != []:
                Res.append(('elsif',Cond,Less,Else))
            else:
                Res.append(('else',Cond,More))
        elif Item[0] == 'for':
            Var = Item[1]
            Init = seq_expr(Item[2])
            End = seq_expr(Item[3])
            Body = seqCode(Item[4],Mod)
            Res.append(('for',('=',Var,Init),('<',Var,End),('=',Var,('+',Var,1)),Body))
        elif Item[0] == 'case':
            Cond = seq_expr(Item[1])
            Stmnt = ('case',Cond,[])
            for Case in Item[2]:
                Label = seq_expr(Case[1])
                if Label == 'OTHERS': Label = 'default'
                if len(Case)==3:
                    Seq = seqCode(Case[2],Mod)
                    Stmnt[2].append((Label,Seq))
                elif Case[0] == 'default':
                    if Case[1] == []:
                        Seq = ''
                    else:
                        Seq = seqCode(Case[1],Mod)
                    Stmnt[2].append(('default',Seq))
                else:
                    Stmnt[2].append((Label,'null'))
            Res.append(Stmnt)
        else:
            logs.log_error('seqCode got "%s"' % str(Item))
    return ['list',Res]

def splitElsif(More):
    Bef,Aft = [],[]
    for Item in More:
        if Item[0] == 'elsif':
            return Bef,Item
        else:
            Bef.append(Item)
    return Bef,Aft


RESERVED = ['int']
OPS = {'LTSym':'<','MOD':'%','<=':'<=','**':'**','GTSym':'>','GESym':'>=','XOR':'^','Star':'*','Slash':'/','+':'+','-':'-','*':'*','/':'/','AND':'&','OR':'|','EQSym':'==','/=':'!=','Ampersand':'&'}
def seq_expr(Code):
    if type(Code) is str: 
        if (Code[0] == "'") and(Code[-1]=="'"):
            return Code[1:-1]
        if (Code[0] == '"') and(Code[-1]=='"'):
            return "%d'b%s" % (len(Code)-2,Code[1:-1])
        if (Code[0] == 'x' ) and (Code[-1] == '"'):
            Code = "'h"+Code[2:-1]
        if Code in RESERVED:
            return 'x_'+Code
        return Code
    if Code==[]: return 0;
    if (type(Code) is list)and(len(Code)==1):
        return seq_expr(Code[0])
#    print('SEQ_EXPR',Code)
    if type(Code) is tuple:
        if Code[0]=='event':
            return ('function','edge',[Code[1]])
        if Code[0]=='question':
            Cond = seq_expr(Code[1])
            Yes = seq_expr(Code[2])
            No = seq_expr(Code[3])
            return ('question',Cond,Yes,No)
        elif Code[0]=='!':
            return ('!',seq_expr(Code[1]))
        elif Code[0]=='expr':
            return seq_expr(Code[1:])
        elif Code[0] in OPS:
            A = seq_expr(Code[1])
            B = seq_expr(Code[2])
            return (OPS[Code[0]],A,B)
        elif Code[0] in ['subbus','bus']:
            Bus = Code[1]
            Hi = seq_expr(Code[2])
            Lo = seq_expr(Code[3])
            return ('subbus',Bus,(Hi,Lo))
        elif Code[0] in ['subbit','func']:
            Bus = Code[1]
            if Bus == 'std_logic_vector':
                return seq_expr(Code[2])
            if Bus == 'signed':
                return seq_expr(Code[2])
            if Bus == 'unsigned':
                return seq_expr(Code[2])
            if Bus in ['to_integer','to_unsigned']:
                return seq_expr(Code[2][0])
            if len(Code[2])>1:
                Res = []
                for Item in Code[2]:
                    Res.append(seq_expr(Item))
                return ('funcall',Bus,Res)

            Ind = seq_expr(Code[2])
            return ('subbit',Bus,Ind)
        elif Code[0]=='default':
            return seq_expr(Code[1])
            
    logs.log_error('seq_expr got "%s" %s' % (str(Code),type(Code)))
    return Code

def renameDeep(Code,Renames):
    if type(Code) is str:
        if Code in Renames:
            return Renames[Code]
        return Code

    if type(Code) is int: return Code

    if type(Code) is list:
        for ind,Item in enumerate(Code):
            Item0 = renameDeep(Item,Renames)
            Code[ind] = Item0
        return Code
    if type(Code) is tuple:
        List = list(Code)
        New = renameDeep(List,Renames)
        return tuple(New)
        
    logs.log_error('renameDeep got %s' % (type(Code)))
    return Code


