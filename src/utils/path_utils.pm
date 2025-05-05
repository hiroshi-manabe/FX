package path_utils;
use strict;
use warnings;
use Exporter 'import';
use FindBin;
use Inline Python => <<'END_PY';
import path_utils as pu
END_PY

our @EXPORT_OK = qw(
    weekly_path
    label_path
    feature_path
    knn_model_path
    report_path
    ensure_parent
);

# Example: "data/weekly/USDJPY/week_2025-13.csv"
sub weekly_path {
    my ($pair, $iso_week) = @_;
    return py_eval("str(pu.weekly('$pair', '$iso_week'))");
}

# Example: "data/labels/pl30/USDJPY/week_2025-13.csv"
sub label_path {
    my ($pair, $iso_week, $tag) = @_;
    $tag //= "pl30";
    return py_eval("str(pu.label_pl('$pair', '$iso_week', '$tag'))");
}

# Example: "data/features/quad_v1/USDJPY/window_10000/week_2025-13.csv"
sub feature_path {
    my ($pair, $iso_week, $window, $alg) = @_;
    $alg //= "quadratic_v1";
    return py_eval("str(pu.features('$pair', '$iso_week', $window, '$alg'))");
}

# Example: "data/models/knn_v1/USDJPY/window_10000/R2_0.9730/week_2025-13.pkl"
sub knn_model_path {
    my ($pair, $iso_week, $window, $r2, $alg) = @_;
    $alg //= "knn_v1";
    return py_eval("str(pu.knn_model('$pair', '$iso_week', $window, $r2, '$alg'))");
}

# Example: "data/reports/USDJPY/2025-13/summary.csv"
sub report_path {
    my ($pair, $iso_week) = @_;
    return py_eval("str(pu.report('$pair', '$iso_week'))");
}

# Ensures parent directory exists
sub ensure_parent {
    my ($path) = @_;
    my $dir = $path;
    $dir =~ s{/[^/]+$}{};
    system("mkdir", "-p", $dir) == 0 or die "Failed to mkdir $dir: $!";
    return $path;
}

1;
