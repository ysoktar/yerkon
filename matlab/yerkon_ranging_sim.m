function yerkon_ranging_sim(varargin)
%YERKON_RANGING_SIM Derive ranging error from waveform bandwidth and multipath.
%
%   The weakest evidence in this project is the ranging error itself. The
%   SX1280 model rests on six published points over 0-250 m; the DWM3000
%   model is a design target expressed as a Gaussian, because no calibrated
%   measurement was available. Both are assumptions about a quantity that
%   physics largely determines: how accurately a receiver can time the
%   arrival of a signal depends on its bandwidth, the multipath around it,
%   and its signal-to-noise ratio.
%
%   This script simulates that directly. It builds the transmitted
%   waveform, passes it through a cluster-based multipath channel, adds
%   noise, runs a leading-edge time-of-arrival estimator, and records the
%   resulting range error. Run over many trials it produces an error
%   distribution derived from the radio's parameters rather than assumed.
%
%   It is written in base MATLAB and needs no toolbox.
%
%   Usage:
%       cd matlab
%       yerkon_ranging_sim                       % default sweep
%       yerkon_ranging_sim('Trials', 400)        % more trials, slower
%       yerkon_ranging_sim('Cases', {'uwb_los'})
%       yerkon_ranging_sim('Trials', 300, 'Parallel', true)
%
%   'Parallel' uses parfor across trials, which needs Parallel Computing
%   Toolbox and is worth it for the long run. It is off by default because
%   the workers draw their own random numbers: results stay statistically
%   the same but stop being bit-for-bit reproducible from the seed.
%
%   Output:
%       export/yerkon_ranging_errors.csv   one row per trial
%       export/yerkon_ranging_summary.csv  one row per case
%
%   The Python side reads these and replaces the assumed error models,
%   tagged as waveform simulation rather than as measurement.

opts = parseOptions(varargin{:});
cases = buildCases();
if ~isempty(opts.Cases)
    keep = false(1, numel(cases));
    for k = 1:numel(cases)
        keep(k) = any(strcmp(cases(k).name, opts.Cases));
    end
    cases = cases(keep);
end
if isempty(cases)
    error('yerkon:noCases', 'No cases selected.');
end

outDir = fullfile(fileparts(mfilename('fullpath')), 'export');
if ~exist(outDir, 'dir'); mkdir(outDir); end
trialPath   = fullfile(outDir, 'yerkon_ranging_errors.csv');
summaryPath = fullfile(outDir, 'yerkon_ranging_summary.csv');

fidTrial = fopen(trialPath, 'w');
if fidTrial < 0
    error('yerkon:cannotWrite', 'Cannot write %s', trialPath);
end
fprintf(fidTrial, 'case,radio,condition,bandwidth_hz,snr_db,true_range_m,trial,range_error_m\n');

fidSummary = fopen(summaryPath, 'w');
fprintf(fidSummary, ['case,radio,condition,bandwidth_hz,snr_db,true_range_m,trials,'...
    'mean_error_m,median_error_m,std_error_m,p95_abs_error_m,max_abs_error_m\n']);

fprintf('YERKON ranging simulation\n');
fprintf('  trials per point : %d\n', opts.Trials);
fprintf('  seed             : %d\n', opts.Seed);
fprintf('  parallel         : %d\n', opts.Parallel);

rngSeed(opts.Seed);
totalStart = tic;

for c = 1:numel(cases)
    cs = cases(c);
    fprintf('\n[%d/%d] %s (%s, %s, BW %.3f MHz)\n', c, numel(cases), cs.name, ...
        cs.radio, cs.condition, cs.bandwidthHz / 1e6);

    for s = 1:numel(cs.snrDb)
        snr = cs.snrDb(s);
        for r = 1:numel(cs.trueRangeM)
            trueRange = cs.trueRangeM(r);
            % Trials first, file second: parfor cannot write to a shared
            % file handle, and the write is cheap next to the simulation.
            errors = zeros(1, opts.Trials);
            if opts.Parallel
                parfor t = 1:opts.Trials
                    errors(t) = oneTrial(cs, snr, trueRange);
                end
            else
                for t = 1:opts.Trials
                    errors(t) = oneTrial(cs, snr, trueRange);
                end
            end
            for t = 1:opts.Trials
                fprintf(fidTrial, '%s,%s,%s,%.0f,%.1f,%.1f,%d,%.6f\n', ...
                    cs.name, cs.radio, cs.condition, cs.bandwidthHz, snr, ...
                    trueRange, t, errors(t));
            end
            fprintf(fidSummary, '%s,%s,%s,%.0f,%.1f,%.1f,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n', ...
                cs.name, cs.radio, cs.condition, cs.bandwidthHz, snr, trueRange, ...
                opts.Trials, mean(errors), median(errors), std(errors), ...
                prctileSimple(abs(errors), 95), max(abs(errors)));
            fprintf('   SNR %5.1f dB, range %6.1f m -> mean %+7.3f m, std %6.3f m, p95|e| %6.3f m\n', ...
                snr, trueRange, mean(errors), std(errors), prctileSimple(abs(errors), 95));
        end
    end
end

fclose(fidTrial);
fclose(fidSummary);

fprintf('\nDone in %.1f s.\n', toc(totalStart));
fprintf('Wrote %s\n', trialPath);
fprintf('Wrote %s\n', summaryPath);
end

% =====================================================================
% Cases
% =====================================================================

function cases = buildCases()
%BUILDCASES The radios and conditions the YERKON report specifies.
%
% UWB is the DWM3000: IEEE 802.15.4z HRP, channel 5, 499.2 MHz bandwidth.
%
% The 2.4 GHz cases are the SX1280 ranging modes. The part supports exactly
% four LoRa bandwidths - 203, 406, 812 and 1625 kHz - and the report does
% not say which YERKON uses, so all four are simulated. Bandwidth is the
% dominant term in timing resolution, so this sweep is the point of the
% exercise.
%
% All four are swept at the same SNR set, and that is a modelling decision
% worth stating. In Turkey and across CEPT the 2400-2483.5 MHz band is
% capped both in total power (100 mW e.i.r.p.) and in density (10 mW/MHz
% e.i.r.p. for non-FHSS wideband modulation). The density cap binds first
% at every SX1280 bandwidth, so the legal transmit power scales with the
% bandwidth: 3.1 dBm at 203 kHz through 12.1 dBm at 1625 kHz. Thermal
% noise scales with bandwidth by the same factor, so the received SNR at a
% given distance is the same in all four configurations. Sweeping one SNR
% set across all four is therefore the like-for-like comparison, and it
% means the wider bandwidths do not buy their accuracy with range.

cases = struct('name', {}, 'radio', {}, 'condition', {}, 'bandwidthHz', {}, ...
    'carrierHz', {}, 'waveform', {}, 'estimator', {}, 'snrDb', {}, ...
    'trueRangeM', {}, 'channel', {});

% UWB uses leading-edge detection, which is what a DW-series chip does and
% what makes multipath rejection possible at all. The narrowband SX1280
% cannot resolve the paths in the first place: its correlation peak is
% hundreds of metres wide, so searching back along it finds noise rather
% than the first arrival. Peak detection with a calibrated offset is what
% that part actually does, and it is what Robinson's 2.83 m offset is.
cases(end+1) = mkCase('uwb_los',  'DWM3000', 'LOS',  499.2e6, 6489.6e6, 'pulse', 'leading', ...
    [10 15 20 25], [10 50 100], svParams('industrial_los'));
cases(end+1) = mkCase('uwb_nlos', 'DWM3000', 'NLOS', 499.2e6, 6489.6e6, 'pulse', 'leading', ...
    [10 15 20 25], [10 50 100], svParams('industrial_nlos'));
cases(end+1) = mkCase('uwb_tunnel', 'DWM3000', 'TUNNEL', 499.2e6, 6489.6e6, 'pulse', 'leading', ...
    [10 15 20 25], [30 75 150], svParams('tunnel'));

% All four SX1280 LoRa bandwidths, LOS and NLOS. 406 kHz is the setting
% Robinson's published ranging sketches use, so that pair is the one with a
% hardware measurement to check against; 1625 kHz is the widest the part
% offers.
cases(end+1) = mkCase('sx1280_203k_los',   'SX1280', 'LOS',  203e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('outdoor_los'));
cases(end+1) = mkCase('sx1280_203k_nlos',  'SX1280', 'NLOS', 203e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('urban_nlos'));
cases(end+1) = mkCase('sx1280_406k_los',   'SX1280', 'LOS',  406e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('outdoor_los'));
cases(end+1) = mkCase('sx1280_406k_nlos',  'SX1280', 'NLOS', 406e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('urban_nlos'));
cases(end+1) = mkCase('sx1280_812k_los',   'SX1280', 'LOS',  812e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('outdoor_los'));
cases(end+1) = mkCase('sx1280_812k_nlos',  'SX1280', 'NLOS', 812e3,  2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('urban_nlos'));
cases(end+1) = mkCase('sx1280_1600k_los',  'SX1280', 'LOS',  1625e3, 2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('outdoor_los'));
cases(end+1) = mkCase('sx1280_1600k_nlos', 'SX1280', 'NLOS', 1625e3, 2450e6, 'chirp', 'peak', ...
    [10 15 20 25], [50 150 250], svParams('urban_nlos'));
end

function c = mkCase(name, radio, condition, bw, fc, waveform, estimator, snrDb, ranges, channel)
c = struct('name', name, 'radio', radio, 'condition', condition, ...
    'bandwidthHz', bw, 'carrierHz', fc, 'waveform', waveform, ...
    'estimator', estimator, 'snrDb', snrDb, 'trueRangeM', ranges, 'channel', channel);
end

function p = svParams(kind)
%SVPARAMS Cluster-based multipath parameters, Saleh-Valenzuela style.
%
% Cluster arrival rate, ray arrival rate, cluster and ray decay constants,
% a Rician K factor, and how much the direct path is attenuated.
%
% The K factor is what separates line of sight from the rest, and leaving
% it out was a real error in the first version of this file. Without a
% dominant direct path an early reflection can outrank it by chance, the
% leading-edge detector locks to whichever crossed threshold first, and
% 499.2 MHz of UWB came out worse than 406 kHz of narrowband LoRa. That is
% backwards: a thousand times the bandwidth is a thousand times the timing
% resolution. With K set, the ordering is right.
%
% NLOS and tunnel entries also carry a first-path attenuation, which is what
% turns a timing problem into a bias: when the direct path is weaker than a
% reflection, a detector reports the reflection's longer path.
%
% Figures follow the shape of the IEEE 802.15.4a channel models rather than
% reproducing any one of them exactly, and are this project's parameters.

switch kind
    case 'industrial_los'
        p = struct('clusterRate', 0.0048e9, 'rayRate', 1.13e9, ...
            'clusterDecayS', 17e-9, 'rayDecayS', 6.0e-9, ...
            'firstPathAttenDb', 0, 'riceanKDb', 12, ...
            'nClusters', 4, 'raysPerCluster', 12, ...
            'excessDelaySpreadS', 40e-9);
    case 'industrial_nlos'
        p = struct('clusterRate', 0.0048e9, 'rayRate', 1.13e9, ...
            'clusterDecayS', 27e-9, 'rayDecayS', 10.0e-9, ...
            'firstPathAttenDb', 9, 'riceanKDb', -6, ...
            'nClusters', 6, 'raysPerCluster', 16, ...
            'excessDelaySpreadS', 90e-9);
    case 'tunnel'
        % A bore guides the signal: strong late arrivals from the walls,
        % long delay spread, direct path still present but not dominant.
        p = struct('clusterRate', 0.008e9, 'rayRate', 2.0e9, ...
            'clusterDecayS', 40e-9, 'rayDecayS', 14.0e-9, ...
            'firstPathAttenDb', 4, 'riceanKDb', 0, ...
            'nClusters', 6, 'raysPerCluster', 20, ...
            'excessDelaySpreadS', 120e-9);
    case 'outdoor_los'
        p = struct('clusterRate', 0.0033e9, 'rayRate', 0.4e9, ...
            'clusterDecayS', 60e-9, 'rayDecayS', 20.0e-9, ...
            'firstPathAttenDb', 0, 'riceanKDb', 12, ...
            'nClusters', 3, 'raysPerCluster', 8, ...
            'excessDelaySpreadS', 200e-9);
    case 'urban_nlos'
        p = struct('clusterRate', 0.0033e9, 'rayRate', 0.4e9, ...
            'clusterDecayS', 90e-9, 'rayDecayS', 30.0e-9, ...
            'firstPathAttenDb', 11, 'riceanKDb', -6, ...
            'nClusters', 5, 'raysPerCluster', 12, ...
            'excessDelaySpreadS', 400e-9);
    otherwise
        error('yerkon:badChannel', 'Unknown channel kind %s', kind);
end
end

% =====================================================================
% One trial
% =====================================================================

function errorM = oneTrial(cs, snrDb, trueRangeM)
%ONETRIAL Transmit, propagate, detect, and report the ranging error.

c = 299792458;
% Oversample well past Nyquist so the leading edge is not quantised by the
% sample grid; the estimator interpolates, but a coarse grid still biases.
fs = 8 * cs.bandwidthHz;

% A known lead-in, so the correlation peak never sits against the start of
% the buffer. Without it a narrowband case is degenerate: at 1.6 MHz the
% correlation peak is about 600 ns wide while 50 m of propagation is only
% 170 ns, so the estimate collapses onto the buffer edge and every trial
% returns the same number.
referenceDelayS = 20 / cs.bandwidthHz;
totalDelayS = referenceDelayS + trueRangeM / c;

tx = makeWaveform(cs, fs);

[tapDelaysS, tapGains] = makeChannel(cs.channel, cs.bandwidthHz);
% The direct path sits at the true delay; every other tap arrives later.
tapDelaysS = tapDelaysS + totalDelayS;

outLen = numel(tx) + ceil(max(tapDelaysS) * fs) + 128;
rx = applyChannel(tx, tapDelaysS, tapGains, fs, outLen);
rx = addNoise(rx, snrDb);

estimatedDelayS = estimateToa(rx, tx, fs, cs.estimator);
errorM = (estimatedDelayS - referenceDelayS) * c - trueRangeM;
end

function w = makeWaveform(cs, fs)
%MAKEWAVEFORM The transmitted signal, at complex baseband.
switch cs.waveform
    case 'pulse'
        % UWB: a short Gaussian pulse whose spectrum matches the channel
        % bandwidth. Timing resolution scales with bandwidth, which is why
        % 500 MHz gives centimetres and 1.6 MHz gives metres.
        tp = 1 / cs.bandwidthHz;
        span = 4 * tp;
        t = -span:1/fs:span;
        w = exp(-(t.^2) / (2 * (tp / 2.5)^2));
        w = w(:) / norm(w);
    case 'chirp'
        % SX1280 ranging uses a LoRa chirp. Sweep the full bandwidth over
        % one symbol; a longer symbol buys processing gain, not resolution.
        symbolTime = 64 / cs.bandwidthHz;
        t = (0:1/fs:symbolTime).';
        k = cs.bandwidthHz / symbolTime;
        w = exp(1j * pi * (k * t.^2 - cs.bandwidthHz * t));
        w = w / norm(w);
    otherwise
        error('yerkon:badWaveform', 'Unknown waveform %s', cs.waveform);
end
end

function [delaysS, gains] = makeChannel(p, bandwidthHz)
%MAKECHANNEL Draw one realisation of the cluster-based multipath channel.
delaysS = [];
gains = [];

clusterDelay = 0;
for ci = 1:p.nClusters
    if ci > 1
        clusterDelay = clusterDelay + exprnd_(1 / p.clusterRate);
    end
    rayDelay = 0;
    for ri = 1:p.raysPerCluster
        if ri > 1
            rayDelay = rayDelay + exprnd_(1 / p.rayRate);
        end
        tau = clusterDelay + rayDelay;
        if tau > p.excessDelaySpreadS
            continue
        end
        if tau == 0
            continue    % the direct path is placed separately below
        end
        power = exp(-clusterDelay / p.clusterDecayS) * exp(-rayDelay / p.rayDecayS);
        amplitude = sqrt(power / 2) * (randn + 1j * randn);
        delaysS(end+1) = tau;             %#ok<AGROW>
        gains(end+1) = amplitude;         %#ok<AGROW>
    end
end

% Normalise the diffuse part, then add the direct path at the strength the
% Rician K factor calls for. In line of sight the direct path is
% deterministic and dominant; in NLOS it is weak and attenuated.
diffusePower = sum(abs(gains).^2);
if diffusePower > 0
    gains = gains / sqrt(diffusePower);
end
directGain = sqrt(10^(p.riceanKDb / 10)) * 10^(-p.firstPathAttenDb / 20);
delaysS = [0, delaysS];
gains = [directGain, gains];

% Total received power is then independent of how many taps the draw
% produced; SNR is set separately below.
gains = gains / norm(gains);

% Taps closer together than the waveform can resolve are not separable, and
% pretending otherwise would overstate what a detector can do.
minSeparation = 1 / (4 * bandwidthHz);
[delaysS, order] = sort(delaysS);
gains = gains(order);
keep = [true, diff(delaysS) > minSeparation];
delaysS = delaysS(keep);
gains = gains(keep);
end

function rx = applyChannel(tx, delaysS, gains, fs, outLen)
%APPLYCHANNEL Sum delayed, scaled copies with sub-sample delay.
rx = zeros(outLen, 1);
for k = 1:numel(delaysS)
    shiftSamples = delaysS(k) * fs;
    contribution = fracDelay(tx, shiftSamples, outLen);
    rx = rx + gains(k) * contribution;
end
end

function y = fracDelay(x, shiftSamples, outLen)
%FRACDELAY Delay a signal by a non-integer number of samples.
%
% Done in the frequency domain so the sub-sample part is exact rather than
% rounded to the sample grid; rounding here would put a floor on the
% measured accuracy that the radio does not actually have.
nfft = 2^nextpow2(outLen + numel(x));
X = fft(x, nfft);
f = (0:nfft-1).' / nfft;
f(f > 0.5) = f(f > 0.5) - 1;
X = X .* exp(-1j * 2 * pi * f * shiftSamples);
y = ifft(X);
y = y(1:outLen);
if isreal(x)
    y = real(y);
end
end

function rx = addNoise(rx, snrDb)
%ADDNOISE Add noise at a stated SNR, referenced to the signal peak.
%
% Not to the buffer average. The buffer is mostly empty either side of the
% arrival, so averaging over it puts the noise far below what the SNR asked
% for, and the first version of this file did exactly that: results barely
% moved between 10 dB and 25 dB because the requested SNR was not the one
% being applied.
signalPower = max(abs(rx).^2);
if signalPower <= 0
    return
end
noisePower = signalPower / (10^(snrDb / 10));
if isreal(rx)
    rx = rx + sqrt(noisePower) * randn(size(rx));
else
    rx = rx + sqrt(noisePower / 2) * (randn(size(rx)) + 1j * randn(size(rx)));
end
end

function delayS = estimateToa(rx, tx, fs, estimator)
%ESTIMATETOA Time of arrival from the matched-filter output.
%
% Two estimators, because the two radios genuinely work differently.
%
% 'leading' searches back from the peak for the first arrival above a
% threshold. The strongest return is often a reflection, and locking to it
% is how multipath becomes a positive range bias; a wideband receiver can
% see the direct path separately and a DW-series chip does exactly this.
%
% 'peak' takes the strongest return. A 1.6 MHz correlation peak is
% hundreds of metres wide, so there is no earlier arrival to find: the
% paths are not separable at that bandwidth. What is left is a constant
% offset, which is what per-unit ranging calibration removes.

nfft = 2^nextpow2(numel(rx) + numel(tx));
corr = ifft(fft(rx, nfft) .* conj(fft(tx, nfft)));
mag = abs(corr(1:numel(rx)));

[peakValue, peakIdx] = max(mag);
noiseFloor = median(mag(1:max(floor(0.05 * numel(mag)), 16)));

if strcmp(estimator, 'peak')
    leadingIdx = peakIdx;
else
    threshold = max(0.35 * peakValue, 6 * noiseFloor);
    leadingIdx = peakIdx;
    searchBack = max(peakIdx - ceil(0.3 * numel(mag)), 2);
    for i = peakIdx:-1:searchBack
        if mag(i) < threshold
            leadingIdx = i + 1;
            break
        end
        leadingIdx = i;
    end
end

% Parabolic interpolation around the detected sample, so the estimate is
% not quantised to the sample grid.
if leadingIdx > 1 && leadingIdx < numel(mag)
    y0 = mag(leadingIdx - 1); y1 = mag(leadingIdx); y2 = mag(leadingIdx + 1);
    denom = (y0 - 2 * y1 + y2);
    if denom ~= 0
        offset = 0.5 * (y0 - y2) / denom;
        offset = max(min(offset, 1), -1);
    else
        offset = 0;
    end
else
    offset = 0;
end

delaySamples = (leadingIdx - 1) + offset;
delayS = delaySamples / fs;
end

% =====================================================================
% Small helpers, so no toolbox is required
% =====================================================================

function x = exprnd_(mu)
x = -mu * log(rand);
end

function v = prctileSimple(x, p)
x = sort(x(:));
if isempty(x); v = NaN; return; end
idx = max(min(ceil(p / 100 * numel(x)), numel(x)), 1);
v = x(idx);
end

function rngSeed(seed)
try
    rng(seed);
catch
    randn('state', seed); %#ok<RAND>
    rand('state', seed);  %#ok<RAND>
end
end

function opts = parseOptions(varargin)
opts = struct('Trials', 200, 'Seed', 42, 'Cases', {{}}, 'Parallel', false);
for k = 1:2:numel(varargin)
    name = varargin{k};
    value = varargin{k+1};
    switch lower(name)
        case 'trials'; opts.Trials = value;
        case 'seed';   opts.Seed = value;
        case 'cases';  opts.Cases = value;
        case 'parallel'; opts.Parallel = logical(value);
        otherwise
            error('yerkon:badOption', 'Unknown option %s', name);
    end
end
end
