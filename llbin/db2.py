


import logs
import module_class
import matches


def run(dbscan):
    dealVsignals(dbscan)
    dealValwayses(dbscan)
COMPONENTS = {}
def dealVsignals(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        ind = 0
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
                Mod.enums[Name] = ('singles',Item[2])
                Vsignals.pop(ind)

            elif Item[0] == 'constant':
                Mod.localparams[Item[1]] = Item[2]
                Vsignals.pop(ind)
            elif Item[0] == 'signal':
                for Sig in Item[1]:
                    if Item[2] == 'std_logic':
                        Mod.add_sig(Sig,'wire',0)
                        Vsignals.pop(ind)
                    elif Item[2] == 'std_logic_vector':
                        Wid = getWid(Item[3])
                        Mod.add_sig(Sig,'wire',Wid)
                        Vsignals.pop(ind)
                    elif Item[2]  in ['integer','unsigned','natural']:
                        Mod.add_sig(Sig,'wire',(31,0))
                        Vsignals.pop(ind)
                    else:
                        Mod.add_sig(Sig,Item[2],0)
                        Vsignals.pop(ind)
            else:
                logs.log_error('VSIGNALS %s' % str(Item))
                ind += 1
            
def getWid(Item):
    if (type(Item) is list)and(len(Item)==1):
        Bus = Item[0]
        if (type(Bus) is tuple) and (Bus[0] == 'busdef'):
            Hi = seq_expr(Bus[1])
            Lo = seq_expr(Bus[2])
            return (Hi,Lo)
    logs.log_error('getWid got "%s"' % str(Item))
    return 0

def dealValwayses(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        ind = 0
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
                Code = seqCode(Item[2],Mod)
                Mod.alwayses.append((Item[1],Code,'always'))
            else:
                logs.log_error('dealValwayses %s' % str(Item))
                Valwayses.pop(ind)


def seqCode(Code,Mod):
    Res = []
    for Item in Code:
        if type(Item) is list:
            if len(Item) == 1:
                Res.append(seqCode(Item[0]))
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
            return ('ifelse',Cond,Yes,No)
        elif Item[0] == 'elsif':
            Cond = seq_expr(Item[1])
            More = seqCode(Item[2],Mod)
            Less,Else = splitElsif(More)
            if Else != []:
                Res.append(('elsif',Cond,Less,Else))
            else:
                Res.append(('else',Cond,More))
        elif Item[0] == 'case':
            Cond = seq_expr(Item[1])
            Stmnt = ('case',Cond,[])
            for Case in Item[2]:
                Label = seq_expr(Case[1])
                if Label == 'OTHERS': Label = 'default'
                if len(Case)==3:
                    Seq = seqCode(Case[2],Mod)
                    Stmnt[2].append((Label,Seq))
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



OPS = {'Star':'*','Slash':'/','+':'+','-':'-','*':'*','/':'/','AND':'&','OR':'|','EQSym':'==','/=':'!=','Ampersand':'&'}
def seq_expr(Code):
    if type(Code) is str: 
        if (Code[0] == "'") and(Code[-1]=="'"):
            return Code[1:-1]
        if (Code[0] == '"') and(Code[-1]=='"'):
            return "%d'b%s" % (len(Code)-2,Code[1:-1])
        return Code
    if Code==[]: return 0;
    if (type(Code) is list)and(len(Code)==1):
        return seq_expr(Code[0])
    if type(Code) is tuple:
        if Code[0]=='event':
            return ('function','edge',[Code[1]])
        if Code[0]=='question':
            Cond = seq_expr(Code[1])
            Yes = seq_expr(Code[2])
            No = seq_expr(Code[3])
            return ('question',Cond,Yes,No)
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
            Ind = seq_expr(Code[2])
            return ('subbit',Bus,Ind)
        elif Code[0]=='default':
            return seq_expr(Code[1])
            
    logs.log_error('seq_expr got "%s" %s' % (str(Code),type(Code)))
    return Code
