#!/usr/bin/env perl

use strict;
use warnings;

=head1 NAME

health.cgi - Monitor the health of this httpd container

=head1 DESCRIPTION

This CGI script takes no arguments and ignores the CGI parameters. It
produces CGI-compliant output i.e. HTTP headers (including the Status:
pseudo-header which Apache turns into the HTTP status line) followed
by the HTTP body.

The script forks into the background upon its first invocation and
thereafter monitors a list of URLs, and reports the state into a plain
text file that gets atomically updated. The "main thread" (actually,
further invocations of the same Perl script) serves the file, assuming
that it is less than 10 seconds old.

=cut

use Readonly;
use Fcntl qw(O_RDWR LOCK_EX);
use IO::All;
use File::Glob;
use CGI::Carp;

Readonly::Scalar our $pid_file => "/run/lock/health-cgi.pid";
Readonly::Scalar our $state_file => "/run/health-cgi.out";
Readonly::Scalar our $max_state_file_age_seconds => 10;

ensure_background_task_running();
CGI::Carp->import(qw(fatalsToBrowser));

my $state_io = io($state_file);
if (! $state_io->exists) {
  die "$state_file does not exist";
} elsif ((my $age_seconds = time() - $state_io->mtime)
           > $max_state_file_age_seconds) {
  die <<"ERROR";
$state_file is too old ($age_seconds seconds, limit $max_state_file_age_seconds)
ERROR
} else {
  my $metrics = $state_file->slurp;
  print <<"ALL_DONE_BYE"; exit(0);
Status: 200 OK
Server: health.cgi
Content-Type: text/plain; version=0.0.4

$metrics
ALL_DONE_BYE
}

#################################################################

sub ensure_background_task_running {
  return;  # XXX
  my $pid_io = io($pid_file)->mode(O_RDWR);
  "" > $pid_io;  # Open it
  flock($pid_io->io_handle, LOCK_EX) or die <<FLOCK_IT;
Unable to lock $pid_file: $!
FLOCK_IT
  my $pid < $pid_io;
  if ($pid and (1 == kill(0 => $pid))) { return; }

  if ($pid = fork()) {
    $pid > $pid_io;
  } else {
    background_task();
  }
}

sub background_task {
}
