<?php

/*
 * This is a PHP gateway for munin-alert-phue. It will allow you do forward a munin alert
 * from a different network to the network where the lights should be controlled.
 *
 * Munin Alert Phue - Munin alerts updating Philips Hue lights.
 * https://github.com/elmuerte/munin-phue 
 * Copyright (C) 2014 Michiel Hendriks <elmuerte@drunksnipers.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
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
if (empty($key) && isset($_SERVER['PATH_INFO'])) {
        $key = substr($_SERVER['PATH_INFO'], 1);
}

if (!isset($key) || $key == 'bin' || !isset($config[$key])) {
	header('HTTP/1.0 401 Unauthorized');
	die;
}

if (!isset($config['bin'])) {
	header('HTTP/1.0 500 Internal Server Error');
	die('Invalid config. Path to munin-alert-phue.py not set.');
}

$descs = array (
	0 => array ('pipe', 'r'),
	1 => array ('pipe', 'w'),
	2 => array ('pipe', 'w')
);
$pipes = array();

$cmdline = escapeshellcmd($config['bin']);
if (isset($config[$key]['config-file'])) {
   $cmdline .= ' -c '.escapeshellarg($config[$key]['config-file']);
}
if (isset($config[$key]['config-section'])) {
   $cmdline .= ' -s '.escapeshellarg($config[$key]['config-section']);
}

$cmd = proc_open($cmdline, $descs, $pipes);

if (!is_resource($cmd)) {
	header('HTTP/1.0 500 Internal Server Error');
	die('Failed to start process');
}

stream_copy_to_stream(fopen('php://input', 'r'), $pipes[0]);
fclose($pipes[0]);

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
	echo 'Non-zero return value: '.$retval."\n";
}
else {
	header('Content-Type: text/plain');
	echo "OK\n";
}

if ($debug) {
	echo "\nSTDOUT:\n";
	echo $stdout;
	echo "\n\nSTDERR:\n";
	echo $sterr;
}
