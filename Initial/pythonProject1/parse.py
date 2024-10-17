import sys
from lexer import *

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set() #Variables na nadeclare na
        self.labelsDeclared = set() #Eto para sa labels(soonkameHAHA) na nadeclare
        self.labelsGotoed = set() #Yung na goto'ed na variables

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken() #tatawagin dalawang beses kasi nagtatampo. JK. 
        #para ma initialize natin yung current and peek
        pass

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind
        pass

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind
        pass

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got" + self.curToken.kind.name)
        self.nextToken()
        pass

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        pass

    def abort(self, message):
        sys.exit("Error. " + message)
        # program ::= {statement}

    # program ::= {statement}
    def program(self):
        self.emitter.headerLine("#include <stdio.h>")
        self.emitter.headerLine("int main(void){")
        
        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program.
        while not self.checkToken(TokenType.EOF):
            self.statement()

        # Wrap things up.
        self.emitter.emitLine("return 0;")
        self.emitter.emitLine("}")

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)
    
    def statement(self):
        # Check the first token to see what kind of statement this is.

        # "IPAKITA" (expression | string)
        if self.checkToken(TokenType.IPAKITA):
            self.nextToken()

            if self.checkToken(TokenType.PANGUNGUSAP):
                # Simple string.
                self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
                self.nextToken()
            else:
                # Expect an expression.
                self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                self.emitter.emitLine("));")
                # "IF" comparison "THEN" {statement} "ENDIF"

        elif self.checkToken(TokenType.KUNG):
            self.nextToken()
            self.emitter.emit("if(")
            self.comparison()

            self.match(TokenType.EDI)
            self.nl()
            self.emitter.emitLine("){")

                # Zero or more statements in the body.
            while not self.checkToken(TokenType.KUNGKATAPUSAN):
                self.statement()

            self.match(TokenType.KUNGKATAPUSAN)
            self.emitter.emitLine("}")

        elif self.checkToken(TokenType.HABANG):
            self.nextToken()
            self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.ULITIN)
            self.nl()
            self.emitter.emitLine("){")

            # Zero or more statements in the loop body.
            while not self.checkToken(TokenType.HABANGKATAPUSAN):
                self.statement()

            self.match(TokenType.HABANGKATAPUSAN)
            self.emitter.emitLine("}")

            # "LABEL" ident
        elif self.checkToken(TokenType.TATAK):
            self.nextToken()

            # Siguraduhing walang label before kasi masakit magmahal
            # if kabit ka lang pala
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.emitter.emitLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.checkToken(TokenType.PUNTAHAN):
            print("STATEMENT-GOTO")
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.emitter.emitLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)

        # "LET" ident "=" expression 
        # Asignatura ni siya
        elif self.checkToken(TokenType.ITAKDA):
            self.nextToken()

            #  Check if ident exists in symbol table. If not, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            self.emitter.emit(self.curToken.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            
            self.expression()
            self.emitter.emitLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.IPASOK):
            self.nextToken()

            #If wala pang variable. Declare mo na! Wag ka na mag intay
            #Makuha pa siya ng iba
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")


            self.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
            self.emitter.emitLine(self.curToken.text + " = 0;")
            self.emitter.emit("scanf(\"%")
            self.emitter.emitLine("*s\");")
            self.emitter.emitLine("}")
            self.match(TokenType.IDENT)

        # This is not a valid statement. Error!
        else:
            self.abort("Invalid statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")

        # Newline.
        self.nl()

    def nl(self):
        print("NEWLINE")

        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):
        self.expression()
        # Must be at least one comparison operator and another expression.
        if self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

        # Can have 0 or more comparison operator and expressions.
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

     # Return true if the current token is a comparison operator.
    def isComparisonOperator(self):
           return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

    def expression(self):
        self.term()
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PAGPAPARAMI) or self.checkToken(TokenType.PAGBABAWAS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

     # term ::= unary {( "/" | "*" ) unary}
    def term(self):
        self.unary()
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()


    # unary ::= ["+" | "-"] primary
    def unary(self):
        # Optional unary +/-
        if self.checkToken(TokenType.PAGPAPARAMI) or self.checkToken(TokenType.PAGBABAWAS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()        
        self.primary()
    
    # primary ::= number | ident
    def primary(self):
        if self.checkToken(TokenType.NUMERO): 
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            # Error!
            self.abort("Unexpected token at " + self.curToken.text)