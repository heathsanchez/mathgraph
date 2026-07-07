# Recon Report

## Verdict

`PROMOTE_LEAN_RECON`

## Decision

JSON:
{
  "verdict": "PROMOTE_LEAN_RECON",
  "issue": {
    "url": "https://github.com/lovecn/lovecn.github.io/issues/4",
    "title": "\u90a3\u4e9b\u5e74\uff0c\u6211\u4eec\u4e00\u8d77\u8e29\u8fc7\u7684\u5751\u548c\u5f00\u53d1\u6280\u5de7",
    "state": "OPEN",
    "labels": [],
    "comment_count": 1,
    "updatedAt": "2017-08-07T02:21:46Z"
  },
  "has_lean": true,
  "has_tests": true,
  "has_benchmark": true,
  "has_money": true,
  "has_surface": true,
  "risk": false
}

## Issue body excerpt

记录开发中那些坑坑洼洼，欢迎补充，我会不断总结更新

1.json格式问题 
json格式非常严格，不能有空格，tab，换行符，否则解析不了
关于json的规定：
1） 并列的数据之间用逗号（", "）分隔。
2） 映射用冒号（": "）表示。
3） 并列数据的集合（数组）用方括号("[]")表示。
4） 映射的集合（对象）用大括号（"{}"）表示。
关于PHP对json支持说明：
json_encode只支持UTF-8编码的数据；
json_decode永远只反映一个PHP对象，带上第二个参数true可返回数组

``` php
$replace = array(' '=>'','\n'=>'','\t'=>'');
$replace_json=  trim(strtr($json,$replace));
$response = '{"retcode":"0","retmsg":"OK","cre_id_enc":"","cre_type":"","fee_type":"1","listid":"1221085301201410240000001024","out_trade_no":"201410246763831","partner":"1221085301","pay_fee":"0","sign":"PTamau\x2BjkynA00cASKJ6Nd3QwFSBP44TKSqmmdCd\x2F\x2B0o8ViSt3fp5vQr0Fc73U42NhtImfnHzbynoUjURiNLW5O4hI61xkG\x2F97JRPRE0nHuvtAumqXfbVCsLveugE52HRZsJvm3EG7pL6GlhYf8ng6qxiUrDyn89PFVZ04Wd8Gk\x3D","total_fee":"1000000","unfreeze_fee":"1000000","user_name_enc":""}';
$data = json_decode($string);
    switch (json_last_error()) {
        case JSON_ERROR_NONE:
            echo ' - No errors';
            break;
        case JSON_ERROR_DEPTH:
            echo ' - Maximum stack depth exceeded';
            break;
        case JSON_ERROR_STATE_MISMATCH:
            echo ' - Underflow or the modes mismatch';
            break;
        case JSON_ERROR_CTRL_CHAR:
            echo ' - Unexpected control character found';
            break;
        case JSON_ERROR_SYNTAX:
            echo ' - Syntax error, malformed JSON';
            break;
        case JSON_ERROR_UTF8:
            echo ' - Malformed UTF-8 characters, possibly incorrectly encoded';
            break;
        default:
            echo ' - Unknown error';
            break;
    }
错误类型为 - Syntax error, malformed JSON
json中包含十六进制的ASCII字符，所以json_decode无法识别，返回NULL。使用下面的代码进行转码：
$json = str_ireplace( '\x', '\\\\x', $response );
print_r( json_decode($json,true));见 [例子](http://3v4l.org/WVVrj)
其他常见问题解决方法：
#1.不能有多余的逗号(,) 
用正则替换掉，
preg_replace('/,\s*([\]}])/m', '$1', $json) 
#2.只能使用双引号(")
在JSON里只用"来表示字符串，例如
{'aa':'sdf'}
'adf'
['1', '2']
这些使用'的统统不能解析，而且对象的属性也必须用"，也就是只能用双引号.. 
直接用str_replace("'", '"', $json) 来替换就好了，，不过就是会把所有单引号转换为双引号 。
```

2.utf-8 BOM问题[参照之前一文](http://lovecn.github.io/utf8.html)
BOM为文件开头的3个字节EFBFBB,php不会忽略，因此返回的json解析不了

``` php
$res = substr($result, 3);
$arr = json_decode($res, true);
function remove_utf8_bom($text) { 
$bom = pack('H*','EFBBBF'); 
$text = preg_replace("/^$bom/", '', $text);
 return $text;
 } 
$header = array(
    "User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"
);
$curl = curl_init('http://www.btc38.com/trade/getTradeList.php?coinname=XRP');
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_HTTPHEADER, $header);
$res = curl_exec($curl);
curl_close($curl);
//$res = substr($res, 3);
$data=json_decode($res,true);
var_dump($data);

```

3.js数据类型判断

``` javascript
typeof null =='object'  // true 
typeof [] =='object' // true 
typeof {} =='object' // true 
判断数组靠谱解法是 Object.prototype.toString.call(arr) === '[object Array]'
// 类型判断
function isType(type){
    return function(o){
        return Object.prototype.toString.call(o) === '[object ' + type + ']';
    }
}
var isArray = isType("Array");
如果用jq：$.type(obj);
```

4.赋值表达式

``` php
if($var = 1) {
//判断始终成立
}
if(1 = $var) {
//error
}
```

5.浮点数，这个很多语言会有,php处理大数据使用`bcmath`扩展

``` php
console.log(0.1+0.2);//0.30000000000000004
console.log((0.1*10+0.2*10)/10);//0.3
使用JavaScript内置的函数toPrecision或toFixed来保留一定的精度：

(0.1 + 0.2).toPrecision(10) == 0.3
> true

(0.1 + 0.2).toFixed(10) == 0.3
> true
$str = 0.68;
var_dump(intval($str * 100));//68
$str= 0.58;
var_dump(intval($str * 100));//57
var_dump(intval(strval($str* 100)));//58
$f = 12132435556776658;
echo $f;//1.2132435556777E+16
printf('%.0f',$f);//12132435556776658
echo number_format($f,0,'','');//12132435556776658
```

6.MySQL类型转换

``` php
mysql> create table temp(a varchar(10));
Query OK, 0 rows affected (0.01 sec)

mysql> insert into temp  values('a');
Query OK, 1 row affected (0.01 sec)

mysql> insert into temp  values('1');
Query OK, 1 row affected (0.00 sec)

mysql> select * from temp where a = 1;
+------+
| a    |
+------+
| 1    |
+------+
1 row in set, 1 warning (0.01 sec)

mysql> select * from temp where a = 0;
+------+
| a    |
+------+
| a    |
+------+
1 row in set, 1 warning (0.00 sec)

```

7.foreach引用

``` php

$items = array('a','b','c');
foreach($items as &$v){

}

foreach($items as $v){

}

print_r($items);
以下为解释
首先第一个foreach，每次循环都使得当前item的值变成引用，
array(3) { [ 0 ]=> &string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> string(1) "c" } 
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> &string(1) "b" [ 2 ]=> string(1) "c" } 
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> &string(1) "c" }
当foreach运行完，得到结果是：
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> &string(1) "c" }

当执行第二个foreach的时候，每次循环都是把值写入$v引用的地址空间，也就是$items[ 2 ]，
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> &string(1) "a" } //$items[ 0 ] = a ，写入$items[ 2 ]
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> &string(1) "b" } //$items[ 1 ] = b ，写入$items[ 2 ]
array(3) { [ 0 ]=> string(1) "a" [ 1 ]=> string(1) "b" [ 2 ]=> &string(1) "b" } //$items[ 2 ] = &c，是$items[ 2 ]的地址，把它的值(b)取出来写入$items[ 2 ]

注：留意“ & ”符号，使用var_dump替换print_r打印数据
解决方案：只要在第一个循环最后加上unset（$v） 就可以避免这种情况发生了
```

8.使用trim函数不能去除2个以上的连续点号(.)

``` php
echo trim('abcdcba...','...');//abcdcba error  改为 trim('abcdcba...','\.\.\.');
echo trim('abcdcba...','a..d');//...  把a b c d 都去掉。因为省略号的原因，所以trim函数的第二个参数不能用..开头或者结尾
echo trim("abcdcba","abc")."\n";//把a b c分别去掉
```

9.crontab 添加一个定时任务没有生效
最常见的原因就是： 你在脚本里面的命令没有使用绝对路径。
10.[时间处理](http://3v4l.org/77C0T) require php5.3+

``` php
function date($from, $now) {
    $timezone = new DateTimeZone('Asia/Shanghai');
    $now = new DateTime($now, $timezone);
    $from = new DateTime($from, $timezone);
    $between = $now->diff($from);

    if(!$between->invert) return false;

    /** 如果超过了一年 **/
    if($between->y) 
        return $from->format('Y年m月d日');

    /** 一年内大于七天 **/
    if($between->days > 6) 
        return $from->format('n月j日');

    /** 一个礼拜内但是大于两天**/
    if($between->days > 1)
        return $between->format('%d天前');

    /** 如果是昨天 **/
    if($between->days)
        return $from->format('昨天 H:i');

    /** 如果一天之内超过一个小时 **/
    if($between->h > 1)
        return $between->format('%h小时前');

    if($between->i > 1)
        return $between->format('%i分钟前');

    return $between->s ? $between->format('%s秒前') : '刚刚';
}
echo date('2014-11-11 11:11:11', 'now');
```

11.json_encode中文处理

``` php
function encode_json($str){
    $code = json_encode($str);
    return preg_replace("#\\\u([0-9a-f]+)#ie", "iconv('UCS-2', 'UTF-8', pack('H4', '\\1'))", $code);
}
echo   encode_json('中文');//中文
echo json_encode('中文',JSON_UNESCAPED_UNICODE );//require php5.4+
function unicode2utf8($str){
        $str = '{"str":"'.$str.'"}';    //组合成json格式
    $strarray = json_decode($str,true); //json转换为数组，利用 JSON 对 \uXXXX 的支持来把转义符恢复为 Unicode 字符
    return $strarray['str'];
    }


## Inventory excerpt

top files
《数字货币基金-仓位管理之道》全文整理.pdf
整理笔记-2012.chm
壁虎漫步.crx
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
正则.png
信息安全大赛题目/题目.txt
信息安全大赛题目/明文猜解/GoodLuck.php
信息安全大赛题目/数据库注入/index.php
信息安全大赛题目/数据库注入/injection.sql
信息安全大赛题目/数据库注入/query.php
信息安全大赛题目/JavaScript解密/GoodLuck.html
Alipay.php
another/撩汉全攻略  绿茶婊秘笈.pdf
another/魔鬼约会学-阮琦.pdf
another/魔鬼搭讪学：这样追女孩真的很容易-魔鬼咨询师.pdf
another/魔鬼约会学-阮琦.txt
another/魔鬼搭讪学：这样追女孩真的很容易-魔鬼咨询师.txt
another/蓝灯使用流程.docx
another/赛风.exe
another/2018中国区块链行业分析报告.pdf
another/gfwpsiphon31.exe
another/gohls.exe
another/google python风格指南(中文版).pdf
another/Laravel框架关键技术解析 [陈昊].pdf
app.js
area.sql
arr_sort.php
article.css
biaobai.html
callback.png
carbon.php
chat/app.js
chat/index.js
chat/package.json
chat/public/index.html
chat/public/main.js
chat/public/style.css
check_chinese.php
checkgit.sh
Chinese_to_py.php
citys.html
citys.text
Cn2pinyin.php
confession.html
copyzhihu.html
curl_cookie.php
downexcel.php
download.php
downloadapp.html
downphp.php
dragupload.php
excelreader.php
FFmpeg_Joiner.exe
finally.py
fulllisttstomp4.py
functions.php
game/.DS_Store
game/authorization.html
game/create_code.php
game/css/.DS_Store
game/css/css.css
game/db.sql
game/do_ajax.php
game/images/dl.png
game/images/fanhui.png
game/images/jinru.png
game/images/line.png
game/images/portrait.png
game/images/sq.png
game/images/ss_m.png
game/images/tj.png
game/images/topbg.jpg
game/images/tuichu.png
game/images/wanjia.png
game/images/yzm.png
game/index.html
game/index.php
game/login.html
game/login.php
game/register.html
game/register.php
game/returncard.html
game/returncard.php
git基本操作指南-TortoiseGit用户手册.docx
git基本操作指南.docx
handlererror.php
happy_birthday.html
hole.php
html5drag.html
html5upload.html
htmlcode.html
index.html
internet.html
javascript.md
jay.html
jay.jpg
jqueryvalidation.html
kaolafm
开源系统代码分析与laravel框架.zip
login_qq.py
logindouban.py
loginv2ex.py
loginzhihu.py
love.html
M3U8 Downloader.exe
markdown.js
marquee.html
menulist.html
movie.m3u8
mpdfphp.php
my_word_cloud.py
myheart.html
myphantomjs.py
mysql_type.php
new_resume.html
Number.js
old_project/20130226.sql
old_project/20130311.sql
old_project/add.php
old_project/adodb-time.inc.php
old_project/adodb.inc.php
old_project/ajax.pager.php
old_project/ajax.php
old_project/backup.php
old_project/city.js
old_project/class.rc4crypt.php
old_project/common/common.css
old_project/common/jquery-ui-1.8.16.custom.min.js
old_project/common/jquery-ui-timepicker-addon.js
old_project/common/jquery-ui-timepicker.css
old_project/common/jquery-ui.css
old_project/common/jquery.1.5.2.js
old_project/common/jquery.blockui.js
old_project/common/jquery.ckform.js
old_project/common/topback.gif
old_project/config.php
old_project/curl.php
old_project/date.php
old_project/delete.php
old_project/edit.php
old_project/index.php
old_project/index2.php
old_project/jquery.anyDrag.js
old_project/jquery.form.js
old_project/jquery.multi-select.js
old_project/js.html
old_project/json2.js
old_project/manage.php
old_project/manage2.php
old_project/mess.php
old_project/multiselect.css
old_project/nusoap.php
old_project/pager.class.php
old_project/pager.php
old_project/pdo.class.php
old_project/pdo.php
old_project/player.sql
old_project/RcAdoSlave.php
old_project/RcPager.php
old_project/scrolltopcontrol.js
old_project/serverSoap.php
old_project/smarty/Config_File.class.php
old_project/smarty/debug.tpl
old_project/smarty/Smarty_Compiler.class.php
old_project/smarty/Smarty.class.php
old_project/stat_live.php
old_project/stat.php
old_project/tel.php
old_project/templates_c/%%17^17E^17E6A590%%manage.html.php
old_project/templates_c/%%1A^1AB^1AB9BADF%%login.html.php
old_project/templates_c/%%37^375^375448EA%%add.tpl.php
old_project/templates_c/%%45^45E^45E480CD%%index.tpl.php
old_project/templates_c/%%58^582^58260C52%%manage.tpl.php
old_project/templates_c/%%6B^6BA^6BA9C0AB%%vote.html.php
old_project/templates_c/%%6D^6D0^6D0D8E79%%edit.html.php
old_project/templates_c/%%6D^6D5^6D5521DC%%stat_live.html.php
old_project/templates_c/%%77^774^774BE9C9%%index.html.php
old_project/templates_c/%%81^81F^81F8E8D9%%stat_live.tpl.php
old_project/templates_c/%%AC^AC4^AC4C5AFC%%tel.html.php
old_project/templates_c/%%BC^BCA^BCA8A035%%mess.tpl.php
old_project/templates_c/%%C4^C4D^C4D4DFC7%%mess.html.php
old_project/templates_c/%%CB^CBA^CBAC809C%%vote.tpl.php
old_project/templates_c/%%D2^D23^D233EC6A%%add.html.php
old_project/templates_c/%%D9^D95^D9574DD9%%edit.tpl.php
old_project/templates_c/%%E8^E80^E80E6BD6%%stat.tpl.php
old_project/templates_c/%%F9^F99^F99E63E7%%tel.tpl.php
old_project/templates_c/%%FD^FD8^FD83CACE%%stat.html.php
old_project/templates/add.tpl
old_project/templates/edit.tpl
old_project/templates/index.tpl
old_project/templates/manage.tpl
old_project/templates/mess.tpl
old_project/templates/stat_live.tpl
old_project/templates/stat.tpl
old_project/templates/tel.tpl
old_project/templates/vote.tpl
old_project/vote.php
old_project/words.txt
old_project/YMDClass.js
one.mp4
onlyloveyou.html
page-visibility.html
parent_caterogy/action.php
parent_caterogy/categoryadd.php
parent_caterogy/categoryedit.php
parent_caterogy/categorys.sql
parent_caterogy/db.php
parent_caterogy/function.php
parent_caterogy/index.php
parent_caterogy/js/submitForm.js
parent_caterogy/styles/style.css
parent_caterogy/test.php
paste.php
pay.php
php_manual_zh_review.chm
php_to_excel.php
php面试.txt
phpanalysis/demo.php
phpanalysis/dict_build.php
phpanalysis/dict/base_dic_full.dic
phpanalysis/dict/readme.txt
phpanalysis/dict/words_addons.dic
phpanalysis/phpanalysis.class.php
phpanalysis/readme/license.txt
phpanalysis/readme/readme.txt
phpmarkdown/demo/demo.php
phpmarkdown/demo/editor.html
phpmarkdown/demo/exchangeMarkdown.php
phpmarkdown/demo/html_2_md.md
phpmarkdown/demo/html_back.html
phpmarkdown/demo/markdown_back.md
phpmarkdown/demo/markdown_document.md
phpmarkdown/demo/markdown_html.html
phpmarkdown/demo/md_2_html.html
phpmarkdown/LICENSE
phpmarkdown/markdown.class.php
phpmarkdown/README.md
phprequest.php
pinyin.js
pool.py
postjson.php
python_tricks.html
python2 vs python3.png
pythontip.html
README.md
record.php
resume.md
saveexcel.py
segmentfault_1111.py
segmentfault_1111.rar.rar
segmentfault_1111.txt
simhei.ttf
simple.py
skill.jpg
slim.php
stackoverflow.php
test_sign.php
test.sh
testsplinter.py
time.js
tokbox.html
tokbox.php
tool.js
unicode_encode.php
unicode.html
upload_view.html
upload.php
uploadfile.html
uploadfile.php
usermedia.html
utf8.html
vhallsort.php
video.html
Visibilitydemo.html
vue.html
waitalone.py
weather.html
webapi_for_app app接口定义 [VhallTech]_20150521212616.png
webhook.html
wechatMultiPay/.idea/misc.xml
wechatMultiPay/.idea/modules.xml
wechatMultiPay/.idea/MultiPay.iml
wechatMultiPay/.idea/php.xml
wechatMultiPay/.idea/workspace.xml
wechatMultiPay/classes/Autoloader.php
wechatMultiPay/classes/Config.php
wechatMultiPay/classes/Curl.php
wechatMultiPay/classes/Encryption.php
wechatMultiPay/classes/Pay.php
wechatMultiPay/classes/PayFactory.php
wechatMultiPay/multipay.php
wechatMultiPay/README.md
weibo.py
weibo2.py
wxMessage.css
ximadown.py
ximalaya.py
zh_pinyin,php
zhihu.py
zhihuanswer.py

build/test files
./chat/package.json
./phpmarkdown/README.md
./README.md
./wechatMultiPay/README.md


## Grep excerpt

===== judge hits =====
./php面试.txt:1158:为%XX,其中 XX 为 该符号以16进制表示的 ASCII
./phpmarkdown/LICENSE:110:menu, a prominent item in the list meets this criterion.
./phpmarkdown/LICENSE:598:ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
./phpmarkdown/LICENSE:605:GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
./carbon.php:653:    /////////////////////// WEEK SPECIAL DAYS /////////////////////////
./excelreader.php:1098:									// continuation it is in straightforward ASCII encoding
./fulllisttstomp4.py:23:import unittest
./信息安全大赛题目/JavaScript解密/GoodLuck.html:49:	var chrsz = 8; /* bits per input character. 8 - ASCII; 16 - Unicode */
./信息安全大赛题目/JavaScript解密/GoodLuck.html:232:	* If chrsz is ASCII, characters >255 have their hi-byte silently ignored.
./utf8.html:116:###ASCII
./utf8.html:117:> 计算机只能处理数字，如果要处理文本，就必须先把文本转换为数字才能处理.最早只有127个字母被编码到计算机里，也就是大小写英文字母、数字和一些符号，这个编码表被称为ASCII编码，比如大写字母A的编码是65，小写字母z的编码是122
./utf8.html:118:> ASCII 码使用7位二进制数来表示128个字符，也就是用一个字节来表示，最前的一位默认为 0。linux命令查看man ascii
./utf8.html:121:> 如果把最后一位也用起来的话，也就是8位二进制，那么就可以表示256个字符了，于是扩展 ASCII 码诞生，保留原始的7位的基础上，使用了最前的一位。
./utf8.html:152:> 在UTF-8文件中放置BOM主要是微软的习惯，BOM其实是为UTF-16和UTF-32准备的，微软在UTF-8使用BOM是因为这样可以把UTF-8和ASCII等编码明确区分开
./phpanalysis/readme/license.txt:445:THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
./phpanalysis/readme/license.txt:450:FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
./unicode.html:110:###ASCII
./unicode.html:111:> 计算机只能处理数字，如果要处理文本，就必须先把文本转换为数字才能处理.最早只有127个字母被编码到计算机里，也就是大小写英文字母、数字和一些符号，这个编码表被称为ASCII编码，比如大写字母A的编码是65，小写字母z的编码是122
./unicode.html:112:> ASCII 码使用7位二进制数来表示128个字符，也就是用一个字节来表示，最前的一位默认为 0。linux命令查看man ascii
./unicode.html:115:> 如果把最后一位也用起来的话，也就是8位二进制，那么就可以表示256个字符了，于是扩展 ASCII 码诞生，保留原始的7位的基础上，使用了最前的一位。
./unicode.html:121:> 例如当用三个字节存储一个字符时，它同时也可以被理解为存储了三个 ASCII 码，另外我们之前知道 ASCII 码只需要一个字节，但是如果 Unicode 规定每个字符使用三个字节来存储的话，那岂不是额外浪费两个字节的空间？
./unicode.html:122:> ASCII编码和Unicode编码的区别：ASCII编码是1个字节，而Unicode编码通常是2个字节。
./unicode.html:124:> 字母A用ASCII编码是十进制的65，二进制的01000001；
./unicode.html:126:> 字符0用ASCII编码是十进制的48，二进制的00110000，注意字符'0'和整数0是不同的；
./unicode.html:128:> 汉字中已经超出了ASCII编码的范围，用Unicode编码是十进制的20013，二进制的01001110 00101101。把ASCII编码的A用Unicode编码，只需要在前面补0就可以，因此，A的Unicode编码是00000000 01000001。
./unicode.html:129:> 字符	ASCII	Unicode	UTF-8
./unicode.html:152:> 在UTF-8文件中放置BOM主要是微软的习惯，BOM其实是为UTF-16和UTF-32准备的，微软在UTF-8使用BOM是因为这样可以把UTF-8和ASCII等编码明确区分开
./area.sql:473:INSERT INTO `area` VALUES (471, 102100108, '磁县', NULL, '056500', '0310', 37, 1, 'CIXIAN', 'CX', 1);
./area.sql:577:INSERT INTO `area` VALUES (575, 102106100, '安次区', NULL, '065000', '0316', 43, 1, 'ANCIQU', 'ACQ', 1);
./area.sql:692:INSERT INTO `area` VALUES (690, 103105102, '榆次区', NULL, '030600', '0354', 53, 1, 'YUCIQU', 'YCQ', 1);
./area.sql:1339:INSERT INTO `area` VALUES (1337, 110104100, '慈溪市', NULL, '315300', '0574', 125, 1, 'CIXISHI', 'CXS', 1);
./area.sql:2197:INSERT INTO `area` VALUES (2195, 117110100, '慈利县', NULL, '427200', '0744', 232, 1, 'CILIXIAN', 'CLX', 1);
./area.sql:3415:INSERT INTO `area` VALUES (3413, 131109102, '莿桐', NULL, '647', '008865', 410, 1, 'CITONG', 'CT', 1);
./old_project/nusoap.php:3799:				if(preg_match('/^(ISO-8859-1|US-ASCII|UTF-8)$/i',$enc)){
./old_project/nusoap.php:3802:					$this->xml_encoding = 'US-ASCII';
./old_project/nusoap.php:3805:				// should be US-ASCII for HTTP 1.0 or ISO-8859-1 for HTTP 1.1
./old_project/nusoap.php:3828:						if (preg_match('/^(ISO-8859-1|US-ASCII|UTF-8)$/i',$enc)) {
./old_project/nusoap.php:3831:							$this->xml_encoding = 'US-ASCII';
./old_project/nusoap.php:3834:						// should be US-ASCII for HTTP 1.0 or ISO-8859-1 for HTTP 1.1
./old_project/nusoap.php:3862:						if (preg_match('/^(ISO-8859-1|US-ASCII|UTF-8)$/i',$enc)) {
./old_project/nusoap.php:3865:							$this->xml_encoding = 'US-ASCII';
./old_project/nusoap.php:3868:						// should be US-ASCII for HTTP 1.0 or ISO-8859-1 for HTTP 1.1
./old_project/nusoap.php:4320:			if(preg_match('/^(ISO-8859-1|US-ASCII|UTF-8)$/i',$enc)){
./old_project/nusoap.php:4323:				$this->xml_encoding = 'US-ASCII';
./old_project/nusoap.php:4326:			// should be US-ASCII for HTTP 1.0 or ISO-8859-1 for HTTP 1.1
./old_project/nusoap.php:7468:				// we are only going to return the first part here...sorry about that
./old_project/nusoap.php:7664:			if(preg_match('/^(ISO-8859-1|US-ASCII|UTF-8)$/i',$enc)){
./old_project/nusoap.php:7667:				$this->xml_encoding = 'US-ASCII';
./old_project/nusoap.php:7670:			// should be US-ASCII for HTTP 1.0 or ISO-8859-1 for HTTP 1.1
./old_project/adodb.inc.php:3731:		'DECIMAL' => 'N',
./old_project/adodb.inc.php:3735:		'DOUBLE PRECISION' => 'N',
./old_project/adodb.inc.php:3750:		'SQLDECIMAL' => 'N', 
./old_project/city.js:32:	var str = {"1":{"n":"\u4e2d\u56fd","s":{"11":{"n":"\u5317\u4eac","c":{"1":{"n":"\u4e1c\u57ce"},"2":{"n":"\u897f\u57ce"},"5":{"n":"\u671d\u9633"},"6":{"n":"\u4e30\u53f0"},"7":{"n":"\u77f3\u666f\u5c71"},"8":{"n":"\u6d77\u6dc0"},"9":{"n":"\u95e8\u5934\u6c9f"},"11":{"n":"\u623f\u5c71"},"12":{"n":"\u901a\u5dde"},"13":{"n":"\u987a\u4e49"},"21":{"n":"\u660c\u5e73"},"24":{"n":"\u5927\u5174"},"26":{"n":"\u5e73\u8c37"},"27":{"n":"\u6000\u67d4"},"28":{"n":"\u5bc6\u4e91"},"29":{"n":"\u5ef6\u5e86"}}},"12":{"n":"\u5929\u6d25","c":{"1":{"n":"\u548c\u5e73"},"2":{"n":"\u6cb3\u4e1c"},"3":{"n":"\u6cb3\u897f"},"4":{"n":"\u5357\u5f00"},"5":{"n":"\u6cb3\u5317"},"6":{"n":"\u7ea2\u6865"},"26":{"n":"\u6ee8\u6d77\u65b0\u533a"},"10":{"n":"\u4e1c\u4e3d"},"11":{"n":"\u897f\u9752"},"12":{"n":"\u6d25\u5357"},"13":{"n":"\u5317\u8fb0"},"21":{"n":"\u5b81\u6cb3"},"22":{"n":"\u6b66\u6e05"},"23":{"n":"\u9759\u6d77"},"24":{"n":"\u5b9d\u577b"},"25":{"n":"\u84df\u53bf"}}},"13":{"n":"\u6cb3\u5317","c":{"1":{"n":"\u77f3\u5bb6\u5e84","r":{"2":"\u957f\u5b89\u533a","3":"\u6865\u4e1c\u533a","4":"\u6865\u897f\u533a","5":"\u65b0\u534e\u533a","7":"\u4e95\u9649\u77ff\u533a","8":"\u88d5\u534e\u533a","21":"\u4e95\u9649\u53bf","23":"\u6b63\u5b9a\u53bf","24":"\u683e\u57ce\u53bf","25":"\u884c\u5510\u53bf","26":"\u7075\u5bff\u53bf","27":"\u9ad8\u9091\u53bf","28":"\u6df1\u6cfd\u53bf","29":"\u8d5e\u7687\u53bf","30":"\u65e0\u6781\u53bf","31":"\u5e73\u5c71\u53bf","32":"\u5143\u6c0f\u53bf","33":"\u8d75\u53bf","81":"\u8f9b\u96c6\u5e02","82":"\u85c1\u57ce\u5e02","83":"\u664b\u5dde\u5e02","84":"\u65b0\u4e50\u5e02","85":"\u9e7f\u6cc9\u5e02"}},"2":{"n":"\u5510\u5c71","r":{"2":"\u8def\u5357\u533a","3":"\u8def\u5317\u533a","4":"\u53e4\u51b6\u533a","5":"\u5f00\u5e73\u533a","7":"\u4e30\u5357\u533a","8":"\u4e30\u6da6\u533a","23":"\u6ee6\u3000\u53bf","24":"\u6ee6\u5357\u53bf","25":"\u4e50\u4ead\u53bf","27":"\u8fc1\u897f\u53bf","29":"\u7389\u7530\u53bf","30":"\u5510\u6d77\u53bf","81":"\u9075\u5316\u5e02","83":"\u8fc1\u5b89\u5e02"}},"3":{"n":"\u79e6\u7687\u5c9b","r":{"2":"\u6d77\u6e2f\u533a","3":"\u5c71\u6d77\u5173\u533a","4":"\u5317\u6234\u6cb3\u533a","21":"\u9752\u9f99\u6ee1\u65cf\u81ea\u6cbb\u53bf","22":"\u660c\u9ece\u53bf","23":"\u629a\u5b81\u53bf","24":"\u5362\u9f99\u53bf"}},"4":{"n":"\u90af\u90f8","r":{"2":"\u90af\u5c71\u533a","3":"\u4e1b\u53f0\u533a","4":"\u590d\u5174\u533a","6":"\u5cf0\u5cf0\u77ff\u533a","21":"\u90af\u90f8\u53bf","23":"\u4e34\u6f33\u53bf","24":"\u6210\u5b89\u53bf","25":"\u5927\u540d\u53bf","26":"\u6d89\u3000\u53bf","27":"\u78c1\u3000\u53bf","28":"\u80a5\u4e61\u53bf","29":"\u6c38\u5e74\u53bf","30":"\u90b1\u3000\u53bf","31":"\u9e21\u6cfd\u53bf","32":"\u5e7f\u5e73\u53bf","33":"\u9986\u9676\u53bf","34":"\u9b4f\u3000\u53bf","35":"\u66f2\u5468\u53bf","81":"\u6b66\u5b89\u5e02"}},"5":{"n":"\u90a2\u53f0","r":{"2":"\u6865\u4e1c\u533a","3":"\u6865\u897f\u533a","21":"\u90a2\u53f0\u53bf","22":"\u4e34\u57ce\u53bf","23":"\u5185\u4e18\u53bf","24":"\u67cf\u4e61\u53bf","25":"\u9686\u5c27\u53bf","26":"\u4efb\u3000\u53bf","27":"\u5357\u548c\u53bf","28":"\u5b81\u664b\u53bf","29":"\u5de8\u9e7f\u53bf","30":"\u65b0\u6cb3\u53bf","31":"\u5e7f\u5b97\u53bf","32":"\u5e73\u4e61\u53bf","33":"\u5a01\u3000\u53bf","34":"\u6e05\u6cb3\u53bf","35":"\u4e34\u897f\u53bf","81":"\u5357\u5bab\u5e02","82":"\u6c99\u6cb3\u5e02"}},"6":{"n":"\u4fdd\u5b9a","r":{"2":"\u65b0\u5e02\u533a","3":"\u5317\u5e02\u533a","4":"\u5357\u5e02\u533a","21":"\u6ee1\u57ce\u53bf","22":"\u6e05\u82d1\u53bf","23":"\u6d9e\u6c34\u53bf","24":"\u961c\u5e73\u53bf","25":"\u5f90\u6c34\u53bf","26":"\u5b9a\u5174\u53bf","27":"\u5510\u3000\u53bf","28":"\u9ad8\u9633\u53bf","29":"\u5bb9\u57ce\u53bf","30":"\u6d9e\u6e90\u53bf","31":"\u671b\u90fd\u53bf","32":"\u5b89\u65b0\u53bf","33":"\u6613\u3000\u53bf","34":"\u66f2\u9633\u53bf","35":"\u8821\u3000\u53bf","36":"\u987a\u5e73\u53bf","37":"\u535a\u91ce\u53bf","38":"\u96c4\u3000\u53bf","81":"\u6dbf\u5dde\u5e02","82":"\u5b9a\u5dde\u5e02","83":"\u5b89\u56fd\u5e02","84":"\u9ad8\u7891\u5e97\u5e02"}},"7":{"n":"\u5f20\u5bb6\u53e3","r":{"2":"\u6865\u4e1c\u533a","3":"\u6865\u897f\u533a","5":"\u5ba3\u5316\u533a","6":"\u4e0b\u82b1\u56ed\u533a","21":"\u5ba3\u5316\u53bf","22":"\u5f20\u5317\u53bf","23":"\u5eb7\u4fdd\u53bf","24":"\u6cbd\u6e90\u53bf","25":"\u5c1a\u4e49\u53bf","26":"\u851a\u3000\u53bf","27":"\u9633\u539f\u53bf","28":"\u6000\u5b89\u53bf","29":"\u4e07\u5168\u53bf","30":"\u6000\u6765\u53bf","31":"\u6dbf\u9e7f\u53bf","32":"\u8d64\u57ce\u53bf","33":"\u5d07\u793c\u53bf"}},"8":{"n":"\u627f\u5fb7","r":{"2":"\u53cc\u6865\u533a","3":"\u53cc\u6ee6\u533a","4":"\u9e70\u624b\u8425\u5b50\u77ff\u533a","21":"\u627f\u5fb7\u53bf","22":"\u5174\u9686\u53bf","23":"\u5e73\u6cc9\u53bf","24":"\u6ee6\u5e73\u53bf","25":"\u9686\u5316\u53bf","26":"\u4e30\u5b81\u6ee1\u65cf\u81ea\u6cbb\u53bf","27":"\u5bbd\u57ce\u6ee1\u65cf\u81ea\u6cbb\u53bf","28":"\u56f4\u573a\u6ee1\u65cf\u8499\u53e4\u65cf\u81ea\u6cbb\u53bf"}},"9":{"n":"\u6ca7\u5dde","r":{"2":"\u65b0\u534e\u533a","3":"\u8fd0\u6cb3\u533a","21":"\u6ca7\u3000\u53bf","22":"\u9752\u3000\u53bf","23":"\u4e1c\u5149\u53bf","24":"\u6d77\u5174\u53bf","25":"\u76d0\u5c71\u53bf","26":"\u8083\u5b81\u53bf","27":"\u5357\u76ae\u53bf","28":"\u5434\u6865\u53bf","29":"\u732e\u3000\u53bf","30":"\u5b5f\u6751\u56de\u65cf\u81ea\u6cbb\u53bf","81":"\u6cca\u5934\u5e02","82":"\u4efb\u4e18\u5e02","83":"\u9ec4\u9a85\u5e02","84":"\u6cb3\u95f4\u5e02"}},"10":{"n":"\u5eca\u574a","r":{"2":"\u5b89\u6b21\u533a","3":"\u5e7f\u9633\u533a","22":"\u56fa\u5b89\u53bf","23":"\u6c38\u6e05\u53bf","24":"\u9999\u6cb3\u53bf","25":"\u5927\u57ce\u53bf","26":"\u6587\u5b89\u53bf","28":"\u5927\u5382\u56de\u65cf\u81ea\u6cbb\u53bf","81":"\u9738\u5dde\u5e02","82":"\u4e09\u6cb3\u5e02"}},"11":{"n":"\u8861\u6c34","r":{"2":"\u6843\u57ce\u533a","21":"\u67a3\u5f3a\u53bf","22":"\u6b66\u9091\u53bf","23":"\u6b66\u5f3a\u53bf","24":"\u9976\u9633\u53bf","25":"\u5b89\u5e73\u53bf","26":"\u6545\u57ce\u53bf","27":"\u666f\u3000\u53bf","28":"\u961c\u57ce\u53bf","81":"\u5180\u5dde\u5e02","82":"\u6df1\u5dde\u5e02"}}}},"14":{"n":"\u5c71\u897f","c":{"1":{"n":"\u592a\u539f","r":{"5":"\u5c0f\u5e97\u533a","6":"\u8fce\u6cfd\u533a","7":"\u674f\u82b1\u5cad\u533a","8":"\u5c16\u8349\u576a\u533a","9":"\u4e07\u67cf\u6797\u533a","10":"\u664b\u6e90\u533a","21":"\u6e05\u5f90\u53bf","22":"\u9633\u66f2\u53bf","23":"\u5a04\u70e6\u53bf","81":"\u53e4\u4ea4\u5e02"}},"2":{"n":"\u5927\u540c","r":{"2":"\u57ce\u3000\u533a","3":"\u77ff\u3000\u533a","11":"\u5357\u90ca\u533a","12":"\u65b0\u8363\u533a","21":"\u9633\u9ad8\u53bf","22":"\u5929\u9547\u53bf","23":"\u5e7f\u7075\u53bf","24":"\u7075\u4e18\u53bf","25":"\u6d51\u6e90\u53bf","26":"\u5de6\u4e91\u53bf","27":"\u5927\u540c\u53bf"}},"3":{"n":"\u9633\u6cc9","r":{"2":"\u57ce\u3000\u533a","3":"\u77ff\u3000\u533a","11":"\u90ca\u3000\u533a","21":"\u5e73\u5b9a\u53bf","22":"\u76c2\u3000\u53bf"}},"4":{"n":"\u957f\u6cbb","r":{"2":"\u57ce\u3000\u533a","11":"\u90ca\u3000\u533a","21":"\u957f\u6cbb\u53bf","23":"\u8944\u57a3\u53bf","24":"\u5c6f\u7559\u53bf","25":"\u5e73\u987a\u53bf","26":"\u9ece\u57ce\u53bf","27":"\u58f6\u5173\u53bf","28":"\u957f\u5b50\u53bf","29":"\u6b66\u4e61\u53bf","30":"\u6c81\u3000\u53bf","31":"\u6c81\u6e90\u53bf","81":"\u6f5e\u57ce\u5e02"}},"5":{"n":"\u664b\u57ce","r":{"2":"\u57ce\u3000\u533a","21":"\u6c81\u6c34\u53bf","22":"\u9633\u57ce\u53bf","24":"\u9675\u5ddd\u53bf","25":"\u6cfd\u5dde\u53bf","81":"\u9ad8\u5e73\u5e02"}},"6":{"n":"\u6714\u5dde","r":{"2":"\u6714\u57ce\u533a","3":"\u5e73\u9c81\u533a","21":"\u5c71\u9634\u53bf","22":"\u5e94\u3000\u53bf","23":"\u53f3\u7389\u53bf","24":"\u6000\u4ec1\u53bf"}},"7":{"n":"\u664b\u4e2d","r":{"2":"\u6986\u6b21\u533a","21":"\u6986\u793e\u53bf","22":"\u5de6\u6743\u53bf","23":"\u548c\u987a\u53bf","24":"\u6614\u9633\u53bf","25":"\u5bff\u9633\u53bf","26":"\u592a\u8c37\u53bf","27":"\u7941\u3000\u53bf","28":"\u5e73\u9065\u53bf","29":"\u7075\u77f3\u53bf","81":"\u4ecb\u4f11\u5e02"}},"8":{"n":"\u8fd0\u57ce","r":{"2":"\u76d0\u6e56\u533a","21":"\u4e34\u7317\u53bf","22":"\u4e07\u8363\u53bf","23":"\u95fb\u559c\u53bf","24":"\u7a37\u5c71\u53bf","25":"\u65b0\u7edb\u53bf","26":"\u7edb\u3000\u53bf","27":"\u57a3\u66f2\u53bf","28":"\u590f\u3000\u53bf","29":"\u5e73\u9646\u53bf","30":"\u82ae\u57ce\u53bf","81":"\u6c38\u6d4e\u5e02","82":"\u6cb3\u6d25\u5e02"}},"9":{"n":"\u5ffb\u5dde","r":{"2":"\u5ffb\u5e9c\u533a","21":"\u5b9a\u8944\u53bf","22":"\u4e94\u53f0\u53bf","23":"\u4ee3\u3000\u53bf","24":"\u7e41\u5cd9\u53bf","25":"\u5b81\u6b66\u53bf","26":"\u9759\u4e50\u53bf","27":"\u795e\u6c60\u53bf","28":"\u4e94\u5be8\u53bf","29":"\u5ca2\u5c9a\u53bf","30":"\u6cb3\u66f2\u53bf","31":"\u4fdd\u5fb7\u53bf","32":"\u504f\u5173\u53bf","81":"\u539f\u5e73\u5e02"}},"10":{"n":"\u4e34\u6c7e","r":{"2":"\u5c27\u90fd\u533a","21":"\u66f2\u6c83\u53bf","22":"\u7ffc\u57ce\u53bf","23":"\u8944\u6c7e\u53bf","24":"\u6d2a\u6d1e\u53bf","25":"\u53e4\u3000\u53bf","26":"\u5b89\u6cfd\u53bf","27":"\u6d6e\u5c71\u53bf","28":"\u5409\u3000\u53bf","29":"\u4e61\u5b81\u53bf","30":"\u5927\u5b81\u53bf","31":"\u96b0\u3000\u53bf","32":"\u6c38\u548c\u53bf","33":"\u84b2\u3000\u53bf","34":"\u6c7e\u897f\u53bf","81":"\u4faf\u9a6c\u5e02","82":"\u970d\u5dde\u5e02"}},"11":{"n":"\u5415\u6881","r":{"2":"\u79bb\u77f3\u533a","21":"\u6587\u6c34\u53bf","22":"\u4ea4\u57ce\u53bf","23":"\u5174\u3000\u53bf","24":"\u4e34\u3000\u53bf","25":"\u67f3\u6797\u53bf","26":"\u77f3\u697c\u53bf","27":"\u5c9a\u3000\u53bf","28":"\u65b9\u5c71\u53bf","29":"\u4e2d\u9633\u53bf","30":"\u4ea4\u53e3\u53bf","81":"\u5b5d\u4e49\u5e02","82":"\u6c7e\u9633\u5e02"}}}},"15":{"n":"\u5185\u8499\u53e4","c":{"1":{"n":"\u547c\u548c\u6d69\u7279","r":{"2":"\u65b0\u57ce\u533a","3":"\u56de\u6c11\u533a","4":"\u7389\u6cc9\u533a","5":"\u8d5b\u7f55\u533a","21":"\u571f\u9ed8\u7279\u5de6\u65d7","22":"\u6258\u514b\u6258\u53bf","23":"\u548c\u6797\u683c\u5c14\u53bf","24":"\u6e05\u6c34\u6cb3\u53bf","25":"\u6b66\u5ddd\u53bf"}},"2":{"n":"\u5305\u5934","r":{"2":"\u4e1c\u6cb3\u533a","3":"\u6606\u90fd\u4ed1\u533a","4":"\u9752\u5c71\u533a","5":"\u77f3\u62d0\u533a","6":"\u767d\u4e91\u9102\u535a\u77ff\u533a","7":"\u4e5d\u539f\u533a","21":"\u571f\u9ed8\u7279\u53f3\u65d7","22":"\u56fa\u9633\u53bf","23":"\u8fbe\u5c14\u7f55\u8302\u660e\u5b89\u8054\u5408\u65d7"}},"3":{"n":"\u4e4c\u6d77","r":{"2":"\u6d77\u52c3\u6e7e\u533a","3":"\u6d77\u5357\u533a","4":"\u4e4c\u8fbe\u533a"}},"4":{"n":"\u8d64\u5cf0","r":{"2":"\u7ea2\u5c71\u533a","3":"\u5143\u5b9d\u5c71\u533a","4":"\u677e\u5c71\u533a","21":"\u963f\u9c81\u79d1\u5c14\u6c81\u65d7","22":"\u5df4\u6797\u5de6\u65d7","23":"\u5df4\u6797\u53f3\u65d7","24":"\u6797\u897f\u53bf","25":"\u514b\u4ec0\u514b\u817e\u65d7","26":"\u7fc1\u725b\u7279\u65d7","28":"\u5580\u5587\u6c81\u65d7","29":"\u5b81\u57ce\u53bf","30":"\u6556\u6c49\u65d7"}},"5":{"n":"\u901a\u8fbd","r":{"2":"\u79d1\u5c14\u6c81\u533a","21":"\u79d1\u5c14\u6c81\u5de6\u7ffc\u4e2d\u65d7","22":"\u79d1\u5c14\u6c81\u5de6\u7ffc\u540e\u65d7","23":"\u5f00\u9c81\u53bf","24":"\u5e93\u4f26\u65d7","25":"\u5948\u66fc\u65d7","26":"\u624e\u9c81\u7279\u65d7","81":"\u970d\u6797\u90ed\u52d2\u5e02"}},"6":{"n":"\u9102\u5c14\u591a\u65af","r":{"2":"\u4e1c\u80dc\u533a","21":"\u8fbe\u62c9\u7279\u65d7","22":"\u51c6\u683c\u5c14\u65d7","23":"\u9102\u6258\u514b\u524d\u65d7","24":"\u9102\u6258\u514b\u65d7","25":"\u676d\u9526\u65d7","26":"\u4e4c\u5ba1\u65d7","27":"\u4f0a\u91d1\u970d\u6d1b\u65d7"}},"7":{"n":"\u547c\u4f26\u8d1d\u5c14","r":{"2":"\u6d77\u62c9\u5c14\u533a","21":"\u963f\u8363\u65d7","22":"\u83ab\u529b\u8fbe\u74e6\u8fbe\u65a1\u5c14\u65cf\u81ea\u6cbb\u65d7","23":"\u9102\u4f26\u6625\u81ea\u6cbb\u65d7","24":"\u9102\u6e29\u514b\u65cf\u81ea\u6cbb\u65d7","25":"\u9648\u5df4\u5c14\u864e\u65d7","26":"\u65b0\u5df4\u5c14\u864e\u5de6\u65d7","27":"\u65b0\u5df4\u5c14\u864e\u53f3\u65d7","81":"\u6ee1\u6d32\u91cc\u5e02","82":"\u7259\u514b\u77f3\u5e02","83":"\u624e\u5170\u5c6f\u5e02","84":"\u989d\u5c14\u53e4\u7eb3\u5e02","85":"\u6839\u6cb3\u5e02"}},"8":{"n":"\u5df4\u5f66\u6dd6\u5c14","r":{"2":"\u4e34\u6cb3\u533a","21":"\u4e94\u539f\u53bf","22":"\u78f4\u53e3\u53bf","23":"\u4e4c\u62c9\u7279\u524d\u65d7","24":"\u4e4c\u62c9\u7279\u4e2d\u65d7","25":"\u4e4c\u62c9\u7279\u540e\u65d7","26":"\u676d\u9526\u540e\u65d7"}},"9":{"n":"\u4e4c\u5170\u5bdf\u5e03","r":{"2":"\u96c6\u5b81\u533a","21":"\u5353\u8d44\u53bf","22":"\u5316\u5fb7\u53bf","23":"\u5546\u90fd\u53bf","24":"\u5174\u548c\u53bf","25":"\u51c9\u57ce\u53bf","26":"\u5bdf\u54c8\u5c14\u53f3\u7ffc\u524d\u65d7","27":"\u5bdf\u54c8\u5c14\u53f3\u7ffc\u4e2d\u65d7","28":"\u5bdf\u54c8\u5c14\u53f3\u7ffc\u540e\u65d7","29":"\u56db\u5b50\u738b\u65d7","81":"\u4e30\u9547\u5e02"}},"22":{"n":"\u5174\u5b89","r":{"1":"\u4e4c\u5170\u6d69\u7279\u5e02","2":"\u963f\u5c14\u5c71\u5e02","21":"\u79d1\u5c14\u6c81\u53f3\u7ffc\u524d\u65d7","22":"\u79d1\u5c14\u6c81\u53f3\u7ffc\u4e2d\u65d7","23":"\u624e\u8d49\u7279\u65d7","24":"\u7a81\u6cc9\u53bf"}},"25":{"n":"\u9521\u6797\u90ed\u52d2","r":{"1":"\u4e8c\u8fde\u6d69\u7279\u5e02","2":"\u9521\u6797\u6d69\u7279\u5e02","22":"\u963f\u5df4\u560e\u65d7","23":"\u82cf\u5c3c\u7279\u5de6\u65d7","24":"\u82cf\u5c3c\u7279\u53f3\u65d7","25":"\u4e1c\u4e4c\u73e0\u7a46\u6c81\u65d7","26":"\u897f\u4e4c\u73e0\u7a46\u6c81\u65d7","27":"\u592a\u4ec6\u5bfa\u65d7","28":"\u9576\u9ec4\u65d7","29":"\u6b63\u9576\u767d\u65d7","30":"\u6b63\u84dd\u65d7","31":"\u591a\u4f26\u53bf"}},"29":{"n":"\u963f\u62c9\u5584","r":{"21":"\u963f\u62c9\u5584\u5de6\u65d7","22":"\u963f\u62c9\u5584\u53f3\u65d7","23":"\u989

