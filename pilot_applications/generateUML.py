'''
created on 09.05.2018

author twirtz
'''

import re
import os
from typing import List, Tuple

CLASSSTRUCTNAME_PATTERN     = "(class\s+)([A-Za-z0-9]+)(\(([A-Za-z0-9,\s]*)\))?:"
MEMBERFUNCTIONSTRUCTURE_PATTERN   = '[\s]+(def)\s+([_A-Za-z0-9]+)\(([\[\]_A-Za-z0-9,:="\s]*)\)(\s*->\s*([\(\)\[\]\s,A-Za-z0-9]+))?:'#"[\s]+(def)\s+([_A-Za-z0-9]+)\(([\[\]_A-Za-z0-9,:\s]*)\)(\s*->\s*([\[\]A-Za-z0-9]+))?:"
FUNCTIONSTRUCTURE_PATTERN   = "(def)\s+([_A-Za-z0-9]+)\(([\[\]_A-Za-z0-9,:\s]*)\)(\s*->\s*([\[\]A-Za-z0-9]+))?:"
class argType:

    def __init__(self,
                 name : str,
                 type = None):
        self.name = name
        self.type = type

    def __str__(self):
        strRep = self.name
        if self.type is not None:
            return strRep + " : " + str(self.type)
        else:
            return strRep

class functType:

    def __init__(self,
                 name       : str,
                 returnType = None):

        self._argList   = []
        self.name       = name
        self.returnType = returnType

    def addArg(self,arg : argType):
        self._argList.append(arg)

    def __str__(self):
        strRep = self.name + "("

        for arg in self._argList:
            strRep = strRep + str(arg) + ", "

        if len(self._argList) >0:
            strRep = strRep[:-2] + ")" +( "" if self.returnType is None else " : " + self.returnType)
        else:
            strRep = strRep + ")" + ("" if self.returnType is None else " : " + self.returnType)

        return strRep

class classType:

    def __init__(self,
                 name : str):
        self.name               = name
        self._memFuncList       = []
        self._parentClassList   = []


    def addParentClass(self, cl : str):
        self._parentClassList.append(cl)

    def addMemberFunction(self, func : functType):
        self._memFuncList.append(func)

    def __str__(self):
        strRep = ""

        for cl in self._parentClassList:
            strRep = strRep + cl + " --> " + self.name +"\n"

        strRep = strRep + "class " + self.name + "{\n"

        for f in self._memFuncList:
            strRep = strRep + "+" + str(f) + "\n"

        strRep = strRep + "}"

        return strRep

def processArg(arg : str):
    args = arg.split(":")

    if len(args) == 1 :
        return argType(args[0])
    elif len(args) ==2 :
        return argType(args[0].strip(),args[1].strip())


def getPythonScripts(files: List[str]):
    '''

    Parameters
    ----------
    files

    Returns
    -------

    '''
    pythonScripts = []

    for f in files:
        n = os.path.splitext(f)
        if len(n) is not 2:
            continue
        if (n[1] == ".py") &(n[0] != "__init__"):
            pythonScripts.append(f)

    return pythonScripts

def transformPathToPackageStructure(path : str):
    '''

    Parameters
    ----------
    path

    Returns
    -------

    '''

    if len(path) == 0:
        return "."
    else:
        return path.replace("//",".").replace("\\",".").replace("\/",".")

def printPackageStructure(struc: List[Tuple]):
    '''

    Parameters
    ----------
    struc

    Returns
    -------

    '''
    for p, fl,_ in moduleList:
        print("package:",p)
        for f in fl:
            print("\tmodule:",os.path.splitext(f)[0])

if __name__ == "__main__":
    rootDirPath = os.getcwd() + "/../"

    moduleList =[]

    for path, dirs, files in os.walk(rootDirPath):
        moduleList.append((transformPathToPackageStructure(path[len(rootDirPath):]),getPythonScripts(files),path))

    moduleList = list(filter(lambda  x : len(x[1]) != 0, moduleList))

    printPackageStructure(moduleList)

    class_pattern = re.compile(CLASSSTRUCTNAME_PATTERN)
    funct_pattern = re.compile(MEMBERFUNCTIONSTRUCTURE_PATTERN)

    fileName = moduleList[2][1][-1]

    umlRep = "@startuml\n"

    for n, ml , p in moduleList:
        for m in ml:


            with open(p +"/"  + m) as f:
                currentClass = None
                for line in f.readlines():
                    classRegEx = class_pattern.search(line)
                    functRegEx = funct_pattern.search(line)
                    if classRegEx is not None:
                        if currentClass is not None:
                            umlRep = umlRep + "\n" + str(currentClass)
                        className, dependencies = classRegEx.group(2),classRegEx.group(4)
                        currentClass = classType(className)
                        if (dependencies is not None) & (dependencies != ""):
                            for a in dependencies.split(","):
                                currentClass.addParentClass(a.strip())
                    elif functRegEx is not None:
                        funcName, args, rt  = functRegEx.group(2), functRegEx.group(3), functRegEx.group(5)
                        funcStr             = functType(name = funcName, returnType = rt)

                        for a in args.split(","):
                            arg = processArg(a)
                            if arg.name =="self":
                                continue
                            funcStr.addArg(arg)
                        currentClass.addMemberFunction(funcStr)
                if currentClass is not None:
                    umlRep = umlRep + "\n" + str(currentClass)

    umlRep = umlRep + "\n@enduml"
    with open(rootDirPath + "/concept/library_uml.uml","w") as f:
        f.writelines(umlRep)
