<?php

	/**
	 * Central phpPgAdmin configuration.  As a user you may modify the
	 * settings here for your particular configuration.
	 *
	 * $Id: config.inc.php-dist,v 1.55 2008/02/18 21:10:31 xzilla Exp $
	 */

	$conf['servers'][0]['desc'] = 'PostgreSQL';
	$conf['servers'][0]['host'] = 'timescaledb';
	$conf['servers'][0]['port'] = 5432;

    // Minimum length users can set their password to.
	$conf['min_password_length'] = 1;

	// Width of the left frame in pixels (object browser)
	$conf['left_width'] = 200;

	// Which look & feel theme to use
	$conf['theme'] = 'default';

    // See: https://github.com/phppgadmin/phppgadmin/blob/master/conf/config.inc.php-dist
	$conf['servers'][0]['sslmode'] = 'allow';
	$conf['servers'][0]['defaultdb'] = 'template1';
	$conf['servers'][0]['pg_dump_path'] = '/usr/bin/pg_dump';
	$conf['servers'][0]['pg_dumpall_path'] = '/usr/bin/pg_dumpall';
	$conf['default_lang'] = 'auto';
	$conf['extra_session_security'] = true;
	$conf['autocomplete'] = 'default on';
	$conf['extra_login_security'] = true;
	$conf['owned_only'] = false;
	$conf['show_comments'] = true;
	$conf['show_advanced'] = false;
	$conf['show_system'] = false;
	$conf['show_oids'] = false;
	$conf['max_rows'] = 30;
	$conf['max_chars'] = 50;
	$conf['use_xhtml_strict'] = false;
	$conf['help_base'] = 'http://www.postgresql.org/docs/%s/interactive/';
	$conf['ajax_refresh'] = 3;
	$conf['plugins'] = array();

	/*****************************************
	 * Don't modify anything below this line *
	 *****************************************/

	$conf['version'] = 19;

?>
