% uwb_waveform_ranging.m
%
% Waveform-level UWB ranging simulation: generates a Gaussian RF pulse,
% propagates it through a synthetic multipath channel plus AWGN, estimates
% range via matched-filter leading-edge detection, and writes one row per
% (true range, trial) to a CSV that locbench3d's Python importer
% (locbench3d/hardware/matlab_uwb_import.py) reads as MATLAB_WAVEFORM
% evidence.
%
% Requires MATLAB with Communications Toolbox (gauspuls, awgn) and Signal
% Processing Toolbox (xcorr). Uses IEEE 802.15.4 UWB channel 5 nominal
% parameters (center frequency 6489.6 MHz, bandwidth 499.2 MHz) as
% defaults; these two numbers are from general knowledge of the 802.15.4
% UWB PHY channelization (matching the widely cited DW1000 channel 5
% configuration), not independently re-verified against the standard text
% in this session -- see docs/LIMITATIONS.md.
%
% Self-calibration: the leading-edge detector's absolute delay-to-time
% conversion is derived by hand in comments below, but since this script
% has never been executed, that derivation is unverified. To make the
% *reported ranging error* robust to a possible constant offset error in
% that derivation, the script first runs one noiseless, multipath-free
% reference trial at a known delay and measures the detector's raw output
% against it; every subsequent trial's raw output has that same
% reference-derived offset subtracted before being reported as a range.
% This cancels a wrong (but consistent) constant bias in the conversion;
% it does not fix an inconsistent one, so still sanity-check a first run
% (see below).
%
% IMPORTANT: this script has never been executed. No MATLAB license or
% Communications Toolbox was available in the environment this project
% was built in (see docs/LIMITATIONS.md). It has been reviewed carefully
% but is not validated the way every Python module in this project is
% (each of those has a passing pytest suite; this does not). Before
% trusting its output, sanity-check a run: with multipath_amplitude set to
% [0, 0] and snr_db set very high (e.g. 60), every error_m should come out
% near zero at every range. If it does not, the detector or the
% calibration step has a bug that needs fixing before the multipath/noise
% results mean anything.
%
% Usage:
%   Open in MATLAB and run, or from a terminal:
%     matlab -batch "run('uwb_waveform_ranging.m')"
%   Then feed the output CSV into the Python pipeline:
%     python -m locbench3d.cli run-all --config ... --matlab-uwb-csv matlab/matlab_uwb_waveform_results.csv

clear; clc;

%% ---- Configuration ----
center_freq_hz  = 6489.6e6;     % IEEE 802.15.4 UWB channel 5 nominal center frequency
bandwidth_hz    = 499.2e6;      % IEEE 802.15.4 UWB channel 5 nominal bandwidth
sample_rate_hz  = 40e9;         % oversampled well above bandwidth for fine timing resolution
snr_db          = 15;           % received SNR after the channel, dB
true_ranges_m   = 1:2:51;       % true one-way ranges to simulate, meters
n_trials        = 20;           % Monte Carlo repeats per range
multipath_delay_ns  = [3, 7];   % extra one-way delay of each reflected path, ns
multipath_amplitude = [0.6, 0.3]; % relative amplitude of each reflected path (set to [0 0] to disable for the sanity check above)
leading_edge_threshold = 0.3;   % fraction of peak |correlation| used for leading-edge detection
speed_of_light_m_s = 299792458; % must match locbench3d.core.timing.SPEED_OF_LIGHT_M_S
reference_delay_s = 50e-9;      % known delay used for the one-time calibration trial
output_csv = fullfile(fileparts(mfilename('fullpath')), 'matlab_uwb_waveform_results.csv');
rng_seed_base = 1;

%% ---- Template pulse (used both to transmit and as the matched-filter reference) ----
fractional_bw = bandwidth_hz / center_freq_hz;
pulse_half_span_s = 3 / bandwidth_hz;   % a few pulse widths on either side
t_template = -pulse_half_span_s : 1/sample_rate_hz : pulse_half_span_s;
template_pulse = gauspuls(t_template, center_freq_hz, fractional_bw);

%% ---- Calibration: measure the detector's fixed offset against a known delay ----
[calib_raw_tau_s, ~] = detect_delay(template_pulse, t_template, reference_delay_s, ...
    [], [], 0, sample_rate_hz, leading_edge_threshold, pulse_half_span_s);
calibration_offset_s = calib_raw_tau_s - reference_delay_s;
fprintf('Calibration: reference delay %.3f ns, raw detector output %.3f ns, offset %.3f ns\n', ...
    reference_delay_s*1e9, calib_raw_tau_s*1e9, calibration_offset_s*1e9);

%% ---- Main sweep ----
results = table();
row_idx = 0;

for range_idx = 1:numel(true_ranges_m)
    true_range_m = true_ranges_m(range_idx);
    tau0_s = true_range_m / speed_of_light_m_s;  % one-way delay for the direct path

    for trial = 1:n_trials
        seed = rng_seed_base * 100000 + range_idx * 1000 + trial;
        rng(seed, 'twister');

        [raw_tau_s, success] = detect_delay(template_pulse, t_template, tau0_s, ...
            multipath_delay_ns, multipath_amplitude, snr_db, sample_rate_hz, ...
            leading_edge_threshold, pulse_half_span_s);

        if ~success
            estimated_range_m = NaN;
            error_m = NaN;
        else
            calibrated_tau_s = raw_tau_s - calibration_offset_s;
            estimated_range_m = calibrated_tau_s * speed_of_light_m_s;
            error_m = estimated_range_m - true_range_m;
        end

        row_idx = row_idx + 1;
        results.measurement_id(row_idx)    = row_idx;
        results.true_range_m(row_idx)      = true_range_m;
        results.estimated_range_m(row_idx) = estimated_range_m;
        results.error_m(row_idx)           = error_m;
        results.bandwidth_hz(row_idx)      = bandwidth_hz;
        results.center_freq_hz(row_idx)    = center_freq_hz;
        results.snr_db(row_idx)            = snr_db;
        results.sample_rate_hz(row_idx)    = sample_rate_hz;
        results.multipath_profile{row_idx} = sprintf('%s ns @ %s', mat2str(multipath_delay_ns), mat2str(multipath_amplitude));
        results.trial(row_idx)             = trial;
        results.seed(row_idx)              = seed;
    end
end

writetable(results, output_csv);
fprintf('Wrote %d rows to %s\n', height(results), output_csv);

%% ---- Helper: build a channel realization and detect the leading-edge delay ----
function [raw_tau_s, success] = detect_delay(template_pulse, t_template, direct_delay_s, ...
        multipath_delay_ns, multipath_amplitude, snr_db, sample_rate_hz, threshold_fraction, pulse_half_span_s)

    if isempty(multipath_delay_ns)
        max_extra_delay_s = 0;
    else
        max_extra_delay_s = max(multipath_delay_ns) * 1e-9;
    end
    window_span_s = direct_delay_s + max_extra_delay_s + 2 * pulse_half_span_s;
    t_rx = 0 : 1/sample_rate_hz : window_span_s;
    received = zeros(size(t_rx));

    received = add_delayed_pulse(received, t_rx, template_pulse, t_template, direct_delay_s, 1.0);
    for k = 1:numel(multipath_delay_ns)
        extra_delay_s = multipath_delay_ns(k) * 1e-9;
        received = add_delayed_pulse(received, t_rx, template_pulse, t_template, ...
            direct_delay_s + extra_delay_s, multipath_amplitude(k));
    end

    received = awgn(received, snr_db, 'measured');

    [correlation, lags] = xcorr(received, template_pulse);
    correlation_magnitude = abs(correlation);
    peak_value = max(correlation_magnitude);
    if peak_value <= 0
        raw_tau_s = NaN;
        success = false;
        return;
    end
    above_threshold = find(correlation_magnitude >= threshold_fraction * peak_value, 1, 'first');
    if isempty(above_threshold)
        raw_tau_s = NaN;
        success = false;
        return;
    end
    lag_samples = lags(above_threshold);
    raw_tau_s = lag_samples / sample_rate_hz;  % uncalibrated; see calibration step in the caller
    success = true;
end

%% ---- Helper: add a delayed, scaled copy of a template pulse into a receive window ----
function rx = add_delayed_pulse(rx, t_rx, template_pulse, t_template, delay_s, amplitude)
    sample_rate_hz = 1 / (t_rx(2) - t_rx(1));
    pulse_t_abs = t_template + delay_s;         % absolute arrival times of the template samples
    valid = pulse_t_abs >= t_rx(1) & pulse_t_abs <= t_rx(end);
    if ~any(valid)
        return;
    end
    indices = round((pulse_t_abs(valid) - t_rx(1)) * sample_rate_hz) + 1;
    indices = max(min(indices, numel(rx)), 1);
    rx(indices) = rx(indices) + amplitude * template_pulse(valid);
end
