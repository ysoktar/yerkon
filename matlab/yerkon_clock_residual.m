function yerkon_clock_residual(out_dir)
% YERKON_CLOCK_RESIDUAL  Measure what a frequency-offset estimate leaves behind.
%
% Measures one default: clock.crystal.residual_ppm, currently 0,5 and the
% least supported number in the model. It decides whether single-sided
% two-way ranging works on the SX1280, because in that scheme the residual
% offset multiplies a sixteen-millisecond reply delay. At 0,5 ppm that is
% 1,20 m; at ten, uncorrected, it is 24,1 m.
%
% Method. Dechirping a LoRa up-chirp gives a beat at (offset - mu*tau);
% dechirping a down-chirp gives (offset + mu*tau). Their SUM is twice the
% frequency offset with the timing cancelled; their difference is the
% timing with the offset cancelled. Spectra are accumulated across the
% preamble before the peak is taken, because bin estimates are circular
% and averaging them arithmetically is wrong. A parabolic interpolation
% then gets below the 1587 Hz bin, which is 0,65 ppm on its own and would
% otherwise swamp the answer.
%
% The signal-to-noise axis is post-correlation, which is where the link
% budget lives: a link at the SX1280's -20 dB in-band threshold sits at
% +10 dB after the 30,1 dB despreading gain, and a close one at +50.
%
% Base MATLAB only. No toolboxes.
%
% Usage:
%   yerkon_clock_residual                 % writes .\out
%   yerkon_clock_residual('C:\path\out')

if nargin < 1 || isempty(out_dir); out_dir = fullfile(pwd, 'out'); end
if ~exist(out_dir, 'dir'); mkdir(out_dir); end

SF        = 10;            % spreading factor of the ranging mode
BW        = 1625e3;        % Hz, widest SX1280 LoRa bandwidth
CARRIER   = 2450e6;        % Hz
N         = 2^SF;
Tsym      = N / BW;        % 630 us
PREAMBLE  = 8;             % symbols accumulated before the peak is taken
DELAY_CH  = 3.7;           % a fractional timing offset, so the sum is earned
TRIALS    = 300;

snr_db      = 5:5:40;      % post-correlation, where links actually close
offsets_ppm = [2 5 10 20]; % crystal offsets to try

rng(20260910, 'twister');

reply_s = (12 + ceil(8*16/SF)) * Tsym + 300e-6;   % frame plus turnaround

fprintf('YERKON clock residual\n');
fprintf('  SF%d, BW %.0f kHz, symbol %.0f us, bin %.0f Hz = %.3f ppm\n', ...
        SF, BW/1e3, Tsym*1e6, BW/N, (BW/N)/CARRIER*1e6);
fprintf('  %d preamble symbols, %d trials, reply delay %.2f ms\n\n', ...
        PREAMBLE, TRIALS, reply_s*1e3);

k    = (0:N-1).';
up   = exp(1j*2*pi*( k.^2/(2*N) ));
down = conj(up);
up_d   = frac_delay(up,   DELAY_CH, N);
down_d = frac_delay(down, DELAY_CH, N);

rows = zeros(0, 5);

for oi = 1:numel(offsets_ppm)
    ppm = offsets_ppm(oi);
    cfo = ppm * 1e-6 * CARRIER;
    ramp = exp(1j*2*pi*cfo*k/BW);

    for si = 1:numel(snr_db)
        snr = snr_db(si);
        % Unit power per chip, and the FFT supplies the despreading gain,
        % so the chip-rate noise is N times the post-correlation figure.
        sigma = sqrt(10^(-snr/10) * N / 2);
        residual = zeros(TRIALS, 1);

        for t = 1:TRIALS
            acc_up = zeros(N, 1);
            acc_dn = zeros(N, 1);
            for p = 1:PREAMBLE
                n1 = sigma*(randn(N,1) + 1j*randn(N,1));
                n2 = sigma*(randn(N,1) + 1j*randn(N,1));
                acc_up = acc_up + abs(fft((up_d   .* ramp + n1) .* conj(up)));
                acc_dn = acc_dn + abs(fft((down_d .* ramp + n2) .* conj(down)));
            end
            bins = wrap_bins(interp_bin(acc_up) + interp_bin(acc_dn), N) / 2;
            estimated = bins * BW / N;
            residual(t) = abs(estimated - cfo) / CARRIER * 1e6;
        end

        rms_ppm = sqrt(mean(residual.^2));
        metres  = 0.5 * rms_ppm*1e-6 * reply_s * 299792458;

        rows(end+1, :) = [ppm snr rms_ppm metres reply_s]; %#ok<AGROW>
        fprintf('  %2d ppm in, SNR %+3d dB -> residual %8.4f ppm, %7.3f m\n', ...
                ppm, snr, rms_ppm, metres);
    end
end

path = fullfile(out_dir, 'clock_residual.csv');
write_csv(path, {'offset_ppm','snr_db','residual_ppm_rms','single_sided_error_m','reply_s'}, rows);

fprintf('\nWrote %s\n', path);
fprintf('This is additive noise only: no phase noise, no multipath, and no\n');
fprintf('drift during the exchange. A real part will be worse, so read the\n');
fprintf('answer as a floor rather than as the figure.\n');
fprintf('Send the file back and `yerkon calibrate` turns it into a default.\n');
end

% -------------------------------------------------------------------------

function y = frac_delay(x, chips, N)
% A fractional delay as a phase ramp in frequency. Circular, which is what
% a symbol-synchronous receiver sees anyway.
k = (0:N-1).';
y = ifft(fft(x) .* exp(-1j*2*pi*chips*k/N));
end

function b = interp_bin(magnitude)
% Peak bin with a parabolic correction, so the estimate is not quantised
% to the FFT bin.
N = numel(magnitude);
[~, index] = max(magnitude);
left  = magnitude(mod(index-2, N) + 1);
mid   = magnitude(index);
right = magnitude(mod(index,   N) + 1);
denom = left - 2*mid + right;
if denom == 0
    delta = 0;
else
    delta = 0.5 * (left - right) / denom;
    delta = max(min(delta, 0.5), -0.5);
end
b = (index - 1) + delta;      % zero-based
end

function d = wrap_bins(d, N)
d = mod(d + N/2, N) - N/2;
end

function write_csv(path, header, rows)
fid = fopen(path, 'w');
fprintf(fid, '%s\n', strjoin(header, ','));
for i = 1:size(rows, 1)
    fprintf(fid, '%.10g', rows(i,1));
    fprintf(fid, ',%.10g', rows(i,2:end));
    fprintf(fid, '\n');
end
fclose(fid);
end
