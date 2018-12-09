

import os,sys,string,pickle,types

import logs
import traceback
import module_class as mcl
import matches
import pprint

def main():
    load_parsed('.')



def load_parsed(Rundir):
    db.Global = mcl.module_class('global_module')
#    try: 
    if True:
        load_db1('%s/db0.pickle'%Rundir)
        Key = ('design_file', 1)
        dumpDataBase(db.db)
        scan1(Key)
        dumpScanned(db,'bef_')
        for ind,LL in enumerate(db.Scanned):
            L2 = simplify(LL)
            db.Scanned[ind]=L2

            
        dumpScanned(db,'')
#    except:
#        load_db1('db0.pickle')
#        Key = 'Main',1
#        scan1(Key)
#        dumpScanned(db)
#        logs.log_fatal('reading file probably failed on syntax')
    logs.log_info('total matches run %s'%matches.totalcount)
    matches.reportIt()
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

    if (len(List)==1)and(List[0] in db.db):
        scan1(List[0])
        return

    Vars = matches.matches(List,'!design_unit !..design_unit..')
    if Vars:
        scan1(Vars[0])
        scan1(Vars[1])
        return
    Vars = matches.matches(List,'!context_clause !library_unit')
    if Vars:
        scan1(Vars[0])
        scan1(Vars[1])
        return

    Vars = matches.matches(List,'!..context_item.. !context_item')
    if Vars:
        scan1(Vars[0])
        scan1(Vars[1])
        return

    Vars = matches.matches(List,'LIBRARY  !logical_name_list ?')
    if Vars:
        LL = get_list(Vars[0])
        print('library %s'%str(LL))
        return

    Vars = matches.matches(List,'USE  !selected_name !...selected_name.. ?')
    if Vars:
        LL0 = get_list(Vars[0])
        LL1 = get_list(Vars[1])
        db.Scanned.append(('use',LL0+LL1))
        return
        
    Vars = matches.matches(List,'ENTITY  ?t IS !.generic_clause. !.port_clause. !entity_declarative_part !.BEGIN__entity_statement_part. END ? ? ?')
    if Vars:
        Gen = get_list(db.db[Vars[1]])
        Port = get_list(db.db[Vars[2]])
        Decls = get_list(db.db[Vars[3]])
        Body = get_list(db.db[Vars[4]])
        db.Scanned.append(('entity',Vars[0],Gen,Port,Decls,Body))
        return

    Vars = matches.matches(List,'ARCHITECTURE  ?t OF !name IS  !architecture_declarative_part BEGIN_ !architecture_statement_part END ? ? ?')
    if Vars:
        Name = get_list(db.db[Vars[1]])
        Decls = get_list(db.db[Vars[2]])
        Body = get_list(db.db[Vars[3]])
        db.Scanned.append(('archi',Vars[0],Name,Decls,Body))
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






def inDb(Item):
    return (type(Item) is tuple)and(len(Item)==2)and(Item in db.db)

def dumpScanned(db,Pref=''):
    File = open('%sscanned.dump'%Pref,'w')
    for Item in db.Scanned:
        Kind = Item[0]
        Name = Item[1]
        if Kind=='archi':
            Str = '%s %s lens = io=%d prm=%d stuff=%d'%(Kind,Name,len(Item[2]),len(Item[3]),len(Item[4]))
            File.write('\n\n%s\n'%Str)
            if type(Item[2]) is list:
                for X in Item[2]:
                    File.write('item2 : %s\n'%(str(X)))
            else:
                File.write('item2 : %s\n'%(Item[2]))

            for X in Item[3]:
                File.write('item3 : %s\n'%(str(X)))
            if type(Item[4]) is list:
                for X in Item[4]:
                    XX = nicePrint(X)
                    File.write('item4 : %s\n'%(XX))
            else:
                File.write('item4 : %s\n'%(nicePrint(Item[4])))
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
            File.write('?? %s %s\n'%(Item[0],Item[1]))
    File.close()

def dumpDataBase(db):
    Keys = list(db.keys())
    Keys.sort()
    Fout = open('database.dump','w')
    for Key in Keys:
        Fout.write('db %s %s\n'%(Key,db[Key]))



def get_list(Item):
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
        Ok=True
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

    Vars = matches.matches(Item,'?t !...logical_name..')
    if Vars:
        L1 = get_list(db.db[Vars[1]])
        return [Vars[0]]+L1

    Vars = matches.matches(Item,'!..package_body_declarative_item.. !package_body_declarative_item')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!..package_declarative_item.. !package_declarative_item')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!..block_declarative_item.. !block_declarative_item')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!concurrent_statement !..concurrent_statement..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!local_generic_element !...local_generic_element..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!formal_generic_element !...formal_generic_element..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!...formal_generic_element.. ? !formal_generic_element')
    if Vars:
#        L0 = get_list(db.db[Vars[0]])
#        L1 = get_list(db.db[Vars[1]])
        LL = get_iterative_list_1(Item,'!...formal_generic_element..','!formal_generic_element','?')
        return LL

    Vars = matches.matches(Item,'!formal_port_element !...formal_port_element..')
    if Vars:
#        L0 = get_list(db.db[Vars[0]])
#        L1 = get_list(db.db[Vars[1]])
        LL = get_iterative_list_2(Item,'!formal_port_element','!...formal_port_element..')
#        return L0+L1
        return LL

    Vars = matches.matches(Item,'!local_port_element !...local_port_element..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!name !...name..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!...discrete_range.. Comma !discrete_range')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!...function_parameter_element.. ? !function_parameter_element')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[2]])
        return L0+L1

    Vars = matches.matches(Item,'!sign !term')
    if Vars:
        L0 = get_list_db(Vars[0])
        L1 = get_list_db(Vars[1])
        return [(L0[0],L1[0])]
    Vars = matches.matches(Item,'!name !aggregate')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return [('aggregate',L0,L1)]

    Vars = matches.matches(Item,'!..waveform__WHEN__condition__ELSE.. !waveform WHEN !expression ELSE')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('when_else',A,B,C)]

    Vars = matches.matches(Item,'GENERIC LeftParen !local_generic_list ? ?')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        return [('generic',L0)]

    Vars = matches.matches(Item,'GENERIC LeftParen !formal_generic_list ? ?')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        return [('generic',L0)]
    Vars = matches.matches(Item,'GENERIC MAP LeftParen !association_list ?')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        return [('generic_map',L0)]

    Vars = matches.matches(Item,'!waveform_element !...waveform_element..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!...name.. Comma !name')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!sequential_statement !..sequential_statement..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!...element_association.. Comma !element_association')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!prefix Dot !suffix')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('dot',A,B)]
    Vars = matches.matches(Item,'!name RANGE Box')
    if Vars:
        A = get_list_db(Vars[0])
        return [('box_range',A)]

    Vars = matches.matches(Item,'!association_element !...association_element..')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!..process_declarative_item..    !process_declarative_item')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1
    Vars = matches.matches(Item,'!...formal_port_element.. ? !formal_port_element')
    if Vars:
        LL =  get_iterative_list_1(Item,'!...formal_port_element..','!formal_port_element',Middle='?'):
#        L0 = get_list(db.db[Vars[0]])
#        L1 = get_list(db.db[Vars[2]])
#        return L0+L1
    Vars =  matches.matches(Item,'!..case_statement_alternative.. !case_statement_alternative')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars =  matches.matches(Item,'!subprogram_declarative_part !subprogram_declarative_item')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return L0+L1

    Vars = matches.matches(Item,'!subprogram_specification ?')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        return L0

    Vars = matches.matches(Item,'!subprogram_specification IS !subprogram_declarative_part BEGIN_ !sequence_of_statements END ? ?')
    if Vars:
        Sub = get_list(db.db[Vars[0]])
        Decls = get_list(db.db[Vars[1]])
        Seq = get_list(db.db[Vars[2]])
        return [('subprogram',Sub,Decls,Seq)]

    Vars = matches.matches(Item,'!a_label !unlabeled_process_statement')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return [('labeled_process',L0,L1)]

    Vars = matches.matches(Item,'!a_label !unlabeled_generate_statement')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return [('labeled_gen',L0,L1)]

    Vars = matches.matches(Item,'PORT LeftParen !formal_port_list ? ?')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        return [('port',L0)]

    Vars = matches.matches(Item,'!.CONSTANT. !identifier_list Colon !.IN. !type_mark !.constraint. !.VarAsgn__expression.')
    if Vars:
        Who = get_list(db.db[Vars[0]])
        Ilist = get_list(db.db[Vars[1]])
        In = get_list(db.db[Vars[2]])
        Type    = get_list(db.db[Vars[3]])
        Constr    = get_list(db.db[Vars[4]])
        Var    = get_list(db.db[Vars[5]])
        return [('constant',Who,Ilist,In,Type,Constr,Var)]


    Vars = matches.matches(Item,'CONSTANT !identifier_list Colon !subtype_indication !.VarAsgn__expression.  ?')
    if Vars:
        Ilist = get_list(db.db[Vars[0]])
        Subtype = get_list(db.db[Vars[1]])
        Expr    = get_list(db.db[Vars[2]])
        return [('constant',Ilist,Subtype,Expr)]

    Vars = matches.matches(Item,'VARIABLE !identifier_list Colon !subtype_indication !.VarAsgn__expression.  ?')
    if Vars:
        Ilist = get_list(db.db[Vars[0]])
        Subtype = get_list(db.db[Vars[1]])
        Expr    = get_list(db.db[Vars[3]])
        return [('variable',Ilist,Subtype,Expr)]



    Vars = matches.matches(Item,'SIGNAL !identifier_list Colon !subtype_indication !.signal_kind. !.VarAsgn__expression.  ?')
    if Vars:
        Ilist = get_list(db.db[Vars[0]])
        Subtype = get_list(db.db[Vars[1]])
        Kind = get_list(db.db[Vars[2]])
        Expr    = get_list(db.db[Vars[3]])
        return [('signal',Ilist,Subtype,Kind,Expr)]

    Vars = matches.matches(Item,'!.SIGNAL. !identifier_list Colon !.mode. !type_mark !.constraint. !.BUS. !.VarAsgn__expression.')
    if Vars:
        Sig = get_list_db(Vars[0])
        Ilist = get_list(db.db[Vars[1]])
        Mode = get_list(db.db[Vars[2]])
        Type = get_list(db.db[Vars[3]])
        Constr    = get_list(db.db[Vars[4]])
        Bus    = get_list(db.db[Vars[5]])
        Var    = get_list(db.db[Vars[6]])
        return [('signal',Ilist,Mode,Type,Constr,Bus,Var)]

    Vars = matches.matches(Item,'!.SIGNAL. !identifier_list Colon !.local_port_mode. !type_mark !.constraint.')
    if Vars:
        Ilist = get_list(db.db[Vars[0]])
        Mode = get_list(db.db[Vars[1]])
        Type = get_list(db.db[Vars[2]])
        Constr    = get_list(db.db[Vars[3]])
        return [('signal',Ilist,Mode,Type,Constr)]


    Vars = matches.matches(Item,'PROCESS !.sensitivity_list. !process_declarative_part BEGIN_ !sequence_of_statements END PROCESS ? ?')
    if Vars:
        Sense = get_list(db.db[Vars[0]])
        Decls = get_list(db.db[Vars[1]])
        Seqs = get_list(db.db[Vars[2]])
        return [('process',Sense,Decls,Seqs)]

    Vars = matches.matches(Item,'?t !...identifier..')
    if Vars:
        Ident = get_list(db.db[Vars[1]])
        if Ident==[]:
            return [Vars[0]]
        return [Vars[0],Ident[0]]

    Vars = matches.matches(Item,':= !expression')
    if Vars:
        Expr = get_list(db.db[Vars[0]])
        return Expr
        
    Vars = matches.matches(Item,'!type_mark !.constraint.')
    if Vars:
        L0 = get_list(db.db[Vars[0]])
        L1 = get_list(db.db[Vars[1]])
        return [(L0,L1)]

    Vars = matches.matches(Item,'!label Colon')
    if Vars:
        Label =  get_list(db.db[Vars[0]])
        return [Label]

    Vars = matches.matches(Item,'LeftParen !signal_list !RightParen_ERR')
    if Vars:
        return get_list(db.db[Vars[0]])

    Vars = matches.matches(Item,'LeftParen !element_association  !...element_association.. !RightParen_ERR')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[1])
        return L0+L1

    Vars = matches.matches(Item,'!...procedure_parameter_element.. ? !procedure_parameter_element')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[2])
        return L0+L1

    Vars = matches.matches(Item,'LeftParen !procedure_parameter_element  !...procedure_parameter_element.. !RightParen_ERR')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[1])
        return L0+L1
    Vars = matches.matches(Item,'!.procedure_parameter_object_class. !identifier_list Colon !.procedure_parameter_mode. !type_mark !.constraint. !.VarAsgn__expression.')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[1])
        L2 =  get_list_db(Vars[2])
        L3 =  get_list_db(Vars[3])
        L4 =  get_list_db(Vars[4])
        L5 =  get_list_db(Vars[5])
        return [('procedure',L0,L1,L2,L3,L4,L5)]

    Vars = matches.matches(Item,'!simple_expression !direction !simple_expression')
    if Vars:
        L0 =  get_list(db.db[Vars[0]])
        L1 =  get_list(db.db[Vars[1]])
        L2 =  get_list(db.db[Vars[2]])
        return [(L1[0],L0[0],L2[0])]

    Vars = matches.matches(Item,'!simple_expression !.relop__simple_expression.')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[1])
        if L1==[]:
            return L0
        return [('relop',L0+L1)]

    Vars = matches.matches(Item,'!primary !.DoubleStar__primary.')
    if Vars:
        L0 =  get_list_db(Vars[0])
        L1 =  get_list_db(Vars[1])
        if L1==[]:
            return L0

        return [('dstar',L0,L1)]

    Vars = matches.matches(Item,'Comma ?t !...identifier..')
    if Vars:
        L1 =  get_list(db.db[Vars[1]])
        if L1==[]:
            return [Vars[0]]
        return [Vars[0]]+L1
        
    Vars = matches.matches(Item,'IF !condition')
    if Vars:
        Cond = get_list(db.db[Vars[0]])
        return [('if',Cond)]

    Vars = matches.matches(Item,'IF !condition THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts.. !.ELSE__seq_of_stmts. END IF ?')
    if Vars:
        Cond = get_list(db.db[Vars[0]])
        Yes  = get_list(db.db[Vars[1]])
        No  = get_list(db.db[Vars[2]])
        No2  = get_list(db.db[Vars[3]])
        return [('ifelse',Cond,Yes,No,No2)]

    Vars = matches.matches(Item,'ELSIF !condition THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts.. !.ELSE__seq_of_stmts.')
    if Vars:
        Cond = get_list(db.db[Vars[0]])
        Yes = get_list(db.db[Vars[1]])
        No = get_list(db.db[Vars[2]])
        No2 = get_list(db.db[Vars[3]])
        return [('elsif2',Cond,Yes,No,No2)]

    Vars = matches.matches(Item,'ELSE !sequence_of_statements')
    if Vars:
        Seq = get_list(db.db[Vars[0]])
        return Seq
    Vars = matches.matches(Item,'ELSIF !condition THEN !sequence_of_statements !..ELSIF__THEN__seq_of_stmts..')
    if Vars:
        Cond = get_list(db.db[Vars[0]])
        Yes = get_list(db.db[Vars[1]])
        No = get_list(db.db[Vars[2]])
        return [('elsif',Cond,Yes,No)]

    Vars = matches.matches(Item,'CASE !expression IS !case_statement_alternative !..case_statement_alternative.. END CASE ?')
    if Vars:
        Cond = get_list(db.db[Vars[0]])
        Case0 = get_list(db.db[Vars[1]])
        Case1 = get_list(db.db[Vars[2]])
        return [('case',Cond,Case0+Case1)]






    Vars = matches.matches(Item,'!target VarAsgn !expression ?')
    if Vars:
        Dst = get_list(db.db[Vars[0]])
        Src  = get_list(db.db[Vars[1]])
        return [('assign',Dst,Src)]
        
    Vars = matches.matches(Item,'!target LESym !.TRANSPORT. !waveform ?')
    if Vars:
        Dst = get_list(db.db[Vars[0]])
        Trs  = get_list(db.db[Vars[1]])
        Src  = get_list(db.db[Vars[2]])
        if Trs==[]:
            return [('<=',Dst[0],Src[0])]
        return [('<=',Dst[0],Src[0],Trs[0])]
        
    Vars = matches.matches(Item,'!target LESym !.TRANSPORT. !..waveform__WHEN__condition__ELSE.. !waveform ?')
    if Vars:
        Dst = get_list(db.db[Vars[0]])
        Trs  = get_list(db.db[Vars[1]])
        Src0  = get_list(db.db[Vars[2]])
        Src1  = get_list(db.db[Vars[3]])
        if Trs==[]:
            return [('<=',Dst,Src0,Src1)]
        return [('<=',Dst,Src0,Src1,Trs)]

    Vars = matches.matches(Item,'!target LESym !.GUARDED. !.TRANSPORT. !..waveform__WHEN__condition__ELSE.. !waveform ?')
    if Vars:
        Dst = get_list(db.db[Vars[0]])
        Guard  = get_list(db.db[Vars[1]])
        Trs  = get_list(db.db[Vars[2]])
        Src0  = get_list(db.db[Vars[3]])
        Src1  = get_list(db.db[Vars[4]])
        return [('<=',Dst,Src0,Src1,Guard,Trs)]

    Vars = matches.matches(Item,'!relational_operator !simple_expression')
    if Vars:
        Op = get_list(db.db[Vars[0]])
        Expr  = get_list(db.db[Vars[1]])
        return [(Op[0],Expr[0])]
    Vars = matches.matches(Item,'!relation !XORXNOR  !relation')
    if Vars:
        Op0 = get_list(db.db[Vars[0]])
        Op = get_list(db.db[Vars[1]])
        Op1  = get_list(db.db[Vars[2]])
        return [(Op,Op0,Op1)]
    Vars = matches.matches(Item,'!relation..XOR__relation.. !XORXNOR  !relation')
    if Vars:
        Op0 = get_list(db.db[Vars[0]])
        Op = get_list(db.db[Vars[1]])
        Op1  = get_list(db.db[Vars[2]])
        return [(Op,Op0,Op1)]

    Vars = matches.matches(Item,'!relation..OR__relation.. OR  !relation')
    if Vars:
        Op0 = get_list(db.db[Vars[0]])
        Op1  = get_list(db.db[Vars[1]])
        return [('OR',Op0,Op1)]
    Vars = matches.matches(Item,'!relation ?t  !relation')
    if Vars:
        Op0 = get_list(db.db[Vars[0]])
        Op = Vars[1]
        Op1  = get_list(db.db[Vars[2]])
        return [(Op,Op0,Op1)]
        

    Vars = matches.matches(Item,'!expression !.AFTER__expression.')
    if Vars:
        Op = get_list(db.db[Vars[0]])
        Expr  = get_list(db.db[Vars[1]])
        return [(Op,Expr)]
    Vars = matches.matches(Item,'UNTIL !expression')
    if Vars:
        Expr = get_list(db.db[Vars[0]])
        return [('until',Expr)]

    Vars = matches.matches(Item,'RANGE !range')
    if Vars:
        Op = get_list(db.db[Vars[0]])
        return [('range',Op)]
    Vars = matches.matches(Item,'WAIT !.sensitivity_clause. !.condition_clause. !.timeout_clause. ?')
    if Vars:
        Sense = get_list(db.db[Vars[0]])
        Cond = get_list(db.db[Vars[1]])
        Timeout = get_list(db.db[Vars[2]])
        return [('wait',Sense,Cond,Timeout)]
        
    Vars = matches.matches(Item,'NOT !primary')
    if Vars:
        Pr = get_list(db.db[Vars[0]])
        return [('not',Pr)]
    Vars = matches.matches(Item,'DoubleStar !primary')
    if Vars:
        Pr = get_list(db.db[Vars[0]])
        return [('**',Pr)]

    Vars = matches.matches(Item,'WHEN !choices Arrow !sequence_of_statements')
    if Vars:
        Choices = get_list(db.db[Vars[0]]) 
        Seq = get_list_db(Vars[1]) 
        return [('when',Choices,Seq)]
    Vars = matches.matches(Item,'!choice !..Bar__choice..')
    if Vars:
        Choice = get_list(db.db[Vars[0]]) 
        Bar = get_list(db.db[Vars[1]]) 
        if Bar==[]: return [Choice]
        return [('bar',Choice,Bar)]

    Vars = matches.matches(Item,'!..Bar__choice.. Bar !choice')
    if Vars:
        Bars = get_list(db.db[Vars[0]]) 
        Choice = get_list(db.db[Vars[1]]) 
        return [('bar',Bars,Choice)]

    Vars = matches.matches(Item,'!name Arrow !OPEN_or_expression')
    if Vars:
        A =get_list(db.db[Vars[0]])
        B =get_list(db.db[Vars[1]])
        return [('arrow_or',A,B)]

    Vars = matches.matches(Item,'!term !multiplying_operator !factor')
    if Vars:
        A =get_list(db.db[Vars[0]])
        B =get_list(db.db[Vars[1]])
        C =get_list(db.db[Vars[2]])
        return [('multing',A,B,C)]
    Vars = matches.matches(Item,'!.sign.term..add_op__term.. !adding_operator !term')
    if Vars:
        A =get_list(db.db[Vars[0]])
        B =get_list(db.db[Vars[1]])
        C =get_list(db.db[Vars[2]])
        return [(B[0],A[0],C[0])]

    Vars = matches.matches(Item,'!name Apostrophe !attribute_designator !.aggregate.')
    if Vars:
        A =get_list(db.db[Vars[0]])
        B =get_list(db.db[Vars[1]])
        C =get_list(db.db[Vars[2]])
        return [('apostrophe',A,B,C)]

    Vars = matches.matches(Item,'COMPONENT ?t !.GENERIC__local_generic_list. !.PORT__local_port_list. END COMPONENT ?')
    if Vars:
        Name = Vars[0]
        Gen = get_list(db.db[Vars[1]])
        Ports = get_list_db(Vars[2])
        return [('component',Name,Gen,Ports)]

    Vars = matches.matches(Item,'PORT LeftParen !local_port_list ? ?')
    if Vars:
        Ports = get_list_db(Vars[0])
        return [('ports',Ports)]
        
    Vars = matches.matches(Item,'!a_label !name !.generic_map_aspect. !.port_map_aspect. ?')
    if Vars:
        Label = get_list(db.db[Vars[0]])
        Name = get_list(db.db[Vars[1]])
        Generics = get_list(db.db[Vars[2]])
        Ports = get_list(db.db[Vars[3]])
        return [('instance',Label,Name,Generics,Ports)]
        
    Vars = matches.matches(Item,'PORT MAP LeftParen !association_list  ?')
    if Vars:
        List = get_list(db.db[Vars[0]])
        return [('conns',List)]

    Vars = matches.matches(Item,'!...local_port_element.. ? !local_port_element')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[2]])
        return A+B

    Vars = matches.matches(Item,'Comma !association_element !...association_element..')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B

    Vars = matches.matches(Item,'RETURN !.expression. ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        return [('return',A)]

    Vars = matches.matches(Item,'PROCEDURE !designator !.procedure_parameter_list.')
    if Vars:
        A = get_list_db(Vars[0])
        B = get_list_db(Vars[1])
        return [('taskhead',A,B)]
    


    Vars = matches.matches(Item,'FUNCTION !designator !.function_parameter_list. RETURN !type_mark')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('funchead',A,B,C)]

    Vars = matches.matches(Item,'!.iteration_scheme. LOOP !sequence_of_statements END LOOP ? ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('loop',A,B)]

    Vars = matches.matches(Item,'FOR !generate_parameter_specification')
    if Vars:
        A = get_list(db.db[Vars[0]])
        return [('gen_for',A)]

    Vars = matches.matches(Item,'FOR !expression')
    if Vars:
        A = get_list(db.db[Vars[0]])
        return [('for',A)]
    Vars = matches.matches(Item,'!abstract_literal !name')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('abstract',A,B)]

    Vars = matches.matches(Item,'FOR !loop_parameter_specification')
    if Vars:
        A = get_list(db.db[Vars[0]])
        return A

    Vars = matches.matches(Item,'SUBTYPE ?t IS !subtype_indication ?')
    if Vars:
        Def =get_list_db(Vars[1])
        return [('typedef',Vars[0],Def)]

    Vars = matches.matches(Item,'TYPE ?t IS !type_definition ?')
    if Vars:
        Def = get_list_db(Vars[1])
        return [('typedef',Vars[0],Def)]

    Vars = matches.matches(Item,'LeftParen !enumeration_literal !...enumeration_literal.. ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('enumlist',A+B)]

    Vars = matches.matches(Item,'!...enumeration_literal.. Comma !enumeration_literal')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B




    Vars = matches.matches(Item,'LeftParen !function_parameter_element !...function_parameter_element.. ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B

    Vars = matches.matches(Item,'?t IN !discrete_range')
    if Vars:
        Range =  get_list(db.db[Vars[1]])
        return [('in',Vars[0],Range)]

    Vars = matches.matches(Item,'!.function_parameter_object_class. !identifier_list Colon !.function_parameter_mode. !type_mark !.constraint. !.VarAsgn__expression.')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        D = get_list(db.db[Vars[3]])
        E = get_list(db.db[Vars[4]])
        F = get_list(db.db[Vars[5]])
        return [('funcparam',A,B,C,D,E,F)]

    Vars = matches.matches(Item,'ARRAY LeftParen !index_subtype_definition !...index_subtype_definition.. ? OF !subtype_indication')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[3]])
        return [('array',A,B,C)]

    Vars = matches.matches(Item,'ARRAY !index_constraint OF !subtype_indication')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('array',A,B)]

    Vars = matches.matches(Item,'!choice !..Bar__choice.. Arrow !expression')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('choice_arrow',A,B,C)]
        
    Vars = matches.matches(Item,'LeftParen !discrete_range  !...discrete_range.. ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('discrete',A+B)]
    Vars = matches.matches(Item,'!generation_scheme  GENERATE  !set_of_statements END GENERATE ? ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('generate',A,B)]
    Vars = matches.matches(Item,'ASSERT !expression !.REPORT__expression. !.SEVERITY__expression. ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('assert',A,B,C)]
    Vars = matches.matches(Item,'REPORT !expression')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        return [('report',A)]
    Vars = matches.matches(Item,'SEVERITY !expression')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        return [('severity',A)]
    Vars = matches.matches(Item,'ATTRIBUTE ?t Colon !type_mark ?')        
    if Vars:
        A = Vars[0]
        B = get_list(db.db[Vars[1]])
        return [('attribute',A,B)]
        
    Vars = matches.matches(Item,'!entity_name_list Colon !entity_class')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B

    Vars = matches.matches(Item,'!entity_designator !...entity_designator..')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B


    Vars = matches.matches(Item,'ATTRIBUTE !attribute_designator OF !entity_specification IS  !expression ?')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('attribute',A,B,C)]
    Vars = matches.matches(Item,'RECORD !element_declaration !..element_declaration.. END ?')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('record',A+B)]

    Vars = matches.matches(Item,'!..element_declaration.. !element_declaration')        
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return A+B

    Vars = matches.matches(Item,'!identifier_list Colon !element_subtype_definition ?')
    if Vars:
        A = get_list(db.db[Vars[0]])
        B = get_list(db.db[Vars[1]])
        return [('member',A,B)]
        
    Vars = matches.matches(Item,'ALIAS ?t Colon !subtype_indication IS !name ?')
    if Vars:
        A = Vars[0]
        B = get_list(db.db[Vars[1]])
        C = get_list(db.db[Vars[2]])
        return [('alias',A,B,C)]

    Vars =  matches.matches(Item,'NULL_ !Semicolon_ERR')
    if Vars:
        return []
    Vars =  matches.matches(Item,'!name !Semicolon_ERR')
    if Vars:
        AA = get_list_db(Vars[0])
#        logs.log_error('matches !name %d %s'%(len(AA),str(AA)))
        return AA

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
        while LL[-1]==[]: LL.pop(-1)
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

if __name__=='__main__':
    main()


