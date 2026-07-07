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
echo unicode2utf8("\u4E2D");//中
console.log(unescape('\u4e2d'));//中
#python 
import json
编码：把一个Python对象编码转换成Json字符串   json.dumps()
解码：把Json格式字符串解码转换成Python对象   json.loads()
Python2中同时存在str和unicode两种字符串类型，Python3字符串一开始就是Unicode
```

12.检测ip

``` php
var_dump ( filter_var ( 'bob@example.com' ,  FILTER_VALIDATE_EMAIL ));//"bob@example.com"
var_dump ( filter_var ( 'bob@example' ,  FILTER_VALIDATE_EMAIL ));//bool(false)
 var_dump ( filter_var ( 'http://example.com' ,  FILTER_VALIDATE_URL ,  FILTER_FLAG_PATH_REQUIRED ));//bool(false)
function chk_ip($ip){ 
   if(ip2long($ip)=="-1" ||  ip2long($ip)  ===  FALSE) { 
      return false; 
   } 
   return true; 
} 
var_export(chk_ip("10.111.149.42")); //true
var_export(chk_ip("10.111.256.42")); //false
```

13.交换两个变量的值

``` php
$a = "php";
$b = "java";
 //list()不是函数，是语言结构，它是将数组中的值赋给一些变量
list($a,$b) = array($b,$a);
echo $a.'---'.$b; //java---php
$a = explode('-',$a.'-'.$b);
$b =$a[0];
$a =$a[1];
echo $a.'---'.$b; //java---php
#python
a,b = b,a
print a,b
list(,$a,$b)=array(1,2,3);
```

14.in_array strpos  array_slice

``` php
if (in_array(0, array('phpjs'))) {
    echo 'exist';
}
if (!in_array(0, array('phpjs'),true)) {
    echo 'not exist';
}
$mystring  =  'abc' ;
 $findme    =  'a' ;
 $pos  =  strpos ( $mystring ,  $findme );

 // 注意这里使用的是 ===。简单的 == 不能像我们期待的那样工作，
// 因为 'a' 是第 0 位置上的（第一个）字符。
 if ( $pos  ===  false ) {
    echo  "The string ' $findme ' was not found in the string ' $mystring '" ;
} else {
    echo  "The string ' $findme ' was found in the string ' $mystring '" ;
    echo  " and exists at position  $pos " ;
}
注意 array_slice()  默认会重新排序并重置数组的数字索引
$input  = array( "a" ,  "b" ,  "c" ,  "d" ,  "e" );
 print_r ( array_slice ( $input ,  2 , - 1 ));

Array
(
    [0] => c
    [1] => d
)
print_r ( array_slice ( $input ,  2 , - 1 ,  true ));
Array
(
    [2] => c
    [3] => d
)

```

15.静态服务器

``` php
php -S localhost:8888 -t /var/www #require php5.4+
python -m SimpleHTTPServer 8888
16.下标带引号
// define('key','language');
$arr = array('key'=>'js','language'=>'php');
echo $arr[key];//php
17.js sort 
// firefox 和 chrome 是 [1024, 6, 5, 3, 2, 1]
// safari 中顺序没变
[1,3,2,5,6,1024].sort(function(a, b) {
    return b > a;
});

// 在各中浏览器工作一致的方法
// 用正负和零来排序，而不是 true/false
[1,3,2,5,6,1024].sort(function(a, b) {
    return b - a;
});
```

18.mysql order by

``` php
 CREATE TABLE `table` (
 `id` int(9) DEFAULT NULL,
 `name` char(10) DEFAULT NULL,
 `type` varchar(15) NOT NULL DEFAULT '0',
 KEY `id` (`id`),
 KEY `name` (`name`),
 KEY `type` (`type`)
)
mysql> select *from table order by type ;
+------------+-------+------+
| id         | name  | type |
+------------+-------+------+
| 1234567890 | luo   | 0    |
|        300 | phpjs | 10   |
|        100 | phpjs | 2    |
|        100 | phpjs | 3    |
|        500 | php   | 5    |
|        500 | php   | 6    |
+------------+-------+------+
6 rows in set (0.02 sec)

mysql> select *from table order by abs(type) ;
+------------+-------+------+
| id         | name  | type |
+------------+-------+------+
| 1234567890 | luo   | 0    |
|        100 | phpjs | 2    |
|        100 | phpjs | 3    |
|        500 | php   | 5    |
|        500 | php   | 6    |
|        300 | phpjs | 10   |
+------------+-------+------+
6 rows in set (0.03 sec)
```

19.php mb_substr

``` php

// 对于没有指定编码的字符串，mb_substr是使用PHP默认编码进行处理的 5.6以下都是ISO-8859-1，而只有5.6以上才是UTF-8
$str='中文编码';
echo mb_substr($str,0,2);//5.6 ok 5.6以下乱码
echo mb_substr($str,0,2,'utf-8');//中文

```

20.自动类型转换
"0123"会解析成十进制的123,而0123会解析成八进制
<任意非纯数字字符串> == 0 //===>true
就是"aaa" == 0 //===> true
"0123" == 0 //===> false
"0123" == 123 //====>true
21.isNaN()  缺陷 

``` javascript
console.log(isNaN('hello'));  // true
console.log(isNaN(['x']));    // true
console.log(isNaN({}));       // true
var My = {
  isNaN: function (x) { return x !== x; }
}
在即将到来的ECMAScript 6中, 有一个Number.isNaN() 方法提供可靠的NaN值检测
console.log(Number.isNaN(NaN));            // true
console.log(Number.isNaN(Math.sqrt(-2)));  // true
console.log(Number.isNaN('hello'));        // false
console.log(Number.isNaN(['x']));          // false
console.log(Number.isNaN({}));             // false
```

22.使用||来提供默认值

function setAge(age) {
    this.age = age || 10;
}
这种方式你没法设置age为0，因为0是false，因此下面的方法应该是一个更好的方案
this.age = (typeof age !== "undefined") ? age : 10;

23.// 格式化显示日期时间

// <param name="x">待显示的日期时间，例如new Date()</param>
// <param name="y">需要显示的格式，例如yyyy-MM-dd hh:mm:ss</param>
function date2str(x,y) {
    var z ={y:x.getFullYear(),M:x.getMonth()+1,d:x.getDate(),h:x.getHours(),m:x.getMinutes(),s:x.getSeconds()};
    return y.replace(/(y+|M+|d+|h+|m+|s+)/g,function(v) {return ((v.length>1?"0":"")+eval('z.'+v.slice(-1))).slice(-(v.length>2?v.length:2))});
}
alert(date2str(new Date(),"yy-M-d h:m:s"));
alert(date2str(new Date(),"yyyy-MM-d h:m:s"));
24.数组内都是数字，或者期望按数字为主的排序方式。

var money = [12, 3, 7.4, 200];
var compare = function(a, b) {return a - b;};
console.log(money.sort(compare)); // [3, 7.4, 12, 200]
//console.log(money.sort(function(a, b) {return a - b;})); // [3, 7.4, 12, 200]
对于字符串的元素来说，和数字的差不多，无非就是不同的排序函数，那如果是对象呢？

var people = [
    {
        name: 'Alice',
        id: 1234
    },
    {
        name: 'Bob',
        id: 567
    }
];
var compare = function(a, b) {return a.id - b.id;}
console.log(people.sort(compare)); // Bob is before Alice now
对于元素的排序函数传递的参数都一样，两个数组中的元素，然后此处主要比较两个对象元素的 id 的值，来进行排序的。
25.“JS函数的参数是否可以引用传递？”，昨天 Zjmainstay 给出了代码：

function test(user) {  user['age'] = '24';}
var my = {  name : 'Zjmainstay'}
test(my);
console.log(my);
控制台输出：{name: “Zjmainstay”, age: “24″}

看这效果，貌似就是引用传递的。那么将此代码小小修改后

function test(user) {  user = {  name : 'sijiaomao'};}
var my = {  name : 'Zjmainstay'}
test(my);
console.log(my);
如果是引用传递，控制台输出 {  name : ‘sijiaomao’} 才是符合预期的

26.mouseover 和 mouseout是冒泡的，如果鼠标移动到它们的子元素，同样会触发该事件，而
mouseenter 和  mouseleave是不会冒泡的。

27.
使用$.grep()方法删除数组中的元素。
var array = ['a', 'b', 'c']; 
$.grap(array, function(value, index){return value=='b';}, true);
上面的代码将删除数组array中的元素'b'。
$.trim(str)：删除字符串两端的空白字符。
$.unique(array);去除数组array中的重复项
$.inArray(obj, array);
$.merge(array1, array2);
$.each(obj, fn);
$.map(array, fn);
var tempArr=$.map( [0,1,2], function(i){ return i + 4; });
tempArr内容为：[4,5,6]
var tempArr=$.map( [0,1,2], function(i){ return i > 0 ? i + 1 : null; });
tempArr内容为：[2,3]
$.merge(arr1,arr2):合并两个数组并删除其中重复的项目。
如：$.merge( [0,1,2], [2,3,4] ) //返回[0,1,2,3,4]
28.apache绑定多个域名
Listen 80

// Listen for virtual host requests on all IP addresses
NameVirtualHost *:80

<VirtualHost *:80>
DocumentRoot /www/example1
ServerName www.example.com
# Other directives here

</VirtualHost>

<VirtualHost *:80>
DocumentRoot /www/example2
ServerName www.example.org
# Other directives here

</VirtualHost>
必须开启NameVirtualHost *:80，否则无论绑定多少个域名，全部都会指向第一个virtualhost的documentroot
29.对于mysql的int来说它的长度是不变的及为4个字节、对于插入数据数据大小也是不变的。

```
 带符号的数值大小范围为：-2147483648 到214748347

 无符号的：0到4294967295

 int(x)的x并不能改变int类型字段存入数据值的大小【即不能限制数值的范围】

 举个示例说

int(2)能存入214748347。

int(1)也能存入214748347。
```

30.$s = 1526564646463333565222;
echo $s;
//1.5265646464633E+21
PHP如何才可以将浮点型的字符串反转换为 原始值？

function getTrueValue($str){
    //@todo
}
$str = '1.5265646464633E+21';
用sprintf或者number_format

$s = 1526564646463333565222;
printf("%.0f", $s);
echo "\r\n";
echo number_format($s,0,'','');

31.isset vs array_key_exists 判断一个变量是否真正被设置（区分未设置和设置值为null），array_key_exists()函数或许更好
if (! isset($data['keyShouldBeSet'])) { 
    // do this if 'keyShouldBeSet' isn't set 
}
if (! array_key_exists('keyShouldBeSet', $data)) { 
    // do this if 'keyShouldBeSet' isn't set 
}
1. $_POST ajax

// js 
$.ajax({ 
    url: 'http://my.site/some/path', 
    method: 'post', 
    data: JSON.stringify({a: 'a', b: 'b'}), 
    contentType: 'application/json' 
}); 
注意代码中的 contentType: 'application/json' ，我们是以json数据格式来发送的数据。在服务端，我们仅输出$_POST数组：

// php 
var_dump($_POST); 
你会很惊奇的发现，结果是下面所示：
array(0) { } 
为什么是这样的结果呢？我们的json数据 {a: 'a', b: 'b'} 哪去了呢？
答案就是PHP仅仅解析Content-Type为 application/x-www-form-urlencoded 或 multipart/form-data的Http请求。之所以这样是因为历史原因，PHP最初实现$_POST时，最流行的就是上面两种类型。因此虽说现在有些类型（比如application/json）很流行，但PHP中还是没有去实现自动处理。
因为$_POST是全局变量，所以更改$_POST会全局有效。因此对于Content-Type为 application/json 的请求，我们需要手工去解析json数据，然后修改$_POST变量。
// php 
$_POST = json_decode(file_get_contents('php://input'), true); 
此时，我们再去输出$_POST变量，则会得到我们期望的输出：
array(2) { ["a"]=> string(1) "a" ["b"]=> string(1) "b" }

$d = new DateTime("7:00", new DateTimeZone("Asia/Shanghai"));
echo $d->format("Y-m-d H:i:s");
