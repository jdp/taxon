start
  = expr

expr
  = tag
  / fn

tag
  = "\"" str:[A-Za-z0-9\-\_]+ "\"" { return str.join(""); }

fn
  = name:fnName "(" _* args:fnArgList+ _* ")" {
      var e = {};
      e[name] = args[0];
      return e;
    }

fnName
  = "and"
  / "or"
  / "not"

fnArgList
  = head:expr _* tail:("," _* expr)* {
      var res = [head];
      for (i = 0; i < tail.length; i++) {
        res.push(tail[i][2]);
      }
      return res; 
    }

_
  = [ \t\n]