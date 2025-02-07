#!/usr/bin/perl

=head1 NAME

merge_fpm_confs.pl - Merge php-fpm config files and avoid setting the same variable twice.

=cut

use strict;
use warnings;
use v5.21;

open(my $orig, $ARGV[0]) or die "Cannot open $ARGV[0]: $!";
open(my $overrides, $ARGV[1]) or die "Cannot open $ARGV[1]: $!";

my $fpm_var_re = qr/\s*([a-zA-Z0-9_.]+)\s*/;
my $fpm_assignment_statement_re = qr/^$fpm_var_re=/;
my $unset_pragma_re = qr/;;$fpm_var_re is unset/;

my @override_lines = <$overrides>;

my %overridden = map { (m/$fpm_assignment_statement_re/
                        or m/$unset_pragma_re/) ? ($1 => 1) : () } @override_lines;

die "Overrides: " . join(" ", map { qq("$_") } %overridden) if "what you want" eq "debug";

while(my $line = <$orig>) {
  if (my ($setting) = $line =~ $fpm_assignment_statement_re) {
    next if $overridden{$setting};
  }
  print $line;
}

print($_) for (@override_lines);

1;
