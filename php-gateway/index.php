<?php

/*
 * This is a PHP gateway for munin-alert-phue. It will allow you do forward a munin alert
 * from a different network to the network where the lights should be controlled.
 *
 * Copyright 2014 Michiel Hendriks <elmuerte@drunknsipers.com>
 *
 * Released under the terms of GNU Public License version 3 or later
 * https://github.com/elmuerte/munin-phue 
 */

//Reject any non-put request
if ($_SERVER['REQUEST_METHOD'] != 'PUT') {
	header('HTTP/1.0 400 Bad Request');
	die;
}

$config = array();
// If set to true, stdout/stderr is returned in the request
$debug = false;

/*
 * The config file should contain the following entries
 * $config['bin'] = '/path/to/munin-alert-phue.py';
 * $config['key']['config-file'] = '/path/to/phue-config.ini';
 * $config['key']['config-section'] = 'default';
 */
@include(dirname(__FILE__).'/config.php');

$key = '';
if (isset($HTTP_REQUEST_VARS['key'])) {
	$HTTP_REQUEST_VARS['key'];
}
if (empty($key)) {
	// TODO check path for key
}

if (!isset($key) || $key == 'bin' || !isset($config['key'])) {
	header('HTTP/1.0 401 Unauthorized');
	die;
}

if (!isset($config['bin'])) {
	header('HTTP/1.0 500 Internal Server Error');
	die('Invalid config. Path to munin-alert-phue.py not set.');
}

$descs = array (
	0 => array ("file", "php://input", "r"),
	1 => array ("pipe", "w"),
	2 => array ("pipe", "w")
);
$pipes = array();

$cmdline = escapeshellcmd($config['bin']);

$cmd = proc_open($cmdline, $descs, $pipes);

if (!is_resource($cmd)) {
	header('HTTP/1.0 500 Internal Server Error');
	die('Failed to start process');
}

$stdout = '';
$stderr = '';
if ($debug) {
	$stdout = stream_get_contents($pipes[1]);
	$stderr = stream_get_contents($pipes[2]);
}
else {
	stream_get_contents($pipes[1]);
	stream_get_contents($pipes[2]);
}
fclose($pipes[0]);
fclose($pipes[1]);
fclose($pipes[2]);

$retval = proc_close($cmd);
if ($retval != 0) {
	header('HTTP/1.0 500 Internal Server Error');
	header('Content-Type: text/plain');
	echo 'Non-zero return value: '.$retval.'\n';
}
else {
	header('Content-Type: text/plain');
	echo 'OK\n';
}

if ($debug) {
	echo '\nSTDOUT:\n';
	echo $stdout;
	echo '\n\nSTDERR:\n';
	echo $sterr;
}