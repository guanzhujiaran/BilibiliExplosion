var r, i, o;
function a(t, e) {
    var n = "undefined" != typeof Symbol && t[Symbol.iterator] || t["@@iterator"];
    if (!n) {
        if (Array.isArray(t) || (n = C(t)) || e && t && "number" == typeof t.length) {
            n && (t = n);
            var r = 0
              , i = function() {};
            return {
                s: i,
                n: function() {
                    return r >= t.length ? {
                        done: !0
                    } : {
                        done: !1,
                        value: t[r++]
                    }
                },
                e: function(t) {
                    throw t
                },
                f: i
            }
        }
        throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
    }
                var o, a = !0, s = !1;
                return {
                    s: function() {
                        n = n.call(t)
                    },
                    n: function() {
                        var t = n.next();
                        return a = t.done,
                        t
                    },
                    e: function(t) {
                        s = !0,
                        o = t
                    },
                    f: function() {
                        try {
                            a || null == n.return || n.return()
                        } finally {
                            if (s)
                                throw o
                        }
                    }
                }
            }
            function s(t, e, n) {
                return e = c(e),
                function(t, e) {
                    if (e && ("object" === O(e) || "function" == typeof e))
                        return e;
                    if (void 0 !== e)
                        throw new TypeError("Derived constructors may only return object or undefined");
                    return function(t) {
                        if (void 0 === t)
                            throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
                        return t
                    }(t)
                }(t, function() {
                    try {
                        var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], (function() {}
                        )))
                    } catch (t) {console.error(t)}
                    return function() {
                        return !!t
                    }()
                }() ? Reflect.construct(e, n || [], c(t).constructor) : e.apply(t, n))
            }
            function c(t) {
                return (c = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function(t) {
                    return t.__proto__ || Object.getPrototypeOf(t)
                }
                )(t)
            }
            function u(t, e) {
                return (u = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function(t, e) {
                    return t.__proto__ = e,
                    t
                }
                )(t, e)
            }
            function l(t, e) {
                var n = Object.keys(t);
                if (Object.getOwnPropertySymbols) {
                    var r = Object.getOwnPropertySymbols(t);
                    e && (r = r.filter((function(e) {
                        return Object.getOwnPropertyDescriptor(t, e).enumerable
                    }
                    ))),
                    n.push.apply(n, r)
                }
                return n
            }
            function f(t) {
                for (var e = 1; e < arguments.length; e++) {
                    var n = null != arguments[e] ? arguments[e] : {};
                    e % 2 ? l(Object(n), !0).forEach((function(e) {
                        p(t, e, n[e])
                    }
                    )) : Object.getOwnPropertyDescriptors ? Object.defineProperties(t, Object.getOwnPropertyDescriptors(n)) : l(Object(n)).forEach((function(e) {
                        Object.defineProperty(t, e, Object.getOwnPropertyDescriptor(n, e))
                    }
                    ))
                }
                return t
            }
            function p(t, e, n) {
                return (e = w(e))in t ? Object.defineProperty(t, e, {
                    value: n,
                    enumerable: !0,
                    configurable: !0,
                    writable: !0
                }) : t[e] = n,
                t
            }
            function d(t, e) {
                return function(t) {
                    if (Array.isArray(t))
                        return t
                }(t) || function(t, e) {
                    var n = null == t ? null : "undefined" != typeof Symbol && t[Symbol.iterator] || t["@@iterator"];
                    if (null != n) {
                        var r, i, o, a, s = [], c = !0, u = !1;
                        try {
                            if (o = (n = n.call(t)).next,
                            0 === e) {
                                if (Object(n) !== n)
                                    return;
                                c = !1
                            } else
                                for (; !(c = (r = o.call(n)).done) && (s.push(r.value),
                                s.length !== e); c = !0)
                                    ;
                        } catch (t) {
                            console.error(t)
                            u = !0,
                            i = t
                        } finally {
                            try {
                                if (!c && null != n.return && (a = n.return(),
                                Object(a) !== a))
                                    return
                            } finally {
                                if (u)
                                    throw i
                            }
                        }
                        return s
                    }
                }(t, e) || C(t, e) || function() {
                    throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
                }()
            }
            function h() {
                "use strict";
                /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/facebook/regenerator/blob/main/LICENSE */
                h = function() {
                    return e
                }
                ;
                var t, e = {}, n = Object.prototype, r = n.hasOwnProperty, i = Object.defineProperty || function(t, e, n) {
                    t[e] = n.value
                }
                , o = "function" == typeof Symbol ? Symbol : {}, a = o.iterator || "@@iterator", s = o.asyncIterator || "@@asyncIterator", c = o.toStringTag || "@@toStringTag";
                function u(t, e, n) {
                    return Object.defineProperty(t, e, {
                        value: n,
                        enumerable: !0,
                        configurable: !0,
                        writable: !0
                    }),
                    t[e]
                }
                try {
                    u({}, "")
                } catch (t) {
                    console.error(t)
                    u = function(t, e, n) {
                        return t[e] = n
                    }
                }
                function l(t, e, n, r) {
                    var o = e && e.prototype instanceof g ? e : g
                      , a = Object.create(o.prototype)
                      , s = new I(r || []);
                    return i(a, "_invoke", {
                        value: T(t, n, s)
                    }),
                    a
                }
                function f(t, e, n) {
                    try {
                        return {
                            type: "normal",
                            arg: t.call(e, n)
                        }
                    } catch (t) {
                        console.error(t)
                        return {
                            type: "throw",
                            arg: t
                        }
                    }
                }
                e.wrap = l;
                var p = "suspendedStart"
                  , d = "executing"
                  , v = "completed"
                  , m = {};
                function g() {}
                function y() {}
                function b() {}
                var w = {};
                u(w, a, (function() {
                    return this
                }
                ));
                var _ = Object.getPrototypeOf
                  , C = _ && _(_(j([])));
                C && C !== n && r.call(C, a) && (w = C);
                var x = b.prototype = g.prototype = Object.create(w);
                function S(t) {
                    ["next", "throw", "return"].forEach((function(e) {
                        u(t, e, (function(t) {
                            return this._invoke(e, t)
                        }
                        ))
                    }
                    ))
                }
                function E(t, e) {
                    function n(i, o, a, s) {
                        var c = f(t[i], t, o);
                        if ("throw" !== c.type) {
                            var u = c.arg
                              , l = u.value;
                            return l && "object" == O(l) && r.call(l, "__await") ? e.resolve(l.__await).then((function(t) {
                                n("next", t, a, s)
                            }
                            ), (function(t) {
                                n("throw", t, a, s)
                            }
                            )) : e.resolve(l).then((function(t) {
                                u.value = t,
                                a(u)
                            }
                            ), (function(t) {
                                return n("throw", t, a, s)
                            }
                            ))
                        }
                        s(c.arg)
                    }
                    var o;
                    i(this, "_invoke", {
                        value: function(t, r) {
                            function i() {
                                return new e((function(e, i) {
                                    n(t, r, e, i)
                                }
                                ))
                            }
                            return o = o ? o.then(i, i) : i()
                        }
                    })
                }
                function T(e, n, r) {
                    var i = p;
                    return function(o, a) {
                        if (i === d)
                            throw Error("Generator is already running");
                        if (i === v) {
                            if ("throw" === o)
                                throw a;
                            return {
                                value: t,
                                done: !0
                            }
                        }
                        for (r.method = o,
                        r.arg = a; ; ) {
                            var s = r.delegate;
                            if (s) {
                                var c = k(s, r);
                                if (c) {
                                    if (c === m)
                                        continue;
                                    return c
                                }
                            }
                            if ("next" === r.method)
                                r.sent = r._sent = r.arg;
                            else if ("throw" === r.method) {
                                if (i === p)
                                    throw i = v,
                                    r.arg;
                                r.dispatchException(r.arg)
                            } else
                                "return" === r.method && r.abrupt("return", r.arg);
                            i = d;
                            var u = f(e, n, r);
                            if ("normal" === u.type) {
                                if (i = r.done ? v : "suspendedYield",
                                u.arg === m)
                                    continue;
                                return {
                                    value: u.arg,
                                    done: r.done
                                }
                            }
                            "throw" === u.type && (i = v,
                            r.method = "throw",
                            r.arg = u.arg)
                        }
                    }
                }
                function k(e, n) {
                    var r = n.method
                      , i = e.iterator[r];
                    if (i === t)
                        return n.delegate = null,
                        "throw" === r && e.iterator.return && (n.method = "return",
                        n.arg = t,
                        k(e, n),
                        "throw" === n.method) || "return" !== r && (n.method = "throw",
                        n.arg = new TypeError("The iterator does not provide a '" + r + "' method")),
                        m;
                    var o = f(i, e.iterator, n.arg);
                    if ("throw" === o.type)
                        return n.method = "throw",
                        n.arg = o.arg,
                        n.delegate = null,
                        m;
                    var a = o.arg;
                    return a ? a.done ? (n[e.resultName] = a.value,
                    n.next = e.nextLoc,
                    "return" !== n.method && (n.method = "next",
                    n.arg = t),
                    n.delegate = null,
                    m) : a : (n.method = "throw",
                    n.arg = new TypeError("iterator result is not an object"),
                    n.delegate = null,
                    m)
                }
                function L(t) {
                    var e = {
                        tryLoc: t[0]
                    };
                    1 in t && (e.catchLoc = t[1]),
                    2 in t && (e.finallyLoc = t[2],
                    e.afterLoc = t[3]),
                    this.tryEntries.push(e)
                }
                function A(t) {
                    var e = t.completion || {};
                    e.type = "normal",
                    delete e.arg,
                    t.completion = e
                }
                function I(t) {
                    this.tryEntries = [{
                        tryLoc: "root"
                    }],
                    t.forEach(L, this),
                    this.reset(!0)
                }
                function j(e) {
                    if (e || "" === e) {
                        var n = e[a];
                        if (n)
                            return n.call(e);
                        if ("function" == typeof e.next)
                            return e;
                        if (!isNaN(e.length)) {
                            var i = -1
                              , o = function n() {
                                for (; ++i < e.length; )
                                    if (r.call(e, i))
                                        return n.value = e[i],
                                        n.done = !1,
                                        n;
                                return n.value = t,
                                n.done = !0,
                                n
                            };
                            return o.next = o
                        }
                    }
                    throw new TypeError(O(e) + " is not iterable")
                }
                return y.prototype = b,
                i(x, "constructor", {
                    value: b,
                    configurable: !0
                }),
                i(b, "constructor", {
                    value: y,
                    configurable: !0
                }),
                y.displayName = u(b, c, "GeneratorFunction"),
                e.isGeneratorFunction = function(t) {
                    var e = "function" == typeof t && t.constructor;
                    return !!e && (e === y || "GeneratorFunction" === (e.displayName || e.name))
                }
                ,
                e.mark = function(t) {
                    return Object.setPrototypeOf ? Object.setPrototypeOf(t, b) : (t.__proto__ = b,
                    u(t, c, "GeneratorFunction")),
                    t.prototype = Object.create(x),
                    t
                }
                ,
                e.awrap = function(t) {
                    return {
                        __await: t
                    }
                }
                ,
                S(E.prototype),
                u(E.prototype, s, (function() {
                    return this
                }
                )),
                e.AsyncIterator = E,
                e.async = function(t, n, r, i, o) {
                    void 0 === o && (o = Promise);
                    var a = new E(l(t, n, r, i),o);
                    return e.isGeneratorFunction(n) ? a : a.next().then((function(t) {
                        return t.done ? t.value : a.next()
                    }
                    ))
                }
                ,
                S(x),
                u(x, c, "Generator"),
                u(x, a, (function() {
                    return this
                }
                )),
                u(x, "toString", (function() {
                    return "[object Generator]"
                }
                )),
                e.keys = function(t) {
                    var e = Object(t)
                      , n = [];
                    for (var r in e)
                        n.push(r);
                    return n.reverse(),
                    function t() {
                        for (; n.length; ) {
                            var r = n.pop();
                            if (r in e)
                                return t.value = r,
                                t.done = !1,
                                t
                        }
                        return t.done = !0,
                        t
                    }
                }
                ,
                e.values = j,
                I.prototype = {
                    constructor: I,
                    reset: function(e) {
                        if (this.prev = 0,
                        this.next = 0,
                        this.sent = this._sent = t,
                        this.done = !1,
                        this.delegate = null,
                        this.method = "next",
                        this.arg = t,
                        this.tryEntries.forEach(A),
                        !e)
                            for (var n in this)
                                "t" === n.charAt(0) && r.call(this, n) && !isNaN(+n.slice(1)) && (this[n] = t)
                    },
                    stop: function() {
                        this.done = !0;
                        var t = this.tryEntries[0].completion;
                        if ("throw" === t.type)
                            throw t.arg;
                        return this.rval
                    },
                    dispatchException: function(e) {
                        if (this.done)
                            throw e;
                        var n = this;
                        function i(r, i) {
                            return s.type = "throw",
                            s.arg = e,
                            n.next = r,
                            i && (n.method = "next",
                            n.arg = t),
                            !!i
                        }
                        for (var o = this.tryEntries.length - 1; o >= 0; --o) {
                            var a = this.tryEntries[o]
                              , s = a.completion;
                            if ("root" === a.tryLoc)
                                return i("end");
                            if (a.tryLoc <= this.prev) {
                                var c = r.call(a, "catchLoc")
                                  , u = r.call(a, "finallyLoc");
                                if (c && u) {
                                    if (this.prev < a.catchLoc)
                                        return i(a.catchLoc, !0);
                                    if (this.prev < a.finallyLoc)
                                        return i(a.finallyLoc)
                                } else if (c) {
                                    if (this.prev < a.catchLoc)
                                        return i(a.catchLoc, !0)
                                } else {
                                    if (!u)
                                        throw Error("try statement without catch or finally");
                                    if (this.prev < a.finallyLoc)
                                        return i(a.finallyLoc)
                                }
                            }
                        }
                    },
                    abrupt: function(t, e) {
                        for (var n = this.tryEntries.length - 1; n >= 0; --n) {
                            var i = this.tryEntries[n];
                            if (i.tryLoc <= this.prev && r.call(i, "finallyLoc") && this.prev < i.finallyLoc) {
                                var o = i;
                                break
                            }
                        }
                        o && ("break" === t || "continue" === t) && o.tryLoc <= e && e <= o.finallyLoc && (o = null);
                        var a = o ? o.completion : {};
                        return a.type = t,
                        a.arg = e,
                        o ? (this.method = "next",
                        this.next = o.finallyLoc,
                        m) : this.complete(a)
                    },
                    complete: function(t, e) {
                        if ("throw" === t.type)
                            throw t.arg;
                        return "break" === t.type || "continue" === t.type ? this.next = t.arg : "return" === t.type ? (this.rval = this.arg = t.arg,
                        this.method = "return",
                        this.next = "end") : "normal" === t.type && e && (this.next = e),
                        m
                    },
                    finish: function(t) {
                        for (var e = this.tryEntries.length - 1; e >= 0; --e) {
                            var n = this.tryEntries[e];
                            if (n.finallyLoc === t)
                                return this.complete(n.completion, n.afterLoc),
                                A(n),
                                m
                        }
                    },
                    catch: function(t) {
                        for (var e = this.tryEntries.length - 1; e >= 0; --e) {
                            var n = this.tryEntries[e];
                            if (n.tryLoc === t) {
                                var r = n.completion;
                                if ("throw" === r.type) {
                                    var i = r.arg;
                                    A(n)
                                }
                                return i
                            }
                        }
                        throw Error("illegal catch attempt")
                    },
                    delegateYield: function(e, n, r) {
                        return this.delegate = {
                            iterator: j(e),
                            resultName: n,
                            nextLoc: r
                        },
                        "next" === this.method && (this.arg = t),
                        m
                    }
                },
                e
            }
function v(t, e, n, r, i, o, a) {
                try {
                    var s = t[o](a)
                      , c = s.value
                } catch (t) {
                    console.error(t)
                    return void n(t)
                }
                s.done ? e(c) : Promise.resolve(c).then(r, i)
            }
            function m(t) {
                return function() {
                    var e = this
                      , n = arguments;
                    return new Promise((function(r, i) {
                        var o = t.apply(e, n);
                        function a(t) {
                            v(o, r, i, a, s, "next", t)
                        }
                        function s(t) {
                            v(o, r, i, a, s, "throw", t)
                        }
                        a(void 0)
                    }
                    ))
                }
            }
            function g(t, e) {
                if (!(t instanceof e))
                    throw new TypeError("Cannot call a class as a function")
            }
            function y(t, e) {
                for (var n = 0; n < e.length; n++) {
                    var r = e[n];
                    r.enumerable = r.enumerable || !1,
                    r.configurable = !0,
                    "value"in r && (r.writable = !0),
                    Object.defineProperty(t, w(r.key), r)
                }
            }
            function b(t, e, n) {
                return e && y(t.prototype, e),
                n && y(t, n),
                Object.defineProperty(t, "prototype", {
                    writable: !1
                }),
                t
            }
            function w(t) {
                var e = function(t, e) {
                    if ("object" != O(t) || !t)
                        return t;
                    var n = t[Symbol.toPrimitive];
                    if (void 0 !== n) {
                        var r = n.call(t, e || "default");
                        if ("object" != O(r))
                            return r;
                        throw new TypeError("@@toPrimitive must return a primitive value.")
                    }
                    return ("string" === e ? String : Number)(t)
                }(t, "string");
                return "symbol" == O(e) ? e : e + ""
            }
            function _(t) {
                return function(t) {
                    function x(t, e) {
                (null == e || e > t.length) && (e = t.length);
                for (var n = 0, r = new Array(e); n < e; n++)
                    r[n] = t[n];
                return r
            }
                    if (Array.isArray(t))
                        return x(t)
                }(t) || function(t) {
                    if ("undefined" != typeof Symbol && null != t[Symbol.iterator] || null != t["@@iterator"])
                        return Array.from(t)
                }(t) || C(t) || function() {
                    throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
                }()
            }
            function C(t, e) {
                if (t) {
                    if ("string" == typeof t)
                        return x(t, e);
                    var n = Object.prototype.toString.call(t).slice(8, -1);
                    return "Object" === n && t.constructor && (n = t.constructor.name),
                    "Map" === n || "Set" === n ? Array.from(t) : "Arguments" === n || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? x(t, e) : void 0
                }
            }

            function O(t) {
                return (O = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(t) {
                    return typeof t
                }
                : function(t) {
                    return t && "function" == typeof Symbol && t.constructor === Symbol && t !== Symbol.prototype ? "symbol" : typeof t
                }
                )(t)
            }
var t, e, n, o, a, s, c, u;
!function(t) {
                                        t[t.DEFAULT_SOURCE = 0] = "DEFAULT_SOURCE",
                                        t[t.ALBUM = 1] = "ALBUM",
                                        t[t.ARTICLE = 2] = "ARTICLE",
                                        t[t.NOTE = 3] = "NOTE",
                                        t[t.OGV_COMMENT = 4] = "OGV_COMMENT",
                                        t[t.ARTICLE_H5 = 5] = "ARTICLE_H5",
                                        t[t.WORD = 6] = "WORD",
                                        t[t.REPOST = 7] = "REPOST",
                                        t[t.MANGA_EP = 8] = "MANGA_EP"
                                    }(t || (t = {}))
,(u = e || (e = {}))[u.DEFAULT = 0] = "DEFAULT",
                                    u[u.TEXT = 1] = "TEXT",
                                    u[u.PICTURES = 2] = "PICTURES",
                                    u[u.LINE = 3] = "LINE",
                                    u[u.REFERENCE = 4] = "REFERENCE",
                                    u[u.SORTED_LIST = 5] = "SORTED_LIST",
                                    u[u.UNSORTED_LIST = 6] = "UNSORTED_LIST",
                                    u[u.LINK_CARD = 7] = "LINK_CARD",
                                    u[u.CODE = 8] = "CODE",
                                    function(t) {
                                        t[t.LEFT = 0] = "LEFT",
                                        t[t.MIDDLE = 1] = "MIDDLE",
                                        t[t.RIGHT = 2] = "RIGHT"
                                    }(n || (n = {})),
                                    function(t) {
                                        t[t.DEFAULT = 0] = "DEFAULT",
                                        t[t.WORDS = 1] = "WORDS",
                                        t[t.EMOTE = 2] = "EMOTE",
                                        t[t.AT = 3] = "AT",
                                        t[t.BIZ_LINK = 4] = "BIZ_LINK",
                                        t[t.FORMULA = 5] = "FORMULA"
                                    }(o || (o = {})),
                                    function(t) {
                                        t[t.DEFAULT = 0] = "DEFAULT",
                                        t[t.VIDEO = 1] = "VIDEO",
                                        t[t.RESERVE = 2] = "RESERVE",
                                        t[t.VOTE = 3] = "VOTE",
                                        t[t.LIVE = 4] = "LIVE",
                                        t[t.LOTTERY = 5] = "LOTTERY",
                                        t[t.MATCH = 6] = "MATCH",
                                        t[t.GOODS = 7] = "GOODS",
                                        t[t.OGV_SS = 8] = "OGV_SS",
                                        t[t.OGV_EP = 9] = "OGV_EP",
                                        t[t.MANGA = 10] = "MANGA",
                                        t[t.CHEESE = 11] = "CHEESE",
                                        t[t.VIDEO_TS = 12] = "VIDEO_TS",
                                        t[t.AT = 13] = "AT",
                                        t[t.HASH_TAG = 14] = "HASH_TAG",
                                        t[t.CV = 15] = "CV",
                                        t[t.URL = 16] = "URL",
                                        t[t.MAIL = 17] = "MAIL",
                                        t[t.LBS = 18] = "LBS",
                                        t[t.ACTIVITY = 19] = "ACTIVITY",
                                        t[t.ATTACH_CARD_OFFICIAL_ACTIVITY = 20] = "ATTACH_CARD_OFFICIAL_ACTIVITY",
                                        t[t.GAME = 21] = "GAME",
                                        t[t.DECORATION = 22] = "DECORATION",
                                        t[t.UP_TOPIC = 23] = "UP_TOPIC",
                                        t[t.UP_ACTIVITY = 24] = "UP_ACTIVITY",
                                        t[t.UP_MAOER = 25] = "UP_MAOER",
                                        t[t.MEMBER_GOODS = 26] = "MEMBER_GOODS",
                                        t[t.OPENMALL_UP_ITEMS = 27] = "OPENMALL_UP_ITEMS",
                                        t[t.MUSIC = 29] = "MUSIC",
                                        t[t.MEMBER_TICKET = 31] = "MEMBER_TICKET",
                                        t[t.REPOST_PIC_URL = 32] = "REPOST_PIC_URL",
                                        t[t.REPOST_PIC_DYN_URL = 33] = "REPOST_PIC_DYN_URL",
                                        t[t.OGV_FOLLOW_CARD = 34] = "OGV_FOLLOW_CARD",
                                        t[t.ARTICLE_GOODS = 35] = "ARTICLE_GOODS",
                                        t[t.ARTICLE_TAG = 36] = "ARTICLE_TAG"
                                    }(a || (a = {})),
                                    function(t) {
                                        t[t.DEFAULT = 0] = "DEFAULT",
                                        t[t.NINE_CELL = 1] = "NINE_CELL",
                                        t[t.SCROLL = 2] = "SCROLL"
                                    }(s || (s = {})),
                                    function(t) {
                                        t[t.TAG_NONE = 0] = "TAG_NONE",
                                        t[t.TAG_LBS = 1] = "TAG_LBS"
                                    }(c || (c = {}));
var l = function(t) {
                                        return "object" == O(t)
                                    }
                                      , p = function(t) {
                                        return t.replace(/^(http(s)?:)?\/\//, "https://")
                                    }
                                      , v = function(t, e) {
                                        return e > t.length - 1 ? null : e < 0 ? e < -t.length ? null : -1 === e ? t[t.length - 1] : t.slice(e, e + 1)[0] : t[e]
                                    }
                                      , y = function(t) {
                                        return t < 256 && t >= 0
                                    }
                                      , w = function(t) {
                                        return C(t) ? t.split("@")[0] : t
                                    }
                                      , C = function(t) {
                                        return t.indexOf("/bfs/") > -1
                                    }
                                      , x = "\n"
                                      , S = function(t) {
                                        switch (Number(t)) {
                                        case 0:
                                            return 1;
                                        case 1:
                                            return 2;
                                        case 2:
                                            return 4;
                                        case 3:
                                        case 4:
                                            return 16;
                                        case 5:
                                            return 64;
                                        default:
                                            return 0
                                        }
                                    }
                                      , E = function(t) {
                                        return t.para_type === e.DEFAULT
                                    }
                                      , T = function(t) {
                                        return t.para_type === e.TEXT
                                    }
                                      , k = function(t) {
                                        var e;
                                        return !(null === (e = t.text) || void 0 === e || !e.nodes)
                                    }
                                      , L = function(t) {
                                        var e;
                                        if (!T(t))
                                            return !1;
                                        var n = t.text.nodes;
                                        return 0 === n.length || 1 === n.length && (null === (e = n[0].word) || void 0 === e ? void 0 : e.words) === x
                                    }
                                      , A = function(t) {
                                        return (null == t ? void 0 : t.node_type) === o.WORDS
                                    }
                                      , I = function(t) {
                                        switch (t) {
                                        case 17:
                                        case 18:
                                        default:
                                            return "regular";
                                        case 20:
                                            return "large";
                                        case 22:
                                            return "xLarge";
                                        case 24:
                                            return "xxLarge"
                                        }
                                    }
                                      , j = function(t, e) {
                                        return {
                                            words: t,
                                            font_size: 17,
                                            font_level: I(17),
                                            style: e || {}
                                        }
                                    }
                                      , P = function(t, e) {
                                        return {
                                            node_type: o.WORDS,
                                            word: j(t, e)
                                        }
                                    }
                                      , D = function(t) {
                                        return {
                                            node_type: o.BIZ_LINK,
                                            link: {
                                                link_type: t,
                                                style: {}
                                            }
                                        }
                                    }
                                      , M = function(t) {
                                        var n = [];
                                        return void 0 !== t && n.push(P(t)),
                                        {
                                            para_type: e.TEXT,
                                            text: {
                                                nodes: n
                                            }
                                        }
                                    }
                                      , R = function() {
                                        return {
                                            para_type: e.PICTURES,
                                            pic: {
                                                style: s.NINE_CELL,
                                                pics: []
                                            }
                                        }
                                    }
                                      , N = function(t, n) {
                                        return n ? (n.para_type = e.LINK_CARD,
                                        n.link_card || (n.link_card = {
                                            card: {
                                                link_type: a.DEFAULT
                                            }
                                        })) : n = {
                                            para_type: e.LINK_CARD,
                                            link_card: {
                                                card: {
                                                    link_type: a.DEFAULT
                                                }
                                            }
                                        },
                                        t && (n.link_card.card.link_type = t.type,
                                        n.link_card.card.biz_id = t.id),
                                        n
                                    }
                                      , B = function(t, r) {
                                        return r ? (r.para_type = e.LINE,
                                        r.format = {
                                            align: n.MIDDLE
                                        },
                                        r.line = {
                                            pic: t
                                        },
                                        r) : {
                                            para_type: e.LINE,
                                            format: {
                                                align: n.MIDDLE
                                            },
                                            line: {
                                                pic: t
                                            }
                                        }
                                    }
                                      , $ = function(t) {
                                        return JSON.parse(JSON.stringify(t))
                                    }
                                      , V = function(t, n) {
                                        var r = []
                                          , i = {
                                            para_type: e.DEFAULT
                                        }
                                          , a = function() {
                                            i = {
                                                para_type: e.DEFAULT
                                            }
                                        }
                                          , s = function(t) {
                                            t.para_type !== e.DEFAULT && (r.push(t),
                                            i = t)
                                        };
                                        try {
                                            for (var c = 0; c < t.length; c++) {
                                                var u = t[c]
                                                  , l = {
                                                    para_type: e.DEFAULT
                                                };
                                                if ("string" == typeof u.insert) {
                                                    var f = u.insert;
                                                    if (/^\n+$/.test(f)) {
                                                        if (!u.attributes) {
                                                            var p = f;
                                                            if (f.length > 1) {
                                                                if (c === t.length - 1) {
                                                                    var d = v(r, -1);
                                                                    new Array(T(d) && A(v(d.text.nodes, -1)) ? f.length : f.length - 1).fill(!0).forEach((function() {
                                                                        r.push(M(x))
                                                                    }
                                                                    ));
                                                                    break
                                                                }
                                                                p = p.substring(1)
                                                            }
                                                            l = M(p),
                                                            n && n(l, {
                                                                attrs: u.attributes,
                                                                text: p
                                                            }, i),
                                                            s(l);
                                                            continue
                                                        }
                                                        if (n) {
                                                            var h = v(r, -1);
                                                            T(i) ? n(h, {
                                                                attrs: u.attributes,
                                                                text: f
                                                            }, v(r, -2), r) : (n(l = M(f), {
                                                                attrs: u.attributes,
                                                                text: f === x ? "" : f
                                                            }, v(r, -1)),
                                                            s(l))
                                                        }
                                                        a();
                                                        continue
                                                    }
                                                    var m = f.split(x);
                                                    if (1 === m.length) {
                                                        if (l = M(f),
                                                        n && n(l, {
                                                            attrs: u.attributes,
                                                            text: f
                                                        }, i),
                                                        T(l) && T(i)) {
                                                            var g, y;
                                                            if (L(i)) {
                                                                i.text.nodes = _(l.text.nodes);
                                                                continue
                                                            }
                                                            null === (g = i.text) || void 0 === g || (y = g.nodes).push.apply(y, _(l.text.nodes))
                                                        } else
                                                            s(l);
                                                        continue
                                                    }
                                                    for (var b = 0; b < m.length; b++) {
                                                        var w = m[b];
                                                        if ("" === w) {
                                                            if (0 === b && (!i || T(i)))
                                                                continue;
                                                            if (b === m.length - 1) {
                                                                a();
                                                                continue
                                                            }
                                                            w = x
                                                        } else if (0 === b && T(i)) {
                                                            var C, O;
                                                            l = M(w),
                                                            n && n(l, {
                                                                attrs: u.attributes,
                                                                text: f
                                                            }, i),
                                                            null === (C = i.text) || void 0 === C || (O = C.nodes).push.apply(O, _(l.text.nodes));
                                                            continue
                                                        }
                                                        l = M(w),
                                                        n && n(l, {
                                                            attrs: u.attributes,
                                                            text: w
                                                        }, i),
                                                        s(l)
                                                    }
                                                } else {
                                                    var S = u.insert
                                                      , I = Object.keys(S)[0];
                                                    n && n(l, {
                                                        blot: {
                                                            name: I,
                                                            value: S[I]
                                                        },
                                                        attrs: u.attributes
                                                    }, i),
                                                    s(l)
                                                }
                                            }
                                        } catch (t) {
                                            console.error(t)
                                            r = []
                                        }
                                        var j = [];
                                        return r.forEach((function(t) {
                                            E(t) || (k(t) && (t.text.nodes = t.text.nodes.reduce((function(t, e) {
                                                return t.length > 0 && function(t, e) {
                                                    if (t.node_type !== o.WORDS || e.node_type !== o.WORDS)
                                                        return !1;
                                                    var n, r, i = $(t.word), a = $(e.word), s = i.words || "", c = a.words || "";
                                                    return delete i.words,
                                                    delete a.words,
                                                    n = i,
                                                    r = a,
                                                    JSON.stringify(n) === JSON.stringify(r) && (t.word.words = s + c,
                                                    !0)
                                                }(v(t, -1), e) || t.push(e),
                                                t
                                            }
                                            ), []),
                                            function(t) {
                                                if (T(t)) {
                                                    var e = v(t.text.nodes, -1);
                                                    if (A(e)) {
                                                        var n = e.word.words
                                                          , r = n.length;
                                                        r > 1 && n[r - 2] !== x && n[r - 1] === x && (e.word.words = n.slice(0, -1))
                                                    }
                                                }
                                            }(t)),
                                            j.push(t))
                                        }
                                        )),
                                        j
                                    };


function F(t) {
                                        return (F = "function" == typeof Symbol && "symbol" == O(Symbol.iterator) ? function(t) {
                                            return O(t)
                                        }
                                        : function(t) {
                                            return t && "function" == typeof Symbol && t.constructor === Symbol && t !== Symbol.prototype ? "symbol" : O(t)
                                        }
                                        )(t)
                                    }
                                    var H, U = function(t, e) {
                                        return t.para_type === e.para_type
                                    }, z = function() {
                                        return b((function t() {
                                            this.record = function(t) {
                                                if (!(t > 8)) {
                                                    var e = t - 1;
                                                    return this.levelOrderList[e]++,
                                                    this.levelOrderList[e]
                                                }
                                            };
                                            this.reset = function() {
                                                var t = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : 0;
                                                if (0 === t)
                                                    return this.init();
                                                this.levelOrderList = this.levelOrderList.slice(0, t).concat(new Array(9 - t).fill(0))
                                            }

                                        this.init = function() {
                                                this.levelOrderList = new Array(9).fill(0)
                                            }
                                            var e, n, r;
                                            g(this, t),
                                            e = this,
                                            r = [],
                                            (n = function(t) {
                                                var e = function(t, e) {
                                                    if ("object" !== F(t) || null === t)
                                                        return t;
                                                    var n = t[Symbol.toPrimitive];
                                                    if (void 0 !== n) {
                                                        var r = n.call(t, "string");
                                                        if ("object" !== F(r))
                                                            return r;
                                                        throw new TypeError("@@toPrimitive must return a primitive value.")
                                                    }
                                                    return String(t)
                                                }(t);
                                                return "symbol" === F(e) ? e : String(e)
                                            }(n = "levelOrderList"))in e ? Object.defineProperty(e, n, {
                                                value: r,
                                                enumerable: !0,
                                                configurable: !0,
                                                writable: !0
                                            }) : e[n] = r,
                                            this.init()
                                        }
                                        ), [{
                                            key: "record",
                                            value: function(t) {
                                                if (!(t > 8)) {
                                                    var e = t - 1;
                                                    return this.levelOrderList[e]++,
                                                    this.levelOrderList[e]
                                                }
                                            }
                                        }, {
                                            key: "reset",
                                            value: function() {
                                                var t = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : 0;
                                                if (0 === t)
                                                    return this.init();
                                                this.levelOrderList = this.levelOrderList.slice(0, t).concat(new Array(9 - t).fill(0))
                                            }
                                        }, {
                                            key: "init",
                                            value: function() {
                                                this.levelOrderList = new Array(9).fill(0)
                                            }
                                        }])
                                    }(), W = function(t, n, r, i) {
                                        t.para_type === e.TEXT && (t.para_type = "ordered" === n ? e.SORTED_LIST : e.UNSORTED_LIST,
                                        q(t, {
                                            list_format: {
                                                level: r,
                                                order: i
                                            }
                                        }))
                                    }, q = function(t, e) {
                                        t.format ? Object.assign(t.format, e) : t.format = e
                                    }, G = function(t) {
                                        return "right" === t ? n.RIGHT : "center" === t ? n.MIDDLE : n.LEFT
                                    }, Y = function(t, e) {
                                        q(t, {
                                            align: G(e)
                                        })
                                    }, Z = function(t) {
                                        t.para_type === e.TEXT && t.text.nodes.forEach((function(t) {
                                            switch (t.node_type) {
                                            case o.WORDS:
                                                t.word.style.bold = !0;
                                                break;
                                            case o.BIZ_LINK:
                                                t.link.style ? t.link.style.bold = !0 : t.link.style = {
                                                    bold: !0
                                                }
                                            }
                                        }
                                        ))
                                    }, X = function(t) {
                                        t.para_type === e.TEXT && t.text.nodes.forEach((function(t) {
                                            switch (t.node_type) {
                                            case o.WORDS:
                                                t.word.style.italic = !0;
                                                break;
                                            case o.BIZ_LINK:
                                                t.link.style ? t.link.style.italic = !0 : t.link.style = {
                                                    italic: !0
                                                }
                                            }
                                        }
                                        ))
                                    }, J = function(t) {
                                        t.para_type === e.TEXT && t.text.nodes.forEach((function(t) {
                                            switch (t.node_type) {
                                            case o.WORDS:
                                                t.word.style.strikethrough = !0;
                                                break;
                                            case o.BIZ_LINK:
                                                t.link.style ? t.link.style.strikethrough = !0 : t.link.style = {
                                                    strikethrough: !0
                                                }
                                            }
                                        }
                                        ))
                                    }, K = function(t) {
                                        t.para_type === e.TEXT && t.text.nodes.forEach((function(t) {
                                            switch (t.node_type) {
                                            case o.WORDS:
                                                t.word.style.underline = !0;
                                                break;
                                            case o.BIZ_LINK:
                                                t.link.style ? t.link.style.underline = !0 : t.link.style = {
                                                    underline: !0
                                                }
                                            }
                                        }
                                        ))
                                    }, Q = function(t, n) {
                                        var r, i = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : -1;
                                        t.para_type === e.TEXT && (null === (r = t.text) || void 0 === r ? void 0 : r.nodes) && (-1 === i ? t.text.nodes.forEach((function(t) {
                                            t.word.color = n
                                        }
                                        )) : t.text.nodes[i] && (t.text.nodes[i].word.color = n))
                                    }, tt = function() {
                                        var t = m(h().mark((function t(e, n) {
                                            var r;
                                            return h().wrap((function(t) {
                                                for (; ; )
                                                    switch (t.prev = t.next) {
                                                    case 0:
                                                        return r = [],
                                                        e.forEach((function(t) {
                                                            r.push(n(t))
                                                        }
                                                        )),
                                                        t.next = 4,
                                                        Promise.all(r);
                                                    case 4:
                                                    case "end":
                                                        return t.stop()
                                                    }
                                            }
                                            ), t)
                                        }
                                        )));
                                        return function(e, n) {
                                            return t.apply(this, arguments)
                                        }
                                    }(), et = function() {
                                        var t = m(h().mark((function t(n, r) {
                                            return h().wrap((function(t) {
                                                for (; ; )
                                                    switch (t.prev = t.next) {
                                                    case 0:
                                                        return t.next = 2,
                                                        tt(n.paragraphs, (function(t) {
                                                            var n;
                                                            return t.para_type === e.PICTURES ? tt((null === (n = t.pic) || void 0 === n ? void 0 : n.pics) || [], (function(t) {
                                                                return C(t.url) ? r((e = t.url,
                                                                {
                                                                    url: "".concat(e, "@info")
                                                                })).then((function(e) {
                                                                    return function(t, e) {
                                                                        t.url = p(w(t.url)),
                                                                        t.width = e.width,
                                                                        t.height = e.height,
                                                                        t.size = e.file_size / 1024
                                                                    }(t, e)
                                                                }
                                                                )) : Promise.resolve();
                                                                var e
                                                            }
                                                            )) : Promise.resolve()
                                                        }
                                                        ));
                                                    case 2:
                                                    case "end":
                                                        return t.stop()
                                                    }
                                            }
                                            ), t)
                                        }
                                        )));
                                        return function(e, n) {
                                            return t.apply(this, arguments)
                                        }
                                    }();
                                    !function(t) {
                                        t.ImageUpload = "imageUpload",
                                        t.Tag = "tag"
                                    }(H || (H = {}));
                                    var nt, rt = new z, it = function(t, e) {
                                        var n = Number(e.replace("px", ""));
                                        t.text.nodes[0].word.font_size = n,
                                        t.text.nodes[0].word.font_level = I(n)
                                    }, ot = function(t, n, r) {
                                        var i, c, u = n.blot, f = n.attrs;
                                        if (u)
                                            switch (u.name) {
                                            case H.Tag:
                                                t.para_type = e.TEXT,
                                                c = u.value,
                                                function t(e) {
                                                    "object" == O(e) && (Array.isArray(e) ? e.forEach((function(e) {
                                                        t(e)
                                                    }
                                                    )) : function(e) {
                                                        for (var n in e) {
                                                            var r = e[n];
                                                            switch (O(r)) {
                                                            case "object":
                                                                t(r);
                                                                break;
                                                            case "boolean":
                                                                !1 === r && delete e[n];
                                                                break;
                                                            case "number":
                                                                0 === r && delete e[n];
                                                                break;
                                                            case "string":
                                                                "" === r && delete e[n]
                                                            }
                                                        }
                                                    }(e))
                                                }(i = JSON.parse(JSON.stringify(c))),
                                                t.text = {
                                                    nodes: [{
                                                        node_type: o.BIZ_LINK,
                                                        link: {
                                                            link_type: a.VIDEO_TS,
                                                            video_ts: i
                                                        }
                                                    }]
                                                };
                                                break;
                                            case H.ImageUpload:
                                                t.para_type = e.PICTURES,
                                                t.pic = {
                                                    style: s.NINE_CELL,
                                                    pics: [{
                                                        url: u.value.url,
                                                        width: u.value.width
                                                    }]
                                                }
                                            }
                                        else if (t.para_type !== e.DEFAULT && l(f)) {
                                            var p = 1;
                                            for (var d in f)
                                                switch (d) {
                                                case "size":
                                                    it(t, f[d]);
                                                    break;
                                                case "bold":
                                                    f[d] && Z(t);
                                                    break;
                                                case "italic":
                                                    f[d] && X(t);
                                                    break;
                                                case "strike":
                                                    f[d] && J(t);
                                                    break;
                                                case "underline":
                                                    f[d] && K(t);
                                                    break;
                                                case "color":
                                                    Q(t, f[d]);
                                                    break;
                                                case "list":
                                                    if (p = (f.indent || 0) + 1,
                                                    W(t, f[d], p, 1),
                                                    r) {
                                                        var h, v, m = (null === (h = r.format) || void 0 === h || null === (v = h.list_format) || void 0 === v ? void 0 : v.level) || 0;
                                                        U(t, r) ? m < p && rt.reset(m) : rt.init()
                                                    }
                                                    t.format.list_format.order = rt.record(p) || 1
                                                }
                                        }
                                    }, at = new z;
                                    !function(t) {
                                        t.CutOff = "cut-off",
                                        t.NativeImage = "native-image",
                                        t.VideoCard = "video-card",
                                        t.ArticleCard = "article-card",
                                        t.LiveCard = "live-card",
                                        t.VoteCard = "vote-card",
                                        t.GoodsCard = "goods-card",
                                        t.MallCard = "mall-card"
                                    }(nt || (nt = {}));

var st = function (t, n) {
        t.para_type === e.TEXT && t.text.nodes.forEach((function (t) {
            var e, r = 17;
            switch (n) {
                case 1:
                    r = 24;
                    break;
                case 2:
                    r = 22
            }
            switch (t.node_type) {
                case o.WORDS:
                    t.word && (t.word.font_size = r, t.word.font_level = I(r), t.word.style.bold = !0);
                    break;
                case o.BIZ_LINK:
                    (null === (e = t.link) || void 0 === e ? void 0 : e.style) && (t.link.style.font_size = r, t.link.style.font_level = I(r), t.link.style.bold = !0)
            }
        }))
    }, ct = function (t) {
        t.para_type === e.TEXT && (t.para_type = e.REFERENCE)
    }, ut = function (t, r, i, o) {
        var c, u, f, p, d, h, v = r.blot, m = r.attrs, g = r.text;
        if (v) switch (v.name) {
            case nt.CutOff:
                B({
                    url: v.value.url, height: S(v.value.type)
                }, t), i && L(i) && (i.para_type = e.DEFAULT);
                break;
            case nt.NativeImage:
                if (l(v.value) && (t.para_type = e.PICTURES, t.pic = {
                    style: s.NINE_CELL, pics: [{
                        url: w(v.value.url), width: v.value.width, height: v.value.height, size: v.value.size / 1024
                    }]
                }, null != m && m.align)) switch (m.align) {
                    case "center":
                        q(t, {
                            align: n.MIDDLE
                        });
                        break;
                    case "right":
                        q(t, {
                            align: n.RIGHT
                        })
                }
                break;
            case nt.VideoCard:
                var y, b = (null === (y = v.value) || void 0 === y ? void 0 : y.id) || "";
                /^av\d+$/i.test(b) && (b = b.replace(/^av/i, "")), b && N({
                    type: a.VIDEO, id: b
                }, t);
                break;
            case nt.ArticleCard:
                (null === (c = v.value) || void 0 === c ? void 0 : c.id) && N({
                    type: a.CV, id: v.value.id.replace("cv", "")
                }, t);
                break;
            case nt.LiveCard:
                (null === (u = v.value) || void 0 === u ? void 0 : u.id) && N({
                    type: a.LIVE, id: v.value.id.replace("lv", "")
                }, t);
                break;
            case nt.VoteCard:
                (null === (f = v.value) || void 0 === f ? void 0 : f.id) && N({
                    type: a.VOTE, id: v.value.id
                }, t);
                break;
            case nt.GoodsCard:
                (null === (p = v.value) || void 0 === p ? void 0 : p.id) && N({
                    type: a.ARTICLE_GOODS, id: v.value.id
                }, t);
                break;
            case nt.MallCard:
                (null === (d = v.value) || void 0 === d ? void 0 : d.id) && (v.value.id.startsWith("pw") ? N({
                    type: a.MEMBER_TICKET, id: v.value.id.replace("pw", "")
                }, t) : v.value.id.startsWith("sp") && N({
                    type: a.MEMBER_GOODS, id: v.value.id.replace("sp", "")
                }, t))
        } else if (t.para_type !== e.DEFAULT && l(m)) {
            var C = 1;
            for (var O in m.link && function (t, n, r) {
                var i = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : -1;
                if (t.para_type === e.TEXT && null !== (r = t.text) && void 0 !== r && r.nodes) if (-1 === i) for (var o = 0; o < t.text.nodes.length; o++) {
                    var s = D(a.URL);
                    s.link.show_text = t.text.nodes[o].word.words, s.link.link = n, t.text.nodes[o] = s
                } else if (t.text.nodes[i]) {
                    var c = D(a.URL);
                    c.link.show_text = t.text.nodes[i].word.words, c.link.link = n, t.text.nodes[i] = c
                }
            }(t, m.link), m) switch (O) {
                case "sublock":
                    if (null !== (h = m[O]) && void 0 !== h && h.blockquote && (t.para_type = e.REFERENCE), Y(t, m[O].align), i && k(i) && k(t)) {
                        var E, T, A;
                        if (G(m[O].align) !== (null === (E = i.format) || void 0 === E ? void 0 : E.align)) break;
                        if (o) {
                            var I = o.findIndex((function (e) {
                                return e === t
                            }));
                            I > -1 && o.splice(I, 1)
                        }
                        1 === (null === (T = i.text) || void 0 === T ? void 0 : T.nodes.length) && t.text.nodes.unshift(P(x)), g && t.text.nodes.push(P(g)), (A = i.text.nodes).push.apply(A, _(t.text.nodes)), t.para_type = e.DEFAULT
                    }
                    break;
                case "header":
                    st(t, m[O]);
                    break;
                case "bold":
                    m[O] && Z(t);
                    break;
                case "strike":
                    m[O] && J(t);
                    break;
                case "italic":
                    m[O] && X(t);
                    break;
                case "color":
                    Q(t, m[O]);
                    break;
                case "align":
                    Y(t, m[O]);
                    break;
                case "link":
                default:
                    break;
                case "blockquote":
                    m[O] && ct(t);
                    break;
                case "list":
                    if (C = (m.indent || 0) + 1, W(t, m[O], C, 1), i) {
                        var j, M,
                            R = (null === (j = i.format) || void 0 === j || null === (M = j.list_format) || void 0 === M ? void 0 : M.level) || 0;
                        U(t, i) ? R < C && at.reset(R) : at.init()
                    }
                    t.format.list_format.order = at.record(C) || 1
            }
        }
    },
    lt = {
        html2json: function (t) {
            t = function (t) {
                return t.replace(/<\?xml.*\?>\n/, "").replace(/<!doctype.*\>\n/, "").replace(/<!DOCTYPE.*\>\n/, "")
            }(t);
            var e = [], n = {
                node: "root", child: []
            };
            return HTMLParser(t, {
                start: function (t, i, o) {
                    r(t, i, o);
                    var a = {
                        node: "element", tag: t
                    };
                    if (0 !== i.length && (a.attr = i.reduce((function (t, e) {
                        var n = e.name, r = e.value;
                        return r.match(/ /) && (r = r.split(" ")), t[n] ? Array.isArray(t[n]) ? t[n].push(r) : t[n] = [t[n], r] : t[n] = r, t
                    }), {})), o) {
                        var s = e[0] || n;
                        void 0 === s.child && (s.child = []), s.child.push(a)
                    } else e.unshift(a)
                }, end: function (t) {
                    r(t);
                    var i = e.shift();
                    if (i.tag !== t && console.error("invalid state: mismatch end tag"), 0 === e.length) n.child.push(i); else {
                        var o = e[0];
                        void 0 === o.child && (o.child = []), o.child.push(i)
                    }
                }, chars: function (t) {
                    r(t);
                    var i = {
                        node: "text", text: t
                    };
                    if (0 === e.length) n.child.push(i); else {
                        var o = e[0];
                        void 0 === o.child && (o.child = []), o.child.push(i)
                    }
                }, comment: function (t) {
                    r(t);
                    var n = {
                        node: "comment", text: t
                    }, i = e[0];
                    void 0 === i.child && (i.child = []), i.child.push(n)
                }
            }), n
        }, json2html: function t(e) {
            var n = "";
            e.child && (n = e.child.map((function (e) {
                return t(e)
            })).join(""));
            var r = "";
            if (e.attr && "" !== (r = Object.keys(e.attr).map((function (t) {
                var n = e.attr[t];
                return Array.isArray(n) && (n = n.join(" ")), t + '="' + n + '"'
            })).join(" ")) && (r = " " + r), "element" === e.node) {
                var i = e.tag;
                return ["area", "base", "basefont", "br", "col", "frame", "hr", "img", "input", "isindex", "link", "meta", "param", "embed"].indexOf(i) > -1 ? "<" + e.tag + r + "/>" : "<" + e.tag + r + ">" + n + "</" + e.tag + ">"
            }
            return "text" === e.node ? e.text : "comment" === e.node ? "\x3c!--" + e.text + "--\x3e" : "root" === e.node ? n : void 0
        }
    },
    ft = function (t, n) {
        t.para_type === e.TEXT && t.text.nodes.forEach((function (t) {
            if (t.word) {
                var e = 1 === n ? 24 : 22;
                t.word.font_size = e, t.word.font_level = I(e), t.word.style.bold = !0
            }
        }))
    },
    pt = function (t, e) {
        t = JSON.parse(JSON.stringify(t));
        var n = function (n) {
            var r, i = t[n];
            switch (n) {
                case "class":
                    Array.isArray(i) || (t[n] = t[n].split(" ")), t[n].forEach((function (t) {
                        t.startsWith("color-") && ((r = function (t) {
                            switch (t) {
                                case "color-blue-01":
                                    return "#56c1fe";
                                case "color-lblue-01":
                                    return "#73fdea";
                                case "color-green-01":
                                    return "#89fa4e";
                                case "color-yellow-01":
                                    return "#fff359";
                                case "color-pink-01":
                                    return "#ff968d";
                                case "color-purple-01":
                                    return "#ff8cc6";
                                case "color-blue-02":
                                    return "#02a2ff";
                                case "color-lblue-02":
                                    return "#18e7cf";
                                case "color-green-02":
                                    return "#60d837";
                                case "color-yellow-02":
                                    return "#fbe231";
                                case "color-pink-02":
                                    return "#ff654e";
                                case "color-blue-03":
                                    return "#0176ba";
                                case "color-lblue-03":
                                    return "#068f86";
                                case "color-green-03":
                                    return "#1db100";
                                case "color-yellow-03":
                                    return "#f8ba00";
                                case "color-pink-03":
                                    return "#ee230d";
                                case "color-purple-03":
                                    return "#cb297a";
                                case "color-blue-04":
                                    return "#004e80";
                                case "color-lblue-04":
                                    return "#017c76";
                                case "color-green-04":
                                    return "#017001";
                                case "color-yellow-04":
                                    return "#ff9201";
                                case "color-pink-04":
                                    return "#b41700";
                                case "color-purple-04":
                                    return "#99195e";
                                case "color-gray-01":
                                    return "#d6d5d5";
                                case "color-gray-02":
                                    return "#929292";
                                case "color-gray-03":
                                    return "#5f5f5f";
                                default:
                                    return ""
                            }
                        }(t)) && e(["style", "color"], r))
                    }));
                    break;
                case "style":
                    Array.isArray(i) && i.join("").split(";").forEach((function (t) {
                        var r = d(t.split(":"), 2), i = r[0], o = r[1];
                        switch (i) {
                            case "color":
                                e([n, i], function (t) {
                                    var e = ["0", "0", "0"];
                                    if ("string" == typeof t) {
                                        var n = t.match(/\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}/);
                                        (null == n ? void 0 : n[0]) && (e = n[0].split(",").map((function (t) {
                                            var e = parseInt(t.trim());
                                            return y(e) ? e < 10 ? "0".concat(e.toString(16)) : e.toString(16) : "00"
                                        })))
                                    } else e = t.map((function (t) {
                                        var e = parseInt(String(t).trim());
                                        return y(e) ? e < 10 ? "0".concat(e.toString(16)) : e.toString(16) : "00"
                                    }));
                                    return "#".concat(e.join(""))
                                }(o));
                                break;
                            case "text-align":
                            case "text-decoration":
                            case "font-weight":
                                e([n, i], o)
                        }
                    }))
            }
        };
        for (var r in t) n(r)
    }, dt = function (t, e, n) {
        var r;
        switch (e) {
            case "color":
                t.color = n;
                break;
            case "font-weight":
                (null === (r = n.startsWith) || void 0 === r ? void 0 : r.call(n, "bold")) && (t.style.bold = !0);
                break;
            case "text-decoration":
                "line-through" === n && (t.style.strikethrough = !0)
        }
    }, ht = function t(e, n, r) {
        var i, o = j("");
        if (n && (n.words || "text" !== e.node ? (n.color && (o.color = n.color), Object.assign(o.style, f({}, n.style))) : o = n), r = r || [], "text" === e.node) return o.words = e.text || "", r.push(o), r;
        switch (e.tag) {
            case "strong":
                o.style.bold = !0;
                break;
            case "em":
                o.style.italic = !0;
                break;
            case "br":
                o.words = x
        }
        return e.attr && pt(e.attr, (function (t, e) {
            "style" === t[0] && dt(o, t[1], e)
        })), null !== (i = e.child) && void 0 !== i && i.length ? e.child.forEach((function (e) {
            t(e, o, r)
        })) : o.words && r.push(o), r || []
    }, vt = function (t) {
        var e;
        return "latex" === (null === (e = t.attr) || void 0 === e ? void 0 : e.type)
    }, mt = function t(n, r) {
        r.child && r.child.forEach((function (e, r) {
            var i, s;
            switch (e.tag) {
                case "p":
                    r > 0 && n.text.nodes.push(P(x)), t(n, e);
                    break;
                case "br":
                    n.text.nodes.push(P(x));
                    break;
                case "a":
                    !function (t, e, n, r) {
                        var i = D(a.URL);
                        i.link.show_text = (null === (n = e.child) || void 0 === n || null === (r = n[0]) || void 0 === r ? void 0 : r.text) || "网页链接", i.link.link = e.attr.href, t.push(i)
                    }(n.text.nodes, e);
                    break;
                case "span":
                case "strong":
                    (i = n.text.nodes).push.apply(i, _(ht(e).map((function (t) {
                        return {
                            node_type: o.WORDS, word: t
                        }
                    }))));
                    break;
                case "img":
                    vt(e) && n.text.nodes.push((s = decodeURIComponent(e.attr.alt), {
                        node_type: o.FORMULA, formula: {
                            latex_content: s
                        }
                    }));
                    break;
                default:
                    "text" === e.node && k(n) && n.text.nodes.push(P(e.text))
            }
        })), 0 === n.text.nodes.length && (n.para_type = e.DEFAULT)
    }, gt = function (t, e) {
        var n;
        return "string" == typeof t ? e.indexOf(t) > -1 ? t : "" : (null === (n = e.match(t)) || void 0 === n ? void 0 : n[0]) || ""
    }, yt = function (t, e) {
        if ("string" == typeof e) return gt(t, e);
        for (var n = 0; n < e.length; n++) {
            var r = gt(t, e[n]);
            if (r) return r
        }
        return ""
    }, bt = "cut-off-", wt = function (t) {
        return yt(new RegExp("".concat(bt, "\\d")), t)
    },
    _t = ["article-card", "video-card", "fanju-card", "music-card", "shop-card", "caricature-card", "live-card", "game-card", "goods-card", "vote-display"],
    Ct = function (t, e) {
        return (t.attr[e] || "").split(",")
    }, xt = function (t) {
        if ("string" == typeof t) {
            var e = Number(t);
            if (isNaN(e)) return;
            return e
        }
    }, Ot = function (t) {
        return {
            url: p(t.attr.src), width: xt(t.attr.width), height: xt(t.attr.height)
        }
    }, St = function (t, r) {
        if (r.child) if (r.child.length <= 2) {
            var i = {
                para_type: e.DEFAULT
            };
            r.child.forEach((function (e) {
                var r, o, a, s, c, u, l;
                switch (e.tag) {
                    case "img":
                        vt(e) || (null === (r = e.attr) || void 0 === r ? void 0 : r.src) && "1" !== (null === (o = e.attr) || void 0 === o ? void 0 : o.height) && ((i = R()).pic.pics.push(Ot(e)), t.push(i));
                        break;
                    case "figcaption":
                        "caption" === (null === (a = e.attr) || void 0 === a ? void 0 : a.class) && (null === (s = e.child) || void 0 === s || null === (c = s[0]) || void 0 === c ? void 0 : c.text) && (i = M(null === (u = e.child) || void 0 === u || null === (l = u[0]) || void 0 === l ? void 0 : l.text), dt(i.text.nodes[0].word, "color", "#999999"), t.push(i), q(i, {
                            align: n.MIDDLE
                        }))
                }
            }))
        } else r.child.forEach((function (e) {
            var n, r;
            if ("img" === e.tag && !vt(e) && null !== (n = e.attr) && void 0 !== n && n.src && "1" !== (null === (r = e.attr) || void 0 === r ? void 0 : r.height)) {
                var i = R();
                i.pic.pics.push(Ot(e)), t.push(i)
            }
        }))
    }, Et = function t(n, r, i) {
        var a = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : 1;
        [e.SORTED_LIST, e.UNSORTED_LIST].includes(i) && r.child && r.child.forEach((function (r, s) {
            var c;
            if ("li" !== r.tag) return "ul" === r.tag && t(n, r, e.UNSORTED_LIST, a + 1), void ("ol" === r.tag && t(n, r, e.SORTED_LIST, a + 1));
            var u = M();
            (c = u.text.nodes).push.apply(c, _(ht(r).map((function (t) {
                return {
                    node_type: o.WORDS, word: t
                }
            })))), W(u, i === e.UNSORTED_LIST ? "bullet" : "ordered", a, s + 1), n.push(u)
        }))
    }, Tt = function (t, e) {
        var n = e || "div";
        return "<".concat(n, ' class="').concat("wrap", '">').concat(t, "</").concat(n, ">")
    }, kt = function (t) {
        var r = function (t, e, n, r) {
            if ("div" === (t = (null === (e = t.child) || void 0 === e ? void 0 : e[0]) || t).tag && "wrap" === (null === (n = t.attr) || void 0 === n ? void 0 : n.class) && null !== (r = t.child) && void 0 !== r && r.length) {
                if (1 === t.child.length) return "p" === t.child[0].tag || "figure" === t.child[0].tag ? t : t.child[0];
                t.tag = "article";
                var i = t.child || [], o = [];
                i.forEach((function (t) {
                    if ("text" !== t.node) if ("element" !== t.node || "img" !== t.tag) o.push(t); else {
                        var e, n = (0, lt.html2json)(Tt('<img src="'.concat(t.attr.src, '">'), "figure"));
                        o.push((null === (e = n.child) || void 0 === e ? void 0 : e[0]) || n)
                    } else {
                        var r;
                        if (t.text === x) return;
                        var i = (0, lt.html2json)(Tt(t.text || "", "p"));
                        o.push((null === (r = i.child) || void 0 === r ? void 0 : r[0]) || i)
                    }
                })), t.child = o
            }
            return t
        }((0, lt.html2json)(Tt(t).replace(/<(?!\/?[a-zA-Z])([^<>]+)>/g, (function (t, e) {
            return "&lt;" + e.replace(/&/g, "&amp;") + "&gt;"
        })))).child || [], i = [];
        return r.forEach((function (t) {
            var r, o, s, c, u, l, f, d, h = {
                para_type: e.DEFAULT
            };
            if ("p" === t.tag) if ("image-package" === (null === (r = t.attr) || void 0 === r ? void 0 : r.class)) "figure" === (null === (o = t.child) || void 0 === o || null === (s = o[0]) || void 0 === s ? void 0 : s.tag) && (t = t.child[0]); else {
                var m = (t.child || []).find((function (t) {
                    return "img" === t.tag
                }));
                if (m && !vt(m)) return void St(i, t)
            } else "div" === t.tag && "img" === (null === (c = t.child) || void 0 === c ? void 0 : c[0].tag) && (t.tag = "figure");
            switch (t.tag) {
                case "p":
                case "h1":
                case "h2":
                case "h3":
                case "h4":
                    if ("p" === t.tag && "p" === (d = t).tag && (null === (u = d.child) || void 0 === u || !u.length || 1 === d.child.length && "br" === d.child[0].tag) && (null === (l = v(i, -1)) || void 0 === l ? void 0 : l.para_type) === e.LINK_CARD) break;
                    h = M(), mt(h, t), "h1" === t.tag && ft(h, 1), "h2" === t.tag && ft(h, 2);
                    break;
                case "blockquote":
                    (h = M()).para_type = e.REFERENCE, mt(h, t);
                    break;
                case "figure":
                    (f = function (t, e) {
                        return "figure" === t.tag && (n = (null === (e = t.attr) || void 0 === e ? void 0 : e.class) || "", !!yt("code-box", n));
                        var n
                    }(t) ? function (t, e) {
                        return null === (e = t.child) || void 0 === e ? void 0 : e.find((function (t) {
                            return "pre" === t.tag && t.attr && t.attr["data-lang"] && t.attr.codecontent
                        }))
                    }(t) : null) ? function (t, n, r, i, o, a) {
                        t.para_type = e.CODE;
                        var s = n.attr.codecontent;
                        "string" != typeof s && (s = s.join(" "));
                        var c = "string" == typeof (null === (r = n.attr) || void 0 === r ? void 0 : r.class) ? null === (i = n.attr) || void 0 === i ? void 0 : i.class : (null === (o = n.attr) || void 0 === o || null === (a = o.class) || void 0 === a ? void 0 : a.join("")) || "";
                        t.code = {
                            lang: c, content: s
                        }
                    }(h, f) : (f = function (t, e) {
                        return null === (e = t.child) || void 0 === e ? void 0 : e.find((function (t) {
                            return "img" === t.tag && t.attr && t.attr.class && function (t) {
                                for (var e = 0; e < _t.length; e++) {
                                    var n = yt(_t[e], t);
                                    if (n) return n
                                }
                                return ""
                            }(t.attr.class)
                        }))
                    }(t)) ? function (t, e) {
                        var n = a.DEFAULT, r = [];
                        if (function (t) {
                            return !!yt(_t[9], t.attr.class)
                        }(e)) r = Ct(e, "data-vote-id"), n = a.VOTE; else switch (r = Ct(e, "aid"), !0) {
                            case function (t) {
                                return !!yt(_t[0], t.attr.class)
                            }(e):
                                n = a.CV;
                                break;
                            case function (t) {
                                return !!yt(_t[1], t.attr.class)
                            }(e):
                                n = a.VIDEO;
                                break;
                            case function (t) {
                                return !!yt(_t[2], t.attr.class)
                            }(e):
                                return void r.forEach((function (e) {
                                    e.indexOf("ss") > -1 ? t.push(N({
                                        type: a.OGV_SS, id: e.replace("ss", "")
                                    })) : e.indexOf("ep") > -1 && t.push(N({
                                        type: a.OGV_EP, id: e.replace("ep", "")
                                    }))
                                }));
                            case function (t) {
                                return !!yt(_t[3], t.attr.class)
                            }(e):
                                n = a.MUSIC, r = r.map((function (t) {
                                    return t.replace("au", "")
                                }));
                                break;
                            case function (t) {
                                return !!yt(_t[4], t.attr.class)
                            }(e):
                                return void r.forEach((function (e) {
                                    e.indexOf("sp") > -1 ? t.push(N({
                                        type: a.MEMBER_GOODS, id: e.replace("sp", "")
                                    })) : e.indexOf("pw") > -1 && t.push(N({
                                        type: a.MEMBER_TICKET, id: e.replace("pw", "")
                                    }))
                                }));
                            case function (t) {
                                return !!yt(_t[5], t.attr.class)
                            }(e):
                                n = a.MANGA;
                                break;
                            case function (t) {
                                return !!yt(_t[6], t.attr.class)
                            }(e):
                                n = a.LIVE;
                                break;
                            case function (t) {
                                return !!yt(_t[7], t.attr.class)
                            }(e):
                                n = a.GAME;
                                break;
                            case function (t) {
                                return !!yt(_t[8], t.attr.class)
                            }(e):
                                n = a.ARTICLE_GOODS, r = r.map((function (t) {
                                    return t.replace("co", "")
                                }))
                        }
                        r.length && n !== a.DEFAULT && r.forEach((function (e) {
                            t.push(N({
                                type: n, id: e
                            }))
                        }))
                    }(i, f) : (f = function (t, e) {
                        return null === (e = t.child) || void 0 === e ? void 0 : e.find((function (t) {
                            return "img" === t.tag && t.attr && t.attr.class && wt(t.attr.class)
                        }))
                    }(t)) ? function (t, e) {
                        var n, r;
                        B((n = e.attr.src, r = parseInt(wt(e.attr.class).replace(bt, "")) - 1, {
                            url: p(n), height: S(r)
                        }), t)
                    }(h, f) : St(i, t);
                    break;
                case "ul":
                case "ol":
                    Et(i, t, "ul" === t.tag ? e.UNSORTED_LIST : e.SORTED_LIST)
            }
            E(h) || (t.attr && pt(t.attr, (function (t, e) {
                "style" === t[0] && function (t, e, r) {
                    "text-align" === e && q(t, {
                        align: "right" === r ? n.RIGHT : "center" === r ? n.MIDDLE : n.LEFT
                    })
                }(h, t[1], e)
            })), i.push(h))
        })), {
            paragraphs: i.filter((function (t) {
                return !E(t)
            }))
        }
    }, Lt = function (e) {
        switch (e.type) {
            case t.ARTICLE:
                return function (t) {
                    var e = [];
                    try {
                        var n = JSON.parse(t).ops;
                        e = V(n, ut)
                    } catch (t) {
                        console.error(`转换opus内容出错！${t}\n${t.stack}`)
                        e = []
                    }
                    return {
                        paragraphs: e
                    }
                }(e.sourceContent);
            case t.NOTE:
                return function (t) {
                    var e = [];
                    try {
                        var n = JSON.parse(t);
                        e = V(n, ot)
                    } catch (t) {
                        console.error(t)
                        e = []
                    }
                    return rt.init(), {
                        paragraphs: e
                    }
                }(e.sourceContent);
            case t.ARTICLE_H5:
                return kt(e.sourceContent);
            default:
                return {
                    paragraphs: []
                }
        }
    }

let toOpusContent = (type, sourceContent) => {
    return Lt({
        type: type,
        sourceContent: sourceContent
    })
}
