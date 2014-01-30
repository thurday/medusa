#!/usr/bin/python

import ast, _ast, sys

imports = []
funVars = []
symTab = []

funMode = False
func = 0

debug_notification = "**** Medusa Notification ****"
debug_warning = "**** Medusa Warning ****"
debugging_message = "**** Medusa Debug ****"
debug_error = "**** Medusa Error ****"

operators = dict()
operators['_ast.Eq'] = "=="
operators['_ast.Gt'] = ">"
operators['_ast.GtE'] = ">="
operators['_ast.Lt'] = "<"
operators['_ast.LtE'] = "<="
operators['_ast.NotEq'] = "!="

outFile = open("out.dart", 'w')
code = "void main() {"

class MyParser(ast.NodeVisitor):
    def __init__(self):
        pass

    def parse(self, code):
        tree = ast.parse(code)
        self.visit(tree)

    def escape(self, s):
        s = s.replace('\\', '\\\\')
        s = s.replace('\n', r'\n')
        s = s.replace('\t', r'\t')
        s = s.replace('\r', r'\r')

        return s

    def parseList(self, theList):
        strList = "["
        i = 0
        l = len(theList)

        while i < l:
            item = theList[i]

            if isinstance(item, _ast.Num):
                v = item.n
            elif isinstance(item, _ast.Name):
                v = item.id
            elif isinstance(item, _ast.Str):
                v = "'" + item.s + "'"
            elif isinstance(item, _ast.List):
                v = self.parseList(item.elts)
            elif isinstance(item, _ast.BinOp):
                v = self.parseExp(item)

            strList += str(v)
            if (i + 1) < l:
                strList += ", "
            i += 1

        strList += "]"
        return strList

    def parseExp(self, expr):
        exp = ""

        if isinstance(expr.left, _ast.BinOp):
            exp += self.parseExp(expr.left)
        else:
            if hasattr(expr.left, 'n'):
                exp += str(expr.left.n)
            else:
                exp += str(expr.left.id)

        if isinstance(expr.op, _ast.Add):
            exp += " + "
        elif isinstance(expr.op, _ast.Sub):
            exp += " - "
        elif isinstance(expr.op, _ast.Mult):
            exp += " * "
        else:
            exp += " / "

        if isinstance(expr.right, _ast.BinOp):
            exp += self.parseExp(expr.right)
        else:
            if hasattr(expr.right, 'n'):
                exp += str(expr.right.n)
            else:
                exp += str(expr.right.id)

        return "(" + exp + ")" #Saxx

    def visit_Print(self, stmt_print):
        global code

        if imports.__contains__("dart:io") == False:
            imports.append("dart:io")

        data = ""
        i = 0
        values = len(stmt_print.values)
        while (i < values):
            code += " stdout.write("

            if isinstance(stmt_print.values[i], _ast.Str):
                data = "'" + self.escape(stmt_print.values[i].s) + "'"
            elif isinstance(stmt_print.values[i], _ast.Num):
                data = stmt_print.values[i].n
            elif isinstance(stmt_print.values[i], _ast.Name):
                data = stmt_print.values[i].id
            elif isinstance(stmt_print.values[i], _ast.List):
                data = self.parseList(stmt_print.values[i].elts)
            elif isinstance(stmt_print.values[i], _ast.BinOp):
                data = self.parseExp(stmt_print.values[i])

            code += str(data) + ");"
            if (i + 1) < values:
                code += " stdout.write(' ');"
            else:
                code += " stdout.write('\\n');";
            i += 1

    def visit_Assign(self, stmt_assign):
        global code, funVars

        for target in stmt_assign.targets:
            if funMode:
                if symTab.__contains__(target.id) == False:
                    symTab.append(target.id)
                    code += " var"
            else:
                if funVars.__contains__(target.id) == False:
                    funVars.append(target.id)
                    code += " var"

            if isinstance(stmt_assign.value, _ast.Num):
                value = stmt_assign.value.n
            elif isinstance(stmt_assign.value, _ast.Str):
                value = "'" + stmt_assign.value.s + "'"
            elif isinstance(stmt_assign.value, _ast.List):
                value = self.parseList(stmt_assign.value.elts)
            elif isinstance(stmt_assign.value, _ast.Name):
                value = stmt_assign.value.id
            elif isinstance(stmt_assign.value, _ast.BinOp):
                value = self.parseExp(stmt_assign.value)

            code += " " + target.id + " = " + str(value) + ";"

    def visit_If(self, stmt_if):
        global code

        code += "if("
        if hasattr(stmt_if.test, 'left'):
            varType = str(type(stmt_if.test.left))[13:-2]
            if varType == "Name":
                if stmt_if.test.left.id == 'True':
                    code += "true"
                elif stmt_if.test.left.id == 'False':
                    code += "false"
                else:
                    code += stmt_if.test.left.id
            elif varType == "Str":
                code += stmt_if.test.left.s
            elif varType == "Num":
                code += str(stmt_if.test.left.n)
            elif varType == "BinOp":
                code += self.parseExp(stmt_if.test.left)
            else:
                print debug_warning
                print "Type not recognized => ", varType
        elif str(type(stmt_if.test))[13:-2] == "Name":
            if stmt_if.test.id == "True":
                code += "true"
            elif stmt_if.test.id == "False":
                code += "false"
            else:
                print type(stmt_if.test.id)

        if hasattr(stmt_if.test, 'ops'):
            code += operators[str(type(stmt_if.test.ops[0]))[8:-2]]

        if hasattr(stmt_if.test, 'comparators'):
            varType = str(type(stmt_if.test.comparators[0]))[13:-2]
            if varType == "Name":
                if stmt_if.test.comparators[0].id == 'True':
                    code += "true"
                elif stmt_if.test.comparators[0].id == 'False':
                    code += "false"
                else:
                    code += stmt_if.test.comparators[0].id
            elif varType == "Str":
                code += stmt_if.test.comparators[0].s
            elif varType == "Num":
                code += str(stmt_if.test.comparators[0].n)
            elif varType == "BinOp":
                code += self.parseExp(stmt_if.test.comparators[0])
            else:
                print debug_warning
                print "Type not recognized => ", varType

        code += ") {"
        for node in stmt_if.body:
            self.visit(node)

        code += "}"
        if len(stmt_if.orelse) > 0:
            code += " else {"
            for node in stmt_if.orelse:
                self.visit(node)
            code += "}"

    def visit_For(self, stmt_For):
        global code

        code += "var flag = false; "
        code += " for (var "
        code += stmt_For.target.id
        code += " in "
        code += stmt_For.iter.id
        code += " ) {"

        for node in stmt_For.body:
            self.visit(node)
        code += "}"

        if len(stmt_For.orelse) > 0:
            for node in stmt_For.orelse:
                self.visit(node)

    def visit_While(self, stmt_while):
        global code

        code += " while ("
        varType = str(type(stmt_while.test.left))[13:-2]

        if varType == "Name":
            if stmt_while.test.left.id == 'True':
                code += "true"
            elif stmt_while.test.left.id == 'False':
                code += "false"
            else:
                code += stmt_while.test.left.id
        elif varType == "Str":
           code += stmt_while.test.left.s
        elif varType == "Num":
            code += str(stmt_while.test.left.n)
        else:
            print debug_warning
            print "Type not recognized => ", varType

        code += operators[str(type(stmt_while.test.ops[0]))[8:-2]]
        varType = str(type(stmt_while.test.comparators[0]))[13:-2]

        if varType == "Name":
            if stmt_while.test.comparators[0].id == 'True':
                code += "true"
            elif stmt_while.test.comparators[0].id == 'False':
                code += "false"
            else:
                code += stmt_while.test.comparators[0].id
        elif varType == "Str":
            code += stmt_while.test.comparators[0].s
        elif varType == "Num":
            code += str(stmt_while.test.comparators[0].n)
        else:
            print debug_warning
            print "Type not recognized => ", varType

        code += ") "
        code += " {"
        for node in stmt_while.body:
            self.visit(node)

        code += stmt_while.test.left.id
        code += "++; "
        code += "}"

    def visit_FunctionDef(self, stmt_function):
        global code, funVars

        temp = code
        code = ""
        funMode = True

        alen = len(stmt_function.args.args)
        code = stmt_function.name + "("

        if alen == 0:
            code += ") {"
        else:
            i = 0
            while i < alen:
                code += stmt_function.args.args[i].id
                funVars.append(stmt_function.args.args[i].id)

                if (i + 1) < alen:
                    code += ", "
                else:
                    code += ") {"
                i += 1

        for node in stmt_function.body:
            self.visit(node)
        funMode = False
        code += " } "
        funVars = []

        code = code + temp

    def visit_Call(self, stmt_call):
        global code

        code += " " + stmt_call.func.id + "("
        alen = len(stmt_call.args)

        if alen == 0:
            code += ");"
        else:
            i = 0
            while i < alen:
                if isinstance(stmt_call.args[i], _ast.Name):
                    p = stmt_call.args[i].id
                elif isinstance(stmt_call.args[i], _ast.Num):
                    p = stmt_call.args[i].n
                elif isinstance(stmt_call.args[i], _ast.Str):
                    p = "'" + stmt_call.args[i].s + "'"
                elif isinstance(stmt_call.args[i], _ast.List):
                    p = self.parseList(stmt_call.args[i].elts)
                elif isinstance(stmt_call.args[i], _ast.BinOp):
                    p = self.parseExp(stmt_call.args[i])

                code += str(p)

                if (i + 1) < alen:
                    code += ", "
                else:
                    code += ");"
                i += 1

MyParser().parse(open(sys.argv[1]).read())

code += " }"

for imp in imports:
    code = "import '" + imp + "'; " + code

outFile.write(code)
outFile.close()