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
            std::cerr << " - More than 100 errors occurred. Stop printing errors" << std::endl;
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
    "from eudplib.epscript.helper import _RELIMP, _IGVA, _CGFW, _ARR, _VARR, _SRET, _SV, _ATTW, _ARRW, _ARRC, _L2V, _LVAR, _LSH\n";

std::string addStubCode(const std::string& s) {
    return stubCode + s;
}
