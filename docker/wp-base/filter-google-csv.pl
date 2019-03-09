#!/usr/bin/perl -w

=head1 NAME

filter-google-csv.pl - Filter CSV from Google Sheets for processing with bash

=head1 SYNOPSIS

curl google.com/somethingsomething | \
   filter-google-csv.pl COLUMNA COLUMNB COLUMNC

=head1 DESCRIPTION

=over

=item *

Cuts first (header) line

=item *

Unquotes everything

=item *

Reorders the columns as mentioned on the command line, and drops
the others

=item *

Eliminate incomplete lines (after dropping columns as per above)

=back

=cut

use strict;

our @permutation;

my @headerfields = decode_line(scalar <STDIN>);
foreach my $i (0..$#headerfields) {
    foreach my $j (0..$#ARGV) {
        if ($headerfields[$i] eq $ARGV[$j]) {
            $permutation[$j] = $i;
        }
    }
}

STDINLINE: while(<STDIN>) {
    my @line = decode_line();
    my @permuted_line;
    COLUMN: foreach my $i (0..$#permutation) {
        next COLUMN unless defined(my $j = $permutation[$i]);
        next STDINLINE unless (my $cell = $line[$j]);
        push @permuted_line, $cell;
    }
    printf "%s\n", join(",", @permuted_line);
}

sub decode_line {
    local $_ = @_ ? $_[0] : $_;
    chomp;
    my @fields = split m/,/;
    map { s/^"(.*)"$/$1/ } @fields;
    return @fields;
}
