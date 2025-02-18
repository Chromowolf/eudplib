#include <string>
#include <stdexcept>
#include <vector>
#include <regex>
#include <iostream>

#include "generator/pygen.h"
#include "generator/eudplibGlobals.h"
#include "parserUtilities.h"

extern int currentTokenizingLine;
extern std::string currentModule;

int errorn = 0;

void throw_error(int code, const std::string& message, int line) {
    if (line == -1) line = currentTokenizingLine;
    if (errorn < 100) {
        std::cerr << "[Error " << code << "] Module \"" << currentModule << "\" Line " << line << " : " << message << std::endl;
        (*pGen) << "# [Error " << code << "] Line " << line << " : " << message << std::endl;
        if (++errorn == 100) {
            std::cerr << " - More than 100 errors occured. Stop printing errors" << std::endl;
        }
    }
}

int resetParserErrorNum() {
    errorn = 0;
    return 0;
}

int getParseErrorNum() {
    return errorn;
}


////

void writeCsOpener(std::ostream& os, const Token* csOpener, const Token* lexpr) {
    os << "if " << csOpener->data;
    applyNegativeOptimization(os, lexpr);
    os << ":" << std::endl;
}

void applyNegativeOptimization(std::ostream& os, const Token *lexpr) {
    if(lexpr->type == TOKEN_LNOT) {
        os << "(" << lexpr->subToken[0]->data << ", neg=True)";
    }
    else if(lexpr->type == TOKEN_NE) {
        os << "(" << lexpr->subToken[0]->data << " == " << lexpr->subToken[1]->data << ", neg=True)";
    }
    else {
        os << "(" << lexpr->data << ")";
    }
}



void commaListIter(std::string& s, std::function<void(std::string&)> func) {
    if (s.empty()) return;

    bool isFirst = true;
    std::string out;
    const char *p = s.c_str(), *p2 = p;
    while(1) {
        while(*p2 != '\0' && *p2 != ',') p2++;
        std::string value(p, p2 - p);
        func(value);
        if(isFirst) isFirst = false;
        else out += ", ";
        out += value;
        if(*p2 == '\0') break;
        p2++;
        while(*p2 == ' ') p2++;
        p = p2;
    }
    s = out;
}

void writeStringList(std::ostream& os, const std::vector<std::string>& slist) {
    if(!slist.empty()) {
        os << slist[0];
        for(size_t i = 1 ; i < slist.size() ; i++) {
            os << ", " << slist[i];
        }
    }
}

void funcNamePreprocess(std::string& s) {
    if(strncmp(s.c_str(), "py_", 3) == 0) return; // Builtin function?
    else if(isBuiltinConst(s)) return;  // Some builtin function don't have f_ prefixes. (b2i4) Pass them as-is
    else if(s[0] == '_' || ('A' <= s[0] && s[0] <= 'Z')) return;  // Name starts with uppercase -> Don't modify
    else s = "f_" + s;
}

void impPathProcess(const std::string& s, std::string& impPath, std::string& impModname) {
    // Preprocess python module.
    auto lastDot = s.find_last_of('.');
    std::string path, modname;
    if(lastDot == std::string::npos) {
        modname = s;
    }
    else {
        path = s.substr(0, lastDot);
        modname = s.substr(lastDot + 1);
    }
    if(strncmp(modname.c_str(), "py_", 3) == 0) {
        impPath = path;
        impModname = modname.substr(3);
    }
    else {
        impPath = path;
        impModname = modname;
    }
}

////


std::string trim(std::string s) {
    // ltrim
    size_t startpos = s.find_first_not_of(" \n\t");
    if (std::string::npos != startpos)
    {
        s = s.substr(startpos);
    }

    // rtrim
    size_t endpos = s.find_last_not_of(" \n\t");
    if (std::string::npos != endpos)
    {
        s = s.substr(0, endpos + 1);
    }
    return s;
}


static std::regex iwCollapseRegex("\n( *)(_t\\d+) = (EUDWhile|EUDIf|EUDElseIf)\\(\\)\n\\1if \\2\\((.+)\\):");
std::string iwCollapse(const std::string& in) {
    return std::regex_replace(in, iwCollapseRegex, "\n$1if $3()($4):");
}

const char* stubCode =
        "## NOTE: THIS FILE IS GENERATED BY EPSCRIPT! DO NOT MODITY\n"
        "from eudplib import *\n"
        "\n"
        "def _RELIMP(path, mod_name):\n"
        "    import inspect, pathlib, importlib.util\n"
        "    p = pathlib.Path(inspect.getabsfile(inspect.currentframe())).parent\n"
        "    for s in path.split(\".\"):\n"
        "        if s == \"\":  p = p.parent\n"
        "        else:  p = p / s\n"
        "    try:\n"
        "        spec = importlib.util.spec_from_file_location(mod_name, p / (mod_name + \".py\"))\n"
        "        module = importlib.util.module_from_spec(spec)\n"
        "        spec.loader.exec_module(module)\n"
        "    except FileNotFoundError:\n"
        "        loader = EPSLoader(mod_name, str(p / (mod_name + \".eps\")))\n"
        "        spec = importlib.util.spec_from_loader(mod_name, loader)\n"
        "        module = loader.create_module(spec)\n"
        "        loader.exec_module(module)\n"
        "    return module\n"
        "\n"
        "def _IGVA(vList, exprListGen):\n"
        "    def _():\n"
        "        exprList = exprListGen()\n"
        "        SetVariables(vList, exprList)\n"
        "    EUDOnStart(_)\n"
        "\n"
        "def _CGFW(exprf, retn):\n"
        "    rets = [ExprProxy(None) for _ in range(retn)]\n"
        "    def _():\n"
        "        vals = exprf()\n"
        "        for ret, val in zip(rets, vals):\n"
        "            ret._value = val\n"
        "    EUDOnStart(_)\n"
        "    return rets\n"
        "\n"
        "def _ARR(items):\n"
        "    k = EUDArray(len(items))\n"
        "    for i, item in enumerate(items):\n"
        "        k[i] = item\n"
        "    return k\n"
        "\n"
        "def _VARR(items):\n"
        "    k = EUDVArray(len(items))()\n"
        "    for i, item in enumerate(items):\n"
        "        k[i] = item\n"
        "    return k\n"
        "\n"
        "def _SRET(v, klist):\n"
        "    return List2Assignable([v[k] for k in klist])\n"
        "\n"
        "def _SV(dL, sL):\n"
        "    [d << s for d, s in zip(FlattenList(dL), FlattenList(sL))]\n"
        "\n"
        "class _ATTW:\n"
        "    def __init__(self, obj, attrName):\n"
        "        self.obj = obj\n"
        "        self.attrName = attrName\n"
        "\n"
        "    def __lshift__(self, r):\n"
        "        setattr(self.obj, self.attrName, r)\n"
        "\n"
        "    def __iadd__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov + v)\n"
        "\n"
        "    def __isub__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov - v)\n"
        "\n"
        "    def __imul__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov * v)\n"
        "\n"
        "    def __ifloordiv__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov // v)\n"
        "\n"
        "    def __iand__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov & v)\n"
        "\n"
        "    def __ior__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov | v)\n"
        "\n"
        "    def __ixor__(self, v):\n"
        "        ov = getattr(self.obj, self.attrName)\n"
        "        setattr(self.obj, self.attrName, ov ^ v)\n"
        "\n"
        "class _ARRW:\n"
        "    def __init__(self, obj, index):\n"
        "        self.obj = obj\n"
        "        self.index = index\n"
        "\n"
        "    def __lshift__(self, r):\n"
        "        self.obj[self.index] = r\n"
        "\n"
        "    def __iadd__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov + v\n"
        "\n"
        "    def __isub__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov - v\n"
        "\n"
        "    def __imul__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov * v\n"
        "\n"
        "    def __ifloordiv__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov // v\n"
        "\n"
        "    def __iand__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov & v\n"
        "\n"
        "    def __ior__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov | v\n"
        "\n"
        "    def __ixor__(self, v):\n"
        "        ov = self.obj[self.index]\n"
        "        self.obj[self.index] = ov ^ v\n"
        "\n"
        "def _L2V(l):\n"
        "    ret = EUDVariable()\n"
        "    if EUDIf()(l):\n"
        "        ret << 1\n"
        "    if EUDElse()():\n"
        "        ret << 0\n"
        "    EUDEndIf()\n"
        "    return ret\n"
        "\n"
        "def _MVAR(vs):\n"
        "    return List2Assignable([\n"
        "        v.makeL() if IsEUDVariable(v) else EUDVariable() << v\n"
        "        for v in FlattenList(vs)])\n"
        "\n"
        "def _LSH(l, r):\n"
        "    if IsEUDVariable(l):  return f_bitlshift(l, r)\n"
        "    else: return l << r\n"
        "\n"
        "## NOTE: THIS FILE IS GENERATED BY EPSCRIPT! DO NOT MODITY\n\n";

std::string addStubCode(const std::string& s) {
    return stubCode + s;
}
