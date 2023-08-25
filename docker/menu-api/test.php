<?php 
$res = file_get_contents('http://localhost:8888/breadcrumb?lang=fr&url=https://www.epfl.ch/campus/services/website/');
$res = json_decode($res, false);
$breadcrumb = '';
foreach ($res->breadcrumb as $key => $val) {
  $breadcrumb .= '<a class="breadcrumb" id="breadcrumb_0'.$key.'" href="'.$val->url.'">'.$val->title.'</a>' . ' > ';
}
echo substr($breadcrumb, 0, -3);
?>
