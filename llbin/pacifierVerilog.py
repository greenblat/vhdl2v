
import string,types
import  module_class
import logs
import matches

def pacifier(Mod):
    simpleTypes(Mod)
    alwayses(Mod)


def alwayses(Mod):
    for Always in Mod.alwayses:
        Sense = Always[0]
        declareRegs(Mod,Always[1])
        if (len(Always[1])==4)and(Always[1][0] in ['if','ifelse']):
            Top = Always[1]
            if Top[0]=='ifelse':
                ClkRst = extractClkRst(Top)
                if type(ClkRst)==types.TupleType:
                    Clk,Rst = ClkRst
                    Always[0] = ['list',Clk,Rst]
                    Always[1][3] = Always[1][3][2]
                else:
                    Always[0]='*'
            elif Top[0]=='if':
                ClkRst = extractClkRst(Top)
                print '>>>>>>>>iextractClkRst>>',ClkRst
                if type(ClkRst)==types.TupleType:
                    Clk,_ = ClkRst
                    Always[0] = Clk
                else:
                    Always[0]='*'
            else:
                Always[0]='*'

        elif (len(Always[1])==3)and(Always[1][0]=='if'):
            ClkRst = extractClkRst(Always[1][1])
            if (ClkRst):
                Always[0]= ClkRst[0]
                Always[1] = Always[1][2]
            else:
                Always[0]='*'

        elif (len(Always[1])==2)and(Always[1][0]=='list'):
            Top = Always[1][1]
            if Top[0]=='ifelse':
                ClkRst = extractClkRst(Top)
                if type(ClkRst)==types.TupleType:
                    Clk,Rst = ClkRst
                    Always[0] = ['list',Clk,Rst]
                    Always[1][1][3] = Always[1][1][3][2]
                else:
                    Always[0]='*'
            elif Top[0]=='if':
                ClkRst = extractClkRst(Top)
                if type(ClkRst)==types.TupleType:
                    Clk,_ = ClkRst
                    Always[0] = Clk
                else:
                    Always[0]='*'
            else:
                Always[0]='*'
        else:
            Always[0]='*'

def extractClkRst(Top):
    Vars =  matches.matches(Top,['subbit', 'rising_edge', '?'])
    if Vars:
        return  ['edge','posedge',Vars[0]],False
    Vars =  matches.matches(Top,['subbit', 'falling_edge', '?'])
    if Vars:
        return  ['edge','negedge',Vars[0]],False
        

    Vars =  matches.matches(Top,['&', ['functioncall', 'event', '?'], ['==', '?', '?']])
    if Vars:
        if Vars[0]==Vars[1]:
            if notZeroValue(Vars[2]):
                return  ['edge','posedge',Vars[0]],False
            else:
                return  ['edge','negedge',Vars[0]],False
        logs.log_error('?????? vars=%s'%str(Vars)) 
        return []


    if len(Top)==4:
        Vars =  matches.matches(Top[1],'== ? ?')
        if Vars:
            Rst = Vars[0]
            if notZeroValue(Vars[1]):
                RR = ('edge','posedge',Rst)
            else:
                RR = ('edge','negedge',Rst)
        else: 
            return False
        if Top[3][0]=='if':
            Vars =  matches.matches(Top[3][1],['&', ['functioncall', 'edge', ['?']], ['==', '?', '?']])
            if Vars and (len(Vars)==3) and (Vars[0]==Vars[1]):
                Clk = Vars[0]
                if notZeroValue(Vars[2]):
                    CC = ('edge','posedge',Clk)
                else:
                    CC = ('edge','negedge',Clk)
                return  CC,RR
            else:
               return False
            logs.log_error('extractClkRst (0)  len==4 %s %s %s %s'%(Top[0],Top[1],Top[3][0],Top[3][1]))
            return False
    if len(Top)==3:
        Vars =  matches.matches(Top,['&', ['functioncall', 'edge', ['?']], ['==', '?', '?']])
        if Vars and (len(Vars)==3) and (Vars[0]==Vars[1]):
            Clk = Vars[0]
            if notZeroValue(Vars[2]):
                CC = ('edge','posedge',Clk)
            else:
                CC = ('edge','negedge',Clk)
            return  CC,False
        else:
            return False


#    logs.log_error('extractClkRst (1) len=%d %s'%(len(Top),str(Top)))
    return False



def declareRegs(Mod,Struct):
    Regs = scanForRegs(Struct)
    for Net in Regs:
        if Net not in Mod.nets:
            logs.log_error('net not defined for declareRegs "%s"'%str(Net))
        else:
            Dir,Wid = Mod.nets[Net]
            if Dir=='wire':
                Mod.nets[Net] = ('reg',Wid)
            elif Dir=='output':
                Mod.nets[Net] = ('output reg',Wid)
            elif Dir=='reg':
                pass
            else:
                logs.log_error('pacifierVerilog: net %s tried to be reg'%Net)

def scanForRegs(Struct):
    Regs=[]
    if (type(Struct) ==  types.ListType)and(len(Struct)==1):
        return scanForRegs(Struct[0])
    if Struct==[]: return []
    if (type(Struct) in [types.TupleType,types.ListType])and(Struct[0] in ['=','<=']):
        Nets = module_class.support_set(Struct[1],False)
        for Net in Nets:
            if Net not in Regs: Regs.append(Net)
            return Regs
    if (type(Struct) ==  types.ListType)and(Struct[0]=='list'):
        for Item in Struct:
            More = scanForRegs(Item)
            for Net in More:
                if Net not in Regs: Regs.append(Net)
        return Regs
    if (type(Struct) ==  types.ListType):
        if (Struct[0]=='comment'):
            return []
        if (Struct[0]=='if'):
            return scanForRegs(Struct[2])
        if (Struct[0]=='ifelse'):
            More = scanForRegs(Struct[2])+scanForRegs(Struct[3])
            for Net in More:
                if Net not in Regs: Regs.append(Net)
            return Regs
        if (Struct[0]=='case'):
            LL = Struct[2]
            for Case in LL:
                PP = Case[1]
                More = scanForRegs(PP)
                for Net in More:
                    if Net not in Regs: Regs.append(Net)
            return Regs
        if (Struct[0]=='for'):
            R1 = Struct[1][1]
            More = scanForRegs(Struct[4])
            return [R1]+More

        logs.log_error('scanForRegs encountered(0) "%s"'%str(Struct))
        
    if type(Struct) in [types.StringType,types.IntType]: return []

    logs.log_error('scanForRegs encountered(1) "%s"'%str(Struct))
    return Regs


     
def notZeroValue(Val):
    if Val=='0': return False
    if Val=='1': return True
    if type(Val) in [types.TupleType,types.ListType]:
        if Val[0]=='bin':
            return notZeroValue(Val[2])
    try:
        X = eval(Val)
        if X!=0: return True
    except:
        return False

VKEYWORDS  = string.split('input output inout') 

def simpleTypes(Mod):
    for Net in Mod.nets:
        if Net in VKEYWORDS:
            AA = Mod.nets.pop(Net)
            Mod.nets[Net+'x']=AA

    for Inst in Mod.insts:
        Obj = Mod.insts[Inst]
        if '.' in Obj.Type:
            wrds = string.split(Obj.Type,'.')
            Obj.Type = wrds[-1]
        for Pin in Obj.conns:
            if Pin in VKEYWORDS:
                Sig = Obj.conns.pop(Pin)
                Obj.conns[Pin+'x']=Sig

    for ind,(Dst,Src,AA,BB) in enumerate(Mod.hard_assigns):
        Dst = renameIt(Dst,Mod)
        Src = renameIt(Src,Mod)
        Mod.hard_assigns[ind]=(Dst,Src,AA,BB)

    for ind,Alw in enumerate(Mod.alwayses):
        Alw = renameIt(Alw,Mod)
        Mod.alwayses[ind]=Alw

def renameIt(What,Mod):
    if type(What)==types.StringType:
        if What in VKEYWORDS:
            return What+'x'
    if type(What)==types.IntType:
        return What
    if type(What)==types.TupleType:
        What = list(What)
        return renameIt(What,Mod)
    if type(What)==types.ListType:
        if (len(What)>1)and(What[0]=='funccall'):
            Func = What[1]
            if Func=='length':
                Net = What[2]
                if Net in Mod.nets:
                    Dir,Wid = Mod.nets[Net]
                    Len = eval(str(Wid[0]))+1
                    return Len
                else:
                    return  ['functioncall','$width',What[1:]]
            return ['functioncall']+What[1:]
        for ind,Item in enumerate(What):
            Item = renameIt(Item,Mod)
            What[ind]=Item
        return What

    return What

