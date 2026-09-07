function yerkon_imu_char(varargin)
%YERKON_IMU_CHAR Characterise a BNO085-class IMU with MathWorks' own model.
%
%   The fusion filter currently uses acceleration noise and bias figures
%   this project chose (0.08 and 0.03 m/s^2). They decide how far the
%   estimate drifts between range fixes, which in a tunnel is the whole
%   result, and they were not taken from anything.
%
%   This replaces them with a characterisation of a properly specified
%   sensor model. imuSensor implements the stochastic terms a real MEMS
%   unit has, including bias instability as a random walk rather than the
%   constant offset the Python model assumes. What comes out is the
%   quantity the filter actually needs: how far a receiver drifts on
%   inertial data alone over the length of a realistic outage.
%
%   Requires Sensor Fusion and Tracking Toolbox (imuSensor).
%
%   Usage:
%       cd matlab
%       yerkon_imu_char
%       yerkon_imu_char('Runs', 200)
%
%   Output:
%       export/yerkon_imu_drift.csv    free-inertial drift vs outage length
%       export/yerkon_imu_params.csv   the sensor parameters used
%
%   Send both files back.

opts = parseOptions(varargin{:});

if ~(exist('imuSensor', 'file') || exist('imuSensor', 'builtin'))
    error('yerkon:noImuSensor', ...
        ['imuSensor not found. It comes with Sensor Fusion and Tracking ' ...
         'Toolbox or Navigation Toolbox; run yerkon_env_check to confirm.']);
end

outDir = fullfile(fileparts(mfilename('fullpath')), 'export');
if ~exist(outDir, 'dir'); mkdir(outDir); end

fs = opts.SampleRateHz;
params = bno085ClassParameters();

fprintf('YERKON IMU characterisation\n');
fprintf('  sample rate : %g Hz\n', fs);
fprintf('  runs        : %d\n', opts.Runs);
fprintf('  outages     : %s s\n', mat2str(opts.OutageSeconds));

% ---- write the parameters actually used, so the numbers are traceable ----
fidP = fopen(fullfile(outDir, 'yerkon_imu_params.csv'), 'w');
fprintf(fidP, 'parameter,value,unit\n');
fprintf(fidP, 'sample_rate,%g,Hz\n', fs);
fprintf(fidP, 'accel_noise_density,%g,(m/s^2)/sqrt(Hz)\n', params.accelNoiseDensity);
fprintf(fidP, 'accel_bias_instability,%g,m/s^2\n', params.accelBiasInstability);
fprintf(fidP, 'accel_random_walk,%g,(m/s^2)*sqrt(Hz)\n', params.accelRandomWalk);
fprintf(fidP, 'gyro_noise_density,%g,(rad/s)/sqrt(Hz)\n', params.gyroNoiseDensity);
fprintf(fidP, 'gyro_bias_instability,%g,rad/s\n', params.gyroBiasInstability);
fprintf(fidP, 'gyro_random_walk,%g,(rad/s)*sqrt(Hz)\n', params.gyroRandomWalk);
fclose(fidP);

% ---- build the sensor ----
imu = imuSensor('accel-gyro', 'SampleRate', fs);
imu.Accelerometer = accelparams( ...
    'NoiseDensity', params.accelNoiseDensity, ...
    'BiasInstability', params.accelBiasInstability, ...
    'RandomWalk', params.accelRandomWalk, ...
    'ConstantBias', params.accelConstantBias);
imu.Gyroscope = gyroparams( ...
    'NoiseDensity', params.gyroNoiseDensity, ...
    'BiasInstability', params.gyroBiasInstability, ...
    'RandomWalk', params.gyroRandomWalk, ...
    'ConstantBias', params.gyroConstantBias);

maxOutage = max(opts.OutageSeconds);
n = round(maxOutage * fs) + 1;

% A vehicle holding a steady speed through a gentle bend: the same motion
% the Python tracks use, so the drift figure applies to that case rather
% than to a stationary bench test.
speed = opts.SpeedMps;
turnRateRad = deg2rad(opts.TurnRateDegPerSec);
trueAccel = zeros(n, 3);
trueAccel(:, 2) = speed * turnRateRad;      % centripetal, body frame
trueAngVel = zeros(n, 3);
trueAngVel(:, 3) = turnRateRad;

drift = zeros(opts.Runs, numel(opts.OutageSeconds));
velErr = zeros(opts.Runs, numel(opts.OutageSeconds));

fprintf('\nrunning');
for r = 1:opts.Runs
    reset(imu);
    [measAccel, ~] = imu(trueAccel, trueAngVel);

    % Free inertial: integrate what the sensor reported against what was
    % true. No aiding, which is exactly the situation during a range gap.
    accelError = measAccel - trueAccel;
    velocityError = cumsum(accelError, 1) / fs;
    positionError = cumsum(velocityError, 1) / fs;

    for k = 1:numel(opts.OutageSeconds)
        idx = min(round(opts.OutageSeconds(k) * fs) + 1, n);
        drift(r, k) = norm(positionError(idx, :));
        velErr(r, k) = norm(velocityError(idx, :));
    end
    if mod(r, max(round(opts.Runs / 20), 1)) == 0
        fprintf('.');
    end
end
fprintf(' done\n\n');

fidD = fopen(fullfile(outDir, 'yerkon_imu_drift.csv'), 'w');
fprintf(fidD, ['outage_s,runs,position_drift_p50_m,position_drift_p95_m,'...
    'position_drift_max_m,velocity_error_p50_m_s,velocity_error_p95_m_s\n']);

fprintf('%8s %12s %12s %12s\n', 'outage', 'drift p50', 'drift p95', 'vel p95');
for k = 1:numel(opts.OutageSeconds)
    d = drift(:, k);
    v = velErr(:, k);
    fprintf(fidD, '%.2f,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n', ...
        opts.OutageSeconds(k), opts.Runs, ...
        prctileSimple(d, 50), prctileSimple(d, 95), max(d), ...
        prctileSimple(v, 50), prctileSimple(v, 95));
    fprintf('%7.2fs %11.4f m %11.4f m %10.4f m/s\n', opts.OutageSeconds(k), ...
        prctileSimple(d, 50), prctileSimple(d, 95), prctileSimple(v, 95));
end
fclose(fidD);

fprintf('\nWrote %s\n', fullfile(outDir, 'yerkon_imu_drift.csv'));
fprintf('Wrote %s\n', fullfile(outDir, 'yerkon_imu_params.csv'));
fprintf('\nSend both CSV files back.\n');
end

function p = bno085ClassParameters()
%BNO085CLASSPARAMETERS Stochastic terms for a consumer MEMS unit.
%
% The BNO085 datasheet specifies fused orientation accuracy rather than
% raw Allan-variance terms, so these are typical figures for the class of
% MEMS part inside it. They are this project's numbers, not the vendor's,
% and the parameter file records them so the drift result can be re-derived
% if better figures turn up.

p.accelNoiseDensity     = 0.0016;   % (m/s^2)/sqrt(Hz), ~160 ug/sqrt(Hz)
p.accelBiasInstability  = 0.0008;   % m/s^2
p.accelRandomWalk       = 0.0004;   % (m/s^2)*sqrt(Hz)
p.accelConstantBias     = [0.02 0.02 0.02];

p.gyroNoiseDensity      = 1.2e-4;   % (rad/s)/sqrt(Hz), ~0.007 dps/sqrt(Hz)
p.gyroBiasInstability   = 2.0e-5;   % rad/s
p.gyroRandomWalk        = 1.0e-5;   % (rad/s)*sqrt(Hz)
p.gyroConstantBias      = [1e-3 1e-3 1e-3];
end

function v = prctileSimple(x, p)
x = sort(x(:));
if isempty(x); v = NaN; return; end
idx = max(min(ceil(p / 100 * numel(x)), numel(x)), 1);
v = x(idx);
end

function opts = parseOptions(varargin)
opts = struct('Runs', 100, 'SampleRateHz', 100, ...
    'OutageSeconds', [0.2 0.5 1 2 5 10 30], ...
    'SpeedMps', 13.9, 'TurnRateDegPerSec', 2.5);
for k = 1:2:numel(varargin)
    switch lower(varargin{k})
        case 'runs';              opts.Runs = varargin{k+1};
        case 'sampleratehz';      opts.SampleRateHz = varargin{k+1};
        case 'outageseconds';     opts.OutageSeconds = varargin{k+1};
        case 'speedmps';          opts.SpeedMps = varargin{k+1};
        case 'turnratedegpersec'; opts.TurnRateDegPerSec = varargin{k+1};
        otherwise
            error('yerkon:badOption', 'Unknown option %s', varargin{k});
    end
end
end
