function yerkon_env_check()
%YERKON_ENV_CHECK Report what this MATLAB install can run.
%
%   Run this first. The ranging simulation is written in base MATLAB on
%   purpose and needs no toolbox, but knowing what is available decides
%   whether the IMU and channel models can be taken from MathWorks' own
%   implementations instead of hand-rolled ones.
%
%   Usage:
%       cd matlab
%       yerkon_env_check

fprintf('=== YERKON MATLAB environment ===\n');
fprintf('version      : %s\n', version);
fprintf('release      : %s\n', version('-release'));
fprintf('computer     : %s\n', computer);
fprintf('pwd          : %s\n', pwd);

% Ask MATLAB what is installed rather than guessing at licence feature
% names. An earlier version of this check called license('test', 'signal')
% and friends, which are ver() arguments and not licence features, so every
% toolbox came back missing while the functions in them were plainly there.
installed = ver;
names = {installed.Name};

fprintf('\ninstalled products (%d):\n', numel(names));
for k = 1:numel(names)
    fprintf('  %s  %s\n', names{k}, installed(k).Version);
end

wanted = {'Signal Processing Toolbox', 'Communications Toolbox', ...
    'Navigation Toolbox', 'Sensor Fusion and Tracking Toolbox', ...
    'Statistics and Machine Learning Toolbox', 'Phased Array System Toolbox', ...
    'Parallel Computing Toolbox'};

fprintf('\ntoolboxes this project could use:\n');
for k = 1:numel(wanted)
    present = any(strcmp(wanted{k}, names));
    fprintf('  [%s] %s\n', tern(present, 'YES', 'no '), wanted{k});
end

fprintf('\nfunctions the scripts may use:\n');
probe = {'gauspuls', 'xcorr', 'awgn', 'imuSensor', 'insfilterNonholonomic', ...
    'insfilterErrorState', 'gpsSensor', 'writematrix', 'randn'};
for k = 1:numel(probe)
    found = exist(probe{k}, 'file') || exist(probe{k}, 'builtin');
    fprintf('  [%s] %s\n', tern(found, 'YES', 'no '), probe{k});
end

fprintf('\nwrite test:\n');
outDir = fullfile(pwd, 'export');
if ~exist(outDir, 'dir'); mkdir(outDir); end
probeFile = fullfile(outDir, 'write_test.txt');
fid = fopen(probeFile, 'w');
if fid > 0
    fprintf(fid, 'ok\n');
    fclose(fid);
    delete(probeFile);
    fprintf('  [YES] can write to %s\n', outDir);
else
    fprintf('  [no ] cannot write to %s\n', outDir);
end

fprintf('\n=== end ===\n');
end

function out = tern(cond, a, b)
if cond
    out = a;
else
    out = b;
end
end
