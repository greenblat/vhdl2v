#! /usr/bin/python

TODO = '''
1. make regs
2. recognize always
3. variables in process
'''


import os,sys,string,types
import pickle
import traceback
NewName = os.path.expanduser('~')
sys.path.append('%s/verification_libs'%NewName)

import logs 
import moduleBuilder as mod
import helpers

info = logs.log_info

ENTITIES={}
ARCHITECTURES={}
TYPES = {}
COMPONENTS ={}

DUMMY = [['RRRFFF','Identifier','9999','9999']]

import cleanVhdl
import vyaccer2
import reworkMyLex
import vhdllexer

def main():
    if len(sys.argv)>1:
        Fname = sys.argv[1]
        cleanVhdl.run(Fname)
        vhdllexer.run_lexer('cleaned.vhd','lex.out')
        reworkMyLex.run('lex.out','lex2.out')
        vyaccer2.run_yacc(False,'lex2.out','.','aaa.vhdl')

    info('starting vhdl2v by IliaG 4.sep.2018')
    File = open('db0.pickle')
    Adb = pickle.load(File)
    reportAdb(Adb,'fff0')
    print 'step0'
    cleanComas(Adb)
    reportAdb(Adb,'fff1')
    print 'step1'
    rounds0(Adb)
    reportAdb(Adb,'fff2')
    print 'step2'
    rounds1(Adb)
    reportAdb(Adb,'fff3')
    print 'step3'

    dones = 1
    while dones>0:
        dones = removeUnused(Adb)
    print 'step4'
    scanStuff_new(Adb)
    print 'step5'
    makeVerilog(Adb)
    print 'step6'
    mod.dumpVerilog()
    reportAdb(Adb,'fff4')


def cleanComas(Adb):
    for Key in Adb:
        List = Adb[Key]
        Res = []
        for Item in List:
            if (len(Item)==4)and(Item[0] in ['Comma','Semicolon']):
                pass
            else:
                Res.append(Item)
        Adb[Key]=Res


def rounds0(Adb):
    while True:
        Bef = len(Adb.keys())
        info('rounds0 bef=%d'%Bef)
        oneRound0(Adb)
        Aft = len(Adb.keys())
        info('rounds0 aft %d -> %d'%(Bef,Aft))
        if Aft==Bef: return


def oneRound0(Adb):
    F0,F4 = findEnds(Adb)
    info('oneRound0 f0=%d f4=%d'%(len(F0),len(F4)))
    useF0_F4(Adb,F0,F4)
    return Adb
def useF0_F4(Adb,F0,F4):
    for Key in F0:
        Adb.pop(Key)
    for Key in F4:
        Adb.pop(Key)

    for Key in Adb:
        Old = Adb[Key]
        New = simplify0(Old,F0,F4)
        if New!=Old:
            Adb[Key]=New


def simplify0(Old,F0,F4):
    New = []
    for ind,Key in enumerate(Old):
        if Key not in F0:
            New.append(Key)
            
#    for Key in F0:
#        if Key in New:
#            Ind = New.index(Key)
#            New.pop(Ind)

    for ind,Key in enumerate(New):
        if Key in F4:
            New[ind]=F4[Key]
            
#    for Key in F4:
#        if Key in New:
#            Ind = New.index(Key)
#            New[Ind]=F4[Key]
    return New

def removeUnused(Adb):
    Defined=[]
    Used=[]
    dones = 0
    for Key in Adb.keys():
        Defined.append(Key)
        List = Adb[Key]
        for Item in List:
            if len(Item)==2:
                Used.append(Item)
    for Key in Defined:
        if Key not in Used:
            if Key[0] !='design_file':
                Adb.pop(Key)
                dones += 1
    info('removeUnused %d'%dones)
    return dones



def findEnds(Adb):
    F4 = {}
    F0 = []
    for Key in Adb.keys():
        if Key[0] not in ['enumeration_literal','...enumeration_literal..']:
            Val = Adb[Key]
            if (len(Val)==1)and(len(Val[0])==4):
                F4[Key] = Val[0]
            if (Val==[]):
                F0.append(Key)
    return F0,F4

def rounds1(Adb):
    while True:
        Bef = len(Adb.keys())
        doTwos(Adb)
        Aft = len(Adb.keys())
        info('rounds1 bef=%d aft=%d'%(Bef,Aft))
        if Aft==Bef: return

def findOnes(Adb):
    F2 = {}
    for Key in Adb.keys():
        Val = Adb[Key]
        if (len(Val)==1)and(len(Val[0])==2):
            F2[Val[0]] = Key
    return F2

def doTwos(Adb):
    F2 = findOnes(Adb)
    Del = []
    for Key in Adb.keys():
        if Key in F2:
            Val = Adb[Key]
            if (len(Val)>1):
                Bef = F2[Key]
                Adb[Bef]=Val
                Del.append(Key)
    for Bef in Del:
        Adb.pop(Bef)




def scanStuff_new(Adb):
    RootKey =  ('design_file', 1)
    if RootKey not in Adb:
        logs.log_error('no design file found')
        return
    Root = Adb[ ('design_file', 1)]
    scanStuff_deep(Root,Adb)

def scanStuff_deep(Root,Adb):
    if (type(Root)==types.TupleType) and (Root in Adb):
        workOnItem(Root,Adb)
    else:
        for Item in Root:
            scanStuff_deep(Item,Adb)


def workOnItem(Item,Adb):
    if type(Item)==types.ListType:
        List = Item
    else:
        List = Adb[Item]
    if matches(List,"!design_unit !..design_unit.."):
        workOnItem(List[0],Adb)
        workOnItem(List[1],Adb)
    elif matches(List,"!..context_item.. !context_item"):
        workOnItem(List[0],Adb)
        workOnItem(List[1],Adb)
    elif matches(List,"!context_clause !library_unit"):
        workOnItem(List[0],Adb)
        workOnItem(List[1],Adb)
    elif matches(List,"LIBRARY ?"):
        pass
    elif matches(List,"USE ?"):
        pass
    else: 
        Vars = matches(List,'ARCHITECTURE ? OF ? IS BEGIN_ !architecture_statement_part END')
        if Vars:
            architecture_new(1,Vars,Adb)
            return

        Vars = matches(List,'ARCHITECTURE ? OF ? IS !architecture_declarative_part BEGIN_ !architecture_statement_part END')
        if Vars:
            architecture_new(0,Vars,Adb)
            return

        Vars = matches(List,'ENTITY ? IS !.generic_clause. !.port_clause. END')
        if Vars:
            entity_new(0,Vars,Adb)
            return

        Vars = matches(List,'ENTITY ? IS !.port_clause. END')
        if Vars:
            entity_new(1,Vars,Adb)
            return

        Vars = matches(List,'PACKAGE ? IS !package_declarative_part END')
        if Vars:
            package_new(Vars,Adb)
            return
        Vars = matches(List,'PACKAGE BODY ? IS !package_body_declarative_part END ?')
        if Vars:
            package_new(Vars,Adb)
            return
        logs.log_error('dont know to treat "%s"'%str(List))
    

def package_new(Vars,Adb):
    Package = Vars[0][0]
    LL = getList_new(Adb[Vars[1]],Adb)
    for ind,Item in enumerate(LL):
        info('package_new %s %d %s'%(Package,ind,Item))

def entity_new(Kind,Vars,Adb):
    if Kind==0:
        Gmatch = matches(Adb[Vars[1]],'GENERIC LeftParen !formal_generic_list RightParen')
        if Gmatch:
            Glist = getList_new(Adb[Gmatch[0]],Adb)

        Pmatch = matches(Adb[Vars[2]],'PORT LeftParen !formal_port_list RightParen')
        if Pmatch:
            Plist = getList_new(Adb[Pmatch[0]],Adb)
        ENTITIES[Vars[0][0]] = (Glist,Plist)
    elif Kind==1:
        Pmatch = matches(Adb[Vars[1]],'PORT LeftParen !formal_port_list RightParen')
        if Pmatch:
            Plist = getList_new(Adb[Pmatch[0]],Adb)
        ENTITIES[Vars[0][0]] = ([],Plist)
    else:
        log.log_error('entity kind missing %s'%Kind)
TRACE = []
def getList_new(Item,Adb):
    TRACE.append(Item)
    Res = getList_new__(Item,Adb)
#    checkList(Res)
    TRACE.pop(-1)
    return Res

CHECKGOODS = string.split('enumlit generic_map if signal_list else case wait input output port_map std_logic_vector integer unsigned port boolean')
def checkList(Res):
    if (type(Res)==types.TupleType):
        if len(Res)==4:
            if Res[1] in ['Identifier']:
                logs.log_error('checkList(1) got "%s"'%str(Res),True)
                print traceback.print_stack()
                return
        if len(Res)==2:
            if (Res[0] not in CHECKGOODS)and(type(Res[0])!=types.IntType):
                logs.log_error('checkList(2) got "%s"'%str(Res),True)
                print traceback.print_stack()
                return
    if (type(Res)==types.ListType):
        for Item in Res:
            checkList(Item)
    if (type(Res)==types.TupleType):
        for Item in Res:
            checkList(Item)


def getList_new__(Item,Adb):
    Vars = matches(Item,'!formal_generic_element !...formal_generic_element..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return [AA]+BB

    Vars = matches(Item,'!local_generic_element !...local_generic_element..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return [AA]+BB

    Vars = matches(Item,'!...formal_generic_element.. !formal_generic_element')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+[BB]
    Vars = matches(Item,'!...local_generic_element.. !local_generic_element')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+[BB]

    Vars = matches(Item,'!formal_port_element !...formal_port_element..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return [AA]+BB

    Vars = matches(Item,'!local_port_element !...local_port_element..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        LL = AA+BB
        return LL
    Vars = matches(Item,'!...local_port_element.. !local_port_element')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+BB

    Vars = matches(Item,'!...formal_port_element.. !formal_port_element')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        LL =  AA+BB
        return LL


    Vars = matches(Item,'!..block_declarative_item.. !block_declarative_item')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+[BB]

    Vars = matches(Item,'!concurrent_statement !..concurrent_statement..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return [AA]+BB

    Vars = matches(Item,'!association_element !...association_element..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return [AA]+BB
    Vars = matches(Item,'!sequential_statement !..sequential_statement..')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        CC = mergeToList([AA],BB)
        return CC

    Vars = matches(Item,'RETURN ?')
    if Vars:
        Ret = getExpr(Vars[0],Adb)
        return [('return',Ret)]

    Vars = matches(Item,'!..process_declarative_item.. !process_declarative_item')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+[BB]
    Vars = matches(Item,'!..case_statement_alternative..  !case_statement_alternative')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+BB


    Vars = matches(Item,'!..package_body_declarative_item..  !package_body_declarative_item')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+BB

    Vars = matches(Item,'!..package_declarative_item..  !package_declarative_item')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        return AA+BB

    Vars = matches(Item,'SUBTYPE ? IS !subtype_indication')
    if Vars:
        Name = Vars[0][0]
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        return [('subtype',Name,Subtype)]
        

    Vars = matches(Item,'FUNCTION ? !.function_parameter_list. RETURN ?')
    if Vars:
        Func = Vars[0][0]
        Params = getList_new(Adb[Vars[1]],Adb)
        What = getExpr(Vars[2],Adb)
        return [('function',Func,Params,What)]
    Vars = matches(Item,'!subprogram_specification IS !subprogram_declarative_part BEGIN_ !sequence_of_statements END')
    if Vars:
        Sub = getList_new(Adb[Vars[0]],Adb)
        Decl = getList_new(Adb[Vars[1]],Adb)
        Seq = getList_new(Adb[Vars[2]],Adb)
        return [('subprogram',Sub,Decl,Seq)]

    Vars = matches(Item,'!a_label !unlabeled_process_statement')
    if Vars:
        AA = getList_new(Adb[Vars[1]],Adb) 
        Label = getLabel(Adb[Vars[0]],Adb)
        if len(AA)==1: AA=AA[0]
        return [('process',Label,AA[1],AA[2],AA[3])]


    Vars = matches(Item,'!a_label !unlabeled_generate_statement')
    if Vars:
        AA = getList_new(Adb[Vars[1]],Adb) 
        Label = getLabel(Adb[Vars[0]],Adb)
        return [('generate',Label,AA)]

    Vars = matches(Item,'? <= !waveform')
    if Vars:
        Expr = getExpr(Adb[Vars[1]],Adb)
        Dst = getExpr(Vars[0],Adb)
        return [('<=',Dst,Expr)]


    Vars = matches(Item,'RECORD !element_declaration !..element_declaration.. END RECORD')
    if Vars:
        AA = getRecordElem(Adb[Vars[0]],Adb) 
        BB = getList_new(Adb[Vars[1]],Adb)
        return [('record',[AA]+BB)]

    Vars = matches(Item,'RECORD !element_declaration END RECORD')
    if Vars:
        BB = getRecordElem(Adb[Vars[0]],Adb)
        return [('record',[BB])]

    Vars = matches(Item,'!..element_declaration.. !element_declaration')
    if Vars:
        AA = getList_new(Adb[Vars[0]],Adb) 
        BB = getRecordElem(Adb[Vars[1]],Adb)
        return AA+[BB]

    Vars = matches(Item,'ALIAS ? Colon ? IS ?')
    if Vars:
        Alias = getExpr(Vars[0],Adb)
        Type = getExpr(Vars[1],Adb)
        Is = getExpr(Vars[2],Adb)
        return [('alias',Alias,Type,Is)]
        


    Vars = matches(Item,'? <= !..waveform__WHEN__condition__ELSE.. ?')
    if Vars:
        Dst = getExpr(Vars[0],Adb)
        Expr = getExpr(Adb[Vars[1]],Adb)
        Else = getExpr(Vars[2],Adb)
        Expr = ['question',Expr,Else]
        Expr = reworkWHENELSE(Expr)
        return [('<=',Dst,Expr)]


    Vars = matches(Item,'? => ?')
    if Vars:
        Expr = getExpr(Vars[1],Adb)
        return [('=>',Vars[0][0],Expr)]

    Vars = matches(Item,'? <= ?')
    if Vars:
        Dst = getExpr(Vars[0],Adb)
        Src = getExpr(Vars[1],Adb)
        return [('<=',Dst,Src)]

    Vars = matches(Item,'!generation_scheme GENERATE !set_of_statements END GENERATE')
    if Vars:
        LL = getList_new(Adb[Vars[1]],Adb)
        What = Adb[Vars[0]]
        if What[0][0]=='FOR':
            if What[1] in Adb:
                X = [('FOR','FOR',0,0)]+Adb[What[1]]
                Sch = getExpr(X,Adb)
            else:
                Sch = getList_new(What[1],Adb)
        else:            
            Sch = getList_new(Adb[Vars[0]],Adb)
        return [('generate',Sch,LL)]

    Vars = matches(Item,'? Colon ? !.constraint. !.VarAsgn__expression.')
    if Vars:
        Expr2 = getVarAsgn(Adb[Vars[2]],Adb)
        Expr3 = getVarAsgn(Adb[Vars[3]],Adb)
        logs.log_info('420 vars %s   expr2=%s expr3=%s'%(str(Vars),Expr2,Expr3))
        return []

    Vars = matches(Item,'? Colon ? !.VarAsgn__expression.')
    if Vars:
        Expr = getVarAsgn(Adb[Vars[2]],Adb)
        return [('var_assign',Vars[0][0],Vars[1][0],Expr)]

#    Vars = matches(Item,'? Colon IN std_logic')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('input',LL,0)]
#
#    Vars = matches(Item,'? Colon BUFFER std_logic')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('output',LL,0)]
#
#    Vars = matches(Item,'? Colon OUT std_logic')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('output',LL,0)]

    Vars = matches(Item,'? Colon ?dir  ?wire  !.constraint.')
    if Vars:
        LL = getExpr(Vars[0],Adb)
        Dir = helpers.verilogDir[Vars[1]]
        return [(Dir,LL,getConstraint(Adb[Vars[3]],Adb))]

#    Vars = matches(Item,'? Colon INOUT std_logic_vector !.constraint.')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('output',LL,getConstraint(Adb[Vars[1]],Adb))]
#
#    Vars = matches(Item,'? Colon BUFFER std_logic_vector !.constraint.')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('output',LL,getConstraint(Adb[Vars[1]],Adb))]
#
#
#    Vars = matches(Item,'? Colon IN std_logic_vector !.constraint.')
#    if Vars:
#        LL = getExpr(Vars[0],Adb)
#        return [('input',LL,getConstraint(Adb[Vars[1]],Adb))]

    Vars = matches(Item,'? Colon ?dir ?')
    if Vars:
        LL = getExpr(Vars[0],Adb)
        Dir = helpers.verilogDir[Vars[1]]
        Kind = getExpr(Vars[2],Adb)
        return [(Dir,LL,Kind)]

    Vars = matches(Item,'SIGNAL ? Colon ? !.VarAsgn__expression.')
    if Vars:
        return [('signal',getExpr(Vars[0],Adb),getExpr(Vars[1],Adb),getVarAsgn(Adb[Vars[2]],Adb))]

    Vars = matches(Item,'SIGNAL ? Colon !subtype_indication')
    if Vars:
        Signal = getExpr(Vars[0],Adb)
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        return [('signal',Signal,Subtype)]
    Vars = matches(Item,'SIGNAL ? Colon ?')
    if Vars:
        Signal = getExpr(Vars[0],Adb)
        return [('signal',Signal,Vars[1][0])]


    Vars = matches(Item,'Constant ? Colon ? !.VarAsgn__expression.')
    if Vars:
        return [('constant',Vars[0][0],getExpr(Vars[1],Adb),getVarAsgn(Adb[Vars[2]],Adb))]

    Vars = matches(Item,'!a_label ENTITY ? !.generic_map_aspect. !.port_map_aspect.')
    if Vars:
        Label = getLabel(Adb[Vars[0]],Adb)
        What = Vars[1][0]
        Gens = getList_new(Adb[Vars[2]],Adb)
        Ports = getList_new(Adb[Vars[3]],Adb)
        return [('instance',Label,What,Gens,Ports)]

    Vars = matches(Item,'!a_label ENTITY ? !.port_map_aspect.')
    if Vars:
        Label = getLabel(Adb[Vars[0]],Adb)
        What = Vars[1][0]
        Ports = getList_new(Adb[Vars[2]],Adb)
        return [('instance',Label,What,[],Ports)]

    Vars = matches(Item,'!a_label ? !.generic_map_aspect. !.port_map_aspect.')
    if Vars:
        Label = getLabel(Adb[Vars[0]],Adb)
        What = Vars[1][0]
        Gens = getList_new(Adb[Vars[2]],Adb)
        Ports = getList_new(Adb[Vars[3]],Adb)
        return [('instance',Label,What,Gens,Ports)]

    Vars = matches(Item,'GENERIC MAP LeftParen !association_list RightParen')
    if Vars:
        LL = getList_new(Adb[Vars[0]],Adb)
        return [('generic_map',LL)]

    Vars = matches(Item,'!a_label ? !.port_map_aspect.')
    if Vars:
        Label = getLabel(Adb[Vars[0]],Adb)
        LL = getList_new(Adb[Vars[2]],Adb)
        return [('instance',Label,Vars[1][0],[],LL)]

    Vars = matches(Item,'PORT MAP LeftParen !association_list RightParen')
    if Vars:
        LL = getList_new(Adb[Vars[0]],Adb)
        return [('port_map',LL)]

    Vars = matches(Item,'PORT LeftParen !local_port_list RightParen')
    if Vars:
        LL = getList_new(Adb[Vars[0]],Adb)
        return LL


    Vars = matches(Item,'LeftParen !signal_list RightParen')
    if Vars:
        LL = getList_new(Adb[Vars[0]],Adb)
        return [('signal_list',LL)]

    Vars = matches(Item,'!...enumeration_literal.. !enumeration_literal' )
    if Vars:
        AA = getExpr(Vars[1],Adb)
        BB = getList_new(Adb[Vars[0]],Adb)
        LL = mergeToList(BB,[AA],'enumlit')
        return LL

    if Item==[]: return []


    Vars = matches(Item,'LeftParen !enumeration_literal !...enumeration_literal.. RightParen')
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        LL = mergeToList([AA],BB,'enumlit')
        return LL
    
    Vars = matches(Item,'LeftParen ? !...enumeration_literal.. RightParen')
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        LL = mergeToList([AA],BB,'enumlit')
        return LL
    Vars = matches(Item,'!...enumeration_literal.. ?')
    if Vars:
        AA = getExpr(Vars[1],Adb)
        BB = getList_new(Adb[Vars[0]],Adb)
        LL = mergeToList(BB,[AA],'enumlit')
        return LL

    Vars = matches(Item,'LeftParen ? RightParen')
    if Vars:
        LL = getExpr(Vars[0],Adb)
        return [LL]

    Vars = matches(Item,'WAIT !.condition_clause.')
    if Vars:
        LL = getExpr(Adb[Vars[0]],Adb)
        return [('wait',LL)]

    Vars = matches(Item,'CASE !expression IS !case_statement_alternative  !..case_statement_alternative.. END CASE')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL0 = getList_new(Adb[Vars[1]],Adb)
        LL1 = getList_new(Adb[Vars[2]],Adb)
        CC = mergeToList(LL0,LL1)
        return [('case',Cond,CC)]

    Vars = matches(Item,'CASE ? IS !case_statement_alternative  !..case_statement_alternative.. END CASE')
    if Vars:
        Cond = getExpr(Vars[0],Adb)
        LL0 = getList_new(Adb[Vars[1]],Adb)
        LL1 = getList_new(Adb[Vars[2]],Adb)
        CC = mergeToList(LL0,LL1)
        return [('case',Cond,CC)]


    Vars = matches(Item,'IF !condition')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        return [('if',Cond)]

    Vars = matches(Item,'IF !condition THEN END IF')
    if Vars:
        return []

    Vars = matches(Item,'IF !condition THEN !sequence_of_statements END IF')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL = getList_new(Adb[Vars[1]],Adb)
        LL = listify(LL)
        return [('if',Cond,LL)]

    Vars = matches(Item,'ELSIF ? THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts..')
    if Vars:
        Cond = getExpr(Vars[0],Adb)
        LL0 = getList_new(Adb[Vars[1]],Adb)
        LL1 = getList_new(Adb[Vars[2]],Adb)
        LL0 = listify(LL0)
        LL1 = listify(LL1)
        return [('ifelse',Cond,LL0,LL1)]

    Vars = matches(Item,'ELSIF ? THEN !sequence_of_statements')
    if Vars:
        Cond = getExpr(Vars[0],Adb)
        LL0 = getList_new(Adb[Vars[1]],Adb)
        LL0 = listify(LL0)
        return [('ifelse',Cond,LL0)]

    Vars = matches(Item,'WHEN OTHERS =>')
    if Vars:
        return [('case','default')]
    Vars = matches(Item,'WHEN OTHERS => Null')
    if Vars:
        return [('case','default')]

    Vars = matches(Item,'WHEN ? => !sequence_of_statements')
    if Vars:
        Cond = getExpr(Vars[0],Adb)
        LL0 = getList_new(Adb[Vars[1]],Adb)
        return [['case',Cond,LL0]]
    Vars = matches(Item,'? := ?')
    if Vars:
        Dst = getExpr(Vars[0],Adb)
        Src = getExpr(Vars[1],Adb)
        return [(':=',Dst,Src)]

    Vars = matches(Item,'IF !condition THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts.. !.ELSE__seq_of_stmts. END IF')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL0 = listify(getList_new(Adb[Vars[1]],Adb))
        LL1 = listify(getList_new(Adb[Vars[2]],Adb))
        LL2 = listify(getList_new(Adb[Vars[3]],Adb))
        return [('ifelse',Cond,LL0,LL1,LL2)]

    Vars = matches(Item,'IF !condition THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts.. END IF')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL0 = listify(getList_new(Adb[Vars[1]],Adb))
        LL1 = listify(getList_new(Adb[Vars[2]],Adb))
        return [('ifelse',Cond,LL0,LL1)]

    Vars = matches(Item,'IF !condition THEN !sequence_of_statements !.ELSE__seq_of_stmts. END IF')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL0 = listify(getList_new(Adb[Vars[1]],Adb))
        LL1 = listify(getList_new(Adb[Vars[2]],Adb))
        return [('ifelse',Cond,LL0,LL1)]

    Vars = matches(Item,'IF !condition THEN !sequence_of_statements ELSE  END IF')
    if Vars:
        Cond = getExpr(Adb[Vars[0]],Adb)
        LL0 = listify(getList_new(Adb[Vars[1]],Adb))
        return [('if',Cond,LL0)]


    Vars = matches(Item,'ELSE !sequence_of_statements')
    if Vars:
        LL0 = listify(getList_new(Adb[Vars[0]],Adb))
        return [('else',LL0)]

    Vars = matches(Item,'VARIABLE ? Colon !subtype_indication')
    if Vars:
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        return [('variable',Vars[0][0],Subtype)]

    Vars = matches(Item,'VARIABLE ? Colon !subtype_indication !.VarAsgn__expression.')
    if Vars:
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        Assign = getExpr(Adb[Vars[2]],Adb)
        return [('variable',Vars[0][0],Subtype,Assign)]

    Vars = matches(Item,'VARIABLE ? Colon ?')
    if Vars:
        Expr = getExpr(Vars[1],Adb)
        return [('variable',Vars[0][0],Expr)]

    Vars = matches(Item,'GENERIC LeftParen !local_generic_list RightParen')
    if Vars:
        return getList_new(Adb[Vars[0]],Adb)

    Vars = matches(Item,'COMPONENT ? !.GENERIC__local_generic_list. !.PORT__local_port_list.  END COMPONENT')
    if Vars:
        Gens = getList_new(Adb[Vars[1]],Adb)
        Conns = getList_new(Adb[Vars[2]],Adb)
        if Conns[0]=='port': Conns.pop(0)
        COMPONENTS[Vars[0][0]] = (Conns,Gens)
        return []

    Vars = matches(Item,'COMPONENT ? !.PORT__local_port_list.  END COMPONENT')
    if Vars:
        Conns = getList_new(Adb[Vars[1]],Adb)
        if Conns[0]=='port': Conns.pop(0)
        COMPONENTS[Vars[0][0]] = (Conns,[])
        return []

    Vars = matches(Item,'PROCESS !.sensitivity_list. BEGIN_ !sequence_of_statements END PROCESS')
    if Vars:
        Sense = getList_new(Adb[Vars[0]],Adb)
        Stats = getList_new(Adb[Vars[1]],Adb)
        return [('process',[],Sense,Stats)]

    Vars = matches(Item,'PROCESS !.sensitivity_list. !process_declarative_part BEGIN_ !sequence_of_statements END PROCESS')
    if Vars:
        Sense = getList_new(Adb[Vars[0]],Adb)
        Declares = getList_new(Adb[Vars[1]],Adb)
        Stats = getList_new(Adb[Vars[2]],Adb)
        return [('process',Declares,Sense,Stats)]

    Vars = matches(Item,'PROCESS !process_declarative_part BEGIN_ !sequence_of_statements END PROCESS')
    if Vars:
        Declares = getList_new(Adb[Vars[0]],Adb)
        Stats = getList_new(Adb[Vars[1]],Adb)
        return [('process',Declares,[],Stats)]

    Vars = matches(Item,'ASSERT ? ? ?')
    if Vars:
#        A = getExpr(Vars[0],Adb)
#        B = getExpr(Vars[1],Adb)
#        C = getExpr(Vars[2],Adb)
#        return [['comment',A,B,C]]
        return ['comment','assert']

    Vars = matches(Item,'ARRAY LeftParen !index_subtype_definition  RightParen OF !subtype_indication')
    if Vars:
        Index = getConstraint(Adb[Vars[0]],Adb)
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        logs.log_info('subtype %s'%(str(Subtype)))
        return [('array',Index,Subtype)]
    Vars = matches(Item,'ARRAY LeftParen !index_subtype_definition  RightParen OF ?')
    if Vars:
        Index = getConstraint(Adb[Vars[0]],Adb)
        Subtype = getExpr(Vars[1],Adb)
        return [('array',Index,Subtype)]

    Vars = matches(Item,'ARRAY !index_constraint OF !subtype_indication')
    if Vars:
        Index = getConstraint(Adb[Vars[0]],Adb)
        Subtype = getSubtype(Adb[Vars[1]],Adb)
        return [('array',Index,Subtype)]

    Vars = matches(Item,'ARRAY !index_constraint OF ?')
    if Vars:
        Index = getConstraint(Adb[Vars[0]],Adb)
        Subtype = getExpr(Vars[1],Adb)
        return [('array',Index,Subtype)]

    Vars = matches(Item,'!.iteration_scheme. LOOP !sequence_of_statements END LOOP')
    if Vars:
        II = getExpr(Adb[Vars[0]],Adb)
        Seq = getList_new(Adb[Vars[1]],Adb)
        return [('loop',II,Seq)]

    Vars = matches(Item,'TYPE ? IS !type_definition')
    if Vars:
        LL = getList_new(Adb[Vars[1]],Adb)
        Name = Vars[0][0]
        TYPES[Name]=LL
        return [('type',Vars[0][0],LL)]

    Vars = matches(Item,'? !...name..')
    if Vars:
        Expr = getExpr(Vars[0],Adb)
        LL = getList_new(Adb[Vars[1]],Adb)
        return [Expr]+LL

    Vars = matches(Item,'? !...association_element..')
    if Vars:
        LL = getList_new(Adb[Vars[1]],Adb)
        return [['assoc',Vars[0][0]]]+LL

    Vars = matches(Item,'!...name.. ?')
    if Vars:
        LL = getList_new(Adb[Vars[0]],Adb)
        Expr = getExpr(Vars[1],Adb)
        return LL+[Expr]

    Vars = matches(Item,'? Colon ?')
    if Vars:
        return [('definition',Vars[0][0],Vars[1][0])]
    Vars = matches(Item,'? ?')
    if Vars:
        return [getExpr(Vars[0],Adb),getExpr(Vars[1],Adb)]


    logs.log_error('getList_new failed on "%s"'%str(Item))
    reportTrace(TRACE)
    return []

def getRecordElem(List,Adb): 
    Vars = matches(List,'? Colon ?')
    Name = getExpr(Vars[0],Adb)
    Kind = getExpr(Vars[1],Adb)
    return (Name,Kind)

def getSubtype(List,Adb):
    Vars = matches(List,'unsigned !.constraint.')
    if Vars:
        LL = getConstraint(Adb[Vars[0]],Adb)
        return ('unsigned',LL)
    Vars = matches(List,'std_logic_vector !.constraint.')
    if Vars:
        LL = getConstraint(Adb[Vars[0]],Adb)
        return ('std_logic_vector',LL)
    Vars = matches(List,'integer !.constraint.')
    if Vars:
        LL = getConstraint(Adb[Vars[0]],Adb)
        return ('integer',LL)
        
    Vars = matches(List,'? !.constraint.')
    if Vars:
        Type = Vars[0][0]
        LL = getConstraint(Adb[Vars[1]],Adb)
        print 'type',Type,TYPES.keys(),LL
        if Type in TYPES:
            Base = TYPES[Type]
            LL = getConstraint(Adb[Vars[1]],Adb)
            return (Base,LL)
            


    logs.log_error('getSubtype got "%s"'%(str(List)))
    print traceback.print_stack()
    return 'badSubType'

def getLabel(List,Adb):
    if matches(List,'? Colon'):
        return List[0][0]
    logs.log_error('getLabel got "%s"'%(str(List)))
    return 'badLabel'



def getVarAsgn(List,Adb):
    Vars = matches(List,':= ?')
    if Vars:
        Item = Vars[0]
        Expr = getExpr(Item,Adb)
        return Expr
    logs.log_error('getVarAsgn failed on "%s"'%(str(List)))
    return 0

def getConstraint(List,Adb):
    Vars = matches(List,'LeftParen !element_association RightParen')
    if Vars:
        List2 = Adb[Vars[0]]
        Vars2 = matches(List2,'? DOWNTO ?')
        if Vars2:
            return (getExpr(Vars2[0],Adb),getExpr(Vars2[1],Adb))
        else:
            Vars2 = matches(List2,'? TO ?')
            if Vars2:
                return (getExpr(Vars2[0],Adb),getExpr(Vars2[1],Adb))
            else:
                logs.log_error('getConstraint of ( ? ) failed on %s'%str(List2))
    Vars = matches(List,'natural RANGE <>')
    if Vars:
        return ['natural']
    Vars = matches(List,'RANGE !range')
    if Vars:
        Range = Adb[Vars[0]]
        Vars2 = matches(Range,'? TO ?')
        return [('range',Vars2[0][0],Vars2[1][0])]
        
    Vars = matches(List,'LeftParen !discrete_range RightParen')
    if Vars:
        Range = Adb[Vars[0]]
        Vars2 =  matches(Range,'? TO ?')
        if Vars2:
            From = getExpr(Vars2[0],Adb)
            To = getExpr(Vars2[1],Adb)
            return ('range',From,To)
        Vars2 =  matches(Range,'? DOWNTO ?')
        if Vars2:
            From = getExpr(Vars2[0],Adb)
            To = getExpr(Vars2[1],Adb)
            return ('range',From,To)

        logs.log_error('discrete range %s'%(Range))
        return 0

    logs.log_error('getConstraint failed on %s'%(List))
    return 0


def architecture_new(Kind,Vars,Adb):
    if Kind==0:
        Module = Vars[1][0]
        Part0 = getList_new(Adb[Vars[2]],Adb)
        Part1 = getList_new(Adb[Vars[3]],Adb)
        ARCHITECTURES[Module]=(Part0,Part1)
        return
    if Kind==1:
        Module = Vars[1][0]
        Part0 = []
        Part1 = getList_new(Adb[Vars[2]],Adb)
        ARCHITECTURES[Module]=(Part0,Part1)
        return

    logs.log_error('architecture_new kind=%d'%Kind)

def makeVerilog(Adb):
    makeVerilogEntities()
    makeVerilogArchs(Adb)

def unfoldList(Item):
    if (type(Item)==types.ListType)and(len(Item)==1):
        return Item[0]
    return Item
    

def makeVerilogEntities():
    for Module in ENTITIES:
        mod.addModule(Module)
        Glist,Plist = ENTITIES[Module]
        for Item in Glist:
            Item = unfoldList(Item)
            if len(Item)>1:
                mod.addModuleParam(Item[1],0)
        for Item in Plist:
            if len(Item)==1: Item = Item[0]
            try:
                Dir = Item[0]
                Net = Item[1]
                Wid = Item[2]
                try:
                    mod.addWire(Net,Dir,Wid)
                except:
                    logs.log_error('addWire failed "%s %s %s"'%(Dir,Net,Wid))
                    
            except:
                logs.log_error('item in plist is "%s"'%str(Item))

def makeVerilogArchs(Adb):
    for Module in ARCHITECTURES:
        L1,L2 = ARCHITECTURES[Module]
        treatSignals(L1,Module,Adb)
        treatBody(L2,Module)

def treatBody(L2,Module):
    for Item in L2:
        if len(Item)==1: Item=Item[0]
        if Item[0]=='assign':
            mod.addHardAssign(Item[1],Item[2])
        elif Item[0]=='<=':
            mod.addHardAssign(Item[1],Item[2])
        elif Item[0]=='instance':
            Inst = Item[1]
            Type = Item[2]
            Gens = Item[3]
            Ports = Item[4]
            if len(Gens)==1: Gens=Gens[0]
            if len(Ports)==1: Ports=Ports[0]
            if (len(Gens)>0)and(Gens[0]=='generic_map'): Gens = Gens[1]
            if Ports[0]=='port_map': Ports=Ports[1]
            mod.addInstance(Inst,Type)
            for PV in Gens:
                if len(PV)==1: PV=PV[0]
                if PV[0]=='=>':
                    mod.add_instance_param(Inst,PV[1],PV[2])
                else:
                    logs.log_error('add_param_inst failed on "%s"'%(str(PV)))
            if Type in COMPONENTS:
                Pins = COMPONENTS[Type][0]
            else:
                Pins = []
            for ind,PV in enumerate(Ports):
                if len(PV)==1: PV=PV[0]
                if PV[0]=='=>':
                    mod.add_conn(Inst,PV[1],PV[2])
                elif (type(PV)==types.StringType):
                    if ind<len(Pins):
                        Pin = Pins[ind][1]
                        mod.add_conn(Inst,Pin,PV)
                    else:
                        logs.log_error('connection #%d (%d)  does not exist in %s %s (%s)'%(ind,len(Pins),Type,Inst,PV))
                elif (PV[0]=='assoc'):
                    if ind<len(Pins):
                        Pin = Pins[ind][1]
                        mod.add_conn(Inst,Pin,PV[1])
                    else:
                        logs.log_error('connection #%d (%d)  does not exist in %s %s (%s)'%(ind,len(Pins),Type,Inst,PV))
                elif (PV[0] in ['bin','hex']):
                    if ind<len(Pins):
                        Pin = Pins[ind][1]
                        mod.add_conn(Inst,Pin,PV)
                    else:
                        logs.log_error('connection #%d (%d)  does not exist in %s %s (%s)'%(ind,len(Pins),Type,Inst,PV))
                    
                else:
                    logs.log_error('add_conn failed on %s %s "%s"'%(Inst,Type,str(PV)))
        elif Item[0]=='process':
            Stop=False
            if len(Item)==4:
                Label = ''
                Variables = getVarsList('',Item[1])
                Sense = getSenseList(Item[2])
                Flow = getProcessBody(Item[3])
                addAlways([],['list']+Sense,Flow)
                Stop=True
            elif len(Item)==5:
                Label = Item[1]
                Variables = getVarsList('',Item[2])
                Sense = getSenseList(Item[3])
                Flow = getProcessBody(Item[4])
                Flow = useRenames(Variables,Flow)
                addAlways([],['list']+Sense,Flow)
                Stop=True
            elif len(Item)==3:
                Body0 = Item[2]
            else:
                logs.log_error('process has %d len'%len(Item))
                Stop=True

            if (not Stop):
                if len(Body0)==0:
                    logs.log_error('process "%s" has no body'%str(Label))
                    Body = []
                else:
                    Body = Body0[0]
                if len(Body)==4:
                    Newvars = getNewVars(Body[1])
                    Sense = getSenseList(Body[2])
                    Flow = getProcessBody(Body[3])
                    addAlways(Newvars,['list']+Sense,Flow)
                else:
                    logs.log_error('process "%s" body has %d len'%(Label,len(Body)))
        elif Item[0]=='generate':
            Label = Item[1]
            try:
                Cond = Item[2][0][1]
                Body = Item[2][0][2]
                Flow = treatGenBody(Body)
                mod.addGenerate(Cond,Flow)
            except:
                logs.log_error('FAILED! generate %s %s '%(Label,Item))
        else:
            logs.log_error('treatBody failed on "%s"'%(str(Item)))


def treatGenBody(Body):
    LL = []
    for Item in Body:
        if Item[0]=='process':
            Stop=False
            if len(Item)==4:
                Label = ''
                Variables = getVarsList('',Item[1])
                Sense = getSenseList(Item[2])
                Flow = getProcessBody(Item[3])
                LL.append(['always',[],['list']+Sense,Flow])
                Stop=True
            elif len(Item)==5:
                Label = Item[1]
                Variables = getVarsList('',Item[2])
                Sense = getSenseList(Item[3])
                Flow = getProcessBody(Item[4])
                Flow = useRenames(Variables,Flow)
                LL.append(['always',[],['list']+Sense,Flow])
                Stop=True
            elif len(Item)==3:
                Body0 = Item[2]
            else:
                logs.log_error('process has %d len'%len(Item))
                Stop=True

            if (not Stop):
                if len(Body0)==0:
                    logs.log_error('process "%s" has no body'%str(Label))
                    Body = []
                else:
                    Body = Body0[0]
                if len(Body)==4:
                    Newvars = getNewVars(Body[1])
                    Sense = getSenseList(Body[2])
                    Flow = getProcessBody(Body[3])
                    LL.append(['always',Newvars,['list']+Sense,Flow])
                else:
                    logs.log_error('process "%s" body has %d len'%(Label,len(Body)))
            
        else:
            logs.log_error('treatGenBody failed item on "%s"'%str(Item))
    logs.log_error('treatGenBody failed on "%s"'%str(Body))
    return LL



def addAlways(Vars,Sense,Body):  
    mod.addAlways([Sense,Body,'always'])

def getNewVars(List):
    if List==[]: return []
    res= []
    for Item in List:
        if len(Item)==1:
            Item = Item[0]
        if Item[0]=='variable':
            Name = Item[1]
            Kind = Item[2][0]
            Wid = Item[2][1]
            res.append((Name,Kind,Wid))
        else:
            logs.log_error('getNewVars got %s'%str(Item))
    return res
    logs.log_error('getNewVars %s'%str(List))
    return []

def getVarsList(Label,List):
    LL = []
    for Item in List:
        if (type(Item)==types.ListType)and(len(Item)==1): Item=Item[0]
        if (len(Item)>0)and(Item[0]=='variable'):
            addWire(Label+Item[1],Item[2])
            if Label!='':
                LL.append((Item[1],Label+'_'+Item[1]))
        else:
            logs.log_error('getVarsList item=%s'%str(Item))
    return LL

def getSenseList(List):
    LL = []
    for Item in List:
        if type(Item)==types.StringType:
            LL.append(Item)
        elif Item[0]=='signal_list':
            More = getSenseList(Item[1])
            LL.extend(More)
        elif Item[0]=='subbit':
            LL.append(Item[1])
        else:
            logs.log_error('getSenseList got %s'%str(List))
    return LL

def getProcessBody(List):
    return List




def treatSignals(L1,Module,Adb):
    for Item in L1:
        if len(Item)==1: Item=Item[0]
        if Item==[]:
            pass
        elif Item[0]=='signal':
            Sigs = Item[1]
            Wid = Item[2]
            if type(Sigs)==types.ListType:
                for Sig in Sigs:
                    Net = string.lower(Sig)
                    addWire(Net,Wid)
            else:
                Net = string.lower(Sigs)
                addWire(Net,Wid)
        elif Item[0]=='constant':
            Net = string.lower(Item[1])
            Wid = Item[2]
            Val = Item[3]
            addWire(Net,Wid)
            mod.addHardAssign(Net,Val)
        elif Item[0]=='port_map':
            Type = Item[1]
            Ports = Item[2]
            if Ports[0]=='port':
                List = Ports[1]
        elif Item[0]=='type':
            Name = Item[1]
            Kind = Item[2]
            TYPES[Name]=Kind
            info('adding type %s as %s'%(Name,Kind))
        elif Item[0]=='alias':
            Net = string.lower(Item[1])
            Val = Item[3]
            treatSignals([['signal',Net,Item[2]]],Module,Adb)
            mod.addHardAssign(Net,Val)
        else:
            logs.log_error('treat signal failed "%s" '%(str(Item)))

def addWire(Net,Wid):
    if (Wid[0]=='std_logic')or(Wid=='std_logic')or(Wid=='boolean'):
        mod.addWire(Net,'wire',0)
    elif Wid[0]==':':
        mod.addWire(Net,'wire',(Wid[1],Wid[2]))
    elif Wid[0]=='integer':
        mod.addWire(Net,'wire',(31,0))
    elif Wid[0]=='std_logic_vector':
        mod.addWire(Net,'wire',Wid[1])
    elif Wid=='integer':
        mod.addWire(Net,'wire',(31,0))
    elif Wid in ['unsigned','positive']:
        mod.addWire(Net,'wire',(31,0))
    elif Wid[0] in ['unsigned','positive']:
        mod.addWire(Net,'wire',Wid[1])
    elif Wid[0]=='subbus':
        Hi = Wid[2]
        Lo = Wid[3]
        mod.addWire(Net,'wire',(Hi,Lo))
    elif type(Wid) == types.ListType:
        logs.log_error('trying to add wire %s with wid=%s'%(Net,Wid))
    elif (type(Wid)==types.StringType)and(Wid in TYPES):
        info('USING TYPE %s %s %s'%(Wid,Net,TYPES[Wid]))
        mod.addWire(Net,'reg',TYPES[Wid])
    else:
        logs.log_error('adding signal failed net=%s wid=%s '%(Net,Wid))
        info('defined TYPES are %s'%(str(TYPES.keys())))

   
def justify(List,Seq):
    Lseq = string.split(Seq)
    logs.log_info('start justify %d  %d %s %s'%(len(List),len(Lseq),Seq,List))
    if len(List)!=len(Lseq): 
        logs.log_info('justify %d<>%d %s %s'%(len(List),len(Lseq),Seq,List))
        return 
    for ind,Iseq in enumerate(Lseq):
        if Iseq == '?': 
            pass 
        elif Iseq[0] == '!': 
            Look = Iseq[1:]
            if (Look != List[ind][0]): 
                logs.log_info('mismatch (0)  pos=%d look=%s act=%s'%(ind,Look,List[ind][0]))
                return 
        elif (Iseq!=List[ind][0]):
            logs.log_info('mismatch (1) pos=%d look=%s act=%s'%(ind,Iseq,List[ind][0]))
            return 
    logs.log_info('matching %s ok'%Seq) 
KNOWNFUNCTIONS = string.split('ext sxt resize conv_std_logic_vector conv_integer unsigned')
MGROUPS={}
MGROUPS['dir'] = string.split('IN OUT INOUT BUFFER')
MGROUPS['wire'] = string.split('unsigned positive std_logic std_logic_vector')
def matches(List,Seq):
    Lseq = string.split(Seq)
    if len(List)!=len(Lseq): return False
    Vars=[]
    for ind,Iseq in enumerate(Lseq):
        if Iseq == '?': 
            Vars.append(List[ind])
        elif Iseq[0] == '?': 
            Who = List[ind][0]
            if Who in MGROUPS[Iseq[1:]]:
                Vars.append(Who)
            else:
                return False
        elif Iseq == '$': 
            Who = List[ind][0]
            if Who in KNOWNFUNCTIONS:
                Vars.append(List[ind])
            else:
                return False

        elif Iseq[0] == '!': 
            Look = Iseq[1:]
            try:
                if (Look != List[ind][0]): return False
            except:
                return False
            Vars.append(List[ind])
        elif (Iseq!=List[ind][0]):
            return False
    if Vars==[]: return True 
    return Vars 
     


def getExpr(Root,Adb,Father='none'):
    TRACE.append(('expr',Root))
    Res = getExpr__(Root,Adb,Father)
    TRACE.pop(-1)
    return Res


BIOPS = string.split("Ampersand <= GTSym LTSym SRL XOR | - + * Star AND OR DOWNTO GESym EQSym NESym /= ")
VBIOPS = string.split('concat <= > < << ^ | - + * * & | : >= == != !=')
    
def getExpr__(Root,Adb,Father):
    if (type(Root)==types.ListType)and(len(Root)==1):
        return getExpr(Root[0],Adb)
    if (type(Root)==types.TupleType)and(Root in Adb)and(Root[0]=='function_parameter_element'):
        return functionParamElement(Adb[Root],Adb)


    if (type(Root)==types.TupleType)and(Root in Adb):
        return getExpr(Adb[Root],Adb)
    if type(Root)==types.IntType: return Root
    if (len(Root)==4)and(Root[1]=='literal'): return ['bin',1,Root[0][1:-1]]
    if (len(Root)==4)and(Root[1]=='Identifier'): return string.lower(Root[0])
    if (len(Root)==4)and(Root[1]=='DOTTED'): return string.lower(Root[0])
    if (len(Root)==4)and(Root[1]=='DecimalInt'): return int(Root[0])
    if (len(Root)==4)and(Root[1]=='BasedInt'): 
        Str = Root[0]
        if Str[0] in ['x','X']:
            Val = Str[2:-1]
            return ['hex',4*(len(Str)-3),Val]
        if Str[0] in ['b','B']:
            Val = Str[2:-1]
            return ['bin',(len(Str)-3),Val]
        logs.log_error('getExpr of BasedInt got %s'%Str)
        return 0

    if (len(Root)==4)and(Root[1]=='BitStringLit'): return ['bin',len(Root[0])-2,Root[0][1:-1]]
    if (len(Root)==4)and(Root[1]=='OTHERS'): return ['others']

    if (len(Root)==2)and(Root[0][0] == 'NOT'):
        AA = getExpr(Root[1],Adb)
        return [['~',AA]]

    if (len(Root)==3)and(Root[1][0] in BIOPS):
        AA = getExpr(Root[0],Adb)
        BB = getExpr(Root[2],Adb)
        if Root[1][0]=='DOWTO': return [':',AA,BB]
        Ind = BIOPS.index(Root[1][0])
        return [VBIOPS[Ind],AA,BB]
    if (len(Root)==3)and(Root[0][0] == 'LeftParen')and(Root[2][0] == 'RightParen'):
        return getExpr(Root[1],Adb)



    Vars = matches(Root,'!choice =>  ?')
    if Vars:
        Ch = getExpr(Vars[0],Adb)
        return  Ch



    Vars = matches(Root,'? !...identifier..')
    if Vars:
        AA = getExpr(Vars[0],Adb)
        if Vars[1] in Adb:
            LL = Adb[Vars[1]]
            if (len(LL)==2)and(LL[1][1]=='Identifier'):
                BB = [LL[0][0],LL[1][0]]
            else:
                BB =  getExpr(Adb[Vars[1]],Adb)
            return [AA]+BB
        return [AA,Vars[1][0]]


    if (len(Root)==2)and(type(Root)==types.ListType)and(len(Root[0])==4)and(len(Root[1])==2)and(Root[1] in Adb):
        Root2 = level1up(Root,Adb)
        XX= getExpr(Root2,Adb)
        if (XX[0]=='subbit')and(type(XX[2])==types.ListType)and(XX[2][0]==':'):
            return ['subbus',string.lower(XX[1]),XX[2][1],XX[2][2]]
        return XX
    if (len(Root)==3)and(Root[1][0] == "'"):
        return ['funccall',Root[2][0],Root[0][0]]

    if (len(Root)==2)and(type(Root)==types.ListType)and(Root[0] in Adb)and(Root[1] in Adb):
        Expr = getExpr(Root[0],Adb)
        XX =  getExpr([DUMMY+Adb[Root[1]]],Adb)
        XX[1] = Expr
        return XX
    Vars =  matches(Root,"OTHERS => ?")
    if Vars:
        return getExpr(Vars[0],Adb)

    Vars =  matches(Root,"UNTIL ? AND ?")
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getExpr(Vars[1],Adb)
        return ['until',['&',AA,BB]]

    Vars =  matches(Root,"? ? | ?")
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getExpr(Vars[1],Adb)
        CC = getExpr(Vars[2],Adb)
        return [['|',AA,BB,CC]]
    Vars =  matches(Root,"| ?")
    if Vars:
        AA = getExpr(Vars[0],Adb)
        return [['|',AA]]

    Vars =  matches(Root,"? RANGE ?")
    if Vars:
        AA = getExpr(Vars[1],Adb)
        return ['range',Vars[0],AA]

    Vars =  matches(Root,"? TO ?")
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getExpr(Vars[1],Adb)
        return ['to',AA,BB]

    Vars =  matches(Root,"FOR ? IN ? ")
    if Vars:
        Cond = getExpr(Vars[0],Adb)
        Range = getExpr(Vars[1],Adb)
        return ('for',Cond,Range)

    Vars =  matches(Root,"? LeftParen ? !...element_association.. RightParen")
    if Vars:
        Y = getExpr(Vars[1],Adb)
        Z = getExpr(Adb[Vars[2]],Adb,'element_association')
        return ['funccall',Vars[0],[Y,Z]]

    Vars =  matches(Root,"LeftParen ? !...element_association.. RightParen")
    if Vars:
        AA = Vars[0][0]
        BB = getExpr(Adb[Vars[1]],Adb,'element_association')
        LL = mergeToList([AA],BB,'elem')
        return LL
    Vars =  matches(Root,"!...element_association.. ?")
    if Vars:

        AA = Vars[1][0]
        BB = getExpr(Adb[Vars[0]],Adb,'element_association')
        LL = mergeToList(BB,[AA],'elem')
        return LL

    Vars =  matches(Root,"? LeftParen ? ? RightParen")
    if Vars:
        Func = getExpr(Vars[0],Adb)
        Op0 = getExpr(Vars[1],Adb)
        Op1 = getExpr(Vars[2],Adb)
        return [('funccall',Func,[Op0,Op1])]

    if (len(Root)==2)and(type(Root)==types.ListType):
        if (Root[0][1] in ['DecimalInt','BasedInt'])and(Root[0][1] in ['DecimalInt','BasedInt']):
            return ['elem',Root[0][0],Root[1][0]]

    Vars = matches(Root,'? WHEN ? ELSE ?')
    if Vars:
        Cond = getExpr(Vars[1],Adb)
        Yes = getExpr(Vars[0],Adb)
        No = getExpr(Vars[2],Adb)
        return ('question',Cond,Yes,No)

    Vars = matches(Root,'OTHERS ?')
    if Vars:
        return getExpr(Vars[0],Adb)

    Vars = matches(Root,'? WHEN !expression ELSE')
    if Vars:
        Cond = getExpr(Adb[Vars[1]],Adb)
        Yes = getExpr(Vars[0],Adb)
        return ('question1',Cond,Yes)


    Vars = matches(Root,'RANGE ? TO ?')
    if Vars:
        From = getExpr(Vars[0],Adb)
        To = getExpr(Vars[1],Adb)
        return ('range',From,To)

    Vars = matches(Root,'? LeftParen !element_association RightParen')
    if Vars:
        LL = getExpr(Adb[Vars[1]],Adb)
        Name = string.lower(Vars[0][0])
        if Name in ['conv_integer','unsigned']:
            return LL
        return ('subbit',Name,LL)
    Vars = matches(Root,'? LeftParen ? RightParen')
    if Vars:
        LL = getExpr(Vars[1],Adb)
        Name = string.lower(Vars[0][0])
        if Name in ['conv_integer','unsigned']:
            return LL
        return ('subbit',string.lower(Vars[0][0]),LL)

    Vars = matches(Root,'!..waveform__WHEN__condition__ELSE.. ? WHEN ? ELSE')
    if Vars:
        AA = getExpr(Vars[0],Adb)
        Yes = getExpr(Vars[1],Adb)
        Cond = getExpr(Vars[2],Adb)
        Expr = ('question0',AA,Cond,Yes)
        return Expr
    Vars = matches(Root,'LeftParen ? !...enumeration_literal.. RightParen')
    if Vars:
        AA = getExpr(Vars[0],Adb)
        BB = getList_new(Adb[Vars[1]],Adb)
        LL = mergeToList([AA],BB,'enumlit')
        return LL


    if (len(Root)==2)and(type(Root)==types.TupleType)and(Root in Adb):
        LL = Adb[Root]
        if bothIdentifiers(LL):
            return [LL[0][0],LL[1][0]]
#        return getExpr(Adb[Root],Adb)


    if Father=='element_association':
        if bothIdentifiers(Root):
            res=[]
            for X in Root:
                Y = getExpr(X,Adb,'simple')
                res.append(Y)
            return res
        
        


    logs.log_error('getExpr got %s from %s'%(str(Root),Father))
    reportTrace(TRACE)
    traceback.print_stack()
    return Root

def functionParamElement(Root,Adb):
    Vars = matches(Root,'? Colon ?')
    if Vars:
        return ('funcparam',getExpr(Vars[0],Adb),getExpr(Vars[1],Adb))
    logs.log_error('functionParamElement got "%s"'%str(Root))
    return ('funcparam','err','err')

def reportTrace(Trace):
    for Item in Trace:
        info('          %s'%str(Item))
    info('\n\n\n')

def level1up(List,Adb):
    Res = [] 
    for Item in List:
        if (type(Item)==types.TupleType)and(Item in Adb):
            LL = Adb[Item]
            Res.extend(LL)
        else:
            Res.append(Item)
    return Res



def reportAdb(Adb,Which='stam'):
    Fout = open('%s.report'%Which,'w')
    for Key in Adb.keys():
        Val = str(Adb[Key])
#        if len(Val)>150: Val = Val[:150]

        Fout.write('%s report %s   %s\n'%(Which,Key,Val))
    Fout.close()

    Defined=[]
    Used=[]
    for Key in Adb.keys():
        Defined.append(Key)
        List = Adb[Key]
        for Item in List:
            if len(Item)==2:
                if Item not in Adb:
                    info('item %s is not in adb'%(str(Item)))



def listify(List):
    if type(List)==types.ListType:
        if len(List)==0: return List
        if (type(List[0])==types.ListType):
            return ['list']+List
    return List

def reworkWHENELSE(Expr):
    if Expr[0]=='question':
        Else = Expr[2]
        Body = Expr[1]
        if Body[0]=='question1':
            Cond = Body[1]
            Yes  = Body[2]
            No = Else
            return ['question',Cond,Yes,No]
        if Body[0]=='question0':
            Deep =  reworkDeep(Body,[],Else)
            while len(Deep)>=2:
                X = ['question',Deep[-2][0],Deep[-2][1],Deep[-1]]
                Deep.pop(-1)
                Deep.pop(-1)
                Deep.append(X)

            return Deep
    logs.log_error('0>>> %s'%str(Expr))
    return '0'

def reworkDeep(Body,Sofar,Else):
    if Body[0]=='question1':
        Cond = Body[1]
        Yes  = Body[2]
        All = [(Cond,Yes)]+Sofar+[Else]
        return All
    if Body[0]=='question0':
        Cond = Body[2]
        Yes  = Body[3]
        return reworkDeep(Body[1],[(Cond,Yes)]+Sofar,Else)
        
    logs.log_error('reworkDeep got body=%s'%str(Body))
    return []
        
def __reworkWHENELSE(Expr):
    info('expr %s'%str(Expr))
    return '0'

    if len(Expr)==3:
        if Expr[0]=='question1':
            Cond0 = Expr[1][1]
            Yes0  = Expr[1][2]
            No0  = Expr[2]
            Ret = ['question',Cond0,Yes0,No0]
            return Ret
        if Expr[0]=='question':
            if Expr[1][0]=='question1':
                Cond = Expr[1][1]
                Yes = Expr[1][2]
                No = Expr[2]
                return ['question',Cond,Yes,No]
        if Expr[0]=='question':
            if Expr[1][0]=='question0':
                if Expr[1][1][0]=='question1':
                    Cond0 = Expr[1][1][1]
                    Yes0  = Expr[1][1][2]
                    Cond1 = Expr[1][2]
                    Yes1  = Expr[1][3]
                    No    = Expr[2]
                    Ret = ['question',Cond0,Yes0,['question',Cond1,Yes1,No]]
                    return Ret
                elif Expr[1][1][0]=='question0':
                    New = reworkWHENELSE(Expr)
                    logs.log_error('new %s'%(str(New)))
    logs.log_error('rework failed %s %s'%(len(Expr),Expr))
    return Expr


def bothIdentifiers(LL):
    if len(LL)!=2: return False
    if not listtuple(LL): return False
    for Item in LL:
        if Item[1] not in ['Identifier','BitStringLit']: return False
    return True
def listtuple(AA):
    return  type(AA) in [types.ListType, types.TupleType]


def mergeToList(AA,BB,List='list'):
    if type(BB)==types.ListType:
        if (BB!=[]) and (BB[0]==List): BB=BB[1:]
    if type(AA)==types.ListType:
        if (AA!=[])and(AA[0]==List): AA=AA[1:]
    Res = [List]+AA+BB
    return  Res


def useRenames(Variables,Flow):
    if Variables==[]: return Flow
# placeholder ILIA
    return Flow


main()

