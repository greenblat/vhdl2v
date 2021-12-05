
%token	Ampersand				
%token	Apostrophe
%token	LeftParen 				
%token	RightParen 				
%token	DoubleStar 				
%token	Star 				
%token	Plus 				
%token	Comma 				
%token	Minus 				
%token	VarAsgn 				
%token	Colon
%token	Semicolon 				
%token	LESym 				
%token	Box 				
%token	LTSym 				
%token	Arrow 				
%token	EQSym 				
%token	GESym 				
%token	GTSym 				
%token	Bar 				
%token	NESym 				
%token	Dot
%token	Slash
%token	Identifier
%token	DOTTED

%token	DecimalInt
%token	DecimalReal
%token	BasedInt
%token	BasedReal
%token	CharacterLit
%token	literal
%token	StringLit
%token	BitStringLit
%token 	ABS
%token  ACCESS
%token 	AFTER
%token 	ALIAS
%token 	ALL
%token 	AND
%token 	ARCHITECTURE
%token 	ARRAY
%token 	ASSERT
%token 	ATTRIBUTE
%token 	BEGIN_
%token 	BLOCK
%token 	BODY
%token 	BUFFER
%token  BUS
%token 	CASE
%token 	COMPONENT
%token 	CONFIGURATION
%token 	CONSTANT
%token 	DISCONNECT
%token 	DOWNTO
%token 	ELSE
%token 	ELSIF
%token 	END
%token 	ENTITY
%token 	EXIT
%token  FILE_
%token 	FOR
%token 	FUNCTION
%token 	GENERATE
%token 	GENERIC
%token  GUARDED
%token 	IF
%token 	INOUT
%token 	IN
%token 	IS
%token 	LABEL
%token  LIBRARY
%token 	LINKAGE
%token 	LOOP
%token 	MAP
%token 	MOD
%token 	NAND
%token  NEW
%token 	NEXT
%token 	NOR
%token 	NOT
%token 	NULL_
%token 	OF
%token  ON
%token 	OPEN
%token 	OR
%token 	OTHERS
%token 	OUT
%token 	PACKAGE
%token 	PORT
%token 	PROCEDURE
%token 	PROCESS
%token 	RANGE
%token 	RECORD
%token  REGISTER
%token 	REM
%token 	REPORT
%token 	RETURN
%token 	SRL
%token 	SELECT
%token 	SEVERITY
%token 	SIGNAL
%token 	SUBTYPE
%token 	THEN
%token 	TO
%token 	TRANSPORT
%token 	TYPE
%token 	UNITS
%token  UNTIL
%token 	USE
%token 	VARIABLE
%token  WAIT
%token 	WHEN
%token 	WHILE
%token 	WITH
%token 	XOR


%left       AND OR NAND NOR XOR
%left       EQSym NESym LTSym LESym GTSym GESym
%left       Plus Minus Ampersand SRL
%left       Star Slash MOD REM
%right      UNARY_SIGN
%left       DoubleStar
%right      ABS NOT

%nonassoc ELSE
%nonassoc ELSIF


%%
main : clauses ;
clauses : clauses clause | clause;
clause : library_clause | entity_declaration | architecture_body | package ;
library_clause : LIBRARY Identifier Semicolon | USE DOTTED Semicolon ;


package : PACKAGE Identifier IS package_items END Semicolon 
          | PACKAGE BODY Identifier IS package_items END Semicolon ;
package_items : package_item package_items | package_item ;
package_item : signal | typedef | subtypedef | funcdef | proceduredef  ;

subtypedef : SUBTYPE Identifier IS Identifier BusDef Semicolon ;
funcdef : FUNCTION Identifier LeftParen Args RightParen RETURN Identifier Semicolon ;
proceduredef : PROCEDURE Identifier LeftParen Args RightParen Semicolon ;

Args : Arg Semicolon Args | Arg ;
Arg : Identifier Colon Identifier | SIGNAL Identifier Colon Mode Identifier  ;

entity_declaration : 
    ENTITY Identifier IS generic_clause port_clause END Semicolon 
    | ENTITY Identifier IS port_clause END Semicolon ;

architecture_body : 
      ARCHITECTURE Identifier OF Identifier IS components BEGIN_ statements END Semicolon 
    | ARCHITECTURE Identifier OF Identifier IS BEGIN_ statements END Semicolon ;

generic_clause :  GENERIC LeftParen formal_generic_list RightParen Semicolon  ;
port_clause : PORT LeftParen formal_port_list RightParen Semicolon ;

formal_generic_list : formal_generic_element Semicolon formal_generic_list | formal_generic_element  ;
formal_generic_element : 
      Identifier Colon  Identifier   
    | Identifier Colon  IN Identifier   
    | Identifier Colon  Identifier  VarAsgn DecimalInt 
    | Identifier Colon  Identifier  VarAsgn literal 
    | Identifier Colon  Identifier  VarAsgn BitStringLit ;



formal_port_list : formal_port_element Semicolon formal_port_list | formal_port_element ;
formal_port_element : 
    Identifier Colon Mode  Identifier LeftParen Expression DOWNTO Expression RightParen  
    | Identifier Colon Mode  Identifier  ;

Mode : IN | OUT | INOUT ;

components : item components | item ;
item : component | signal | typedef | assertion  ;
statements : statement statements | statement ;
statement : instance | assign | process | generate | assertion | funcall ;

Nat : LeftParen Identifier RANGE Box RightParen ;


assertion : ASSERT Expression REPORT StringLit Identifier Identifier Semicolon ;


typedef :     
    TYPE  Identifier IS ARRAY Nat  OF Identifier BusDef Semicolon  
    | TYPE  Identifier IS ARRAY BusDef OF Identifier Semicolon  
    | TYPE  Identifier IS ARRAY BusDef OF Identifier BusDef  Semicolon  
    | TYPE  Identifier IS ARRAY BusDef OF Identifier LeftParen Expression RightParen Semicolon  
    | TYPE  Identifier IS LeftParen List RightParen Semicolon  ;


assign : 
      Identifier LeftParen Expression RightParen LESym Expression Semicolon 
    | Identifier LeftParen Expression DOWNTO Expression RightParen LESym Expression Semicolon 
    | Identifier LESym Expression Semicolon ;

process : 
    Identifier Colon PROCESS LeftParen List RightParen pdefines BEGIN_ pstatements END Semicolon 
    | Identifier Colon PROCESS LeftParen List RightParen BEGIN_ pstatements END Semicolon 
    | PROCESS LeftParen List RightParen pdefines BEGIN_ pstatements END Semicolon 
    | PROCESS LeftParen List RightParen BEGIN_ pstatements END Semicolon ;


pdefines : pdefine pdefines | pdefine ;
pdefine :
    TYPE  Identifier IS LeftParen List RightParen Semicolon 
    | VARIABLE List Colon Identifier  Semicolon
    | VARIABLE List Colon BusDef  Semicolon
    | VARIABLE List Colon Identifier BusDef  Semicolon
    ;

Dir : DOWNTO | TO ;
BusDef : LeftParen Expression Dir Expression RightParen ;


pstatements : pstatement pstatements | pstatement ;
pstatement : if | sassign | forloop | case  | funcall;

funcall : Identifier LeftParen Identifier Comma List RightParen Semicolon ;

generate : Identifier Colon IF Expression GENERATE generates END Semicolon 
    | Identifier Colon FOR Identifier IN Expression TO Expression GENERATE generates END Semicolon ;

generates : generate_item generates | generate_item ;
generate_item :  instance | sassign  | process | generate;

forloop : FOR Identifier IN Expression TO Expression LOOP pstatement END Semicolon ;

case : CASE Expression IS whens END Semicolon ;

whens : whens one_when | one_when ;

one_when : 
      WHEN BitStringLit Arrow pstatements 
    | WHEN Identifier Arrow pstatements 
    | WHEN OTHERS Arrow pstatements ; 
    | WHEN OTHERS Arrow NULL_ Semicolon ; 



sassign : 
    Identifier LESym Expression Semicolon 
    | Identifier VarAsgn Expression Semicolon 
    | Identifier LeftParen Expression RightParen  LESym Expression Semicolon 
    | Identifier LeftParen Expression DOWNTO Expression RightParen  LESym Expression Semicolon 
    ;

// elsif : IF Expression THEN pstatements ELSIF Expression THEN pstatements END Semicolon ;

if : 
      IF Expression THEN pstatements END Semicolon 
    | IF Expression THEN pstatements ELSE pstatements END Semicolon 
    | IF Expression THEN pstatements elsifs ELSE pstatements END Semicolon 
    | IF Expression THEN pstatements elsifs END Semicolon
    ;

elsifs : elsifs elsif | elsif

elsif : ELSIF Expression THEN pstatements ;

List : List Comma Identifier | Identifier ;

Expressions : Expressions Comma Expression | Expression ;

Simple : literal | Identifier | DecimalInt | BitStringLit | DecimalReal | BasedInt ;

ConstList : LeftParen ConsItems RightParen ;
ConsItems : Simple Comma ConsItems | Simple ;


Expression : literal | Identifier | DecimalInt
    | BitStringLit 
    | DecimalReal 
    | BasedInt
    | LeftParen Expression RightParen
    | Expression DoubleStar Expression 
    | Expression Minus Expression 
    | Expression Slash Expression 
    | Expression Plus Expression 
    | Expression Star Expression 
    | Expression EQSym Expression
    | Expression NESym Expression
    | Expression GTSym Expression
    | Expression GESym Expression
    | Expression LESym Expression
    | Expression Ampersand Expression
    | Expression AND Expression
    | Expression XOR Expression
    | Expression OR Expression
    | NOT Expression
    | LeftParen OTHERS Arrow Expression RightParen 
    | Identifier LeftParen Expressions RightParen 
    | Identifier LeftParen Expression DOWNTO Expression  RightParen 
    | Expression WHEN Expression ELSE Expression 
    | Identifier Apostrophe Identifier
    | Identifier Apostrophe RANGE
    ;
component : 
      COMPONENT Identifier generic_clause PORT LeftParen ports_list RightParen Semicolon END Semicolon 
    | COMPONENT Identifier PORT LeftParen ports_list RightParen Semicolon END Semicolon ; 

signal : 
      SIGNAL List Colon Identifier Semicolon 
    | SIGNAL List Colon Identifier RANGE Expression TO Expression Semicolon 
    | SIGNAL List Colon Identifier BusDef Semicolon  
    | SIGNAL List Colon Identifier VarAsgn Expression Semicolon 
    | CONSTANT Identifier Colon Identifier VarAsgn Expression Semicolon 
    | CONSTANT Identifier Colon Identifier BusDef  VarAsgn Expression Semicolon 
    | CONSTANT Identifier Colon Identifier VarAsgn ConstList Semicolon ;


ports_list : port_def Semicolon ports_list | port_def ; 

port_def : 
    Identifier Colon Mode Identifier 
    | Identifier Colon Mode Identifier LeftParen Expression DOWNTO Expression RightParen ;

instance : 
    Identifier Colon Identifier GENERIC MAP LeftParen maps RightParen PORT MAP LeftParen maps RightParen Semicolon 
    | Identifier Colon Identifier GENERIC MAP LeftParen maps RightParen PORT MAP LeftParen List RightParen Semicolon 
    | Identifier Colon Identifier PORT MAP LeftParen maps RightParen Semicolon 
    | Identifier Colon Identifier PORT MAP LeftParen List RightParen Semicolon ;

maps : map Comma maps | map ;
map : Identifier Arrow Expression ;




