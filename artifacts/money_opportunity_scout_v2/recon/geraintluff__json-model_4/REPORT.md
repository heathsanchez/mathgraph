# Recon Report

## Verdict

`MAYBE_NEEDS_MANUAL_READ`

## Decision

JSON:
{
  "verdict": "MAYBE_NEEDS_MANUAL_READ",
  "issue": {
    "url": "https://github.com/geraintluff/json-model/issues/4",
    "title": "Json model fails some of the tests in th JSON-schema official testsuite",
    "state": "OPEN",
    "labels": [],
    "comment_count": 0,
    "updatedAt": "2015-01-31T10:41:24Z"
  },
  "has_lean": false,
  "has_tests": false,
  "has_benchmark": true,
  "has_money": true,
  "has_surface": true,
  "risk": false
}

## Issue body excerpt

I've generated an error report here:
https://github.com/Muscula/json-schema-benchmark/blob/master/reports/json-model.md

All the test failing marked with `This excludes this validator from performance tests` almost all other validators pass, and are a part of the required parts of the [official JSON-schema test suite](https://github.com/json-schema/JSON-Schema-Test-Suite).


## Inventory excerpt

top files
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/ORIG_HEAD
.git/packed-refs
.gitignore
.gitmodules
bindings/default.css
bindings/default.js
comparison/comparison.js
comparison/index.html
comparison/known-schemas.json
comparison/tests.json
Gruntfile.js
index.html
json-model.js
json-model.js.map
json-model.min.js
json-model.min.js.map
package.json
README.md
source/__footer.js
source/__header.js
source/model-bind.js
source/model.js
source/schema2js.js
tests/00 - Basic schema2js/00 - Basic.js
tests/00 - Basic schema2js/01 - Inter-linking.js
tests/00 - Basic schema2js/02 - Basic links.js
tests/00 - Basic schema2js/03 - Basic validation.js
tests/00 - Basic schema2js/04 - Schema assignment.js
tests/00 - Basic schema2js/05 - Two-stage generation.js
tests/00 - Basic schema2js/06 - Sub-errors.js
tests/00 - Basic schema2js/07 - Track missing schemas.js
tests/00 - Basic schema2js/08 - Link assignment.js
tests/01 - Basic model/00 - Basic.js
tests/01 - Basic model/01 - Events.js
tests/01 - Basic model/02 - Requests.js
tests/01 - Basic model/03 - Iterators.js
tests/01 - Basic model/04 - Schema errors.js
tests/02 - Schema sets/00 - Basic.js
tests/Bugs/advanced-object.js
tests/draft-04-schema.json
tests/json-schema-test-suite.js
tests/uri-templates.js

build/test files
./package.json
./README.md


## Grep excerpt

===== judge hits =====
./json-model.js:167:				return this.createError(ErrorCodes.CIRCULAR_REFERENCE, {urls: Object.keys(urlHistory).join(', ')}, '', '');
./json-model.js:240:	CIRCULAR_REFERENCE: 600, // $ref loop
./json-model.js:3164:			/* Failed attempt at IE9 compatibility (the doc.open() call is failing with "Unspecified Error")
./source/schema2js.js:150:				return this.createError(ErrorCodes.CIRCULAR_REFERENCE, {urls: Object.keys(urlHistory).join(', ')}, '', '');
./source/schema2js.js:223:	CIRCULAR_REFERENCE: 600, // $ref loop
./source/model-bind.js:764:			/* Failed attempt at IE9 compatibility (the doc.open() call is failing with "Unspecified Error")
./tests/Bugs/advanced-object.js:4:describe('Bug from z-schema benchmarking', function () {
./json-model.min.js:1:"use strict";!function(a,b){"function"==typeof define&&define.amd?define([],b):"undefined"!=typeof module&&module.exports?module.exports=b():a.JsonModel=b()}(this,function(){function a(a){var b=String(a).replace(/^\s+|\s+$/g,"").match(/^([^:\/?#]+:)?(\/\/(?:[^:@]*(?::[^:@]*)?@)?(([^:\/?#]*)(?::(\d*))?))?([^?#]*)(\?[^#]*)?(#[\s\S]*)?/);return b?{href:b[0]||"",protocol:b[1]||"",authority:b[2]||"",host:b[3]||"",hostname:b[4]||"",port:b[5]||"",pathname:b[6]||"",search:b[7]||"",hash:b[8]||""}:null}function b(b,c){function d(a){var b=[];return a.replace(/^(\.\.?(\/|$))+/,"").replace(/\/(\.(\/|$))+/g,"/").replace(/\/\.\.$/,"/../").replace(/\/?[^\/]*/g,function(a){"/.."===a?b.pop():b.push(a)}),b.join("").replace(/^\//,"/"===a.charAt(0)?"/":"")}return c=a(c||""),b=a(b||""),c&&b?(c.protocol||b.protocol)+(c.protocol||c.authority?c.authority:b.authority)+d(c.protocol||c.authority||"/"===c.pathname.charAt(0)?c.pathname:c.pathname?(b.authority&&!b.pathname?"/":"")+b.pathname.slice(0,b.pathname.lastIndexOf("/")+1)+c.pathname:b.pathname)+(c.protocol||c.authority||c.pathname?c.search:c.search||b.search)+c.hash:null}function c(a,b){if(b.substring(0,a.length)===a){var c=b.substring(a.length);if(b.length>0&&"/"===b.charAt(a.length-1)||"#"===c.charAt(0)||"?"===c.charAt(0))return!0}return!1}function d(a){return("	"+a.replace(/\n/g,"\n	")).replace(/\t+$/,"")}function e(a){return""===a.split("#")[1]?a.split("#")[0]:a}function f(a,b){return/^[a-zA-Z][a-zA-Z0-9_]*/.test(b)?a+"."+b:a+"["+JSON.stringify(b)+"]"}function g(a,b){var c=b.match(/^[+#./;?&]*/)[0],d=function(a){return-1!==c.indexOf(a)},e=(b.match(/[*]*$/)[0],b.substring(c.length).split(",")),f=[];return d("#")&&f.push('"#"'),d(".")&&f.push('"."'),d("/")&&f.push('"/"'),e.forEach(function(b,c){function e(a){return Array.isArray(s)?-1===s.indexOf(a):"string"==typeof s?s===a:!0}var g=b,h=b.match(/(\:[0-9]+)?([*]*)$/),i=h[1],j=h[2];g=g.substring(0,g.length-h[0].length);var k=",",l="",m=",";j.indexOf("*")+1&&(m="=",d(".")?k=".":d("/")?k="/":d(";")?(k=";",l=encodeURIComponent(g)+"="):(d("?")||d("&"))&&(k="&",l=encodeURIComponent(g)+"="));var n="";d(";")?-1===j.indexOf("*")?(f.push(JSON.stringify(";"+g)),n="="):f.push(JSON.stringify(";")):d("?")&&0==c?f.push(-1===j.indexOf("*")?JSON.stringify("?"+g+"="):JSON.stringify("?")):d("?")||d("&")?f.push(-1===j.indexOf("*")?JSON.stringify("&"+g+"="):JSON.stringify("&")):d("&")?f.push(JSON.stringify("&"+g+"=")):c>0&&f.push(d(".")?'"."':d("/")?'"/"':d("?")?'"&"':'","');var o=[];if(i){var p=parseInt(i.substring(1));o.push(function(a){return"("+a+' || "").substring(0, '+p+")"})}o.push(d("+")||d("#")?function(a){return"encodeURI("+a+")"}:function(a){return"encodeURIComponent("+a+').replace(/!/g, "%21")'});var q=a(g);"string"==typeof q&&(q={code:q});var r=q.code,s=q.type,t=o.length?function(a){return o.forEach(function(b){a=b(a)}),a}:null,u={};if(e("array")){if(!t)return JSON.stringify(l)+" + "+r+".join("+JSON.stringify(k+l)+")";u.array=r+".map(function (x) {\n	return "+(l?JSON.stringify(l)+" + ":"")+t("x")+";\n}).join("+JSON.stringify(k)+")"}e("object")&&(t||(t=function(a){return a}),u.object="Object.keys("+r+").map(function (key) {\n	return "+t("key")+" + "+JSON.stringify(m)+" + "+t(r+"[key]")+";\n}).join("+JSON.stringify(k)+")"),(e("string")||e("number")||e("integer")||e("boolean"))&&(u.plain=t(r));var v;1===Object.keys(u).length?v=u[Object.keys(u)[0]]:(v="",v=u.object&&u.plain?"(typeof "+r+' === "object" ? '+u.object+" : "+u.plain+")":u.object?u.object:u.plain,u.array&&(v="(Array.isArray("+r+") ? "+u.array+" : "+v+")")),n&&(v="("+r+"?"+JSON.stringify(n)+"+"+v+':"")'),f.push(v)}),f.join(" + ")}function h(a){return a.replace(/~/g,"~0").replace(/\//g,"~1")}function i(a){return a.replace(/~1/g,"/").replace(/~0/g,"~")}function j(a){return null==a?[]:a.match(/(^|,)(([^,\\"]|"([^"\\]|\\.)*"?)*)/g).map(function(a){return a.replace(/^,?\s*/,"")})}function k(a){var b=a.match(/^\s*<([^>]*)>/)||null,c={href:b[1]||null},d=a.replace(/^[^>]+>\s*;?/,"");return d.match(/(^|;)(([^;\\"]|"([^"\\]|\\.)*"?)*)/g).map(function(a){a=a.replace(/^\s*(;\s*)?/,"");var b=a.replace(/\=.*/,""),d=a.substring(b.length).replace(/(^\s*=\s*|\s+$)/g,"");if('"'===d.charAt(0))try{d=JSON.parse(d)}catch(e){}c[b]=c[b]||d}),c}function l(a){var b={};return(a.match(/(^\??|&)([^&]+)/g)||[]).forEach(function(a){a=a.substring(1);var c=a.split("=",1)[0],d=a.substring(c.length+1);b[decodeURIComponent(c)]=decodeURIComponent(d)}),b}function m(a){var b=[];for(var c in a)b.push(encodeURIComponent(c)+"="+n(a[c]));return b.length?"?"+b.join("&"):""}function n(a){return encodeURIComponent(a).replace(/%2F/gi,"/")}function o(){}function p(a,b){return T(a,b)}function q(a){this._schemas=a,this._props={},this._patterns={}}function r(a,b){for(var c=a.split("/").slice(1).map(i),d=c.pop(),e=0;e<c.length;e++){var f=c[e];if(!b||"object"!=typeof b){d=null;break}b=b[f]}return{target:b,key:d}}function s(a,c){function d(){a._pokeRootModel(c,n)}function e(){o=null}function f(){if(!--t)for(n.ready=!0;s.length;)s.shift()()}function g(){y={},A={},B={},C=[];for(var a=0;a<x.length;a++)C=C.concat(x[a](w,"",y,A,B))}function l(a,b,c,d){for(var e=d[a]||[],f=y[a]||[],g=[],i=[],j=0;j<e.length;j++)-1===f.indexOf(e[j])&&i.push(e[j]);for(var j=0;j<f.length;j++){var k=f[j];-1===e.indexOf(k)&&g.push(k)}if(g.length||i.length){b.m&&b.m.emit("schemachange",g,i);for(var m in b.c)(null===c||m!==c)&&l(a+"/"+h(m),b.c[m],null,d)}}function m(a){for(var b in a.c){var c=a.c[b];c.m&&c.m.emit("change",""),m(c)}}var n=this;this.dataStore=a,this.storeKey=c,this.state=Date.now();var o=null,p=this.pokeStore=function(){o=o||d()||O(e)||!0};this.url=null,this.http={status:null,headers:{}},this.ready=!0;var s=[];this.whenReady=function(a){return this.ready?O(a):void s.push(a)};var t=0;this.pendingOperation=function(){return this.ready=!1,t++,f};var w=null,x=[],y={},z={},A={},B={},C=[],D=!1;this.reset=function(a,c){t++,x=(c||[]).map(function(a){return t++,"string"==typeof a&&(a=b(n.url||this.dataStore.baseUrl,a)),I.validationErrors(a,f)}),this.ready=1>=t&&!x.length||I.schemasFetched(),this.setPathValue("",a),O(f)};var E={c:{}};this.modelForPath=function(a){for(var b=a.split("/").slice(1).map(i),c=E,d=0;d<b.length;d++){var e=b[d];c=c.c[e]=c.c[e]||{c:{}}}return c.m=c.m||new u(this,a)},this.setPathValue=function(a,b){if(this.state--,p(),a){var c=r(a,w);if(!c.target||"object"!=typeof c.target)return!1;if(c.target[c.key]===b)return!0;"undefined"==typeof b?delete c.target[c.key]:c.target[c.key]=b}else w=b;var d=y;g();for(var e=a.split("/"),f=E,h=1;h<=e.length;h++){var j=e.slice(0,h).join("/"),k=null;if(j!==a&&(k=i(e[h])),l(j,f,k,d),f.m&&f.m.emit("change",a.substring(j.length)),null!==k){if(f=f.c[k],!f)break}else m(f)}return this.ready||D||(D=!0,s.unshift(function(){z={},D=!1;var a=y;g(),l("",E,null,a)})),!0},this.getPathValue=function(a){if(p(),!a)return w;var b=r(a,w);return b.target&&"object"==typeof b.target?b.target[b.key]:void 0},this.getPathSchemas=function(a){return(y[a]||[]).slice(0)},this.getPathSchemaSet=function(a){var b=y[a]||[],c=b.join("\n"),d=b.every(function(a){return"string"==typeof a});if(d)return z[c]=z[c]||new q(b.map(function(a){return U.get(a)}));throw new Error("Non-string schemas not supported yet")},this.getPathLinks=function(a,b){var c=this,d=A[a]||[];return!a&&this.http.headers.link&&(d=d.concat(j(this.http.headers.link).map(k))),d.filter(function(a){return"string"==typeof b&&b!==a.rel?!1:!0}).map(function(a){return new v(c,a)})},this.getPathErrors=function(a,b,c){a=a||"";var d=C.filter(function(b){return b.path==a||!c&&b.path.substring(0,a.length)==a&&"/"==b.path.charAt(a.length)});if(b)for(var e in B)(e==a||!c&&e.substring(0,a.length)==a&&"/"==e.charAt(a.length))&&B[e].forEach(function(a){var b=a.replace(/#.*/,"");d.push($[b]?{code:L.SCHEMA_FETCH_ERROR,path:e,params:{message:$[b].message,status:$[b].httpStatus||null},schema:a}:{code:L.SCHEMA_MISSING,path:e,params:{},schema:a})});return d}}function t(a){return null==a&&(a=""),a+="",a&&"/"!==a.charAt(0)&&(a="/"+h(a)),a}function u(a,b){this._root=a,this._path=b}function v(a,c){this._root=a,this.href=b(a.url,c.href),this.rel=c.rel,this.method=c.method||"GET"}function w(a){var b=Object.keys(Z);if(0===b.length){if(W=V.classes(null,p),V.missing().length)return ab();for(;!a&&_.length;){var c=_.shift();c()}}}function x(a,b){"string"==typeof a&&(b=a,a=null),this.baseUrl=b||(a?a.baseUrl:""),this.parent=a,this.config=a?Object.create(a.config):{keepMs:1e3},this._store=a?Object.create(a._store):{},this._removeTimeouts={}}function y(a){for(var b=a;b.parentNode;)b=b.parentNode;return b===a.ownerDocument}function z(a,b){var c=a.match(/[#\.][^#\.]+/g)||[];return a=a.replace(/[#\.].*/,"")||"span",c.forEach(function(a){"#"===a.charAt(0)?b.id=args.substring(1):b["class"]?b["class"]+=" "+a.substring(1):b["class"]=a.substring(1)}),a||"span"}function A(a,b){var c=Array.prototype.slice.call(arguments,2);"object"!=typeof b&&(c.unshift(b),b=null),b=b||{},a=z(a,b);var d="<"+a;for(var e in b){var f=b[e];"function"==typeof f&&(f=f()),I.is(f)&&(f=f.get()),""===f||f===!0?d+=" "+e.escapeHtml():f&&(d+=" "+e.escapeHtml()+'="'+f.toString().escapeHtml()+'"')}return d+=">"+c.join("")+"</"+a+">"}function B(a,b,c){return bb[b]?bb[b](a,c):null==c?a.removeAttribute(b):void a.setAttribute(b,c)}function C(a,b,c){function d(a){f=f||a,--e||c(a)}var e=1,f=null;if(1===a.nodeType){"a"===a.tagName.toLowerCase()&&(a.hasAttribute("ajax")||a.hasAttribute("data-ajax"))&&b.ajaxLink(a);for(var g=0;g<a.childNodes.length;g++){var h=a.childNodes[g];1===h.nodeType&&(h.hasAttribute(eb)?(e++,b._bindKeyPath(h,h.getAttribute(eb),h.getAttribute(fb),h.getAttribute(gb),d)):(e++,b.unbind(h),C(h,b,d)))}}d()}function D(a,b,c,d,e){function f(a){l=l||a,--k||e(a)}if(1===b.nodeType){for(var g=0;g<b.attributes.length;g++){var h=b.attributes[g].name,i=b.attributes[g].value;a.getAttribute(h)!==i&&B(a,h,i)}for(var j=[],g=0;g<a.attributes.length;g++){var h=a.attributes[g].name;j.push(h)}j.forEach(function(c){b.hasAttribute(c)||B(a,c,null)})}var k=1,l=null,m=c.path;if(!m)return a.nodeValue=b.nodeValue,f(null);for(var n=-1,o=-1,p=1;p<m.length;p++){var q=m[p];if(null!==q){var r=m[p-1];if(null===r){var s=a.childNodes[q+n],t=b.childNodes[p-q+o];k++,D(s,t,c.actions[p-1],d,f)}else if(r===q){n++;var s=a.childNodes[q+n],t=b.childNodes[p-q+o];b.removeChild(t),a.insertBefore(t,s),o--}else{var s=a.childNodes[q+n];a.removeChild(s),n--}}}f()}function E(a,b,c,d){if(a.nodeType===b.nodeType){if(1!==a.nodeType)return{score:.5};if(a.tagName===b.tagName&&("input"!==a.tagName||a.type===b.type)){if(!d&&b.hasAttribute(eb))return a.getAttribute(eb)===b.getAttribute(eb)&&a.getAttribute(fb)===b.getAttribute(fb)&&a.getAttribute(gb)===b.getAttribute(gb)?{score:1}:a.hasAttribute(eb)?{score:.1}:{score:.5};for(var e=1,f=1,g=0;g<a.attributes.length;g++){e++;var h=(a.attributes[g].name,a.attributes[g].value);b.getAttribute(g)===h&&f++}for(var g=0;g<b.attributes.length;g++)a.hasAttribute(b.attributes[g].name)||e++;for(var i=f/e,j=[{score:i,path:[0],actions:[]}],k=[],l=a.childNodes.length,m=b.childNodes.length,n=1,o=l+m+1;o>n;){for(var p=[],q=Math.max(0,n-m);l>=q&&n>=q;q++){var r=a.childNodes[q-1],s=b.childNodes[n-q-1],t={score:-1},u=-1,v=j[q];if(v){var i=0;i>u&&(t={score:v.score+i,path:v.path.concat([q]),actions:v.actions.concat(["add "+s])})}var w=j[q-1];if(w){var i=0;i>u&&(t={score:w.score+i,path:w.path.concat([q]),actions:w.actions.concat(["remove"+r])})}var x=k[q-1];if(x){var y=E(r,s,c)||{score:-1/0};y.score>u&&(t={score:x.score+y.score,path:x.path.concat([null,q]),actions:x.actions.concat(["merge "+r+" -> "+s,y])})}p[q]=t}k=j,j=p.slice(0),p.sort(function(a,b){return b.score-a.score}),j=j.map(function(a){return p.indexOf(a)<c?a:null}),n++}var z=j[l];return z}}}function F(a,c){if(!(this instanceof F))return new F(a,c);var d=this;if(this.registerIndex=c,this.preferDom=!!a.preferDom,("string"==typeof a.canBind||Array.isArray(a.canBind))&&(a.canBind={schema:a.canBind}),"object"==typeof a.canBind){var e=a.canBind;e.schema&&!Array.isArray(e.schema)&&(e.schema=[e.schema]),e.type&&!Array.isArray(e.type)&&(e.type=[e.type]),e.tag&&!Array.isArray(e.tag)&&(e.tag=[e.tag]),this.canBind=function(a,c,d){if(e.tag&&-1===e.tag.indexOf(c))return!1;if(e.type){var f=a.jsonType();if(-1===e.type.indexOf(f))return!1}if(e.schema){var g=a.schemas(),h=a._root.dataStore.baseUrl;if(!e.schema.some(function(a){return a=b(h,a),-1!==g.indexOf(a)}))return!1}return e.filter&&!e.filter(a,c,d)?!1:!0},this.priority=a.priority||0,this.priority+=10*!!e.tag+5*!!e.schema+2*!!e.type}else this.canBind=a.canBind,this.priority=a.priority||0;"function"==typeof a.html?this.html=a.html.bind(a):"string"==typeof a.html&&(this.html=function(){return a.html});var f=a.modelEvents||{};f.change=f.change||function(a,b,c,d){return!d};var g=a.uiEvents||{};this.bindDom=function(a,b,c){var e=function(){return y(c)?void 0:(console.log("Detached from document: ",c),a.unbind(c),clearInterval(h),!0)},h=setInterval(e,1e3),i=a.boundJsonModelEvents={};Object.keys(f).forEach(function(e){var g=f[e],h=i[e]=function(){if(c.boundContext!==a)return d.unbindDom(a,b,c);var e=Array.prototype.slice.call(arguments,0);e=[b,c,a].concat(e);var f=g.apply(this,e);f&&a.bind(b,c)};b.on(e,h)});var j=a.boundUiEvents={};Object.keys(g).forEach(function(e){var f=g[e],h=j[e]=function(){if(c.boundContext!==a)return d.unbindDom(a,b,c);var e=Array.prototype.slice.call(arguments,0);e=[b,c,a].concat(e);var g=f.apply(this,e);g&&a.bind(b,c)};a.ui.on(e,h)}),b.emit("bind",c),j.bind&&j.bind.call(null)},this.unbindDom=function(a,b,c){b.emit("unbind",c),a.boundUiEvents.unbind&&a.boundUiEvents.unbind.call(null);for(var d in a.boundJsonModelEvents){var e=a.boundJsonModelEvents[d];b.off(d,e)}for(var d in a.boundUiEvents){var e=a.boundUiEvents[d];a.ui.off(d,e)}}}function G(a){this._state=0,this._immediateOptions=[],this._concatOptions=[],this._needSort=!1,this.parent=a||{_state:0,_options:function(){return this}.bind([])},this._parentState=a?a.options().length:0}function H(a,b,c){this._bindings=a,this._dataStore=b,this._root=this,this._model=null,this._usedBindings=[],this.ui=this._dataStore.create(c||{}),this.includeDataProperties=!1,this.urlForState=function(a){return"object"==typeof window&&window.location&&"string"==typeof window.location.href&&(a=I.util.url.relative(window.location.href,a)),I.util.url.encodeQuery({json:a})||"?"},this.stateForUrl=function(a){var b=I.util.url.parse(a),c=I.util.url.parseQuery(b.search);return[c.json,{}]}}var I={version:"0.2.24"},J={};J.util={parseUrl:a,resolveUrl:b,isSubUrl:c};var K=J.SchemaStore=function(a){this.schemas=a?Object.create(a.schemas):{},this.missingUrls=a?Object.create(a.missingUrls):{},this.missing=function(b,c){if(void 0===b){if(a){var d=[];for(var e in this.missingUrls)a.missing(e)?d.push(e):delete this.missingUrls[e];return d}return Object.keys(this.missingUrls)}if(this.schemas[b])return!1;var f=b.replace(/#.*/,""),d=!(!this.missingUrls[f]&&f in this.schemas||a&&!a.missing(b));return d&&!c&&(this.missingUrls[f]=!0),d}};K.prototype={child:function(){return new K(this)},add:function(a,b){"object"==typeof a&&(b=a,a=b.id||arguments[1]);var c=a.replace(/#.*/,"");a===c+"#"&&(a=c),b&&(b.id=b.id||a),delete this.missingUrls[c],this.schemas[a]=b,this._searchSchema(b,a)},_searchSchema:function(a,d){if(a&&"object"==typeof a)if(void 0===d?d=a.id:"string"==typeof a.id&&(a.id=d=b(d,a.id)),Array.isArray(a))for(var e=0;e<a.length;e++)this._searchSchema(a[e],d);else{"string"==typeof a.id&&c(d,a.id)&&void 0===this.schemas[a.id]&&(this.schemas[a.id]=a),"string"==typeof a.$ref&&(a.$ref=b(d,a.$ref));for(var f in a)if("enum"!==f)if("object"==typeof a[f])this._searchSchema(a[f],d);else if("$ref"===f){var g=a[f],h=g.replace(/#.*/,"");!h||g in this.schemas||h in this.schemas||(this.missingUrls[h]=!0)}}},resolveRefs:function(a,b){if(a&&void 0!==a.$ref){if(b=b||{},b[a.$ref])return this.createError(L.CIRCULAR_REFERENCE,{urls:Object.keys(b).join(", ")},"","");b[a.$ref]=!0,a=this.get(a.$ref,b)}return a},get:function(a,b,c){var d;if(void 0!==this.schemas[a])return d=this.schemas[a],c?d:this.resolveRefs(d,b);var e=a.replace(/#.*/,""),f=a.substring(e.length+1);if("object"==typeof this.schemas[e]){d=this.schemas[e];var g=decodeURIComponent(f);if(""===g)return c?d:this.resolveRefs(d,b);if("/"!==g.charAt(0))return void 0;for(var h=g.split("/").slice(1),i=0;i<h.length;i++){var j=h[i].replace(/~1/g,"/").replace(/~0/g,"~");if(!d||void 0===d[j])return void 0;d=d[j]}if(void 0!==d)return c?d:this.resolveRefs(d,b)}this.missingUrls[e]=!0}},J.SchemaStore=K;var L=J.ErrorCodes={INVALID_TYPE:0,ENUM_MISMATCH:1,ANY_OF_MISSING:10,ONE_OF_MISSING:11,ONE_OF_MULTIPLE:12,NOT_PASSED:13,NUMBER_MULTIPLE_OF:100,NUMBER_MINIMUM:101,NUMBER_MINIMUM_EXCLUSIVE:102,NUMBER_MAXIMUM:103,NUMBER_MAXIMUM_EXCLUSIVE:104,STRING_LENGTH_SHORT:200,STRING_LENGTH_LONG:201,STRING_PATTERN:202,OBJECT_PROPERTIES_MINIMUM:300,OBJECT_PROPERTIES_MAXIMUM:301,OBJECT_REQUIRED:302,OBJECT_ADDITIONAL_PROPERTIES:303,OBJECT_DEPENDENCY_KEY:304,ARRAY_LENGTH_SHORT:400,ARRAY_LENGTH_LONG:401,ARRAY_UNIQUE:402,ARRAY_ADDITIONAL_ITEMS:403,FORMAT_CUSTOM:500,KEYWORD_CUSTOM:501,CIRCULAR_REFERENCE:600,SCHEMA_MISSING:700,SCHEMA_FETCH_ERROR:701,DOCUMENT_FETCH_ERROR:702,UNKNOWN_PROPERTY:1e3},M=J.uriTemplate=function(a,b){if("function"

